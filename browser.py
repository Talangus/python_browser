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
        self.window.bind("<Up>", self.scrollup)
    
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
        tmp_scroll = self.scroll + SCROLL_STEP
        max_scroll = self.get_max_scroll()
        if tmp_scroll > max_scroll:
            tmp_scroll = max_scroll
        
        self.scroll = tmp_scroll
        self.draw()

    def scrollup(self, e):
        tmp_scroll = self.scroll - SCROLL_STEP
        if tmp_scroll < 0:
            self.scroll = 0
        else:
            self.scroll = tmp_scroll
        
        self.draw()

    def get_page_bottom(self):
        last_index = len(self.display_list) - 1
        last_item = self.display_list[last_index]
        lowest_y = last_item[1]
        return lowest_y
    
    def get_max_scroll(self):
        page_bottom = self.get_page_bottom()
        max_scroll = page_bottom - HEIGHT + VSTEP
        
        return max_scroll


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
    i = 0

    while i < len(text):
        char = text[i]
        if char == '\n':
            if is_paragraph_break(i, text):
                cursor_y += 1.2 * VSTEP
                i += 1
            else:
                cursor_y += VSTEP
            cursor_x = HSTEP
        else:
            display_list.append((cursor_x, cursor_y, char))
            cursor_x += HSTEP
            if past_vertical_border(cursor_x):
                cursor_y += VSTEP
                cursor_x = HSTEP
        i+=1

    return display_list

def is_paragraph_break(i, text):
    if i == len(text) -1:
        return False
    next_char = text[i+1]
    return next_char == '\n'

def past_vertical_border(cursor_x):
        return cursor_x >= WIDTH - HSTEP

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

