from window_layout.tab_layout import TabLayout
from doc_layout.document_layout import DocumentLayout
from html_.html_decode import html_decode
from html_.utils import get_html_parser,get_html_title
from html_.text import Text
from html_.element import Element
from css.css_parser import style, CSSParser
from css.utils import get_css_rules
from js.js_context import JSContext
from js.utils import *
from network.url import URL
from util.utils import *

import urllib
import dukpy

class Tab:
    DEFAULT_STYLE_SHEET = CSSParser(open("css/browser.css").read()).parse()
    
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
        self.referer_policy = None
        self.js = JSContext(self)
    
    def load(self, url, payload=None):
        self.history.append(url)
        self.tab_layout.scroll = 0
        response_headers, body = url.request(self, payload)
        self.url = url
        parser = get_html_parser(body, url)
        nodes = parser.parse()
        self.nodes = html_decode(nodes)
        self.title = get_html_title(self.nodes)
        self.handle_origins(response_headers)
        self.handle_referer_policy(response_headers)

        self.rules = self.DEFAULT_STYLE_SHEET.copy()
        self.rules.extend(get_css_rules(self, url))
        
        self.js.start_runtime_env()
        script_urls = get_external_scripts(self.nodes)
        self.run_scripts(script_urls)        
        
        self.render()
        self.handle_fragment()

    def raster(self, canvas):
        for cmd in list(reversed(self.display_list)):
            cmd.execute(canvas)        

    def run_scripts(self, script_urls):
        for script in script_urls:
            script_url = self.url.resolve(script)
            if not self.allowed_request(script_url):
                print("Blocked script", script, "due to CSP")
                continue
            try:
                _, body = script_url.request(self)
                self.js.run(body)
            except:
                continue

    def handle_origins(self, headers):
        self.allowed_origins = None
        if "content-security-policy" in headers:
            csp = headers["content-security-policy"].split()
            if len(csp) > 0 and csp[0] == "default-src":
                self.allowed_origins = []
                for origin in csp[1:]:
                    self.allowed_origins.append(URL(origin).origin())
                
    def handle_referer_policy(self, headers):
        if "referrer-policy" not in headers:
            return
        
        policy = headers["referrer-policy"]
        if policy in ['no-referrer', 'same-origin']:
            self.referer_policy = policy
    

    def allowed_request(self, url):
        return self.allowed_origins == None or \
            url.origin() in self.allowed_origins

    def render(self):
        self.display_list = []
        style(self.nodes, sorted(self.rules, key=cascade_priority), {})
        self.document = DocumentLayout(self.nodes, self.width)
        self.document.layout()
        paint_tree(self.document, self.display_list)
        # print_tree(self.document) 
        
    def draw(self, canvas, offset):
        for cmd in self.display_list:
            if self.tab_layout.is_below_viewport(cmd): continue
            if self.tab_layout.is_above_viewport(cmd, offset): continue
            cmd.execute(self.tab_layout.scroll - offset, canvas)
        self.tab_layout.handle_scrollbar(canvas, offset)

    def on_resize(self, width, height):
        self.width = width
        self.height = height
        self.tab_layout.update_size()
        self.render()

    def keypress(self, char):
        if self.focus:
            if self.js.dispatch_event("keydown", self.focus): return
            self.focus.attributes["value"] += char
            self.render()

    def backspace(self):
        if self.focus:
            self.focus.attributes["value"] = self.focus.attributes["value"][:-1]
            self.render()

    def enter(self):
        if self.focus:
            self.handle_form(self.focus)
        self.focus = None

    def click(self, x, y):
        self.focus = None
        clicked_elements = self.get_clicked_elements(x, y)
        if not clicked_elements:
            return
        inner_element = clicked_elements['inner']
        interactive_element = clicked_elements['interactive']
        
        if not inner_element:
            return
        if self.js.dispatch_event("click", inner_element): return
        if not interactive_element: return

        if interactive_element.is_tag("a"):
            url = self.url.resolve(interactive_element.attributes["href"])
            self.load(url)

        elif interactive_element.is_tag("button"):
            self.handle_form(interactive_element)

        elif interactive_element.is_tag("input"):
            if is_checkbox(interactive_element):
                self.handle_checkbox_click(interactive_element)
            else:
                interactive_element.attributes["value"] = ""
            
            if self.focus:
                    self.focus.is_focused = False
            self.focus = interactive_element
            interactive_element.is_focused = True

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

    def get_clicked_elements(self, x, y):
        y += self.tab_layout.scroll
        objs = [obj for obj in tree_to_list(self.document, []) if clicked_on_obj(x, y, obj)]
        if not objs: return
        element = objs[-1].node
        clicked_elements = {}

        while element and isinstance(element, Text):
            element = element.parent 
        clicked_elements['inner'] = element

        while element and not self.is_interactive_element(element):
            element = element.parent 
        clicked_elements["interactive"] = element

        return clicked_elements

    def get_clicked_url(self, x, y):
        clicked_elements = self.get_clicked_elements(x, y)
        if not clicked_elements:
            return
        
        interactive_element = clicked_elements['interactive']
        if interactive_element.is_tag("a"):
            return self.url.resolve(interactive_element.attributes["href"])
    
    @staticmethod
    def is_interactive_element(element):
        return (element.tag == "a" and "href" in element.attributes) or \
            (element.tag == "button") or (element.tag == "input")

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
        if self.js.dispatch_event("submit", elt): return
        inputs = [node for node in tree_to_list(elt, [])
                  if isinstance(node, Element)
                  and node.tag == "input"
                  and "name" in node.attributes]
        
        method = 'get' if is_get_form_method(elt) else 'post'

        body = ""
        for input in inputs:
            name = input.attributes["name"]
            name = urllib.parse.quote(name)
            value = input.attributes.get("value", "on") if is_checkbox(input) else input.attributes.get("value", "")
            value = urllib.parse.quote(value)
            body += "&" + name + "=" + value
        body = body[1:]
        
        url = self.url.resolve(elt.attributes["action"])
        if method == "get":
            url.set_query(body)
            self.load(url)
        else:
            self.load(url, body)

    @staticmethod
    def handle_checkbox_click(element):
        if element.has_attribute("checked", ''):
            del element.attributes['checked']
        else:
            element.attributes['checked'] = ''

    def blur(self):
        if self.focus:
            self.focus.is_focused = False
            self.render()
        self.focus = None