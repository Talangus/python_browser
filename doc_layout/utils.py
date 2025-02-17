import tkinter.font

FONTS = {}
DEFAULT_FONT_FAMILY = "Arial"
DEFAULT_WEIGHT = "normal"
DEFAULT_STYLE= "roman"
DEFAULT_SIZE = 12
INPUT_WIDTH_PX = 200

def get_font(size, weight, style, family):
        key = (size, weight, style, family)
        if key not in FONTS:
            font = tkinter.font.Font(size=size, weight=weight,
                slant=style, family=family)
            label = tkinter.Label(font=font)
            FONTS[key] = (font, label)
        return FONTS[key][0]

def get_html_node_font(node):
    weight = node.style["font-weight"]
    style = node.style["font-style"]
    if style == "normal": style = "roman"
    size = int(float(node.style["font-size"][:-2]) * .75)
    font_family = node.style["font-family"]

    return get_font(size, weight, style, font_family)

def last_line_is_empty(last_line):
        if last_line is None:
            return False
        
        return len(last_line.children) == 0

def get_object_index(arr, obj):
    for index, curr_obj in enumerate(arr):
         if curr_obj is obj:
              return index
    return -1     

def split_on_object(arr, split_obj):
    split_index = get_object_index(arr, split_obj)
         
    if split_index > -1:
        return arr[:split_index], arr[split_index:]
    else:
        return arr, []