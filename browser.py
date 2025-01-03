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
from block_layout import BlockLayout
from document_layout import DocumentLayout
from html_parser import HTMLParser
from source_html_parser import SourceHTMLParser
from css_parser import style, CSSParser
from element import Element

class Browser:
    SCROLL_STEP = 100
    HSTEP = 13
    VSTEP = 18
    DEFAULT_STYLE_SHEET = CSSParser(open("browser.css").read()).parse()
    
    def __init__(self):
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

        self.scroll = 0
        self.images = []
        self.display_list = []

        self.window.bind("<Down>", self.on_scrolldown)
        self.window.bind("<Up>", self.on_scrollup)
        self.window.bind("<MouseWheel>", self.on_mouse_wheel)
        self.window.bind("<Configure>", self.on_resize)
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def load(self, url):
        body = url.request()
        parser = get_html_parser(body, url)
        nodes = parser.parse()
        self.nodes = html_decode(nodes)
        rules = self.DEFAULT_STYLE_SHEET.copy()
        rules.extend(self.get_css_rules(url))
        style(self.nodes, sorted(rules, key=cascade_priority), {})
        self.document = DocumentLayout(self.nodes, self.width)
        self.document.layout()
        # print_tree(self.document)
        paint_tree(self.document, self.display_list)
        self.draw() 
        
    def draw(self):
        self.canvas.delete("all")
        self.handle_scrollbar()
        for cmd in self.display_list:
            if self.is_below_viewport(cmd): continue
            if self.is_above_viewport(cmd): continue
            # self.canvas.create_text(x, y - self.scroll, text=c, anchor='nw', font=f)
            cmd.execute(self.scroll, self.canvas)

    def is_below_viewport(self, cmd):
        return cmd.top > self.scroll + self.height
    
    def is_above_viewport(self,cmd):
        return cmd.bottom + Browser.VSTEP < self.scroll

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
        lowest_y = last_item.bottom
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
        self.document = DocumentLayout(self.nodes, self.width)
        self.display_list = []
        self.document.layout()
        paint_tree(self.document, self.display_list)
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
    
    def get_css_links(self):
        links = []
        for node in tree_to_list(self.nodes, []):
            if isinstance(node, Element) and node.tag == "link"\
            and node.attributes.get("rel") == "stylesheet"\
            and "href" in node.attributes:
                links.append(node.attributes["href"])
        return links

    def get_css_rules(self, url):
        rules = []
        rules.extend(self.get_external_css_rules(url))
        rules.extend(self.get_inline_style_rules())
        
        return rules
            
    def get_external_css_rules(self,url):
        rules = []
        links = self.get_css_links()
        for link in links:
            style_url = url.resolve(link)
            try:
                body = style_url.request()
                new_rules = CSSParser(body).parse()
                rules.extend(new_rules)
            except:
                continue
        
        return rules

    def get_inline_style_rules(self):
        rules = []
        nodes = tree_to_list(self.nodes, [])
        for node in nodes:
            if html_node_is(node, 'style'):
                rules.extend(CSSParser(node.children[0].text).parse())

        return rules

def parse_arguments():
    parser = argparse.ArgumentParser(description="Simple python browser.")
    
    parser.add_argument("url",
        type=str,
        nargs="?",
        default=URL.DEFAULT_FILE_PATH, 
        help="The URL to process.")
    
    args = parser.parse_args()
    return args.url

def get_html_parser(body, url):
    if url.is_view_source:
        return SourceHTMLParser(body)
    else:
        return HTMLParser(body)

def paint_tree(layout_object, display_list):
    display_list.extend(layout_object.paint())
    for child in layout_object.children:
        paint_tree(child, display_list)

def is_document_layout(layout_object):
    return type(layout_object) == DocumentLayout

if __name__ == "__main__":
    
    url_arg = parse_arguments()
    url = URL(url_arg)
    Browser().load(url)
    tkinter.mainloop()

    

