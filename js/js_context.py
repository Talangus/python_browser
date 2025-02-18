from css.css_parser import CSSParser
from html_.html_parser import HTMLParser
from html_.element import Element
from util.utils import *
from js.utils import *
import dukpy

RUNTIME_JS = open("js/runtime.js").read()
EVENT_DISPATCH_JS = "new Node(dukpy.handle).dispatchEvent(new Event(dukpy.type))"

class JSContext:
    def __init__(self, tab):
        self.tab = tab
        self.interp = dukpy.JSInterpreter()
        self.node_to_handle = {}
        self.handle_to_node = {}

    def start_runtime_env(self):
        self.export_functions()
        self.interp.evaljs(RUNTIME_JS)
        self.init_html_id_vars()

    def export_functions(self):
        self.interp.export_function("log", print)
        self.interp.export_function("querySelectorAll",
            self.querySelectorAll)
        self.interp.export_function("getAttribute",
            self.getAttribute)
        self.interp.export_function("setAttribute",
            self.setAttribute)
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
        self.interp.export_function("remove_child",
            self.remove_child)

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
    
    def setAttribute(self, handle, key, value):
        elt = self.handle_to_node[handle]

        if key == 'id' and not is_detached(elt):
            if key in elt.attributes:
                self.remove_html_id_vars({elt.attributes['id']: handle})
            self.insert_html_id_vars({value: handle})      

        elt.attributes[key] = value
        self.tab.render()

    def dispatch_event(self, type, elt):
        handle = self.node_to_handle.get(elt, -1)
        do_default = self.interp.evaljs(
            EVENT_DISPATCH_JS, type=type, handle=handle)
        return not do_default

    def innerHTML_set(self, handle, s):
        doc = HTMLParser("<html><body>" + s + "</body></html>").parse()
        new_nodes = doc.children[0].children
        elt = self.handle_to_node[handle]

        id_vars = self.get_html_id_vars(elt, False)
        self.remove_html_id_vars(id_vars)
        elt.children = new_nodes
        for child in elt.children:
            child.parent = elt
        id_vars = self.get_html_id_vars(elt, False)
        self.insert_html_id_vars(id_vars)    
        
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
        id_vars = self.get_html_id_vars(child, True)
        self.insert_html_id_vars(id_vars)
        self.tab.render()

    def insert_before(self,parent_handle, new_handle, refrence_handle):
        parent = self.handle_to_node[parent_handle]
        new_node = self.handle_to_node[new_handle]
        refrence_node = self.handle_to_node[refrence_handle]
        refrence_index = parent.children.index(refrence_node)
        parent.children.insert(refrence_index, new_node)
        id_vars = self.get_html_id_vars(new_node, True)
        self.insert_html_id_vars(id_vars)
        self.tab.render()

    def remove_child(self, parent_handle, child_handle):
        parent = self.handle_to_node[parent_handle]
        child = self.handle_to_node[child_handle]
        child_index = parent.children.index(child)
        if child_index:
            del parent.children[child_index]
            id_vars = self.get_html_id_vars(child, True)
            self.remove_html_id_vars(id_vars)
            self.tab.render()
            return child_handle
        
        return None
    
    def get_html_id_vars(self, tree, include_root):
        tree_ids = {}
        nodes = tree_to_list(tree, [])
        if not include_root: nodes = nodes[1:]
        for node in nodes:
            if isinstance(node, Element) and 'id' in node.attributes:
                handle = self.get_handle(node)
                tree_ids[node.attributes['id']] = handle
        
        return tree_ids

    def init_html_id_vars(self):
        all_id_vars = self.get_html_id_vars(self.tab.nodes, True)
        self.insert_html_id_vars(all_id_vars)

    def insert_html_id_vars(self, id_vars):
        vars_js = ""
        for id in id_vars:
            handle = id_vars[id]
            vars_js += f'var {id} = new Node({handle});'

        self.interp.evaljs(vars_js)
        
    def remove_html_id_vars(self, id_vars):
        vars_js = ""
        for id, _ in id_vars:
            vars_js += f'delete {id};'

        self.interp.evaljs(vars_js)

    
