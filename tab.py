from window_layout.tab_layout import TabLayout
from doc_layout.document_layout import DocumentLayout
from html_.html_decode import html_decode
from html_.utils import get_html_parser,get_html_title
from html_.text import Text
from html_.element import Element
from css.css_parser import style, CSSParser
from css.utils import get_css_rules
from util.utils import *

import urllib

class Tab:
    DEFAULT_STYLE_SHEET = CSSParser(open("./css/browser.css").read()).parse()
    
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.tab_layout = TabLayout(self)
        self.images = []
        self.display_list = []
        self.url = None
        self.history = []
        self.forward_stack = []
        self.focus = None
    
    def load(self, url, payload=None):
        self.history.append(url)
        self.url = url
        self.tab_layout.scroll = 0
        body = url.request(payload)
        parser = get_html_parser(body, url)
        nodes = parser.parse()
        self.nodes = html_decode(nodes)
        self.title = get_html_title(self.nodes)
        
        self.rules = self.DEFAULT_STYLE_SHEET.copy()
        self.rules.extend(get_css_rules(self.nodes ,url))
        self.render()
        self.handle_fragment()
        

    def render(self):
        self.display_list = []
        style(self.nodes, sorted(self.rules, key=cascade_priority), {})
        self.document = DocumentLayout(self.nodes, self.width)
        self.document.layout()
        paint_tree(self.document, self.display_list)
        # print_tree(self.document) 
        
    def draw(self, canvas, offset):
        self.tab_layout.handle_scrollbar(canvas)
        for cmd in self.display_list:
            if self.tab_layout.is_below_viewport(cmd): continue
            if self.tab_layout.is_above_viewport(cmd, offset): continue
            cmd.execute(self.tab_layout.scroll - offset, canvas)

    def on_resize(self, width, height):
        self.width = width
        self.height = height
        self.tab_layout.update_size()
        # self.document = DocumentLayout(self.nodes, width)
        # self.display_list = []
        # self.document.layout()
        # paint_tree(self.document, self.display_list)
        self.render()

    def keypress(self, char):
        if self.focus:
            self.focus.attributes["value"] += char
            self.render()

    def enter(self):
        if self.focus:
            self.handle_form(self.focus)
        self.focus = None

    def click(self, x, y):
        self.focus = None
        element = self.get_clicked_element(x, y)
        if not element:
            return
        
        if element.is_tag("a"):
            url = self.url.resolve(element.attributes["href"])
            self.load(url)

        elif element.is_tag("button"):
            self.handle_form(element)

        elif element.is_tag("input"):
            element.attributes["value"] = ""
            
            if self.focus:
                    self.focus.is_focused = False
            self.focus = element
            element.is_focused = True

            return self.render()    

    def go_back(self):
        if len(self.history) > 1:
            current_page = self.history.pop()
            self.forward_stack.append(current_page)
            back = self.history.pop()
            self.load(back)

    def go_forward(self):
        if len(self.forward_stack) > 0:
            forward_page = self.forward_stack.pop()
            self.load(forward_page)

    def get_clicked_url(self, x, y):
        element = self.get_clicked_element(x, y)
        if element.is_tag("a"):
            url = self.url.resolve(element.attributes["href"])
            return url

    def get_clicked_element(self, x, y):
        y += self.tab_layout.scroll
        objs = [obj for obj in tree_to_list(self.document, []) if clicked_on_obj(x, y, obj)]
        if not objs: return
        element = objs[-1].node
        
        while element:
            if isinstance(element, Text):
                pass
            elif (element.tag == "a" and "href" in element.attributes) or \
                 (element.tag == "button") or (element.tag == "input"):
                return element
               
            element = element.parent 
        
        return None
    
    def handle_fragment(self):
        if not self.url.fragment:
            return
        
        self.tab_layout.scroll_to_hash(self.url.fragment)
        
    def handle_form(self, element):
        while element:
            if element.tag == "form" and "action" in element.attributes:
                return self.submit_form(element)
            element = element.parent

    def submit_form(self, elt):
        inputs = [node for node in tree_to_list(elt, [])
                  if isinstance(node, Element)
                  and node.tag == "input"
                  and "name" in node.attributes]
        body = ""
        for input in inputs:
            name = input.attributes["name"]
            name = urllib.parse.quote(name)
            value = input.attributes.get("value", "")
            value = urllib.parse.quote(value)
            body += "&" + name + "=" + value
        body = body[1:]
        
        url = self.url.resolve(elt.attributes["action"])
        self.load(url, body)