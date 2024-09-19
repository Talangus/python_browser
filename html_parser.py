from utils import *

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

    def parse(self):
        text = ""
        in_tag = False
        in_comment = False
        in_script = False
        i=0
        while i<len(self.body):
            c = self.body[i]
            if in_comment:
                if c != "-" or not self.is_close_comment(i) :
                    i +=1
                else: 
                    in_comment = False
                    i += 3
                continue    
            
            if c == "<":
                if in_script:
                    if not self.is_close_script(i):
                        text+=c
                        i+=1
                        continue

                elif self.is_open_comment(i):
                    in_comment = True
                    i+=1
                    continue
                
                in_tag = True
                if text: self.add_text(text)
                text = ""

            elif c == ">":
                if in_script:
                    text += c
                    i+=1
                    continue

                in_tag = False
                self.add_tag(text)
                if text.startswith("script"):
                    in_script = True
                elif text.startswith("/script"):
                    in_script = False
                text = ""
            else:
                text += c
            i+=1
            
        if not in_tag and text:
            self.add_text(text)
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
        parts = text.split()
        tag = parts[0].casefold()
        attributes = {}
        for attrpair in parts[1:]:
            if "=" in attrpair:
                key, value = attrpair.split("=", 1)
                if len(value) > 2 and value[0] in ["'", "\""]:
                    value = value[1:-1]
                attributes[key.casefold()] = value
                
            else:
                attributes[attrpair.casefold()] = ""
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

    def is_close_comment(self, i):
        return self.body[i:i+3] == "-->" and self.body[i-2:i] != "<!"
    
    def is_open_comment(self, i):
        return self.body[i:i+4] == "<!--"
    
    def is_close_tag(self, tag):
        if not isinstance(tag, str):
            return False
        return tag.startswith("/")

    def close_tag_match_open_tag(self, tag):
        tag_type = tag[1:]
        last_open_tag= self.unfinished[-1].tag
        return tag_type == last_open_tag
    
    def is_close_script(self, i):
        return self.body[i:i+9] == "</script>"