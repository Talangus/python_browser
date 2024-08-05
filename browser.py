import re
import sys
import tkinter
from url import URL
from socket_manager import socket_manager 
from cache import cache
from coordinate import Coordinate
from utils import *

HSTEP, VSTEP = 13, 18
SCROLL_STEP = 100
class Browser:
    def __init__(self):
        self.width = 800
        self.height = 600
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(
            self.window, 
            width=self.width,
            height=self.height
        )
        self.canvas.pack(fill="both", expand=1)
        self.scroll = 0
        self.window.bind("<Down>", self.on_scrolldown)
        self.window.bind("<Up>", self.on_scrollup)
        self.window.bind("<MouseWheel>", self.on_mouse_wheel)
        self.window.bind("<Configure>", self.on_resize)
    
    def load(self, url):
        body = url.request()
        if url.is_view_source:
            text = body
        else:
            text = lex(body)

        self.text = text
        self.display_list = self.layout(text)
        self.draw() 
        
    def draw(self):
        self.canvas.delete("all")
        self.handle_scrollbar()
        for x, y, c in self.display_list:
            if y > self.scroll + self.height: continue
            if y + VSTEP < self.scroll: continue
            self.canvas.create_text(x, y - self.scroll, text=c)

    def on_scrolldown(self, event):
        tmp_scroll = self.scroll + SCROLL_STEP
        max_scroll = self.get_max_scroll()
        if tmp_scroll > max_scroll:
            tmp_scroll = max_scroll
        
        self.scroll = tmp_scroll
        self.draw()

    def on_scrollup(self, event):
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
        max_scroll = page_bottom - self.height + VSTEP
        
        return max_scroll
    
    def on_mouse_wheel(self, event):
        if event.delta > 0:
            self.on_scrollup(event)
        else:
            self.on_scrolldown(event)

    def on_resize(self, event):
        self.width = event.width
        self.height = event.height
        self.display_list = self.layout(self.text)
        self.draw()

    def layout(self, text):
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
                if self.past_vertical_border(cursor_x):
                    cursor_y += VSTEP
                    cursor_x = HSTEP
            i+=1

        return display_list

    def past_vertical_border(self, cursor_x):
        return cursor_x >= self.width - HSTEP*1.7

    def handle_scrollbar(self):
        if not self.need_scrollbar():
            return
        
        top_left ,bottom_right = self.get_scrollbar_coordinates()
        self.canvas.create_rectangle(*top_left ,*bottom_right, fill="blue")

    def need_scrollbar(self):
        return True
    
    def get_scrollbar_coordinates(self):
        bar_width = VSTEP*0.8
        bar_hight = self.get_scorllbar_hight()
        top_left = self.get_scrollbar_top_left()
        bottom_right = Coordinate(top_left.x + bar_width, top_left.y + bar_hight)

        return top_left ,bottom_right

    def get_scorllbar_hight(self):
        page_bottom = self.get_page_bottom()
        viewport_to_page_ratio = self.height / page_bottom
        scrollbar_hight = viewport_to_page_ratio * self.height
        fit_to_screen_hight = scrollbar_hight * 0.92
        return fit_to_screen_hight
        
    def get_scrollbar_top_left(self):
        page_bottom = self.get_page_bottom()
        scroll_to_bottom_ratio = self.scroll / page_bottom
        scroll_bar_top = scroll_to_bottom_ratio * self.height
        fit_to_screen_top = scroll_bar_top + 3
        top_left = Coordinate(self.width - VSTEP, fit_to_screen_top)
        return top_left



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

def is_paragraph_break(i, text):
    if i == len(text) -1:
        return False
    next_char = text[i+1]
    return next_char == '\n'

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

