from window_layout.tab_layout import TabLayout
from doc_layout.document_layout import DocumentLayout
from html_.html_decode import html_decode
from html_.utils import get_html_parser
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

        
    
    def load(self, url):
        self.url = url
        self.display_list = []
        self.tab_layout.scroll = 0
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
        
    def draw(self, canvas):
        self.tab_layout.handle_scrollbar(canvas)
        for cmd in self.display_list:
            if self.tab_layout.is_below_viewport(cmd): continue
            if self.tab_layout.is_above_viewport(cmd): continue
            cmd.execute(self.tab_layout.scroll, canvas)

    def on_resize(self, width, height):
        self.width = width
        self.height = height
        self.tab_layout.update_size()
        self.document = DocumentLayout(self.nodes, width)
        self.display_list = []
        self.document.layout()
        paint_tree(self.document, self.display_list)

    def click(self, x, y):
        y += self.tab_layout.scroll
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
   


    

