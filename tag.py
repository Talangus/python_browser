import re
class Tag:
    def __init__(self, buffer):
        if Tag.is_closing_tag_buffer(buffer) or Tag.is_declaration_buffer(buffer):
            self.tag = buffer
            self.attributes = {}
        else:
            self.tag, self.attributes = Tag.parse_tag_and_attributes(buffer)
    
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
    
    