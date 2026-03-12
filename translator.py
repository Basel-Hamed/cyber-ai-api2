from deep_translator import GoogleTranslator

def translate_bn(text):

    try:
        return GoogleTranslator(source="auto", target="bn").translate(text)
    except:
        return text
