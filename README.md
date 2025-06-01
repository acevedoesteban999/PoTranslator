# PoTranslator - Herramienta de Traducción para .POT y .PO

Herramienta para convertir archivos .pot a archivos .po traducidos automáticamente usando Google Translate, con interfaz gráfica o por línea de comandos.

![Interfaz Gráfica del Traductor](https://github.com/user-attachments/assets/9e127200-25d4-4367-9768-b2eef11d10e2)

## Cómo Usarlo

1. Instale y active el entorno virtual con las librerías especificadas en requirements.txt
2. Dele acceso a internet al servicio de Python del entorno virtual
3. Ejecute el fichero `PoTranslatorGUI.py` para la interfaz visual o `PoTranslatorConsole.py` para la consola
4. Seleccione la dirección del archivo .pot, los idiomas e inicie a traducir
5. Al finalizar, se crearán las traducciones junto al archivo .pot en caso de tener seleccionada la opción `Guardar archivos en el directorio del archivo POT` , de lo contrario se creará una carpeta en la raíz del directorio dentro de `translations` con el nombre del .pot como carpeta donde se ubicarán las traducciones
