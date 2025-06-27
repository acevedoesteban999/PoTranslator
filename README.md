# PoTranslator 

### README Translation
- [English](README.md)
- [Spanish](README.es.md)
- [Portuguese](README.pt.md)
- [French](README.fr.md)

### PoTranslator GUI - How to Use

## Overview
PoTranslator GUI is a user-friendly application for translating and managing .pot/.po files. It allows you to translate text strings into multiple languages, review translations, and save them back to .po files.

![Translator Graphical Interface](media/image1.png)

## Getting Started

1. **Launch the Application**
   - Run the application to open the main window.

2. **Select a POT File**
   - Click "Browse" to select your .pot file (the template file containing original strings).
   - The application will automatically detect available translations in the same directory.

## Main Features

### Translation Management
- **Select Target Languages**: Check the boxes for the languages you want to translate to (Spanish, Portuguese, French, Italian, German, English).
- **Translate All**: Click "Translate All" to automatically translate all selected languages at once.
- **Edit Translations**: Double-click any translation cell to manually edit it.

### Review & Edit
- View all original strings and their translations side by side.
- The table shows:
  - Original text (from .pot file)
  - Translated text for each selected language
- Make changes directly in the table.

### Saving Translations
- Click "Save" to save all translations to their respective .po files.
- Translations are saved in the same directory as your .pot file.

### Settings
- Adjust batch size for translation operations (how many strings are processed at once).
- Choose whether to save files in the POT file directory or a separate translations folder.

### Tips
- Always review automatic translations before saving.
- The application preserves all existing metadata (comments, flags) when saving .po files.
- Use the "Reload Data" button if you make changes to the files outside the application.
- Our application successfully separates format specifiers (such as %s, %d, %f) and HTML/XML tags during translation processes, enabling pure text handling without compromising structural elements.