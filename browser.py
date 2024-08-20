import re
import sys
import tkinter
import argparse
from collections import deque
from PIL import Image, ImageTk
from url import URL
from socket_manager import socket_manager 
from cache import cache
from coordinate import Coordinate
from utils import *
from html_decode import html_decode, is_emoji_char

HSTEP, VSTEP = 13, 18
SCROLL_STEP = 100

class Browser:
    def __init__(self, alt_text_direction):
        self.width = 800
        self.height = 600
        self.hstep = 13
        self.vstep = 18
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(
            self.window, 
            width=self.width,
            height=self.height
        )
        self.canvas.pack(fill="both", expand=1)
        self.scroll = 0
        self.images = []
        self.window.bind("<Down>", self.on_scrolldown)
        self.window.bind("<Up>", self.on_scrollup)
        self.window.bind("<MouseWheel>", self.on_mouse_wheel)
        self.window.bind("<Configure>", self.on_resize)
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        self.alt_text_direction = alt_text_direction
    
    def load(self, url):
        body = url.request()
        if url.is_view_source:
            text = body
        else:
            text = lex(body)
            text = html_decode(text)
        
        self.text = text
        self.display_list = self.layout(text)
        self.draw() 

        
    def draw(self):
        self.canvas.delete("all")
        self.handle_scrollbar()
        for x, y, c in self.display_list:
            if y > self.scroll + self.height: continue
            if y + self.vstep < self.scroll: continue
            if is_emoji_char(c):
                self.draw_emoji(x, y - self.scroll, c)
            else:
                self.canvas.create_text(x, y - self.scroll, text=c)
    
    def draw_emoji(self, x, y, c):
        code_point = ord(c)
        hex_code = format(code_point, 'X')
        path = get_emoji_png_path(hex_code)

        image = Image.open(path)
        resized_image = image.resize((16, 16))
        tk_image = ImageTk.PhotoImage(resized_image)
        self.images.append(tk_image)

        self.canvas.create_image(x,y, image=tk_image)

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

    def on_close(self):
        socket_manager.close_all()
        cache.clear_expired_entries()
        self.window.destroy()

    def get_page_bottom(self):
        last_index = len(self.display_list) - 1
        last_item = self.display_list[last_index]
        lowest_y = last_item[1]
        return lowest_y
    
    def get_max_scroll(self):
        page_bottom = self.get_page_bottom()
        if page_bottom <= self.height:
            max_scroll = 0
        else:
            max_scroll = page_bottom - self.height + self.vstep
        
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
        cursor_y = self.vstep
        lines = text.splitlines()
        lines_queue = deque(lines)
        
        while len(lines_queue) > 0:
            line = lines_queue.popleft()
            
            if line == '':
                if is_paragraph_break(lines_queue):
                    cursor_y += 1.2 * self.vstep
                    lines_queue.popleft()
                else:
                    cursor_y += self.vstep
                continue

            if self.should_split_line(line):
                line, rest = self.split_line(line)
                lines_queue.appendleft(rest)

            cursor_x = self.get_initial_x(line)
            regex_matches = match_on_text_direction(line)
            
            for match in regex_matches:
                if match.group('rtl'):
                    reversed = match.group('rtl')[::-1]
                    line_part = reversed
                else:
                    line_part = match.group('ltr')

                for index, char in enumerate(line_part):
                    char = line_part[index]
                    display_list.append((cursor_x, cursor_y, char))
                    cursor_x += self.hstep
            
            cursor_y += self.vstep
                    

        return display_list

    def past_vertical_border(self, cursor_x):
        return cursor_x >= self.width - self.hstep*1.7

    def handle_scrollbar(self):
        if not self.need_scrollbar():
            return
        
        top_left ,bottom_right = self.get_scrollbar_coordinates()
        self.canvas.create_rectangle(*top_left ,*bottom_right, fill="blue")

    def need_scrollbar(self):
        scrollbar_hight = self.get_scorllbar_hight()
        return scrollbar_hight < self.height
        
    def get_scrollbar_coordinates(self):
        bar_width = self.vstep*0.8
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
        top_left = Coordinate(self.width - self.vstep, fit_to_screen_top)
        return top_left

    def should_split_line(self, line):
        total_length = len(line) * self.hstep
        max_line_length = self.width - 2*self.hstep
        return max_line_length > 0 and total_length > max_line_length
    
    def get_initial_x(self, line):
        if not self.alt_text_direction:
            return self.hstep
        
        total_length = len(line) * self.hstep
        page_border = self.width - self.hstep
        initial_x = page_border - total_length

        return initial_x

    def split_line(self, line):
        max_line_length = self.width - 2*self.hstep
        max_chars_in_line = int(max_line_length / self.hstep)
        rest = line[max_chars_in_line:]
        line = line[:max_chars_in_line]

        return line, rest

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

def match_on_text_direction(str):
    rtl_pattern = r'(?P<rtl>[\u0590-\u08FF]+)'
    ltr_pattern = r'(?P<ltr>[^\u0590-\u08FF]+)'
    combined_pattern = f'({rtl_pattern})|({ltr_pattern})'
    
    matches = re.finditer(combined_pattern, str)
    return matches

def is_paragraph_break(lines_queue):
    next_line = lines_queue[0]
    return next_line == ''

def parse_arguments():
    parser = argparse.ArgumentParser(description="Simple python browser.")
    
    parser.add_argument("url",
        type=str,
        nargs="?",
        default=URL.DEFAULT_FILE_PATH, 
        help="The URL to process.")
    parser.add_argument(
        "-alt", 
        action="store_true", 
        help="Alternate text direction from right to left"
    )

    args = parser.parse_args()
    return args.url, args.alt

if __name__ == "__main__":
    
    url_arg, alt_arg = parse_arguments()
    url = URL(url_arg)
    Browser(alt_text_direction=alt_arg).load(url)
    tkinter.mainloop()

    

