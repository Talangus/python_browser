from util.utils import *
from html_.element import Element
from html_.text import Text
class HTMLParser:

    SELF_CLOSING_TAGS = [
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
    ]

    HEAD_TAGS = [
        "base", "basefont", "bgsound", "noscript",
        "link", "meta", "title", "style", "script",
    ]   
    
    def __init__(self, body):
        self.body = body
        self.unfinished = []
        self.buffer = ""
        self.in_tag = False
        self.in_comment = False
        self.in_script = False
        self.in_single_quote = False
        self.in_double_quote = False
        self.body_index = 0

    def parse(self):
        while not self.finished_parsing():
            c = self.get_current_char()
            
            if self.in_comment:
                if not self.is_close_comment():
                    self.advance_index()
                else: 
                    self.in_comment = False
                    self.advance_index(3)
                continue    
            if c == '"' or c == "'":
                self.add_to_buffer(c)
                self.advance_index()
                if c == "'":
                    self.in_single_quote = not self.in_single_quote
                else:
                    self.in_double_quote = not self.in_double_quote
                continue
            if c == "<":
                if self.should_ignore_meta_char():
                    self.add_to_buffer(c)
                    self.advance_index()
                    continue

                if self.is_open_comment():
                    self.in_comment = True
                    self.advance_index()
                    continue
                
                if self.is_close_script():
                    self.in_script = False
                    
                self.in_tag = True
                if self.buffer: self.add_text(self.buffer)
                self.buffer = ""
                self.advance_index()
            elif c == ">":
                if self.should_ignore_meta_char():
                    self.add_to_buffer(c)
                    self.advance_index()
                    continue

                self.in_tag = False
                self.add_tag(self.buffer)
                if self.buffer_has_script_tag():
                    self.update_script_vars()
                self.buffer = ""
                self.advance_index()
            else:
                self.add_to_buffer(c)
                self.advance_index()
            
        if not self.in_tag and self.buffer:
            self.add_text(self.buffer)
        
        return self.finish()
    
    def add_text(self, text):
        if text.isspace(): return
        self.implicit_tags(None)
        parent = self.unfinished[-1]
        node = Text(text, parent)
        parent.children.append(node)

    def add_tag(self, tag):
        tag, attributes = self.get_attributes(tag)
        if tag.startswith("!"): return
        self.implicit_tags(tag)
        if tag.startswith("/"):
            if len(self.unfinished) == 1: return
            node = self.unfinished.pop()
            parent = self.unfinished[-1]
            parent.children.append(node)
        elif tag in self.SELF_CLOSING_TAGS:
            parent = self.unfinished[-1]
            node = Element(tag, attributes, parent)
            parent.children.append(node)
        else:
            parent = self.unfinished[-1] if self.unfinished else None
            node = Element(tag, attributes, parent)
            self.unfinished.append(node)

    def finish(self):
        if not self.unfinished:
            self.implicit_tags(None)
        while len(self.unfinished) > 1:
            node = self.unfinished.pop()
            parent = self.unfinished[-1]
            parent.children.append(node)
        return self.unfinished.pop()
    
    def get_attributes(self, text):
        tag, *rest = text.split(maxsplit=1)
        tag = tag.casefold()
        attributes = {}
        if len(rest) != 0:
            # attr_pattern = re.compile(r'(\w+)\s*=\s*(".*?"|\'.*?\'|\S+)')
            attr_pattern = re.compile(r'(\w+)(?:\s*=\s*(".*?"|\'.*?\'|\S+))?')
            for match in attr_pattern.findall(rest[0]):
                key, value = match
                if value.startswith(("'", "\"")) and value.endswith(("'", "\"")):
                    value = value[1:-1]  
                attributes[key.casefold()] = value

        return tag, attributes
    
    def implicit_tags(self, tag):
        while True:
            open_tags = [node.tag for node in self.unfinished]
            if open_tags == [] and tag != "html":
                self.add_tag("html")
            elif open_tags == ["html"] and tag not in ["head", "body", "/html"]:
                if tag in self.HEAD_TAGS:
                    self.add_tag("head")
                else:
                    self.add_tag("body")
            elif open_tags == ["html", "head"] and tag not in ["/head"] + self.HEAD_TAGS:
                self.add_tag("/head")
            elif tag == "p" and open_tags[-1] == "p":
                self.add_tag("/p")
            elif tag == "li" and open_tags[-1] == "li":
                self.add_tag("/li")
            elif self.is_close_tag(tag) and not self.close_tag_match_open_tag(tag):
                self.add_tag(tag[1:])
            else:
                break

    def is_close_comment(self):
        i = self.body_index
        c = self.get_current_char()
        return c == '-' and  self.body[i:i+3] == "-->" and self.body[i-2:i] != "<!"
    
    def is_open_comment(self):
        i = self.body_index
        return self.body[i:i+4] == "<!--"
    
    def is_close_tag(self, tag):
        if not isinstance(tag, str):
            return False
        return tag.startswith("/")

    def close_tag_match_open_tag(self, tag):
        tag_type = tag[1:]
        last_open_tag= self.unfinished[-1].tag
        return tag_type == last_open_tag
    
    def is_close_script(self):
        i = self.body_index
        return self.body[i:i+9] == "</script>"
    
    def finished_parsing(self):
        return self.body_index >= len(self.body)
    
    def get_current_char(self):
        return self.body[self.body_index]
    
    def advance_index(self, int=1):
        self.body_index+= int

    def add_to_buffer(self, char):
        self.buffer += char

    def should_ignore_meta_char(self):
        in_quotes = self.in_double_quote or self.in_single_quote
        quotes_condition = self.in_tag and in_quotes
        script_condition = self.in_script and not self.is_close_script()
        return script_condition or quotes_condition
    
    def buffer_has_script_tag(self):
        return self.buffer.startswith("script") or self.buffer.startswith("/script")

    def update_script_vars(self):
        if self.buffer.startswith("script"):
            self.in_script = True
        elif self.buffer.startswith("/script"):
            self.in_script = False
