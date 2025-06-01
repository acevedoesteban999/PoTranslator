from googletrans import Translator
import polib
import re
import asyncio
from pathlib import Path
from typing import List, Dict
from datetime import datetime

class POTranslator:
    def __init__(self, input_pot_file:str , batch_size: int = 20, delay: float = 1.0 ):
        """
        Inicializa el traductor con configuración de lotes y retardo
        
        Args:
            input_pot_file: Ruta al archivo .pot original
            batch_size: Número de textos a traducir en cada lote
            delay: Retardo entre lotes para evitar bloqueos
        """
        self.author_name = "POTRANSLATOR"
        self.author_email = "acevedoesteban999@gmail.com"
        self.plural_forms_map = {
            'es': 'nplurals=2; plural=(n != 1);',
            'en': 'nplurals=2; plural=(n != 1);',
            'pt': 'nplurals=2; plural=(n != 1);'
        }
        self.input_pot_file = input_pot_file
        self.batch_size = batch_size
        self.delay = delay
        self.translator = Translator()
        self.placeholder_regex = re.compile(
            r'({[^}]+}|%[sdf]|%\(\w+\)[sdf]|%\d+\$[sdf]|\[[^\]]+\])')
    
        self.pofile = polib.pofile(input_pot_file)
        self.entries = [entry for entry in self.pofile if entry.msgid and not entry.msgstr]
        self.source_texts = [entry.msgid for entry in self.entries]
        self.pot_metadata = self._extract_pot_metadata(self.pofile)
    
    def _extract_pot_metadata(self, pot_file: polib.POFile) -> dict:
        """Extrae metadatos relevantes del archivo .pot original"""
        metadata = {}
        pot_metadata = pot_file.metadata
        
        # Mapeo de campos a preservar
        preserve_fields = [
            'Project-Id-Version',
            'Report-Msgid-Bugs-To',
            'POT-Creation-Date',
            'Content-Type',
            'Content-Transfer-Encoding'
        ]
        
        for field in preserve_fields:
            if field in pot_metadata:
                metadata[field] = pot_metadata[field]
        
        return metadata

    def _generate_po_metadata(self, pot_metadata: dict, lang_code: str) -> dict:
        """Genera metadatos para el archivo .PO basado en el .pot"""
        lang = lang_code.split('_')[0].lower()
        
        # Campos que siempre se actualizan
        new_metadata = {
            'PO-Revision-Date': datetime.now().strftime('%Y-%m-%d %H:%M%z'),
            'Last-Translator': f'{self.author_name} <{self.author_email}>',
            'Language-Team': f'{self.author_name} <{self.author_email}>',
            'Language': lang_code,
            # 'MIME-Version': '1.0',
            # 'X-Generator': 'Odoo Localization Tool'
        }
        
        # Añadir plural forms si está definido para el idioma
        if lang in self.plural_forms_map:
            new_metadata['Plural-Forms'] = self.plural_forms_map[lang]
        
        # Combinar con metadatos originales (los originales tienen prioridad)
        return {**new_metadata, **pot_metadata}

    def _prepare_texts(self, texts: List[str]) -> tuple:
        """
        Prepara textos para traducción: extrae placeholders y crea versiones temporales
        
        Returns:
            tuple: (textos_preparados, lista_de_placeholders_por_texto)
        """
        prepared_texts = []
        all_placeholders = []
        
        for text in texts:
            placeholders = self.placeholder_regex.findall(text)
            temp_text = text
            for i, ph in enumerate(placeholders):
                temp_text = temp_text.replace(ph, f'__PL_{i}__')
            prepared_texts.append(temp_text)
            all_placeholders.append(placeholders)
            
        return prepared_texts, all_placeholders

    def _restore_placeholders(self, translated_texts: List[str], all_placeholders: List[List[str]]) -> List[str]:
        """
        Restaura los placeholders en los textos traducidos
        """
        restored_texts = []
        for text, placeholders in zip(translated_texts, all_placeholders):
            for i, ph in enumerate(placeholders):
                text = text.replace(f'__PL_{i}__', ph)
            restored_texts.append(text)
        return restored_texts

    async def _translate_batch(self, texts: List[str], src_lang: str, dest_lang: str) -> List[str]:
        """
        Traduce un lote de textos
        """
        if src_lang == dest_lang:
            return texts
            
        try:
            # Preparar textos (manejo de placeholders)
            prepared_texts, all_placeholders = self._prepare_texts(texts)
            
            # Traducir
            translations = await self.translator.translate(prepared_texts, src=src_lang, dest=dest_lang)
            
            # Extraer textos traducidos
            translated_texts = [t.text for t in translations]
            
            # Restaurar placeholders
            restored_texts = self._restore_placeholders(translated_texts, all_placeholders)
            
            return restored_texts
        except Exception as e:
            print(f"Error en lote: {str(e)}")
            return [""] * len(texts)

    async def translate_po_file(
        self,
        output_files: Dict[str, str],  # {'es': 'ruta/es.po', 'fr': 'ruta/fr.po'}
        src_lang: str = 'auto',
    ):
        """
        Traduce un archivo .PO a múltiples idiomas
        
        Args:
            output_files: Diccionario con {idioma: ruta_de_salida}
            src_lang: Idioma origen (default 'auto')
        """
        # Cargar archivo PO
        
        
        # Procesar cada idioma de destino
        for dest_lang, output_file in output_files.items():
            print(f"\nIniciando traducción a {dest_lang}...")
            
            # Crear copia del archivo PO para este idioma
            lang_pofile = polib.pofile(self.input_pot_file)
            po_metadata = self._generate_po_metadata(self.pot_metadata, dest_lang)
            lang_pofile.metadata = po_metadata
            lang_entries = self.entries
            
            # Procesar por lotes
            for i in range(0, len(self.source_texts), self.batch_size):
                batch = self.source_texts[i:i + self.batch_size]
                print(f"Procesando lote {i//self.batch_size + 1}/{(len(self.source_texts)-1)//self.batch_size + 1}")
                
                # Traducir lote
                translated_batch = await self._translate_batch(batch, src_lang, dest_lang)
                
                # Actualizar entradas
                for j, translated_text in enumerate(translated_batch):
                    entry_index = i + j
                    if entry_index < len(lang_entries):
                        lang_entries[entry_index].msgstr = translated_text
                
                # Pequeña pausa entre lotes
                if i + self.batch_size < len(self.source_texts):
                    await asyncio.sleep(self.delay)
            
            # Guardar archivo para este idioma
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            lang_pofile.save(output_file)
            print(f"Traducción a {dest_lang} completada. Archivo guardado en: {output_file}")


if __name__ == "__main__":
    translator = POTranslator(input_pot_file = 'config_website.pot',batch_size=100, delay=1)
    
    SRC_LANG = 'es'  # Idioma origen
    OUTPUT_FILES = {
        'es': 'es.po',    # Español
        'en': 'en.po',    # Francés
        'pt': 'pt.po',     # Portugués
    }
    
    asyncio.run(
        translator.translate_po_file(
            output_files=OUTPUT_FILES,
            src_lang=SRC_LANG,
        )
    )