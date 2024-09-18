import tkinter
import argparse
from collections import deque
from PIL import Image, ImageTk
from url import URL
from socket_manager import socket_manager 
from cache import cache
from coordinate import Coordinate
from utils import *
from html_decode import html_decode
from layout import Layout
from html_parser import HTMLParser

class Browser:
    SCROLL_STEP = 100
    HSTEP = 13
    VSTEP = 18
    
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
        self.images = []

        self.window.bind("<Down>", self.on_scrolldown)
        self.window.bind("<Up>", self.on_scrollup)
        self.window.bind("<MouseWheel>", self.on_mouse_wheel)
        self.window.bind("<Configure>", self.on_resize)
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def load(self, url):
        body = url.request()
        nodes = HTMLParser(body).parse()
        self.nodes = html_decode(nodes)
        print_tree(self.nodes)
        self.display_list = Layout(self.nodes,self.width).display_list
        self.draw() 
        
    def draw(self):
        self.canvas.delete("all")
        self.handle_scrollbar()
        for x, y, c, f in self.display_list:
            if self.is_below_viewport(y): continue
            if self.is_above_viewport(y): continue
            self.canvas.create_text(x, y - self.scroll, text=c, anchor='nw', font=f)
    
    def is_below_viewport(self, y):
        return y > self.scroll + self.height
    
    def is_above_viewport(self,y):
        return y + Browser.VSTEP < self.scroll

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
        tmp_scroll = self.scroll + Browser.SCROLL_STEP
        max_scroll = self.get_max_scroll()
        if tmp_scroll > max_scroll:
            tmp_scroll = max_scroll
        
        self.scroll = tmp_scroll
        self.draw()

    def get_max_scroll(self):
        page_bottom = self.get_page_bottom()
        if page_bottom <= self.height:
            max_scroll = 0
        else:
            max_scroll = page_bottom - self.height + Browser.VSTEP
        
        return max_scroll
    
    def get_page_bottom(self):
        if len(self.display_list) ==0:
            return 0.001
        last_index = len(self.display_list) - 1
        last_item = self.display_list[last_index]
        lowest_y = last_item[1]
        return lowest_y

    def on_scrollup(self, event):
        tmp_scroll = self.scroll - Browser.SCROLL_STEP
        if tmp_scroll < 0:
            self.scroll = 0
        else:
            self.scroll = tmp_scroll
        
        self.draw()

    def on_close(self):
        socket_manager.close_all()
        cache.clear_expired_entries()
        self.window.destroy()

    def on_mouse_wheel(self, event):
        if event.delta > 0:
            self.on_scrollup(event)
        else:
            self.on_scrolldown(event)

    def on_resize(self, event):
        self.width = event.width
        self.height = event.height
        self.display_list = Layout(self.nodes,self.width).display_list
        self.draw()

    def handle_scrollbar(self):
        if not self.need_scrollbar():
            return
        
        top_left ,bottom_right = self.get_scrollbar_coordinates()
        self.canvas.create_rectangle(*top_left ,*bottom_right, fill="blue")

    def need_scrollbar(self):
        scrollbar_hight = self.get_scorllbar_hight()
        return scrollbar_hight < self.height
        
    def get_scrollbar_coordinates(self):
        bar_width = Browser.VSTEP*0.8
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
        top_left = Coordinate(self.width - Browser.VSTEP, fit_to_screen_top)
        return top_left
    
def parse_arguments():
    parser = argparse.ArgumentParser(description="Simple python browser.")
    
    parser.add_argument("url",
        type=str,
        nargs="?",
        default=URL.DEFAULT_FILE_PATH, 
        help="The URL to process.")
    
    args = parser.parse_args()
    return args.url

if __name__ == "__main__":
    
    url_arg = parse_arguments()
    url = URL(url_arg)
    Browser().load(url)
    tkinter.mainloop()

    

