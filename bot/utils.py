import re
import string

PUNCTUATION = string.punctuation


def only_digits(text):
    return "".join(_ for _ in text if _ in ".1234567890")


def prettify(string):
    PRETTIFY_RE = {
            # match repetitions of signs that should not be repeated (like multiple spaces or duplicated quotes)
            'DUPLICATES': re.compile(
                r'(\({2,}|\){2,}|\[{2,}|\]{2,}|\{{2,}|\}{2,}|:{2,}|,{2,}|;{2,}|\+{2,}|\-{2,}|\s{2,}|%{2,}|={2,}|"{2,}|\'{2,})',
                re.MULTILINE
            ),
            # check that a sign cannot have a space before or missing a space after,
            # unless it is a dot or a comma, where numbers may follow (5.5 or 5,5 is ok)
            'RIGHT_SPACE': re.compile(
                r'('
                r'(?<=[^\s\d]),(?=[^\s\d])|\s,\s|\s,(?=[^\s\d])|\s,(?!.)|'  # comma (,)
                r'(?<=[^\s\d\.])\.+(?=[^\s\d\.])|\s\.+\s|\s\.+(?=[^\s\d])|\s\.+(?!\.)|'  # dot (.)
                r'(?<=\S);(?=\S)|\s;\s|\s;(?=\S)|\s;(?!.)|'  # semicolon (;)
                r'(?<=\S):(?=\S)|\s:\s|\s:(?=\S)|\s:(?!.)|'  # colon (:)
                r'(?<=[^\s!])!+(?=[^\s!])|\s!+\s|\s!+(?=[^\s!])|\s!+(?!!)|'  # exclamation (!)
                r'(?<=[^\s\?])\?+(?=[^\s\?])|\s\?+\s|\s\?+(?=[^\s\?])|\s\?+(?!\?)|'  # question (?)
                r'\d%(?=\S)|(?<=\d)\s%\s|(?<=\d)\s%(?=\S)|(?<=\d)\s%(?!.)'  # percentage (%)
                r')',
                re.MULTILINE | re.DOTALL
            ),
            'LEFT_SPACE': re.compile(
                r'('
    
                # quoted text ("hello world")
                r'\s"[^"]+"(?=[\?\.:!,;])|(?<=\S)"[^"]+"\s|(?<=\S)"[^"]+"(?=[\?\.:!,;])|'
    
                # text in round brackets
                r'\s\([^\)]+\)(?=[\?\.:!,;])|(?<=\S)\([^\)]+\)\s|(?<=\S)(\([^\)]+\))(?=[\?\.:!,;])'
    
                r')',
                re.MULTILINE | re.DOTALL
            ),
            # match chars that must be followed by uppercase letters (like ".", "?"...)
            'UPPERCASE_AFTER_SIGN': re.compile(
                r'([\.\?!]\s\w)',
                re.MULTILINE | re.UNICODE
            ),
            'SPACES_AROUND': re.compile(
                r'('
                r'(?<=\S)\+(?=\S)|(?<=\S)\+\s|\s\+(?=\S)|'  # plus (+)
                r'(?<=\S)\-(?=\S)|(?<=\S)\-\s|\s\-(?=\S)|'  # minus (-)
                r'(?<=\S)/(?=\S)|(?<=\S)/\s|\s/(?=\S)|'  # division (/)
                r'(?<=\S)\*(?=\S)|(?<=\S)\*\s|\s\*(?=\S)|'  # multiplication (*)
                r'(?<=\S)=(?=\S)|(?<=\S)=\s|\s=(?=\S)|'  # equal (=)
    
                # quoted text ("hello world")
                r'\s"[^"]+"(?=[^\s\?\.:!,;])|(?<=\S)"[^"]+"\s|(?<=\S)"[^"]+"(?=[^\s\?\.:!,;])|'
    
                # text in round brackets
                r'\s\([^\)]+\)(?=[^\s\?\.:!,;])|(?<=\S)\([^\)]+\)\s|(?<=\S)(\([^\)]+\))(?=[^\s\?\.:!,;])'
    
                r')',
                re.MULTILINE | re.DOTALL
            ),
            'SPACES_INSIDE': re.compile(
                r'('
                r'(?<=")[^"]+(?=")|'  # quoted text ("hello world")
                r'(?<=\()[^\)]+(?=\))'  # text in round brackets
                r')',
                re.MULTILINE | re.DOTALL
            ),
            'SAXON_GENITIVE': re.compile(
                r'('
                r'(?<=\w)\'\ss\s|(?<=\w)\s\'s(?=\w)|(?<=\w)\s\'s\s(?=\w)'
                r')',
                re.MULTILINE | re.UNICODE
            )
    }

    def remove_duplicates(regex_match):
        return regex_match.group(1)[0]

    def uppercase_first_letter_after_sign(regex_match):
        match = regex_match.group(1)
        return match[:-1] + match[2].upper()

    def ensure_right_space_only(regex_match):
        return regex_match.group(1).strip() + ' '

    def ensure_left_space_only(regex_match):
        return ' ' + regex_match.group(1).strip()

    def ensure_spaces_around(regex_match):
        return ' ' + regex_match.group(1).strip() + ' '

    def remove_internal_spaces(regex_match):
        return regex_match.group(1).strip()

    def fix_saxon_genitive(regex_match):
        return regex_match.group(1).replace(' ', '') + ' '

    p = PRETTIFY_RE['DUPLICATES'].sub(remove_duplicates, string)
    p = PRETTIFY_RE['RIGHT_SPACE'].sub(ensure_right_space_only, p)
    p = PRETTIFY_RE['LEFT_SPACE'].sub(ensure_left_space_only, p)
    p = PRETTIFY_RE['SPACES_AROUND'].sub(ensure_spaces_around, p)
    p = PRETTIFY_RE['SPACES_INSIDE'].sub(remove_internal_spaces, p)
    p = PRETTIFY_RE['UPPERCASE_AFTER_SIGN'].sub(uppercase_first_letter_after_sign, p)
    p = PRETTIFY_RE['SAXON_GENITIVE'].sub(fix_saxon_genitive, p)
    p = re.sub('['+PUNCTUATION+']', '', p)
    p = p.strip().lower()
    try:
        return p[0] + p[1:]
    except IndexError:
        return p