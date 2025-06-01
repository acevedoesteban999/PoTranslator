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
        self.batch_size = tk.IntVar(value=250)  # Valor por defecto
        self.is_translating = False
        
        # Crear widgets
        self.create_widgets()
        
    def create_widgets(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Sección de archivo POT
        file_frame = ttk.LabelFrame(main_frame, text="Archivo POT", padding="10")
        file_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(file_frame, text="Archivo .pot:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(file_frame, textvariable=self.pot_file, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(file_frame, text="Examinar", command=self.browse_pot_file).grid(row=0, column=2)
        
        # Sección de configuración
        config_frame = ttk.LabelFrame(main_frame, text="Configuración", padding="10")
        config_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(config_frame, text="Tamaño del lote:").grid(row=0, column=0, sticky=tk.W)
        ttk.Spinbox(config_frame, from_=1, to=500, textvariable=self.batch_size, width=10).grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # Sección de idiomas
        lang_frame = ttk.LabelFrame(main_frame, text="Idiomas de Destino", padding="10")
        lang_frame.pack(fill=tk.X, pady=5)
        
        languages = [
            ("Español (es)", "es"),
            ("Inglés (en)", "en"),
            ("Portugués (pt)", "pt"),
            # ("Francés (fr)", "fr"),
            # ("Italiano (it)", "it"),
            # ("Alemán (de)", "de")
        ]
        
        for i, (text, code) in enumerate(languages):
            var = tk.BooleanVar()
            cb = ttk.Checkbutton(lang_frame, text=text, variable=var)
            cb.grid(row=i//3, column=i%3, sticky=tk.W, padx=5, pady=2)
            self.selected_languages[code] = var
        
        # Sección de ejecución
        exec_frame = ttk.Frame(main_frame, padding="10")
        exec_frame.pack(fill=tk.X, pady=5)
        
        self.translate_btn = ttk.Button(exec_frame, text="Traducir", command=self.start_translation)
        self.translate_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(exec_frame, text="Limpiar Logs", command=self.clear_logs).pack(side=tk.LEFT, padx=5)
        
        # Área de logs
        log_frame = ttk.LabelFrame(main_frame, text="Logs de Ejecución", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_area = scrolledtext.ScrolledText(log_frame, height=15, wrap=tk.WORD)
        self.log_area.pack(fill=tk.BOTH, expand=True)
    
    def browse_pot_file(self):
        if self.is_translating:
            return
            
        file_path = filedialog.askopenfilename(
            title="Seleccionar archivo POT",
            filetypes=[("POT files", "*.pot"), ("All files", "*.*")]
        )
        if file_path:
            self.pot_file.set(file_path)
            self.log(f"Archivo POT seleccionado: {file_path}")
    
    def get_selected_languages(self):
        return [code for code, var in self.selected_languages.items() if var.get()]
    
    def toggle_ui_state(self, enabled):
        """Habilita/deshabilita los controles de la UI durante la traducción"""
        self.is_translating = not enabled
        self.translate_btn.config(state=tk.NORMAL if enabled else tk.DISABLED)
        
        # Deshabilitar todos los checkboxes de idiomas
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.Checkbutton):
                widget.config(state=tk.NORMAL if enabled else tk.DISABLED)
    
    def start_translation(self):
        if self.is_translating:
            return
            
        if not self.pot_file.get():
            messagebox.showerror("Error", "Debe seleccionar un archivo POT")
            return
            
        selected = self.get_selected_languages()
        if not selected:
            messagebox.showerror("Error", "Debe seleccionar al menos un idioma")
            return
            
        self.log("\nIniciando proceso de traducción...")
        self.log(f"Archivo: {self.pot_file.get()}")
        self.log(f"Idiomas: {', '.join(selected)}")
        self.log(f"Tamaño de lote: {self.batch_size.get()}")
        
        self.toggle_ui_state(False)
        
        # Ejecutar en un hilo separado para no bloquear la interfaz
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
                delay=1
            )
            
            # Necesitamos correr la corutina asyncio en su propio loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            for lang in languages:
                self.log(f"\nTraduciendo a {lang}...")
                
                # Crear y configurar la corutina
                coro = translator.translate_po_file(dest_lang=lang)
                
                # Ejecutar la corutina
                loop.run_until_complete(coro)
                
                self.log(f"Traducción a {lang} completada")
            
            self.log("\n¡Traducción completada con éxito!")
            
            # Mostrar ubicación de los archivos generados
            pot_name = Path(pot_file).stem
            output_dir = Path(f"translations/{pot_name}")
            self.log(f"\nArchivos guardados en: {output_dir.resolve()}")
            for lang in languages:
                self.log(f"- {lang}.po")
            
        except Exception as e:
            self.log(f"\nError durante la traducción: {str(e)}")
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