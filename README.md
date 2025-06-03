# PoTranslator 

## README Translation
- [English](README.md)
- [Spanish](README.es.md)
- [Portuguese](README.pt.md)
- [French](README.fr.md)

Tool to convert .pot files into automatically translated .po files using Google Translate, with a graphical interface or command line.

![Translator Graphical Interface](https://github.com/user-attachments/assets/48377205-6435-4919-b549-091cec595f8f)

## Translation Tool for .POT and .PO
## How to Use

1. Install and activate the virtual environment with the libraries specified in requirements.txt
2. Provide internet access to the Python service in the virtual environment
3. Run the file `PoTranslatorGUI.py` for the graphical interface or `PoTranslatorConsole.py` for the console
4. Select the .pot file path, the languages, and start translating
5. Upon completion, translations will be created next to the .pot file if the option `Save files in the POT file directory` is selected; otherwise, a folder will be created in the root directory within `translations` with the name of the .pot file as the folder where the translations will be located
