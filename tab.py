from window_layout.tab_layout import TabLayout
from doc_layout.document_layout import DocumentLayout
from html_.html_decode import html_decode

from html_.utils import get_html_parser,get_html_title
from html_.text import Text
from css.css_parser import style, CSSParser
from css.utils import get_css_rules
from util.utils import *

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
    
    def load(self, url):
        self.history.append(url)
        self.url = url
        self.display_list = []
        self.tab_layout.scroll = 0
        body = url.request()
        parser = get_html_parser(body, url)
        nodes = parser.parse()
        self.nodes = html_decode(nodes)
        self.title = get_html_title(self.nodes)

        rules = self.DEFAULT_STYLE_SHEET.copy()
        rules.extend(get_css_rules(self.nodes ,url))
        style(self.nodes, sorted(rules, key=cascade_priority), {})
        self.document = DocumentLayout(self.nodes, self.width)
        self.document.layout()
        paint_tree(self.document, self.display_list)
        self.handle_fragment()
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
        self.document = DocumentLayout(self.nodes, width)
        self.display_list = []
        self.document.layout()
        paint_tree(self.document, self.display_list)

    def click(self, x, y):
        url = self.get_clicked_url(x, y)
        if url:
            self.load(url)

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

        y += self.tab_layout.scroll
        objs = [obj for obj in tree_to_list(self.document, []) if clicked_on_obj(x, y, obj)]
        if not objs: return
        
        element = objs[-1].node
        while element:
            if isinstance(element, Text):
                pass
            elif element.tag == "a" and "href" in element.attributes:
                url = self.url.resolve(element.attributes["href"])
                return url
               
            element = element.parent 
        
        return None
       
    def handle_fragment(self):
        if not self.url.fragment:
            return
        
        self.tab_layout.scroll_to_hash(self.url.fragment)
        


