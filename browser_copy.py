import tkinter
import argparse
from PIL import Image, ImageTk

from network.url import URL
from network.socket_manager import socket_manager 
from network.cache import cache
from window_layout.window_layout import WindowLayout
from doc_layout.document_layout import DocumentLayout
from html_.html_decode import html_decode
from html_.utils import get_html_parser
from css.css_parser import style, CSSParser
from css.utils import get_css_rules
from util.utils import *

class Browser:
    DEFAULT_STYLE_SHEET = CSSParser(open("./css/browser.css").read()).parse()
    
    def __init__(self):
        self.width = 800
        self.height = 600
        self.window = tkinter.Tk()
        self.window_layout = WindowLayout(self)
        self.canvas = tkinter.Canvas(
            self.window, 
            width=self.width,
            height=self.height,
            bg="white"
        )
        self.canvas.pack(fill="both", expand=1)
        self.images = []
        self.display_list = []
        self.url = None

        self.window.bind("<Down>", self.window_layout.on_scrolldown)
        self.window.bind("<Up>", self.window_layout.on_scrollup)
        self.window.bind("<Button-1>", self.click)
        self.window.bind("<MouseWheel>", self.window_layout.on_mouse_wheel)
        self.window.bind("<Configure>", self.on_resize)
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def load(self, url):
        self.url = url
        self.display_list = []
        self.window_layout.scroll = 0
        body = url.request()
        parser = get_html_parser(body, url)
        nodes = parser.parse()
        self.nodes = html_decode(nodes)
        rules = self.DEFAULT_STYLE_SHEET.copy()
        rules.extend(get_css_rules(self.nodes ,url))
        style(self.nodes, sorted(rules, key=cascade_priority), {})
        self.document = DocumentLayout(self.nodes, self.width)
        self.document.layout()
        paint_tree(self.document, self.display_list)
        # print_tree(self.document)
        self.draw() 
        
    def draw(self):
        self.canvas.delete("all")
        self.window_layout.handle_scrollbar()
        for cmd in self.display_list:
            if self.window_layout.is_below_viewport(cmd): continue
            if self.window_layout.is_above_viewport(cmd): continue
            cmd.execute(self.window_layout.scroll, self.canvas)

    def on_close(self):
        socket_manager.close_all()
        cache.clear_expired_entries()
        self.window.destroy()

    def on_resize(self, event):
        if event.width == 1 or event.height == 1:
            return
        self.width = event.width
        self.height = event.height
        self.window_layout.update_size()
        self.document = DocumentLayout(self.nodes, event.width)
        self.display_list = []
        self.document.layout()
        paint_tree(self.document, self.display_list)
        self.draw()

    def click(self, e):
        x, y = e.x, e.y
        y += self.window_layout.scroll
        objs = [obj for obj in tree_to_list(self.document, []) if clicked_on_obj(x, y, obj)]
        if not objs: return
        
        elt = objs[-1].node
        while elt:
            if isinstance(elt, Text):
                pass
            elif elt.tag == "a" and "href" in elt.attributes:
               url = self.url.resolve(elt.attributes["href"])
               return self.load(url)
            elt = elt.parent
   
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

    

