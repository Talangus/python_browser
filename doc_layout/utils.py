import skia

FONTS = {}
DEFAULT_FONT_FAMILY = "Arial"
DEFAULT_WEIGHT = "normal"
DEFAULT_STYLE= "roman"
DEFAULT_SIZE = 12
INPUT_WIDTH_PX = 200
NAMED_COLORS = {
    "black": "#000000",
    "white": "#ffffff",
    "red": "#ff0000",
    "green": "#008000",
    "blue": "#0000ff",
    "yellow": "#ffff00",
    "cyan": "#00ffff",
    "magenta": "#ff00ff",
    "gray": "#808080",
    "maroon": "#800000",
    "olive": "#808000",
    "lime": "#00ff00",
    "teal": "#008080",
    "navy": "#000080",
    "purple": "#800080",
    "silver": "#c0c0c0",
    "orange": "#ffa500",
    "brown": "#a52a2a",
    "gold": "#ffd700",
    "pink": "#ffc0cb",
    "salmon": "#fa8072",
    "coral": "#ff7f50",
    "chocolate": "#d2691e",
    "crimson": "#dc143c",
    "indigo": "#4b0082",
    "violet": "#ee82ee",
    "plum": "#dda0dd",
    "orchid": "#da70d6",
    "turquoise": "#40e0d0",
    "skyblue": "#87ceeb",
    "lightblue": "#add8e6"
}


def get_font(size, weight, style, family):
    key = (weight, style, family)
    if key not in FONTS:
        if weight == "bold":
            skia_weight = skia.FontStyle.kBold_Weight
        else:
            skia_weight = skia.FontStyle.kNormal_Weight
        if style == "italic":
            skia_style = skia.FontStyle.kItalic_Slant
        else:
            skia_style = skia.FontStyle.kUpright_Slant
        skia_width = skia.FontStyle.kNormal_Width
        style_info = \
            skia.FontStyle(skia_weight, skia_width, skia_style)
        font = skia.Typeface(family, style_info)
        FONTS[key] = font
    return skia.Font(FONTS[key], size)

def linespace(font):
    metrics = font.getMetrics()
    return metrics.fDescent - metrics.fAscent

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

def parse_color(color):
    if color.startswith("#") and len(color) == 7:
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)
        return skia.Color(r, g, b)
    elif color in NAMED_COLORS:
        return parse_color(NAMED_COLORS[color])
    else:
        return skia.ColorBLACK