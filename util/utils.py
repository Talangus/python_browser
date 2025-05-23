import os
import re
from datetime import datetime, timedelta
from pathlib import Path

class CustomError(Exception):
    pass


DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

COOKIE_JAR = {}

def generate_host_key(host, port):
        return host + ':' + str(port)

def split_pathname(pathname):
    directory_path, file_name = os.path.split(pathname)
    return directory_path, file_name
        
def generate_expiration_date(seconds):
    now = datetime.now()
    delta = timedelta(seconds=seconds)
    future_time = now + delta
    future_time_str = future_time.strftime(DATE_FORMAT)

    return future_time_str

def is_expired(time_str):
     valid_until = datetime.strptime(time_str, DATE_FORMAT)
     now = datetime.now()

     return valid_until < now

def read_utf8_line(line_bytes):
    text_and_newline = line_bytes.decode('utf-8')
    text = text_and_newline[:-2]

    return text

def remove_delimiter(content):
    delimiter_length = len('\r\n')
    return content[:-delimiter_length]

def get_emoji_png_path(code_point_hex):
    emoji_dir = "./openmoji-618x618-color"
    filename = f"{code_point_hex}.png"
    path = Path(os.path.join(emoji_dir, filename))

    return path

def match_on_text_direction(str):
    right_to_left_pattern = r'(?P<rtl>[\u0590-\u08FF]+)'
    left_to_right_pattern = r'(?P<ltr>[^\u0590-\u08FF]+)'
    combined_pattern = f'({right_to_left_pattern})|({left_to_right_pattern})'
    
    matches = re.finditer(combined_pattern, str)
    return matches

def is_paragraph_break(lines_queue):
    if len(lines_queue) == 0:
        return False
    
    next_line = lines_queue[0]
    return next_line == ''

def tree_to_list(tree, list):
    list.append(tree)
    for child in tree.children:
        tree_to_list(child, list)
    return list

def print_tree(node, indent=0):
    print(" " * indent, node)
    for child in node.children:
        print_tree(child, indent + 2)

def cascade_priority(rule):
    selector, body = rule
    return selector.priority

def px_str_to_int(px_str):
    return int(float(px_str[:-2]) * .75)

def has_px_ending(property):
    return property[-2:] == 'px'

def is_leaf(node):
    return len(node.children) == 0

def paint_tree(layout_object, display_list):
    if layout_object.should_paint():
        cmds = layout_object.paint()
    for child in layout_object.children:
        paint_tree(child, display_list)

    if layout_object.should_paint_effects():
        cmds = layout_object.paint_effects(cmds)
    display_list.extend(cmds)

def clicked_on_obj(x,y, obj):
    return obj.x <= x < obj.x + obj.width and obj.y <= y < obj.y + obj.height

def is_get_form_method(element):
    return "method" in element.attributes and element.attributes["method"] == 'get'

def is_checkbox(node):
    return node.is_tag("input") and node.has_attribute("type", "checkbox")

def parse_cookie(cookie):
    params = {}
    if ";" in cookie:
        cookie, rest = cookie.split(";", 1)
        for param in rest.split(";"):
            if '=' in param:
                param, value = param.split("=", 1)
            else:
                value = "true"
            params[param.strip().casefold()] = value.casefold()
    
    if "expires" in params:
        params["expires"] = parse_expires(params["expires"])

    return (cookie, params)

def is_cookie_expired(parameters):
    if "expires" not in parameters:
        return False
    
    expires = parameters["expires"]
    current_time = datetime.now()

    return current_time > expires


def parse_expires(expires_str):
    try:
        utc_format = "%a, %d-%b-%Y %H:%M:%S %Z"
        parsed_date = datetime.strptime(expires_str, utc_format)
        return parsed_date
    except ValueError as e:
        raise ValueError(f"Invalid expires format: {expires_str}") from e