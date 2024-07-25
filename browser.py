import re
import sys
from url import URL
from socket_manager import socket_manager 
from cache import cache
from utils import *

def replace_html_entity(regex_match):
    html_entities = {
        "quot": '"', "amp": "&", "lt": "<", "gt": ">"
    }
    entity = regex_match.group(1)
    if entity in html_entities:
        return html_entities[entity]
    else:
        return 'HTML_ENTITY_NOT_SUPOORTED'

def html_decode(string):
    html_encoded_regex = r'&(.*)?;'
    decoded = re.sub(html_encoded_regex, replace_html_entity, string)
    return decoded

def show(body):
    in_tag = False
    output = ''
    for c in body:
        if c == "<":
            in_tag = True
        elif c == ">":
            in_tag = False
        elif not in_tag:
            output = output + c
    decoded = html_decode(output)
    print(decoded)

def load(url):
    body = url.request()
    if url.is_view_source:
        print(body)
    else:
        show(body)    

def get_url_arg():
    if len(sys.argv) > 1:
        return sys.argv[1]
    else:
        return URL.DEFAULT_FILE_PATH

if __name__ == "__main__":
    
    url_arg = get_url_arg()
    url = URL(url_arg)
    load(url)

    socket_manager.close_all()
    cache.clear_expired_entries()

