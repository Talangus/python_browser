import re
import sys
import tkinter
from url import URL
from socket_manager import socket_manager 
from cache import cache
from utils import *

WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
SCROLL_STEP = 100
class Browser:
    def __init__(self):
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(
            self.window, 
            width=WIDTH,
            height=HEIGHT
        )
        self.canvas.pack()
        self.scroll = 0
        self.window.bind("<Down>", self.scrolldown)
    
    def load(self, url):
        body = url.request()
        if url.is_view_source:
            text = body
        else:
            text = lex(body)

        self.display_list = layout(text)
        self.draw() 
        
    def draw(self):
        self.canvas.delete("all")
        for x, y, c in self.display_list:
            if y > self.scroll + HEIGHT: continue
            if y + VSTEP < self.scroll: continue
            self.canvas.create_text(x, y - self.scroll, text=c)

    def scrolldown(self, e):
        self.scroll += SCROLL_STEP
        self.draw()

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

def lex(body):
    in_tag = False
    text = ''
    for c in body:
        if c == "<":
            in_tag = True
        elif c == ">":
            in_tag = False
        elif not in_tag:
            text = text + c
    
    return text

def layout(text):
    display_list = []
    cursor_x, cursor_y = HSTEP, VSTEP
    for c in text:
        display_list.append((cursor_x, cursor_y, c))
        cursor_x += HSTEP
        if cursor_x >= WIDTH - HSTEP:
            cursor_y += VSTEP
            cursor_x = HSTEP
    return display_list

def get_url_arg():
    if len(sys.argv) > 1:
        return sys.argv[1]
    else:
        return URL.DEFAULT_FILE_PATH

if __name__ == "__main__":
    
    url_arg = get_url_arg()
    url = URL(url_arg)
    Browser().load(url)
    tkinter.mainloop()

    socket_manager.close_all()
    cache.clear_expired_entries()

