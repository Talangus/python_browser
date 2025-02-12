from css.css_parser import CSSParser
from util.utils import *
import dukpy

RUNTIME_JS = open("js/runtime.js").read()
EVENT_DISPATCH_JS = "new Node(dukpy.handle).dispatchEvent(dukpy.type)"

class JSContext:
    def __init__(self, tab):
        self.tab = tab
        self.interp = dukpy.JSInterpreter()
        self.node_to_handle = {}
        self.handle_to_node = {}

        self.interp.export_function("log", print)
        self.interp.export_function("querySelectorAll",
            self.querySelectorAll)
        self.interp.export_function("getAttribute",
            self.getAttribute)
        
        self.interp.evaljs(RUNTIME_JS)

    def run(self, code):
        try:
            return self.interp.evaljs(code)
        except dukpy.JSRuntimeError as e:
            print("Script crashed", e)

    def querySelectorAll(self, selector_text):
        selector = CSSParser(selector_text).selector()
        nodes = [node for node
             in tree_to_list(self.tab.nodes, [])
             if selector.matches(node)]
        
        return [self.get_handle(node) for node in nodes]
    
    def get_handle(self, elt):
        if elt not in self.node_to_handle:
            handle = len(self.node_to_handle)
            self.node_to_handle[elt] = handle
            self.handle_to_node[handle] = elt
        else:
            handle = self.node_to_handle[elt]
        return handle
    
    def getAttribute(self, handle, attr):
        elt = self.handle_to_node[handle]
        attr = elt.attributes.get(attr, None)
        return attr if attr else ""
    
    def dispatch_event(self, type, elt):
        handle = self.node_to_handle.get(elt, -1)
        self.interp.evaljs(
            EVENT_DISPATCH_JS, type=type, handle=handle)