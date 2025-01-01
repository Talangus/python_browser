from util.utils import *
from html_.html_parser import HTMLParser


class SourceHTMLParser(HTMLParser):
    flat_tree = []

    def parse(self):
        while not self.finished_parsing():
            c = self.get_current_char()
            
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
        self.flat_tree.append(Text(text, None))
        

    def add_tag(self, tag_content):
        tag_content = "&lt;" + tag_content + "&gt;"
        text_node = Text(tag_content, None)
        text_node.is_html_element_text = True
        self.flat_tree.append(text_node)        
        

    def finish(self):
        preformat_root = Element("pre", {}, None)

        for index, node in enumerate(self.flat_tree):
            node.parent = preformat_root
            if not node.is_html_element_text:
                self.flat_tree[index] = self.wrap_in_bold_element(node)
        preformat_root.children = self.flat_tree
        
        return preformat_root

    @staticmethod
    def wrap_in_bold_element(text_node):
        bold_element = Element("b", {}, text_node.parent)
        text_node.parent = bold_element
        bold_element.children.append(text_node)

        return bold_element
    
