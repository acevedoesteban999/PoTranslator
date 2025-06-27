from ..util.PoTranslator import PoTranslator
import json
HTML_TEXTS = [
    "<div>Click <a href='example.com'>here</a></div>",
]

FORMATED_TEXTS = [
    "__s0__ Click  __s1__ here __e1__ __e0__",
]

def test_html_preparation():
    translator = PoTranslator()
    prepareds, tags = translator._prepare_html(HTML_TEXTS)
    
    assert all([prepared == formated_text for prepared,formated_text in zip(prepareds,FORMATED_TEXTS)])
    assert tags[0][0]['name'] == 'div' and not tags[0][0]['attrs'] 
    assert tags[0][1]['name'] == 'a' and tags[0][1]['attrs']['href'] == 'example.com'

def test_html_restoration():
    translator = PoTranslator()
    translated = FORMATED_TEXTS
    tags = [
        {
            0: {'name': 'div', 'attrs': None},
            1: {'name': 'a', 'attrs': {'href': 'example.com'}}
        }
    ]
    restoreds = translator._restore_html(translated, tags)
    assert all([prepared == html_text for prepared,html_text in zip(restoreds,HTML_TEXTS)])