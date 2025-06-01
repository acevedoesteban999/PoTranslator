import argparse
from util.PoTranslator import PoTranslator
import asyncio
from pathlib import Path

class PoTranslatorConsole:
    def __init__(self):
        self.language_options = {
            '1': ('es', 'Español'),
            '2': ('pt', 'Portugués'),
            '3': ('fr', 'Francés'),
            '4': ('it', 'Italiano'),
            '5': ('de', 'Alemán'),
            '6': ('en', 'Inglés'),
        }

    def display_menu(self):
        print("\nSelecciona los idiomas a traducir (separados por comas):")
        for key, value in self.language_options.items():
            print(f"{key}. {value[1]} ({value[0]})")
        print("0. Traducir")
    
    def get_user_selection(self):
        selected = []
        while True:
            self.display_menu()
            print(f"\nSeleccionadas: [{', '.join(selected) if selected else ''}]")
                
            choice = input("\n: ").strip()
            
            if choice == '0':
                break
                
            invalid = []
            for num in choice.split(','):
                num = num.strip()
                if num in self.language_options:
                    if self.language_options[num][0] not in selected:
                        selected.append(self.language_options[num][0])
                else:
                    invalid.append(num)
            
            if invalid:
                print(f"\nOpciones no válidas: {', '.join(invalid)}")
                continue
                
            if not selected:
                print("\nDebes seleccionar al menos un idioma")
                continue
            
        return selected

    async def run_translation(self, pot_file, languages):
        dest_langs = [lang for lang in languages]
        
        print(f"\nIniciando traducción del archivo: {pot_file}")
        print(f"Idiomas seleccionados: {', '.join(languages)}")
        
        translator = PoTranslator(input_pot_file=pot_file, batch_size=100, delay=1)
        for dest_lang in dest_langs:
            print(f"\nTraduciendo a {dest_lang}...")
            await translator.translate_po_file(dest_lang=dest_lang)
            print(f"Traducción a {dest_lang} completada")
            

def main():
    parser = argparse.ArgumentParser(description='Traductor POT/PO desde consola')
    parser.add_argument('file', nargs='?', help='Archivo .pot a traducir')
    args = parser.parse_args()

    console_translator = PoTranslatorConsole()
    
    # Obtener archivo POT
    pot_file = args.file
    while not pot_file:
        pot_file = input("Introduce la ruta del archivo .pot: ").strip()
        if not Path(pot_file).is_file():
            print("¡El archivo no existe!")
            pot_file = None
    
    # Seleccionar idiomas
    languages = console_translator.get_user_selection()
    if not languages:
        print("\nOperación cancelada")
        return
    
    # Ejecutar traducción
    asyncio.run(console_translator.run_translation(pot_file, languages))

if __name__ == "__main__":
    main()