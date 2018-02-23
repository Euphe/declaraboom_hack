def only_digits(text):
    return "".join(_ for _ in text if _ in ".1234567890")
