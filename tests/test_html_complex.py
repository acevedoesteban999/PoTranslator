from ..util.PoTranslator import PoTranslator
def test_complex_html_preparation():
    translator = PoTranslator()
    html_texts = [
        '<div class="container"><p>Hello <strong>world</strong>!</p><a href="test.com" data-id="123">click</a></div>',
        '<ul><li>Item 1</li><li>Item 2</li></ul>'
    ]
    
    prepareds, tags = translator._prepare_html(html_texts)
    
    assert "__s0__" in prepareds[0] and "__e0__" in prepareds[0]
    assert "__s1__" in prepareds[0] and "__e1__" in prepareds[0]
    assert "__s2__" in prepareds[0] and "__e2__" in prepareds[0]
    
    assert tags[0][0]['name'] == 'div'
    assert tags[0][0]['attrs']['class'] == 'container'
    assert tags[0][1]['name'] == 'p'
    assert tags[0][2]['name'] == 'strong'
    assert tags[0][3]['name'] == 'a'
    assert tags[0][3]['attrs']['href'] == 'test.com'
    assert tags[0][3]['attrs']['data-id'] == '123'
    
    assert tags[1][0]['name'] == 'ul'
    assert tags[1][1]['name'] == 'li'
    assert tags[1][2]['name'] == 'li'

def test_complex_html_restoration():
    translator = PoTranslator()
    translated_texts = [
        "__s0__ __s1__ Hello  __s2__ word __e2__ !  __s3__ haga clic __e3__ __e1__ __e0__",
        "__s0__ __s1__ Element 1 __e1__ __s2__ Element 2 __e2__ __e0__"
    ]
    tags = [
        {
            0: {'name': 'div', 'attrs': {'class': 'container'}},
            1: {'name': 'p', 'attrs': None},
            2: {'name': 'strong', 'attrs': None},
            3: {'name': 'a', 'attrs': {'href': 'test.com', 'data-id': '123'}}
        },
        {
            0: {'name': 'ul', 'attrs': None},
            1: {'name': 'li', 'attrs': None},
            2: {'name': 'li', 'attrs': None}
        }
    ]
    
    restored = translator._restore_html(translated_texts, tags)
    
    expected = [
        "<div class='container'><p>Hello <strong>word</strong>! <a href='test.com' data-id='123'>haga clic</a></p></div>",
        "<ul><li>Element 1</li><li>Element 2</li></ul>"
    ]
    
    assert restored == expected