from kivy.app import App
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.tabbedpanel import TabbedPanel
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.properties import StringProperty, BooleanProperty, ListProperty, ObjectProperty, NumericProperty
from kivy.clock import Clock
from functools import partial
import asyncio
import threading
import polib
from pathlib import Path
from kivy.graphics import Rectangle, Color
from kivy.uix.label import Label
from functools import partial

from util.EditableCell import EditableCell

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
    ui_enable = BooleanProperty(False)
    
    def __init__(self, **kwargs):
        super(PoTranslatorGUI, self).__init__(**kwargs)
        self.selected_languages = []
        self.translation_data = {}
        self.review_data = {'Original':{}}
        self.set_ui_state(False)
    
    def set_ui_state(self, enabled):
        self.ui_enable = enabled
        for child_name,child in self.ids.items():
            if child_name not in ['pot_file_box_layout','pot_file_input', 'browse_button']:
                child.disabled = not enabled
    
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
                selected_file = file_chooser.selection[0]
                self.ids.pot_file_input.text = selected_file
                self._validate_and_load_file(selected_file)
            popup.dismiss()
            
        btn_cancel.bind(on_press=dismiss_popup)
        btn_select.bind(on_press=select_file)
        popup.open()

    def handle_pot_file_input(self, instance):
        file_path = instance.text
        self._validate_and_load_file(file_path)

    def _validate_and_load_file(self, file_path: str):
        if not file_path:
            return
        self.set_ui_state(False)
        
        if not file_path.lower().endswith('.pot'):
            print("Error: El archivo debe tener extensión .pot")
            self.show_message("Error", "Por favor selecciona un archivo .pot válido")
            return
        
        try:
            
            if not Path(file_path).exists():
                print(f"Error: File dont Found - {file_path}")
                self.show_message("Error", f"File dont Found - {file_path}")
                return
            
            self.pot_file_addr = file_path
            
            print(f"POT: {self.pot_file_addr}")
            self.load_pot_for_review(force_reload=True)
            self.set_ui_state(True)
    
        except Exception as e:
            print(f"Error: {str(e)}")
            self.show_message("Error", f"{str(e)}")
        
    
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
                print(f"Error: POT file not found at {self.pot_file_addr}")
                return False
                
            if force_reload:
                pot_entries = polib.pofile(str(pot_path))
                self.review_data['Original'] = {entry.msgid : entry.msgstr for entry in pot_entries if entry.msgid}
            for lang in self.selected_languages:
                po_path = pot_path.parent / f"{lang}.po"
                
                if po_path.exists():
                    try:
                        po_entries = polib.pofile(str(po_path))
                        translations = {entry.msgid: entry.msgstr for entry in po_entries if entry.msgid}
                        
                        self.review_data[lang] = {}
                        for msgid,_ in self.review_data['Original'].items():
                            self.review_data[lang][msgid] = translations.get(msgid, "")
                    except Exception as e:
                        print(f"Error loading {lang}.po: {str(e)}")
                        continue
                else:
                    self.review_data[lang] = {}
            
            
            self.update_translation_grid()
            
            print(f"\nLoaded POT file with {len(self.review_data)} entries")
            if self.selected_languages:
                print(f"Displaying translations for: {', '.join(self.selected_languages)}")
            return True
            
        except Exception as e:
            print(f"Failed to load POT file: {str(e)}")
            return False
    
    def update_translation_column(self, lang, po_file):
        """Update the translation column for a specific language"""
        translations = {entry.msgid: entry.msgstr for entry in po_file if entry.msgid}
        
        msgids = list(self.review_data.get('Original', {}).keys())
        
        for msgid in msgids:
            self.review_data[lang][msgid] = translations.get(msgid)
        
    
    def update_translation_grid(self):
        if 'translation_grid' not in self.ids:
            return
            
        grid = self.ids.translation_grid
        grid.clear_widgets()
        
        msgids = list(self.review_data.get('Original', {}).keys())
        
        grid.cols = len(self.review_data) 
        grid.rows =  len(msgids) + 1 
        
        for lang in self.review_data.keys():
            lbl = Label(text=lang, size_hint_y=None, height=40, bold=True)
            lbl.canvas.before.add(Color(rgba=(0.8, 0.8, 0.8, 1)))
            lbl.canvas.before.add(Rectangle(pos=lbl.pos, size=lbl.size))
            grid.add_widget(lbl)
        
        for msgid in msgids:
            for lang, column_data in self.review_data.items():
                if lang == 'Original':
                    lbl = Label(text=msgid if msgid else '', 
                            size_hint_y=None, height=40,
                            text_size=(None, None), halign='left', valign='middle')
                    lbl.canvas.before.add(Color(rgba=(0.9, 0.9, 0.9, 1)))
                    lbl.canvas.before.add(Rectangle(pos=lbl.pos, size=lbl.size))
                    grid.add_widget(lbl)
                else:
                    txt = EditableCell(text=column_data.get(msgid, ''), 
                                    size_hint_y=None, height=40)
                    txt.bind(text=partial(self.on_cell_edit, lang, msgid))
                    grid.add_widget(txt)
        
        grid.height = max(grid.minimum_height, 500)

    def on_cell_edit(self, lang, msgid, instance, value):
        if lang in self.review_data and msgid in self.review_data[lang]:
            self.review_data[lang][msgid] = value
    
    def translate_all_selected(self):
        if self.is_translating:
            return
            
        if not self.pot_file_addr:
            print("Error: You must select a POT file")
            return
            
        if not self.selected_languages:
            print("Error: You must select at least one language")
            return
            
        print("\nStarting translation process for all selected languages...")
        print(f"File: {self.pot_file_addr}")
        print(f"Languages: {', '.join(self.selected_languages)}")
        print(f"Batch size: {self.batch_size}")
        
        self.is_translating = True
        
        def run_translations():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                translator = PoTranslator(
                    batch_size=self.batch_size, 
                    delay=1,
                    log_funct=print,
                )
                for lang in self.selected_languages:
                    print(f"\nTranslating to '{lang}'...")
                    
                    
                    po_file = polib.pofile(self.pot_file_addr)
                    
                    coro = translator.translate_po_file(
                        new_po_file=po_file,
                        pot_file_addr=self.pot_file_addr,
                        dest_lang=lang
                    )
                    
                    loop.run_until_complete(coro)
                    
                    self.update_translation_column(lang, po_file)
                    
                    def update_ui():
                        self.update_translation_grid()
                        
                    Clock.schedule_once(lambda dt: update_ui())
                    
                    print(f"Translation to '{lang}' completed")
                
                print(f"\nTranslations {', '.join(self.selected_languages)} completed successfully")
                Clock.schedule_once(lambda dt: self.show_message(
                    "Success", 
                    f"Translations {', '.join(self.selected_languages)} completed successfully"
                ))
                
            except Exception as e:
                print(f"\nError during translation: {str(e)}")
                Clock.schedule_once(lambda dt: self.show_message(
                    "Error", 
                    f"Error during translation"
                ))
            finally:
                Clock.schedule_once(lambda dt: setattr(self, 'is_translating', False))
                loop.close()
                
        threading.Thread(target=run_translations, daemon=True).start()
    
    def save_all_translations(self):
        if not self.pot_file_addr:
            print("Error: No POT file loaded")
            return
        if not self.selected_languages:
            print("Error: No Language Selected")
            return
        
        pot_path = Path(self.pot_file_addr)
        
        for lang in self.selected_languages:
            try:
                po_file = polib.pofile(str(pot_path))
                po_file.metadata = PoTranslator._generate_po_metadata(lang, str(pot_path))
                
                for entry in po_file:
                    if entry.msgid in self.review_data[lang]:
                        entry.msgstr = self.review_data[lang][entry.msgid]
                
                po_file_path = pot_path.parent / f"{lang}.po"
                po_file.save(str(po_file_path))
                print(f"Saved translations to {po_file_path}")
            except Exception as e:
                print(f"Error saving {lang}.po: {str(e)}")
        
        self.show_message("Success", "All translations saved successfully")
        print("\nAll translations saved successfully!")
    
    def show_message(self, title, message):
        content = BoxLayout(orientation='vertical', padding=10)
        content.add_widget(Label(text=message))
        btn = Button(text='OK', size_hint_y=None, height=50)
        content.add_widget(btn)
        
        popup = Popup(title=title, content=content, size_hint=(0.8, 0.4))
        btn.bind(on_press=popup.dismiss)
        popup.open()


class PoTranslatorApp(App):
    def build(self):
        return PoTranslatorGUI()

if __name__ == '__main__':
    PoTranslatorApp().run()