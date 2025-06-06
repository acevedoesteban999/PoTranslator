import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from util.PoTranslator import PoTranslator
import asyncio
from pathlib import Path
import threading
import shutil
from functools import partial

class PoTranslatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PoTranslator")
        self.root.geometry("700x600")
        
        # Variables
        self.pot_file = tk.StringVar()
        self.selected_languages = {}
        self.log_messages = []
        self.batch_size = tk.IntVar(value=250)  # Default value
        self.is_translating = False
        self.output_in_source_dir = tk.BooleanVar(value=True)
        self.use_output_in_source_dir = tk.BooleanVar(value=True)
        
        # Create widgets
        self.create_widgets()
        
    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # POT file section
        file_frame = ttk.LabelFrame(main_frame, text="POT File", padding="10")
        file_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(file_frame, text=".Pot file:").grid(row=0, column=0, sticky=tk.W)
        
        # Entry with expandable width
        pot_entry = ttk.Entry(file_frame, textvariable=self.pot_file)
        pot_entry.grid(row=0, column=1, padx=5, sticky=tk.EW)
        
        # Configure grid to make entry expandable
        file_frame.columnconfigure(1, weight=1)
        
        ttk.Button(file_frame, text="Browse", command=self.browse_pot_file).grid(row=0, column=2)
        
        # Configuration section
        config_frame = ttk.LabelFrame(main_frame, text="Settings", padding="10")
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
        lang_frame = ttk.LabelFrame(main_frame, text="Target Languages", padding="10")
        lang_frame.pack(fill=tk.X, pady=5)
        
        languages = [
            ("Spanish (es)", "es"),
            ("Portuguese (pt)", "pt"),
            ("French (fr)", "fr"),
            ("Italian (it)", "it"),
            ("German (de)", "de"),
            ("English (en)", "en"),
        ]
        
        for i, (text, code) in enumerate(languages):
            var = tk.BooleanVar()
            cb = ttk.Checkbutton(lang_frame, text=text, variable=var)
            cb.grid(row=i//3, column=i%3, sticky=tk.W, padx=5, pady=2)
            self.selected_languages[code] = var
        
        # Execution section
        exec_frame = ttk.Frame(main_frame, padding="10")
        exec_frame.pack(fill=tk.X, pady=5)
        
        self.translate_btn = ttk.Button(exec_frame, text="Translate", command=self.start_translation)
        self.translate_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(exec_frame, text="Clear Logs", command=self.clear_logs).pack(side=tk.LEFT, padx=5)
        
        # Log area
        log_frame = ttk.LabelFrame(main_frame, text="Execution Logs", padding="10")
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

if __name__ == "__main__":
    root = tk.Tk()
    app = PoTranslatorGUI(root)
    root.mainloop()