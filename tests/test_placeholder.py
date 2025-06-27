from ..util.PoTranslator import PoTranslator
def test_placeholder_preparation():
    translator = PoTranslator()
    texts = [
        "Hello %s, your balance is {balance}",
        "Click [here] to confirm %(action)s"
    ]
    expected_prepared = [
        "Hello __0__, your balance is __1__",
        "Click __0__ to confirm __1__"
    ]
    expected_placeholders = [
        {'%s', '{balance}'},
        {'[here]', '%(action)s'}
    ]
    
    prepared, placeholders = translator._prepare_placeholders(texts)
    
    assert prepared == expected_prepared
    assert [set(p) for p in placeholders] == expected_placeholders

def test_placeholder_restoration():
    translator = PoTranslator()
    translated_texts = [
        "Hola __0__, su saldo es __1__",
        "Haga clic __0__ para confirmar __1__"
    ]
    placeholders = [
        ['%s', '{balance}'],
        ['[here]', '%(action)s']
    ]
    expected_restored = [
        "Hola %s, su saldo es {balance}",
        "Haga clic [here] para confirmar %(action)s"
    ]
    
    restored = translator._restore_placeholders(translated_texts, placeholders)
    assert restored == expected_restored