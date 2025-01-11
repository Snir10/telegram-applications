from easygoogletranslate import EasyGoogleTranslate

translator = EasyGoogleTranslate(
    source_language='he',
    target_language='en',
    timeout=10
)
result = translator.translate('למה אתה אומר ככה?')

print(result)
