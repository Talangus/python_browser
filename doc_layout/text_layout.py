from doc_layout.utils import *
from doc_layout.draw_text import DrawText

class TextLayout: ##make sure it has the extra features implemented in previuos chapter
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
            self.x1 = self.previous.x2 + space 
        else:
            self.x1 = self.parent.x
        
        self.x2 = self.x1 + self.width
        self.height = self.font.metrics("linespace")

        if self.passed_line_width():
            self.parent.split_line(self)

    def passed_line_width(self):
        return self.x2 > self.parent.width

    def paint(self):
        color = self.node.style["color"]
        return [DrawText(self.x1, self.y, self.word, self.font, color)]