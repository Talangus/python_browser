class Text:
    def __init__(self, text, parent):
        self.text = text
        self.children = []
        self.parent = parent
        self.is_html_element_text = False

    def __repr__(self):
        return repr(self.text)
    
    def is_tag(self, tag):
        return False
    
    def has_attribute(self,key, value):
        return False