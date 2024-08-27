import re
from utils import *

html_entities = {
    "20": " ",
    "21": "!",
    "22": "\"",
    "23": "#",
    "24": "$",
    "25": "%",
    "26": "&",
    "27": "'",
    "28": "(",
    "29": ")",
    "2A": "*",
    "2B": "+",
    "2C": ",",
    "2D": "-",
    "2E": ".",
    "2F": "/",
    "30": "0",
    "31": "1",
    "32": "2",
    "33": "3",
    "34": "4",
    "35": "5",
    "36": "6",
    "37": "7",
    "38": "8",
    "39": "9",
    "3A": ":",
    "3B": ";",
    "3C": "<",
    "3D": "=",
    "3E": ">",
    "3F": "?",
    "40": "@",
    "41": "A",
    "42": "B",
    "43": "C",
    "44": "D",
    "45": "E",
    "46": "F",
    "47": "G",
    "48": "H",
    "49": "I",
    "4A": "J",
    "4B": "K",
    "4C": "L",
    "4D": "M",
    "4E": "N",
    "4F": "O",
    "50": "P",
    "51": "Q",
    "52": "R",
    "53": "S",
    "54": "T",
    "55": "U",
    "56": "V",
    "57": "W",
    "58": "X",
    "59": "Y",
    "5A": "Z",
    "5B": "[",
    "5C": "\\",
    "5D": "]",
    "5E": "^",
    "5F": "_",
    "60": "`",
    "61": "a",
    "62": "b",
    "63": "c",
    "64": "d",
    "65": "e",
    "66": "f",
    "67": "g",
    "68": "h",
    "69": "i",
    "6A": "j",
    "6B": "k",
    "6C": "l",
    "6D": "m",
    "6E": "n",
    "6F": "o",
    "70": "p",
    "71": "q",
    "72": "r",
    "73": "s",
    "74": "t",
    "75": "u",
    "76": "v",
    "77": "w",
    "78": "x",
    "79.": "y",
    "7A": "z",
    "7B": "{",
    "7C": "|",
    "7D": "}",
    "7E": "~",
    "A9":"©"
}


def is_hexadecimal(str):
    if str.startswith(('0x', '0X')):
        str = str[2:]
    
    return all(char in '0123456789abcdefABCDEF' for char in str) and len(str) > 0

def is_emoji_char(char):
    emoji_pattern = re.compile(
        r'['
        r'\U0001F600-\U0001F64F'  # Emoticons
        r'\U0001F300-\U0001F5FF'  # Miscellaneous Symbols and Pictographs
        r'\U0001F680-\U0001F6FF'  # Transport and Map Symbols
        r'\U0001F700-\U0001F77F'  # Alchemical Symbols
        r'\U0001F780-\U0001F7FF'  # Geometric Shapes Extended
        r'\U0001F800-\U0001F8FF'  # Supplemental Arrows-C
        r'\U0001F900-\U0001F9FF'  # Supplemental Symbols and Pictographs
        r'\U0001FA00-\U0001FA6F'  # Chess Symbols
        r'\U0001FA70-\U0001FAFF'  # Symbols and Pictographs Extended-A
        r'\U00002700-\U000027BF'  # Dingbats
        r'\U000024C2-\U0001F251'  # Enclosed Characters
        r'\U0001F1E0-\U0001F1FF'  # Flags (iOS)
        r']+'
    )
    
    return emoji_pattern.match(char)

def replace_html_entity(regex_match):
    entity = regex_match.group(1)
    hex_code = to_hex_code_point(entity)

    if not is_hexadecimal(hex_code):
        return entity
    
    if is_asci_hex(hex_code): 
        return html_entities[hex_code]

    if is_emoji_hex(hex_code):
        return chr(int(hex_code, 16))   
    
    return entity
    
def to_hex_code_point(entity):
    html_names = {
        "quot": '22', "amp": "26", "lt": "3C", "gt": "3E", "copy": "A9"
    }

    if (entity.startswith("#x")):
        return entity[2:].upper()
    if(entity.startswith("#")):
        decimal_number = int(entity[1:])
        hex_string = hex(decimal_number)[2:]
        return hex_string.upper()

    if entity in html_names:
        return html_names[entity]
    else:
        return entity
    
def is_asci_hex(hex_code):
    num = int(hex_code, 16)
    return num > 0 and num < 170

def is_emoji_hex(hex_code):
    num = int(hex_code, 16)
    return num > 0x1F000

def html_decode(tok):
    if not isinstance(tok, Text):
        return tok

    text = tok.text
    html_encoded_regex = r'&(.*?);'
    decoded = re.sub(html_encoded_regex, replace_html_entity, text)
    return Text(decoded)
