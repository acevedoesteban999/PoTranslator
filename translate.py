from googletrans import Translator
import polib
import re
import time
from pathlib import Path
import asyncio

async def translate_po_with_google(
    input_file: str,
    output_file: str,
    dest_lang: str,
    src_lang: str = 'auto',
    delay: float = 0.5  # Delay entre peticiones para evitar bloqueos
):
    """
    Traduce un archivo .PO usando Google Translate (API no oficial)

    Args:
        input_file: Ruta al archivo .PO de entrada
        output_file: Ruta donde guardar el archivo traducido
        dest_lang: Código de idioma objetivo (ej. 'es', 'fr', 'de')
        src_lang: Código de idioma origen (default 'auto' para detección autom)
        delay: Segundos de espera entre traducciones (para evitar bloqueos)
    """
    async def _translate(text, src, dest):
        translator = Translator()
        translated = await translator.translate(text, src=src, dest=dest)
        return translated.text

    # Cargar el archivo .PO
    pofile = polib.pofile(input_file)

    # Expresión regular para placeholders
    placeholder_regex = re.compile(
        r'({[^}]+}|%[sdf]|%\(\w+\)[sdf]|%\d+\$[sdf]|\[[^\]]+\])')

    for entry in pofile:
        if entry.msgid and not entry.msgstr:
            try:
                source_text = entry.msgid

                # 1. Extraer y reemplazar placeholders
                placeholders = placeholder_regex.findall(source_text)
                temp_text = source_text
                for i, ph in enumerate(placeholders):
                    temp_text = temp_text.replace(ph, f'__PL_{i}__')

                # 2. Traducir el texto
                translated_text = await _translate(temp_text, src_lang, dest_lang)
                
                # 3. Restaurar placeholders
                for i, ph in enumerate(placeholders):
                    translated_text = translated_text.replace(f'__PL_{i}__', ph)

                entry.msgstr = translated_text
                print(
                    f"Traducido: {source_text[:50]}... → {translated_text[:50]}...")

                # Esperar para evitar bloqueos
                await asyncio.sleep(delay)

            except Exception as e:
                print(f"Error traduciendo '{source_text[:50]}...': {str(e)}")
                entry.msgstr = ""

    # Guardar el archivo
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    pofile.save(output_file)
    print(f"\nTraducción completada. Archivo guardado en: {output_file}")


# Ejemplo de uso
if __name__ == "__main__":
    INPUT = 'config_website.pot'
    SRC = 'es'
    DEST = 'pt'
    
    asyncio.run(
        translate_po_with_google(
            input_file=INPUT,
            output_file=f"{DEST}.po",
            src_lang=SRC,
            dest_lang=DEST, 
        )
    )