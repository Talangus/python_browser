from doc_layout.utils import *
from doc_layout.draw_text import DrawText

class TextLayout: 
    def __init__(self, node, word, parent, previous):
        self.node = node
        self.word = word
        self.children = []
        self.parent = parent
        self.previous = previous
        

    def layout(self):
        self.font = get_html_node_font(self.node)
        self.width = self.font.measure(self.word)

        if self.previous:
            space = self.previous.font.measure(" ")
            self.x = self.previous.x + self.previous.width + space 
        else:
            self.x = self.parent.x
        
        self.height = self.font.metrics("linespace")

        if self.passed_line_width():
            self.parent.split_line(self)

    def passed_line_width(self):
        return self.x + self.width > self.parent.width

    def paint(self):
        color = self.node.style["color"]
        return [DrawText(self.x, self.y, self.word, self.font, color)]