from kivy.uix.textinput import TextInput


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
