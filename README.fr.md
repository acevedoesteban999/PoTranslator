# Peut

## Traduction de réadme

-   [Anglais](README.md)
-   [Espagnol](README.es.md)
-   [portugais](README.pt.md)
-   [Français](README.fr.md)

Outil pour convertir les fichiers .pot en fichiers .po traduits automatiquement à l'aide de Google Translate, avec une interface graphique ou une ligne de commande.

![Translator Graphical Interface](https://github.com/user-attachments/assets/48377205-6435-4919-b549-091cec595f8f)

## Outil de traduction pour .pot et .po

## Comment utiliser

1.  Installez et activez l'environnement virtuel avec les bibliothèques spécifiées dans exigences.txt
2.  Provide internet access to the Python service in the virtual environment
3.  Exécuter le fichier`PoTranslatorGUI.py`pour l'interface graphique ou`PoTranslatorConsole.py`pour la console
4.  Sélectionnez le chemin du fichier .pot, les langues et commencez à traduire
5.  Une fois terminé, des traductions seront créées à côté du fichier .pot si l'option`Save files in the POT file directory`est sélectionné; Sinon, un dossier sera créé dans le répertoire racine à l'intérieur`translations` with the name of the .pot file as the folder where the translations will be located
