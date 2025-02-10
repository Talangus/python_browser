import tkinter
import argparse

from network.url import URL
from network.socket_manager import socket_manager 
from network.cache import cache
from tab import Tab
from window_layout.chrome import Chrome
from util.utils import *


class Browser:
    def __init__(self):
        self.tabs = []
        self.active_tab = None
        self.width = 800
        self.height = 600
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(
            self.window, 
            width=self.width,
            height=self.height,
            bg="white"
        )
        self.canvas.pack(fill="both", expand=1)
        self.chrome = Chrome(self)
        self.focus = None

        self.window.bind("<Down>", self.handle_scrolldown)
        self.window.bind("<Up>", self.handle_scrollup)
        self.window.bind("<Button-1>", self.handle_click)
        self.window.bind("<MouseWheel>", self.handle_mouse_wheel)
        self.window.bind("<Configure>", self.handle_resize)
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        self.window.bind("<Key>", self.handle_key)
        self.window.bind("<Return>", self.handle_enter)
        self.window.bind("<BackSpace>", self.handle_backspace)
        self.window.bind("<Button-3>", self.handle_middle_click)



    def handle_scrolldown(self, e):
        self.active_tab.tab_layout.on_scrolldown()
        self.draw()

    def handle_scrollup(self, e):
        self.active_tab.tab_layout.on_scrollup()
        self.draw()

    def handle_click(self, e):
        if e.y < self.chrome.bottom:
            if self.focus == 'content':
                self.active_tab.blur()
            self.focus = None
            self.chrome.click(e.x, e.y)
        else:
            self.focus = 'content'
            self.chrome.blur()
            tab_y = e.y - self.chrome.bottom
            self.active_tab.click(e.x, tab_y)
        self.draw()

    def handle_middle_click(self, e):
        if e.y >= self.chrome.bottom:
            tab_y = e.y - self.chrome.bottom
            url = self.active_tab.get_clicked_url(e.x, tab_y)
            if url:
                self.new_tab(url)
                self.draw()

    def handle_mouse_wheel(self, e):
        self.active_tab.tab_layout.on_mouse_wheel(e)
        self.draw()

    def handle_resize(self, event):
        if event.width == 1 or event.height == 1:
            return
        
        self.width = event.width
        self.height = event.height
        self.active_tab.on_resize(event.width, event.height)
        self.draw()

    def handle_key(self, e):
        if len(e.char) == 0: return
        if not (0x20 <= ord(e.char) < 0x7f): return

        if self.chrome.keypress(e.char):
            self.draw()
        elif self.focus == "content":
            self.active_tab.keypress(e.char)
            self.draw()

    def handle_enter(self, e):
        if self.chrome.enter():
            self.draw()
        elif self.focus == "content":
            self.active_tab.enter()
            self.draw()

    def handle_backspace(self, e):
        self.chrome.backspace()
        self.draw()

    def on_close(self):
        socket_manager.close_all()
        cache.clear_expired_entries()
        self.window.destroy()

    def draw(self):
        self.window.title(self.active_tab.title)
        self.canvas.delete("all")
        self.active_tab.draw(self.canvas, self.chrome.bottom)
        for cmd in self.chrome.paint():
            cmd.execute(0, self.canvas)

    def new_tab(self, url):
        new_tab = Tab(self.width, self.height - self.chrome.bottom)
        new_tab.load(url)
        self.active_tab = new_tab
        self.tabs.append(new_tab)
        self.draw()

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
    Browser().new_tab(url)
    tkinter.mainloop()