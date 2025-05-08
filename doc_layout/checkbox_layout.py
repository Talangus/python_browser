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
        self.width = linespace(self.font)
        
        if self.previous:
            space = self.previous.font.measureText(" ")
            self.x = self.previous.x + self.previous.width + space
            first_child = False 
        else:
            self.x = self.parent.x
            first_child = True

        self.height = linespace(self.font)
        
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
    
    def should_paint_effects(self):
        return self.should_paint()

    def self_rect(self):
        return skia.Rect.MakeLTRB(self.x, self.y,
            self.x + self.width, self.y + self.height) 
    
    def paint_effects(self, cmds):
        cmds = paint_visual_effects(
            self.node, cmds, self.self_rect())
        return cmds