import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from util.PoTranslator import PoTranslator
import asyncio
from pathlib import Path
import threading
import shutil
from functools import partial

class PoTranslatorGUI:
    languages = [
            ("Spanish (es)", "es"),
            ("Portuguese (pt)", "pt"),
            ("French (fr)", "fr"),
            ("Italian (it)", "it"),
            ("German (de)", "de"),
            ("English (en)", "en"),
        ]
    
    def __init__(self, root):
        self.root = root
        self.root.title("PoTranslator")
        self.root.geometry("900x700")  # Aumenté el tamaño para mejor visualización
        
        # Variables
        self.pot_file = tk.StringVar()
        self.selected_languages = {}
        self.log_messages = []
        self.batch_size = tk.IntVar(value=250)
        self.is_translating = False
        self.output_in_source_dir = tk.BooleanVar(value=True)
        self.use_output_in_source_dir = tk.BooleanVar(value=True)
        self.review_lang = tk.StringVar(value="es")
        self.review_data = []
        
        # Create widgets
        self.create_widgets()
    
    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # POT file section (siempre visible arriba)
        self.create_pot_file_section(main_frame)
        
        # Notebook (pestañas)
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Pestaña de revisión
        self.create_review_tab()
        
        # Pestaña de ejecución
        self.create_execution_tab()
    
    def create_pot_file_section(self, parent):
        """Sección del archivo POT que siempre está visible"""
        file_frame = ttk.LabelFrame(parent, text="POT File", padding="10")
        file_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(file_frame, text=".pot file:").grid(row=0, column=0, sticky=tk.W)
        
        pot_entry = ttk.Entry(file_frame, textvariable=self.pot_file)
        pot_entry.grid(row=0, column=1, padx=5, sticky=tk.EW)
        
        file_frame.columnconfigure(1, weight=1)  # Hace que el Entry se expanda
        
        ttk.Button(file_frame, text="Browse", command=self.browse_pot_file).grid(row=0, column=2)
    
    def create_review_tab(self):
        """Crea la pestaña de revisión"""
        review_tab = ttk.Frame(self.notebook)
        self.notebook.add(review_tab, text="Translation Review")
        
        # Frame para controles de revisión
        controls_frame = ttk.Frame(review_tab, padding="10")
        controls_frame.pack(fill=tk.X)
        
        ttk.Label(controls_frame, text="Review language:").pack(side=tk.LEFT, padx=5)
        
        lang_combo = ttk.Combobox(controls_frame, textvariable=self.review_lang, 
                                 values=[lang for _,lang in self.languages], width=5)
        lang_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(controls_frame, text="Load Review", 
                  command=self.load_review).pack(side=tk.LEFT, padx=5)
        
        # Treeview para mostrar la comparación
        tree_frame = ttk.Frame(review_tab)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        columns = ("Original", "Translation")
        self.review_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=20)
        
        # Configurar columnas
        self.review_tree.heading("Original", text="Original Text (.pot)")
        self.review_tree.heading("Translation", text="Translated Text (.po)")
        self.review_tree.column("Original", width=400, stretch=tk.YES)
        self.review_tree.column("Translation", width=400, stretch=tk.YES)
        
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
    
    def create_execution_tab(self):
        """Crea la pestaña de ejecución con configuraciones"""
        exec_tab = ttk.Frame(self.notebook)
        self.notebook.add(exec_tab, text="Translation Execution")
        
        # Configuración frame
        config_frame = ttk.LabelFrame(exec_tab, text="Settings", padding="10")
        config_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(config_frame, text="Batch size:").grid(row=0, column=0, sticky=tk.W)
        ttk.Spinbox(config_frame, from_=1, to=500, textvariable=self.batch_size, width=10).grid(row=0, column=1, sticky=tk.W, padx=5)
        
        ttk.Checkbutton(
            config_frame, 
            text="Save files in the POT file directory",
            variable=self.output_in_source_dir
        ).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        ttk.Checkbutton(
            config_frame, 
            text="Use .PO Data from POT file directory",
            variable=self.use_output_in_source_dir
        ).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Languages section
        lang_frame = ttk.LabelFrame(exec_tab, text="Target Languages", padding="10")
        lang_frame.pack(fill=tk.X, pady=5)
        
        
        
        for i, (text, code) in enumerate(self.languages):
            var = tk.BooleanVar()
            cb = ttk.Checkbutton(lang_frame, text=text, variable=var)
            cb.grid(row=i//3, column=i%3, sticky=tk.W, padx=5, pady=2)
            self.selected_languages[code] = var
        
        # Execution buttons
        btn_frame = ttk.Frame(exec_tab, padding="10")
        btn_frame.pack(fill=tk.X)
        
        self.translate_btn = ttk.Button(btn_frame, text="Translate", command=self.start_translation)
        self.translate_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text="Clear Logs", command=self.clear_logs).pack(side=tk.LEFT, padx=5)
        
        # Log area
        log_frame = ttk.LabelFrame(exec_tab, text="Execution Logs", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_area = scrolledtext.ScrolledText(log_frame, height=15, wrap=tk.WORD)
        self.log_area.pack(fill=tk.BOTH, expand=True)
    
    def browse_pot_file(self):
        if self.is_translating:
            return
            
        file_path = filedialog.askopenfilename(
            title="Select POT file",
            filetypes=[("POT files", "*.pot"), ("All files", "*.*")]
        )
        if file_path:
            self.pot_file.set(file_path)
            self.log(f"Selected POT file: {file_path}")
    
    def get_selected_languages(self):
        return [code for code, var in self.selected_languages.items() if var.get()]
    
    def toggle_ui_state(self, enabled):
        """Enable/disable UI controls during translation"""
        self.is_translating = not enabled
        self.translate_btn.config(state=tk.NORMAL if enabled else tk.DISABLED)
        
        # Disable all language checkboxes
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.Checkbutton):
                widget.config(state=tk.NORMAL if enabled else tk.DISABLED)
    
    def start_translation(self):
        if self.is_translating:
            return
            
        if not self.pot_file.get():
            messagebox.showerror("Error", "You must select a POT file")
            return
            
        selected = self.get_selected_languages()
        if not selected:
            messagebox.showerror("Error", "You must select at least one language")
            return
            
        self.log("\nStarting translation process...")
        self.log(f"File: {self.pot_file.get()}")
        self.log(f"Languages: {', '.join(selected)}")
        self.log(f"Batch size: {self.batch_size.get()}")
        
        self.toggle_ui_state(False)
        
        # Run in a separate thread to avoid blocking the UI
        threading.Thread(
            target=self.run_translation,
            args=(self.pot_file.get(), selected, self.batch_size.get()),
            daemon=True
        ).start()
    
    def run_translation(self, pot_file, languages, batch_size):
        try:
            translator = PoTranslator(
                input_pot_file=pot_file, 
                batch_size=batch_size, 
                delay=1,
                output_in_source_dir=self.output_in_source_dir.get(),
                use_output_in_source_dir=self.use_output_in_source_dir.get(),
                log_funct=self.log,
            )
            
            # We need to run the asyncio coroutine in its own loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            for lang in languages:
                self.log(f"\nTranslating to '{lang}'...")
                
                # Create and configure the coroutine
                coro = translator.translate_po_file(dest_lang=lang)
                
                # Run the coroutine
                loop.run_until_complete(coro)
                
                self.log(f"Translation to '{lang}' completed")
            
            self.log("\nTranslation completed successfully!")
            
            # Show location of generated files
            pot_name = Path(pot_file).stem
            output_dir = Path(f"translations/{pot_name}")
            self.log(f"Files saved in: {output_dir.resolve()}")
            for lang in languages:
                self.log(f"- {lang}.po")
            
        except Exception as e:
            self.log(f"\nError during translation: {str(e)}")
        finally:
            loop.close()
            self.root.after(100, partial(self.toggle_ui_state, True))
    
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
        if not self.pot_file.get():
            messagebox.showerror("Error", "You must select a POT file first")
            return
        
        lang = self.review_lang.get()
        pot_path = Path(self.pot_file.get())
        po_path = pot_path.parent / f"{lang}.po"
        
        try:
            # Limpiar treeview
            for item in self.review_tree.get_children():
                self.review_tree.delete(item)
                
            # Leer archivo POT (original)
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