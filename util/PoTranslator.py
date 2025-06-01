from googletrans import Translator
import polib
import re
import asyncio
from pathlib import Path
from typing import List, Dict
from datetime import datetime
import shutil

class PoTranslator:
    def __init__(self, input_pot_file:str , batch_size: int = 20, delay: float = 1.0 , output_in_source_dir = False):
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
        self.output_in_source_dir = output_in_source_dir
        self.input_pot_file = input_pot_file
        self.batch_size = batch_size
        self.delay = delay
        self.translator = Translator()
        self.placeholder_regex = re.compile(
            r'({[^}]+}|%[sdf]|%\(\w+\)[sdf]|%\d+\$[sdf]|\[[^\]]+\])')
    
        pot_pofile = polib.pofile(input_pot_file)
        self.source_texts = [entry.msgid for entry in pot_pofile if entry.msgid and not entry.msgstr]
        self.pot_metadata = self._extract_pot_metadata(pot_pofile)
    
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
                text = text.replace(f'__PL_{i}__', ph).replace(f'__pl_{i}__', ph)
            restored_texts.append(text)
        return restored_texts

    async def _translate_batch(self, texts: List[str], dest_lang: str) -> List[str]:
        """
        Traduce un lote de textos
        """
        
        # Preparar textos (manejo de placeholders)
        prepared_texts, all_placeholders = self._prepare_texts(texts)
        
        # Traducir
        translations = await self.translator.translate(prepared_texts, dest=dest_lang)
        
        # Extraer textos traducidos
        translated_texts = [t.text for t in translations]
        
        # Restaurar placeholders
        restored_texts = self._restore_placeholders(translated_texts, all_placeholders)
        
        return restored_texts
        

    async def translate_po_file(
        self,
        dest_lang: str, 
    ):
        """
        Traduce un archivo .PO a múltiples idiomas
        
        """
    
        # Procesar cada idioma de destino
        # Crear copia del archivo PO para este idioma
        lang_pofile = polib.pofile(self.input_pot_file)
        lang_pofile.metadata = self._generate_po_metadata(self.pot_metadata, dest_lang)
        
        # Procesar por lotes
        for i in range(0, len(self.source_texts), self.batch_size):
            batch = self.source_texts[i:i + self.batch_size]
            print(f"{dest_lang} {i//self.batch_size + 1}/{(len(self.source_texts)-1)//self.batch_size + 1}")
            
            # Traducir lote
            translated_batch = await self._translate_batch(batch, dest_lang)
            
            # Actualizar entradas
            for j, translated_text in enumerate(translated_batch):
                entry_index = i + j
                if entry_index < len(lang_pofile):
                    lang_pofile[entry_index].msgstr = translated_text
            
            # Pequeña pausa entre lotes
            if i + self.batch_size < len(self.source_texts):
                await asyncio.sleep(self.delay)
        
        # Guardar archivo para este idioma
        pot_name = Path(self.input_pot_file).stem  # Obtiene el nombre sin extensión
        if self.output_in_source_dir:
            output_dir = Path(self.input_pot_file).parent
        else:
            output_dir = Path(f"translations/{pot_name}")
            if not output_dir.exists():
                output_dir.mkdir(parents=True)  
        
        output_file = output_dir / f"{dest_lang}.po"
        
        lang_pofile.save(output_file)
