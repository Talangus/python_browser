from doc_layout.draw_rect import DrawRect
from doc_layout.draw_text import DrawText
from window_layout.draw_line import DrawLine
from window_layout.rect import Rect
from html_.text import Text
from doc_layout.utils import *

class CheckboxLayout:
    def __init__(self, node, parent, previous):
        self.node = node
        self.children = []
        self.parent = parent
        self.previous = previous

    def layout(self):
        self.font = get_html_node_font(self.node)
        self.width = self.font.metrics("linespace")
        
        if self.previous:
            space = self.previous.font.measure(" ")
            self.x = self.previous.x + self.previous.width + space
            first_child = False 
        else:
            self.x = self.parent.x
            first_child = True

        self.height = self.font.metrics("linespace")
        
        if not first_child and self.passed_line_width():
            self.parent.split_line(self)

    def passed_line_width(self):
        return self.x + self.width > self.parent.width

    def paint(self):
        cmds = []
        bgcolor = self.node.style.get("background-color", "transparent")
        rect = DrawRect(self.self_rect(), bgcolor, "black")
        cmds.append(rect)

        checked = self.node.has_attribute("checked", '')
        checkmark = " \u2713"
        color = self.node.style["color"]
        if checked:
            cmds.append(DrawText(self.x, self.y, checkmark, self.font, color))
               
        return cmds
    
    def should_paint(self):
        return True
    
    def self_rect(self):
        return Rect(self.x, self.y,
            self.x + self.width, self.y + self.height) 