from googletrans import Translator
import polib
import re
import asyncio
from pathlib import Path
from typing import List, Dict
from datetime import datetime
import shutil

class PoTranslator:
    def __init__(self, batch_size: int = 20, delay: float = 1.0 , log_funct = None):
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
        self.batch_size = batch_size
        self.log_funct = log_funct or print
        self.delay = delay
        self.translator = Translator()
        self.placeholder_regex = re.compile(
            r'({[^}]+}|%[sdf]|%\(\w+\)[sdf]|%\d+\$[sdf]|\[[^\]]+\])')
    
        
        
    

    def _generate_po_metadata(self, lang_code: str,pot_file_addr: str) -> dict:
        """Genera metadatos para el archivo .PO basado en el .pot"""
        
        pot_file = polib.pofile(pot_file_addr)
        pot_metadata = {}
        
        # Mapeo de campos a preservar
        preserve_fields = [
            'Project-Id-Version',
            'Report-Msgid-Bugs-To',
            'POT-Creation-Date',
            'Content-Type',
            'Content-Transfer-Encoding'
        ]
        
        for field in preserve_fields:
            if field in pot_file.metadata:
                pot_metadata[field] = pot_file.metadata[field]
        
        
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
            placeholders_list = self.placeholder_regex.findall(text)
            placeholders = set(placeholders_list)
            temp_text = text
            for i, ph in enumerate(placeholders):
                temp_text = temp_text.replace(ph, f'__{i}__')
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
                text = text.replace(f'__{i}__', ph)
            restored_texts.append(text)
        return restored_texts

    async def _translate_batch(self, texts: List[str], dest_lang: str ,pot_file_addr:str) -> List[str]:
        """
        Traduce un lote de textos, verificando si ya existen traducciones en el archivo .po de salida.
        """
        # Preparar textos (manejo de placeholders)
        prepared_texts, all_placeholders = self._prepare_texts(texts)

        # Verificar si ya existe un archivo .po para el idioma en la salida
        texts_to_translate = prepared_texts
        
        existing_translations = {}
        parent_path = Path(pot_file_addr).parent
        if parent_path:
            file_path = parent_path / f"{dest_lang}.po"
            if file_path:
                po_file = polib.pofile( str(file_path) ) 
                for entry in po_file:
                    if entry.msgid and entry.msgstr:
                        existing_translations[entry.msgid] = entry.msgstr
        self.log_funct(f"{len(existing_translations)} traducciones existentes")
        texts_to_translate = [text for text in prepared_texts if text not in existing_translations]
            
        
        translations = await self.translator.translate(texts_to_translate, dest=dest_lang)
        self.log_funct(f"{len(translations)} traducciones online")
            
        # Combinar traducciones existentes con nuevas traducciones
        translated_texts = []
        for text in prepared_texts:
            try:
                if text in existing_translations:
                    translated_texts.append(existing_translations[text])
                else:
                    if translations:
                        translated_texts.append(translations.pop(0).text)
            except:
                pass
        restored_texts = self._restore_placeholders(translated_texts, all_placeholders)

        return restored_texts
        

    async def translate_po_file(
        self,
        new_po_file:polib.POFile,
        pot_file_addr:str,
        dest_lang: str, 
    ):
        source_texts = [entry.msgid for entry in new_po_file if entry.msgid and not entry.msgstr]
        for i in range(0, len(source_texts), self.batch_size):
            batch = source_texts[i:i + self.batch_size]
            print(f"{dest_lang} {i//self.batch_size + 1}/{(len(source_texts)-1)//self.batch_size + 1}")
            
            translated_batch = await self._translate_batch(batch, dest_lang,pot_file_addr)
            
            for j, translated_text in enumerate(translated_batch):
                entry_index = i + j
                if entry_index < len(new_po_file):
                    new_po_file[entry_index].msgstr = translated_text
            
            if i + self.batch_size < len(source_texts):
                await asyncio.sleep(self.delay)
        
        
        
        
        
