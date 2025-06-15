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

class PoTranslatorGUI(TabbedPanel):
    languages = ["es", "pt", "fr", "it", "de", "en"]
    
    pot_file_addr = StringProperty('')
    batch_size = NumericProperty(250)
    output_in_source_dir = BooleanProperty(True)
    is_translating = BooleanProperty(False)
    log_messages = ListProperty([])
    selected_languages = ListProperty([])
    translation_data = ObjectProperty({})
    review_columns = ListProperty([])
    review_data = ListProperty([])
    
    def __init__(self, **kwargs):
        super(PoTranslatorGUI, self).__init__(**kwargs)
        self.selected_languages = []
        self.translation_data = {}
        self.review_columns = ['Main']
        self.review_data = []
        
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
                self.log(f"Selected POT file: {self.pot_file_addr}")
                self.load_pot_for_review(force_reload=True)
            popup.dismiss()
            
        btn_cancel.bind(on_press=dismiss_popup)
        btn_select.bind(on_press=select_file)
        popup.open()
    
    def toggle_language(self, lang, active):
        if active:
            if lang not in self.selected_languages:
                self.selected_languages.append(lang)
        else:
            if lang in self.selected_languages:
                self.selected_languages.remove(lang)
        
        self.load_pot_for_review()
    
    def load_pot_for_review(self, force_reload=False):
        if not self.pot_file_addr:
            return False
        
        try:
            selected_langs = self.selected_languages.copy()
            
            current_displayed_langs = set(self.review_columns[1:]) if len(self.review_columns) > 1 else set()
            if not force_reload and set(selected_langs) == current_displayed_langs:
                return True
                
            pot_path = Path(self.pot_file_addr)
            pot_entries = polib.pofile(pot_path)
            
            new_columns = ['Main'] + selected_langs
            self.review_columns = new_columns
            
            self.translation_data = {}
            
            for lang in selected_langs:
                if lang not in self.translation_data:
                    self.translation_data[lang] = {}
                    
                po_path = pot_path.parent / f"{lang}.po"
                if po_path.exists():
                    po_entries = polib.pofile(po_path)
                    for entry in po_entries:
                        if entry.msgid:
                            self.translation_data[lang][entry.msgid] = entry.msgstr
            
            # Actualizar datos para la tabla
            new_data = []
            for entry in pot_entries:
                if entry.msgid:
                    row = {'Main': entry.msgid}
                    for lang in selected_langs:
                        row[lang] = self.translation_data[lang].get(entry.msgid, "")
                    new_data.append(row)
            
            self.review_data = new_data
            self.log(f"\nUpdated view with languages: {', '.join(selected_langs)}")
            return True
        except Exception as e:
            self.log(f"Failed to load POT file: {str(e)}")
            return False
    
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
                    
                    # Actualizar la UI con las nuevas traducciones
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
    
    def update_translation_grid(self):
        if not hasattr(self, 'translation_grid'):
            return
            
        grid = self.translation_grid
        grid.clear_widgets()
        
        # Add headers
        for col in self.review_columns:
            lbl = Label(text=col, size_hint_y=None, height=40, bold=True)
            lbl.canvas.before.add(Color(rgba=(0.8, 0.8, 0.8, 1)))
            lbl.canvas.before.add(Rectangle(pos=lbl.pos, size=lbl.size))
            grid.add_widget(lbl)
        
        # Add data rows
        for row in self.review_data:
            for col in self.review_columns:
                if col == 'Main':
                    lbl = Label(text=row[col] if row[col] else '', 
                            size_hint_y=None, height=40,
                            text_size=(None, None), halign='left', valign='middle')
                    lbl.canvas.before.add(Color(rgba=(0.9, 0.9, 0.9, 1)))
                    lbl.canvas.before.add(Rectangle(pos=lbl.pos, size=lbl.size))
                    grid.add_widget(lbl)
                else:
                    txt = EditableCell(text=row.get(col, ''), size_hint_y=None, height=40)
                    txt.bind(text=partial(self.on_cell_edit, row, col))
                    grid.add_widget(txt)

    def on_cell_edit(self, row, col, instance, value):
        row[col] = value
    
    def save_all_translations(self):
        if not self.pot_file_addr:
            self.log("Error: No POT file loaded")
            return
        if not self.translation_data:
            self.log("Error: No Language Selected")
            return
        
        pot_path = Path(self.pot_file_addr)
        
        for lang in self.translation_data:
            try:
                po_file = polib.pofile(str(pot_path))
                po_file.metadata = PoTranslator._generate_po_metadata(lang, str(pot_path))
                
                # Crear diccionario con las traducciones
                translations = {row['Main']: row.get(lang, "") for row in self.review_data}
                
                for entry in po_file:
                    entry.msgstr = translations.get(entry.msgid, "")
                    
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