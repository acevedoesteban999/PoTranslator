from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.tabbedpanel import TabbedPanel
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.checkbox import CheckBox
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.properties import StringProperty, BooleanProperty, ListProperty, ObjectProperty, NumericProperty
from kivy.clock import Clock
from functools import partial
import asyncio
import threading
import polib
from pathlib import Path
from util.PoTranslator import PoTranslator

from kivy.graphics import Rectangle, Color
from kivy.uix.label import Label
from functools import partial

class EditableCell(TextInput):
    def __init__(self, **kwargs):
        super(EditableCell, self).__init__(**kwargs)
        self.multiline = False
        self.background_active = ''
        self.background_normal = ''
        self.padding = [10, 5]
        
        # Propiedad para manejar el color de fondo
        self.background_color = (0.95, 0.95, 0.95, 1)  # Valor inicial
        
        # Bind para cambiar el color cuando cambia el foco
        self.bind(focus=self._on_focus_change)
    
    def _on_focus_change(self, instance, value):
        """Actualiza el color de fondo basado en el estado de foco"""
        if value:  # Si tiene el foco
            self.background_color = (1, 1, 1, 1)  # Blanco
        else:      # Si pierde el foco
            self.background_color = (0.95, 0.95, 0.95, 1)  # Gris claro

class PoTranslatorGUI(TabbedPanel):
    languages = ["es", "pt", "fr", "it", "de", "en"]
    
    pot_file_addr = StringProperty('')
    batch_size = NumericProperty(250)
    output_in_source_dir = BooleanProperty(True)
    is_translating = BooleanProperty(False)
    log_messages = ListProperty([])
    selected_languages = ListProperty([])
    translation_data = ObjectProperty({})
    review_data = ObjectProperty({})
    
    def __init__(self, **kwargs):
        super(PoTranslatorGUI, self).__init__(**kwargs)
        self.selected_languages = []
        self.translation_data = {}
        self.review_data = {'Original':{}}
        
    def browse_pot_file(self):
        content = BoxLayout(orientation='vertical')
        file_chooser = FileChooserListView(filters=['*.pot'])
        content.add_widget(file_chooser)
        
        btn_box = BoxLayout(size_hint_y=None, height=50)
        btn_cancel = Button(text='Cancel')
        btn_select = Button(text='Select')
        btn_box.add_widget(btn_cancel)
        btn_box.add_widget(btn_select)
        content.add_widget(btn_box)
        
        popup = Popup(title='Select POT file', content=content, size_hint=(0.9, 0.9))
        
        def dismiss_popup(instance):
            popup.dismiss()
            
        def select_file(instance):
            if file_chooser.selection:
                self.pot_file_addr = file_chooser.selection[0]
                self.ids.pot_file_input.text = self.pot_file_addr
                self.handle_pot_file_selection(self.pot_file_addr)
            popup.dismiss()
            
        btn_cancel.bind(on_press=dismiss_popup)
        btn_select.bind(on_press=select_file)
        popup.open()
        
    def handle_pot_file_selection(self, text:str=None):
        """Función común para manejar la selección del archivo POT"""
        # Si se pasa el texto como parámetro (desde TextInput), actualizamos pot_file_addr
        
        if not text:
            return
        
        # Validación de extensión .pot
        if not text.lower().endswith('.pot'):
            self.log("Error: El archivo debe tener extensión .pot")
            self.show_message("Error", "Por favor selecciona un archivo .pot válido")
            return
        
        
        try:
            # Verificar si el archivo existe
            if not Path(text).exists():
                self.log(f"Error: Archivo no encontrado - {self.pot_file_addr}")
                self.show_message("Error", "El archivo no existe")
                return
            
            self.pot_file_addr = text
                
            self.log(f"Selected POT file: {self.pot_file_addr}")
            self.load_pot_for_review(force_reload=True)
        except Exception as e:
            self.log(f"Error al cargar el archivo: {str(e)}")
            self.show_message("Error", f"No se pudo cargar el archivo: {str(e)}")
    
    def toggle_language(self, lang, active):
        if active:
            if lang not in self.selected_languages:
                self.selected_languages.append(lang)
        else:
            if lang in self.selected_languages:
                self.selected_languages.remove(lang)
                if lang in self.review_data:
                    del self.review_data[lang]
        self.load_pot_for_review()
    
    def load_pot_for_review(self, force_reload=False):
        if not self.pot_file_addr:
            return False
        
        try:
            pot_path = Path(self.pot_file_addr)
            if not pot_path.exists():
                self.log(f"Error: POT file not found at {self.pot_file_addr}")
                return False
                
            # Load POT file entries
            if force_reload:
                pot_entries = polib.pofile(str(pot_path))
                self.review_data['Original'] = {entry.msgid : entry.msgstr for entry in pot_entries if entry.msgid}
            # Load translations for selected languages
            for lang in self.selected_languages:
                po_path = pot_path.parent / f"{lang}.po"
                
                if po_path.exists():
                    try:
                        po_entries = polib.pofile(str(po_path))
                        translations = {entry.msgid: entry.msgstr for entry in po_entries if entry.msgid}
                        
                        # Update the review data with translations
                        self.review_data[lang] = {}
                        for msgid,_ in self.review_data['Original'].items():
                            self.review_data[lang][msgid] = translations.get(msgid, "")
                    except Exception as e:
                        self.log(f"Error loading {lang}.po: {str(e)}")
                        continue
                else:
                    # If PO file doesn't exist, initialize with empty strings
                    self.review_data[lang] = {}
            
            
            # Update the UI grid
            self.update_translation_grid()
            
            self.log(f"\nLoaded POT file with {len(self.review_data)} entries")
            if self.selected_languages:
                self.log(f"Displaying translations for: {', '.join(self.selected_languages)}")
            return True
            
        except Exception as e:
            self.log(f"Failed to load POT file: {str(e)}")
            return False
    
    def update_translation_column(self, lang, po_file):
        """Update the translation column for a specific language"""
        translations = {entry.msgid: entry.msgstr for entry in po_file if entry.msgid}
        
        for row in self.review_data:
            original_msg = row['Original']
            row[lang] = translations.get(original_msg, "")
        
        self.update_translation_grid()
    
    def update_translation_grid(self):
        if 'translation_grid' not in self.ids:
            return
            
        grid = self.ids.translation_grid
        grid.clear_widgets()
        
        # Obtener todas las claves (msgids) de la columna 'Original'
        msgids = list(self.review_data.get('Original', {}).keys())
        
        # Configurar el GridLayout
        num_columns = len(self.review_data)  # Número de columnas (idiomas + original)
        num_rows = len(msgids) + 1          # +1 para la fila de encabezados
        
        grid.cols = num_columns
        grid.rows = num_rows
        
        # 1. Primero añadir los encabezados de columna
        for lang in self.review_data.keys():
            lbl = Label(text=lang, size_hint_y=None, height=40, bold=True)
            lbl.canvas.before.add(Color(rgba=(0.8, 0.8, 0.8, 1)))
            lbl.canvas.before.add(Rectangle(pos=lbl.pos, size=lbl.size))
            grid.add_widget(lbl)
        
        # 2. Luego añadir los datos por columnas
        for msgid in msgids:
            for lang, column_data in self.review_data.items():
                if lang == 'Original':
                    # Celda no editable para el texto original
                    lbl = Label(text=msgid if msgid else '', 
                            size_hint_y=None, height=40,
                            text_size=(None, None), halign='left', valign='middle')
                    lbl.canvas.before.add(Color(rgba=(0.9, 0.9, 0.9, 1)))
                    lbl.canvas.before.add(Rectangle(pos=lbl.pos, size=lbl.size))
                    grid.add_widget(lbl)
                else:
                    # Celda editable para las traducciones
                    txt = EditableCell(text=column_data.get(msgid, ''), 
                                    size_hint_y=None, height=40)
                    txt.bind(text=partial(self.on_cell_edit, lang, msgid))
                    grid.add_widget(txt)
        
        # Actualizar altura del GridLayout
        grid.height = max(grid.minimum_height, 500)

    def on_cell_edit(self, lang, msgid, instance, value):
        """Actualiza el dato cuando se edita una celda"""
        if lang in self.review_data and msgid in self.review_data[lang]:
            self.review_data[lang][msgid] = value
    
    def translate_all_selected(self):
        if self.is_translating:
            return
            
        if not self.pot_file_addr:
            self.log("Error: You must select a POT file")
            return
            
        if not self.selected_languages:
            self.log("Error: You must select at least one language")
            return
            
        self.log("\nStarting translation process for all selected languages...")
        self.log(f"File: {self.pot_file_addr}")
        self.log(f"Languages: {', '.join(self.selected_languages)}")
        self.log(f"Batch size: {self.batch_size}")
        
        self.is_translating = True
        
        def run_translations():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                for lang in self.selected_languages:
                    self.log(f"\nTranslating to '{lang}'...")
                    
                    translator = PoTranslator(
                        batch_size=self.batch_size, 
                        delay=1,
                        log_funct=self.log,
                    )
                    
                    po_file = polib.pofile(self.pot_file_addr)
                    
                    coro = translator.translate_po_file(
                        new_po_file=po_file,
                        pot_file_addr=self.pot_file_addr,
                        dest_lang=lang
                    )
                    
                    loop.run_until_complete(coro)
                    
                    # Update the UI with new translations
                    def update_ui():
                        self.update_translation_column(lang, po_file)
                    
                    Clock.schedule_once(lambda dt: update_ui())
                    
                    self.log(f"Translation to '{lang}' completed")
                
                self.log(f"\nTranslations {', '.join(self.selected_languages)} completed successfully")
                Clock.schedule_once(lambda dt: self.show_message(
                    "Success", 
                    f"Translations {', '.join(self.selected_languages)} completed successfully"
                ))
                
            except Exception as e:
                self.log(f"\nError during translation: {str(e)}")
                Clock.schedule_once(lambda dt: self.show_message(
                    "Error", 
                    f"Error during translation: {str(e)}"
                ))
            finally:
                Clock.schedule_once(lambda dt: setattr(self, 'is_translating', False))
                loop.close()
                
        threading.Thread(target=run_translations, daemon=True).start()
    
    def save_all_translations(self):
        if not self.pot_file_addr:
            self.log("Error: No POT file loaded")
            return
        if not self.selected_languages:
            self.log("Error: No Language Selected")
            return
        
        pot_path = Path(self.pot_file_addr)
        
        for lang in self.selected_languages:
            try:
                # Create a new PO file based on the POT file
                po_file = polib.pofile(str(pot_path))
                
                # Update metadata
                po_file.metadata = PoTranslator._generate_po_metadata(lang, str(pot_path))
                
                # Create a dictionary with all translations for this language
                translations = {row['Original']: row.get(lang, "") for row in self.review_data}
                
                # Update each entry in the PO file
                for entry in po_file:
                    if entry.msgid in translations:
                        entry.msgstr = translations[entry.msgid]
                
                # Save the PO file
                po_file_path = pot_path.parent / f"{lang}.po"
                po_file.save(str(po_file_path))
                self.log(f"Saved translations to {po_file_path}")
            except Exception as e:
                self.log(f"Error saving {lang}.po: {str(e)}")
        
        self.show_message("Success", "All translations saved successfully")
        self.log("\nAll translations saved successfully!")
    
    def show_message(self, title, message):
        content = BoxLayout(orientation='vertical', padding=10)
        content.add_widget(Label(text=message))
        btn = Button(text='OK', size_hint_y=None, height=50)
        content.add_widget(btn)
        
        popup = Popup(title=title, content=content, size_hint=(0.8, 0.4))
        btn.bind(on_press=popup.dismiss)
        popup.open()
    
    def log(self, message):
        self.log_messages.append(message)
        # Auto-scroll to the bottom
        Clock.schedule_once(lambda dt: setattr(self.ids.log_area, 'cursor', (0, len(self.ids.log_area.text))))