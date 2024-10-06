import re
class Element:
    def __init__(self, tag, attributes, parent):
        self.tag = tag
        self.attributes = attributes
        self.children = []
        self.parent = parent
    
    def __repr__(self):
        return "<" + self.tag + ">"

    def has_class(self, class_name):
        if self.attributes['class']:
            return class_name in self.attributes['class']

        return False

    def is_closing_tag_buffer(buffer):
        return buffer.startswith('/')
    
    def is_declaration_buffer(buffer):
        return buffer.startswith('!')
    
    def parse_tag_and_attributes(buffer):
        tag_pattern = re.compile(r'\s*(\w+)(.*)')
        match = tag_pattern.match(buffer)
        if not match:
            raise Exception("Error parsing tag buffer")
            
        tag_name = match.group(1)
        attributes_string = match.group(2).strip()
        attributes_pattern = re.compile(r'(\w+)\s*=\s*"([^"]*)"')
        attributes = dict(attributes_pattern.findall(attributes_string))

        if "class" in attributes:
            attributes["class"] = attributes["class"].split(' ')

        return tag_name, attributes
    
    