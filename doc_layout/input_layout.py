from doc_layout.draw_rect import DrawRect
from doc_layout.draw_text import DrawText
from window_layout.rect import Rect
from html_.text import Text
from doc_layout.utils import *



class InputLayout:
    def __init__(self, node, parent, previous):
        self.node = node
        self.children = []
        self.parent = parent
        self.previous = previous

    def layout(self):
        self.font = get_html_node_font(self.node)
        self.width = INPUT_WIDTH_PX
        
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
        cmds = []
        bgcolor = self.node.style.get("background-color", "transparent")
        if bgcolor != "transparent":
            rect = DrawRect(self.self_rect(), bgcolor)
            cmds.append(rect)

        if self.node.tag == "input":
            text = self.node.attributes.get("value", "")
        elif self.node.tag == "button":
            if len(self.node.children) == 1 and isinstance(self.node.children[0], Text):
                text = self.node.children[0].text
            else:
                print("Ignoring HTML contents inside button")
                text = ""

        color = self.node.style["color"]
        cmds.append(DrawText(self.x, self.y, text, self.font, color))
        
        return cmds
    
    def should_paint(self):
        return True
    
    def self_rect(self):
        return Rect(self.x, self.y,
            self.x + self.width, self.y + self.height) 