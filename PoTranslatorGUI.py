import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from util.PoTranslator import PoTranslator
import asyncio
from pathlib import Path
import threading
import shutil
from functools import partial
import polib

class PoTranslatorGUI:
    languages = [
            "es",
            "pt",
            "fr",
            "it",
            "de",
            "en",
        ]
    
    def __init__(self, root):
        self.root = root
        self.root.title("PoTranslator")
        self.root.geometry("1200x800") 
        
        
        self.pot_file_addr = tk.StringVar()
        self.selected_languages = {}
        self.log_messages = []
        self.batch_size = tk.IntVar(value=250)
        self.is_translating = False
        self.output_in_source_dir = tk.BooleanVar(value=True)
        self.use_output_in_source_dir = tk.BooleanVar(value=True)
        self.review_lang = tk.StringVar(value="es")
        self.review_data = []
        self.translation_data = {} 
        
        
        self.create_widgets()
    
    def create_widgets(self):
        
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # POT SECTION
        file_frame = ttk.LabelFrame(main_frame, text="POT File", padding="10")
        file_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(file_frame, text=".Pot File:").grid(row=0, column=0, sticky=tk.W)
        
        pot_entry = ttk.Entry(file_frame, textvariable=self.pot_file_addr)
        pot_entry.grid(row=0, column=1, padx=5, sticky=tk.EW)
        
        file_frame.columnconfigure(1, weight=1)
        
        ttk.Button(file_frame, text="Browse", command=self.browse_pot_file).grid(row=0, column=2)
        
        # Notebook 
        self.notebook = ttk.Notebook(main_frame)
        self.create_review_tab()
        
        
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        self.create_settings_tab()
    
    
    def create_review_tab(self):
        review_tab = ttk.Frame(self.notebook)
        self.notebook.add(review_tab, text="Review & Edit")
        
        controls_frame = ttk.Frame(review_tab, padding="10")
        controls_frame.pack(fill=tk.X)
        
        # Checkbuttons 
        lang_frame = ttk.LabelFrame(controls_frame, text="Target Languages", padding="5")
        lang_frame.pack(side=tk.LEFT, padx=5)

        for i, code in enumerate(self.languages):
            var = tk.BooleanVar()
            cb = ttk.Checkbutton(
                lang_frame, 
                text=str(code).upper(), 
                variable=var,
                command=lambda c=code, v=var: self.load_pot_for_review(c, v,True),
            )
            
            cb.grid(row=0, column=i, padx=5, pady=2, sticky=tk.W)
            self.selected_languages[code] = var
        
        # Buttons
        btn_frame = ttk.Frame(controls_frame)
        btn_frame.pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(btn_frame, text="Reload Data", 
                              command=self.reload_data).pack(side=tk.LEFT, padx=5)
      
        
        ttk.Button(btn_frame, text="Translate All", 
                                  command=self.translate_all_selected).pack(side=tk.LEFT, padx=5)
       
        
        
        ttk.Button(btn_frame, text="Save", 
                  command=self.save_all_translations).pack(side=tk.LEFT, padx=5)
        
        # Treeview 
        tree_frame = ttk.Frame(review_tab)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Columns
        self.review_columns = ["Main"]
        self.review_tree = ttk.Treeview(tree_frame, columns=self.review_columns, show="headings", height=25)
        
        self.review_tree.heading("Main", text="Main Text (.pot)")
        self.review_tree.column("Main", width=400, stretch=tk.YES)
        
        # Scrollbars
        yscroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.review_tree.yview)
        xscroll = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.review_tree.xview)
        self.review_tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        
        # Grid layout
        self.review_tree.grid(row=0, column=0, sticky=tk.NSEW)
        yscroll.grid(row=0, column=1, sticky=tk.NS)
        xscroll.grid(row=1, column=0, sticky=tk.EW)
        
        # Configurar expansión
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        
        # Bind para edición
        self.review_tree.bind("<Double-1>", self.on_double_click)
    
    def reload_data(self):
        if not self.pot_file_addr.get():
            messagebox.showerror("Error", "No POT file selected")
            return
            
        self.translation_data = {}
        
        if self.load_pot_for_review(force_reload=True):
            messagebox.showinfo("Success", "Data reloaded successfully")
            self.log("\nData reloaded from files")
    
    def create_settings_tab(self):
        settings_tab = ttk.Frame(self.notebook)
        self.notebook.add(settings_tab, text="Settings")
        
        # Configuración frame
        config_frame = ttk.LabelFrame(settings_tab, text="Translation Settings", padding="10")
        config_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(config_frame, text="Batch size:").grid(row=0, column=0, sticky=tk.W)
        ttk.Spinbox(config_frame, from_=1, to=500, textvariable=self.batch_size, width=10).grid(row=0, column=1, sticky=tk.W, padx=5)
        
        ttk.Checkbutton(
            config_frame, 
            text="Save files in the POT file directory",
            variable=self.output_in_source_dir,
            command=self._set_output_in_source_dir
        ).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # ttk.Checkbutton(
        #     config_frame, 
        #     text="Use .PO Data from POT file directory",
        #     variable=self.use_output_in_source_dir
        # ).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Log area
        log_frame = ttk.LabelFrame(settings_tab, text="Execution Logs", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_area = scrolledtext.ScrolledText(log_frame, height=20, wrap=tk.WORD)
        self.log_area.pack(fill=tk.BOTH, expand=True)
    
    def _set_output_in_source_dir(self):
        if self.output_in_source_dir.get():
            self.output_dir = Path(self.pot_file_addr.get()).parent
        else:
            pot_name = Path(self.pot_file_addr.get()).stem 
            self.output_dir = Path(f"translations/{pot_name}")
            if not self.output_dir.exists():
                self.output_dir.mkdir(parents=True)  
    
    def on_double_click(self, event):
        region = self.review_tree.identify("region", event.x, event.y)
        if region == "cell":
            column = self.review_tree.identify_column(event.x)
            item = self.review_tree.identify_row(event.y)
            
            # No edit main column
            if column != "#1":
                col_index = int(column[1:]) - 1
                lang = self.review_columns[col_index]
                
               
                x, y, width, height = self.review_tree.bbox(item, column)
                current_value = self.review_tree.item(item, "values")[col_index]
                
                
                entry = ttk.Entry(self.review_tree)
                entry.place(x=x, y=y, width=width, height=height)
                entry.insert(0, current_value)
                entry.focus()
                
                def save_edit(event):
                    new_value = entry.get()
                    values = list(self.review_tree.item(item, "values"))
                    values[col_index] = new_value
                    self.review_tree.item(item, values=values)
                    
                  
                    msgid = self.review_tree.item(item, "values")[0]
                    self.translation_data[lang][msgid] = new_value
                    
                    entry.destroy()
                
                entry.bind("<FocusOut>", lambda e: entry.destroy())
                entry.bind("<Return>", save_edit)
    
    def load_pot_for_review(self, code=None, var=None, from_lang_checkbox=False,force_reload=False):
        if not self.pot_file_addr.get():
            if not from_lang_checkbox:
                messagebox.showerror("Error", "You must select a POT file first")
            return False
        
        try:
            selected_langs = self.__get_selected_languages()
            
            current_displayed_langs = set(self.review_columns[1:]) if len(self.review_columns) > 1 else set()
            if not force_reload and set(selected_langs) == current_displayed_langs:
                return True
                
            pot_path = Path(self.pot_file_addr.get())
            pot_entries = polib.pofile(pot_path)
            
            new_columns = ["Main"] + selected_langs
            
            self.review_tree['columns'] = new_columns
            
            for col in new_columns:
                self.review_tree.heading(col, text=col)
                self.review_tree.column(col, width=300, stretch=tk.YES)
            
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
            
            for item in self.review_tree.get_children():
                self.review_tree.delete(item)
                
            for entry in pot_entries:
                if entry.msgid:
                    row_values = [entry.msgid]
                    for lang in selected_langs:
                        row_values.append(self.translation_data[lang].get(entry.msgid, ""))
                    self.review_tree.insert("", tk.END, values=row_values)
            
            self.log(f"\nUpdated view with languages: {', '.join(selected_langs)}")
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load POT file: {str(e)}")
            return False

    def translate_all_selected(self):
        """Traduce todos los idiomas seleccionados"""
        if self.is_translating:
            return
            
        pot_file_addr = self.pot_file_addr.get()
        if not pot_file_addr:
            messagebox.showerror("Error", "You must select a POT file")
            return
            
        lang_selected = self.__get_selected_languages()
        if not lang_selected:
            messagebox.showerror("Error", "You must select at least one language")
            return
            
        self.log("\nStarting translation process for all selected languages...")
        self.log(f"File: {pot_file_addr}")
        self.log(f"Languages: {', '.join(lang_selected)}")
        self.log(f"Batch size: {self.batch_size.get()}")
        
        self.toggle_ui_state(False)
        
        # Crear un nuevo event loop para cada idioma
        def run_translations():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                for lang in lang_selected:
                    self.log(f"\nTranslating to '{lang}'...")
                    
                    # Crear una nueva instancia del traductor para cada idioma
                    translator = PoTranslator(
                        batch_size=self.batch_size.get(), 
                        delay=1,
                        log_funct=self.log,
                    )
                    
                    po_file = polib.pofile(pot_file_addr)
                    
                    coro = translator.translate_po_file(
                        new_po_file=po_file,
                        pot_file_addr=pot_file_addr,
                        dest_lang=lang
                    )
                    
                    loop.run_until_complete(coro)
                    
                    # Actualizar solo la columna del idioma recién traducido
                    self.root.after(0, lambda: self.update_translation_column(lang, po_file))
                    
                    self.log(f"Translation to '{lang}' completed")
                
                self.log(f"\nTranslations {', '.join(lang_selected)} completed successfully")
                self.root.after(0, lambda: messagebox.showinfo(
                    "Success", 
                    f"Translations {', '.join(lang_selected)} completed successfully"
                ))
                
            except Exception as e:
                self.log(f"\nError during translation: {str(e)}")
                self.root.after(0, lambda: messagebox.showerror(
                    "Error", 
                    f"Error during translation: {str(e)}"
                ))
            finally:
                self.root.after(0, partial(self.toggle_ui_state, True))
                loop.close()
                
        threading.Thread(target=run_translations, daemon=True).start()
        
    def update_translation_column(self, lang, po_file):
        """Actualiza una columna específica con las nuevas traducciones"""
        if lang not in self.translation_data:
            self.translation_data[lang] = {}
        
        # Actualizar datos en memoria
        for entry in po_file:
            if entry.msgid:
                self.translation_data[lang][entry.msgid] = entry.msgstr
        
        # Actualizar treeview si la columna existe
        if lang in self.review_columns:
            lang_index = self.review_columns.index(lang)
            
            for item in self.review_tree.get_children():
                values = list(self.review_tree.item(item, "values"))
                msgid = values[0]
                
                if len(values) > lang_index:
                    values[lang_index] = self.translation_data[lang].get(msgid, "")
                    self.review_tree.item(item, values=values)
                else:
                    self.load_pot_for_review()
                    break
    
    def save_all_translations(self):
        if not self.pot_file_addr.get():
            messagebox.showerror("Error", "No POT file loaded")
            return
        if not self.translation_data:
            messagebox.showerror("Error", "No Language Selected")
            return
        
        pot_path = Path(self.pot_file_addr.get())
        
        for lang in self.translation_data:
            try:
                
                po_file = polib.pofile(str(pot_path))
                po_file.metadata = PoTranslator._generate_po_metadata(lang, str(pot_path))
                entries = {}
                for item in self.review_tree.get_children():
                    values = self.review_tree.item(item, "values")
                    msgid = values[0]
                    msgstr = values[self.review_columns.index(lang)]
                    entries.update({
                        msgid:msgstr
                    })
                    
                for entry in po_file:
                    entry.msgstr = entries.get(entry.msgid)
                    
                po_file_path = pot_path.parent / f"{lang}.po"
                po_file.save(str(po_file_path))
                self.log(f"Saved translations to {po_file_path}")
            except Exception as e:
                self.log(f"Error saving {lang}.po: {str(e)}")
        
        messagebox.showinfo("Success", "All translations saved successfully")
        self.log("\nAll translations saved successfully!")
    
    def browse_pot_file(self):
        if self.is_translating:
            return
            
        file_path = filedialog.askopenfilename(
            title="Select POT file",
            filetypes=[("POT files", "*.pot"), ("All files", "*.*")]
        )
        if file_path:
            self.pot_file_addr.set(file_path)
            self.log(f"Selected POT file: {file_path}")
            # Cargar datos automáticamente
            self.load_pot_for_review(force_reload=True)
    
    def toggle_ui_state(self, enabled):
        """Enable/disable UI controls during translation"""
        self.is_translating = not enabled
        
        # Disable all language checkboxes
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.Checkbutton):
                widget.config(state=tk.NORMAL if enabled else tk.DISABLED)
    
    def __get_selected_languages(self):
        return  [lang for lang, var_obj in self.selected_languages.items() if var_obj.get()]
    
    def log(self, message):
        self.log_messages.append(message)
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        self.root.update_idletasks()
    
    def clear_logs(self):
        if not self.is_translating:
            self.log_messages = []
            self.log_area.delete(1.0, tk.END)
            
    def load_review(self):
        if not self.pot_file_addr.get():
            messagebox.showerror("Error", "You must select a POT file first")
            return
        
        lang = self.review_lang.get()
        pot_path = Path(self.pot_file_addr.get())
        po_path = pot_path.parent / f"{lang}.po"
        
        try:
            # Limpiar treeview
            for item in self.review_tree.get_children():
                self.review_tree.delete(item)
                
            # Leer archivo POT (Main)
            pot_entries = self.read_po_entries(pot_path)
            
            # Leer archivo PO (traducción) si existe
            po_entries = {}
            if po_path.exists():
                po_entries = self.read_po_entries(po_path)
            
            # Llenar el treeview
            for msgid, msgstr in pot_entries.items():
                translation = po_entries.get(msgid, "")
                self.review_tree.insert("", tk.END, values=(msgid, translation))
                
            self.log(f"\nLoaded review for language: {lang}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load review: {str(e)}")
    
    def read_po_entries(self, file_path):
        """Lee un archivo PO/POT y devuelve un diccionario con las traducciones"""
        entries = {}
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Parseo simple (esto es básico, podrías usar polib para mejor parsing)
            msgid_blocks = content.split('msgid "')[1:]
            for block in msgid_blocks:
                parts = block.split('msgstr "')
                if len(parts) >= 2:
                    msgid = parts[0].split('"')[0]
                    msgstr = parts[1].split('"')[0]
                    entries[msgid] = msgstr
                    
        except Exception as e:
            self.log(f"Error reading {file_path}: {str(e)}")
        
        return entries

if __name__ == "__main__":
    root = tk.Tk()
    app = PoTranslatorGUI(root)
    root.mainloop()