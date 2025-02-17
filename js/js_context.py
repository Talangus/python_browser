from css.css_parser import CSSParser
from html_.html_parser import HTMLParser
from html_.element import Element
from util.utils import *
import dukpy

RUNTIME_JS = open("js/runtime.js").read()
EVENT_DISPATCH_JS = "new Node(dukpy.handle).dispatchEvent(new Event(dukpy.type))"

class JSContext:
    def __init__(self, tab):
        self.tab = tab
        self.interp = dukpy.JSInterpreter()
        self.node_to_handle = {}
        self.handle_to_node = {}
        self.export_functions()
                
        self.interp.evaljs(RUNTIME_JS)

    def export_functions(self):
        self.interp.export_function("log", print)
        self.interp.export_function("querySelectorAll",
            self.querySelectorAll)
        self.interp.export_function("getAttribute",
            self.getAttribute)
        self.interp.export_function("innerHTML_set",
            self.innerHTML_set)
        self.interp.export_function("children_get",
            self.children_get)
        self.interp.export_function("children_get",
            self.children_get)
        self.interp.export_function("create_element",
            self.create_element)
        self.interp.export_function("append_child",
            self.append_child)
        self.interp.export_function("insert_before",
            self.insert_before)

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
        do_default = self.interp.evaljs(
            EVENT_DISPATCH_JS, type=type, handle=handle)
        return not do_default

    def innerHTML_set(self, handle, s):
        doc = HTMLParser("<html><body>" + s + "</body></html>").parse()
        new_nodes = doc.children[0].children
        elt = self.handle_to_node[handle]
        elt.children = new_nodes
        for child in elt.children:
            child.parent = elt
        self.tab.render()

    def children_get(self, handle):
        elt = self.handle_to_node[handle]
        element_children = []
        for child in elt.children:
            if isinstance(child, Element):
                element_children.append(self.get_handle(child))
        return element_children
    
    def create_element(self, local_name):
        element = Element(local_name, {}, None)
        return self.get_handle(element)
    
    def append_child(self, parent_handle, child_handle):
        parent = self.handle_to_node[parent_handle]
        child = self.handle_to_node[child_handle]
        child.parent = parent
        parent.children.append(child)
        self.tab.render()

    def insert_before(self, node_handle, sibling_handle):
        node = self.handle_to_node[node_handle]
        sibling = self.handle_to_node[sibling_handle]
        if node.parent:
            node_index = node.parent.children.index(node)
            node.parent.children.insert(node_index, sibling)
            self.tab.render()