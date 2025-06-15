from kivy.app import App
from kivy.lang import Builder
from util.kivy.PoTranslatorGUI import PoTranslatorGUI

Builder.load_file('./util/kivy/PoTranslator.kv')


class PoTranslatorApp(App):
    def build(self):
        return PoTranslatorGUI()

if __name__ == '__main__':
    PoTranslatorApp().run()