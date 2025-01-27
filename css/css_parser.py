from html_.element import Element
from util.utils import *
import re


INHERITED_PROPERTIES = {
    "font-size": "16px",
    "font-style": "normal",
    "font-weight": "normal",
    "color": "black",
    "font-family":"Arial",
    "width" : "auto",
    "height": "auto"
}

LIMITED_PROPERTIES = {
    "display" : ["block", "inline"],
    "font-weight": ["normal", "bold"]
}

DEFAULT_PROPERTIES = {
    'display': 'inline'
}

class CSSParser:
    def __init__(self, s):
        self.s = s
        self.i = 0
    
    def whitespace(self):
        while self.i < len(self.s) and self.s[self.i].isspace():
            self.i += 1

    def word(self):
        start = self.i
        while self.i < len(self.s):
            char = self.s[self.i]
            if char.isalnum() or char in "#-.%":
                self.i += 1
            else:
                break
        if not (self.i > start):
            raise Exception("Parsing error")
        return self.s[start:self.i]

    def literal(self, literal):
        if not (self.i < len(self.s) and self.s[self.i] == literal):
            raise Exception("Parsing error")
        self.i += 1

    def pair(self):
        prop = self.word()
        self.whitespace()
        self.literal(":")
        self.whitespace()
        val = self.word()
        return prop.casefold(), val

    def body(self):
        pairs = {}
        while self.i < len(self.s):
            try:
                prop, val = self.pair()
                pairs[prop.casefold()] = val
                self.whitespace()
                self.literal(";")
                self.whitespace()
            except Exception:
                why = self.ignore_until([";", "}"])
                if why == ";":
                    self.literal(";")
                    self.whitespace()
                else:
                    break
        return pairs

    def ignore_until(self, chars):
        while self.i < len(self.s):
            if self.s[self.i] in chars:
                return self.s[self.i]
            else:
                self.i += 1
        return None
    
    def selector(self):
        word = self.word().casefold()
        out = get_base_selector(word)
        self.whitespace()
        while self.i < len(self.s) and self.s[self.i] != "{":
            if self.is_has_selector():
                selector_str = self.get_has_selector_str().strip()
                self.ignore_until(["{"])
                return HasSelector(out, CSSParser(selector_str).selector())
            selector_str = self.word()
            descendant = get_base_selector(selector_str.casefold())
            out = DescendantSelector(out, descendant)
            self.whitespace()
        return out

    def is_has_selector(self):
        has_selector_regex = r"^:has\([^{]+\)"
        return re.search(has_selector_regex, self.s[self.i:])
    
    def get_has_selector_str(self):
        has_selector_regex = r"^:has\(([^{]+)\)"
        match = re.search(has_selector_regex, self.s[self.i:])
        return match.group(1)

    def parse(self):
        rules = []
        while self.i < len(self.s):
            try:
                self.whitespace()
                selector = self.selector()
                self.literal("{")
                self.whitespace()
                body = self.body()
                self.literal("}")
                rules.append((selector, body))
            except Exception:
                why = self.ignore_until(["}"])
                if why == "}":
                    self.literal("}")
                    self.whitespace()
                else:
                    break

        return rules

class TagSelector:
    def __init__(self, tag):
        self.tag = tag
        self.priority = 1

    def matches(self, node):
        return isinstance(node, Element) and self.tag == node.tag

class ClassSelector:
    def __init__(self, css_class):
        self.css_class = css_class
        self.priority = 1.5

    def matches(self, node):
        return isinstance(node, Element) and node.has_class(self.css_class)

class DescendantSelector:
    def __init__(self, ancestor, descendant):
        self.ancestor = ancestor
        self.descendant = descendant
        self.priority = ancestor.priority + descendant.priority

    def matches(self, node):
        if not self.descendant.matches(node): return False
        while node.parent:
            if self.ancestor.matches(node.parent): return True
            node = node.parent
        return False

class HasSelector:
    def __init__(self, ancestor, pending_selector):
        self.ancestor = ancestor
        self.pending_selector = pending_selector
        self.priority = ancestor.priority + pending_selector.priority + 1

    def ancestor_matches(self, node):
        return self.ancestor.matches(node)

class PendingRule:
    def __init__(self, pending_selector, body):
        self.pending_selector = pending_selector
        self.body = body
        self.match = False

def get_base_selector(word):
    if word[0] == '.':
        return ClassSelector(word[1:])
    
    return TagSelector(word)

def add_style(node, property, value):
    if property in LIMITED_PROPERTIES and value not in LIMITED_PROPERTIES[property]:
        return

    node.style[property] = value    

def style(node, rules, pending_rules):
    node.style = DEFAULT_PROPERTIES.copy()
    inherit_style(node)
    rules_style(rules, pending_rules, node)
    inline_style(node)
    convert_font_size_to_px(node)
    
    remaining_rules =  test_pending_selectors(pending_rules, node)
    for child in node.children:
        pending_rules = pending_rules | style(child, rules, remaining_rules)

    has_selector_style(node, pending_rules)
    return pending_rules    

def inherit_style(node):
    for property, default_value in INHERITED_PROPERTIES.items():
        if node.parent:
            value = node.parent.style[property]
        else:
            value = default_value
        add_style(node, property, value)

def rules_style(rules, pending_rules, node):
    for selector, body in rules:
        if isinstance(selector, HasSelector):
            if selector.ancestor_matches(node):
                pending_rules[id(node)] = PendingRule(selector.pending_selector, body)    
        elif selector.matches(node): 
            for property, value in body.items():
                add_style(node, property, value)

def inline_style(node):
    if isinstance(node, Element) and "style" in node.attributes:
        pairs = CSSParser(node.attributes["style"]).body()
        for property, value in pairs.items():
            add_style(node, property, value)

def convert_font_size_to_px(node):
    if node.style["font-size"].endswith("%"):
        if node.parent:
            parent_font_size = node.parent.style["font-size"]
        else:
            parent_font_size = INHERITED_PROPERTIES["font-size"]
        node_pct = float(node.style["font-size"][:-1]) / 100
        parent_px = float(parent_font_size[:-2])
        node.style["font-size"] = str(node_pct * parent_px) + "px"

def test_pending_selectors(pending_rules, node):
    remaining_rules =  pending_rules.copy()
    for ancestor_id in pending_rules:
        pending_rule = pending_rules[ancestor_id]
        selector = pending_rule.pending_selector
        if selector.matches(node):
            pending_rule.match = True
            remaining_rules.pop(ancestor_id)
    
    return remaining_rules

def has_selector_style(node, pending_rules):
    if id(node) in pending_rules:
        node_rule = pending_rules[id(node)]
        if node_rule.match:
            for property, value in node_rule.body.items():
                add_style(node, property, value)