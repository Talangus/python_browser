from util.utils import *
from doc_layout.utils import *
from html_.element import Element
from html_.text import Text
from doc_layout.draw_rect import DrawRect
from doc_layout.text_layout import TextLayout
from doc_layout.line_layout import LineLayout
from doc_layout.input_layout import InputLayout
from doc_layout.checkbox_layout import CheckboxLayout
from window_layout.rect import Rect


class BlockLayout:
    HSTEP = 13
    VSTEP = 18
    DEFAULT_PADDING = 0.7 * VSTEP

    def __init__(self, node, parent, previous):
        self.node = node
        self.parent = parent
        self.previous = previous
        self.children = []
        self.x = None
        self.y = None
        self.width = None
        self.height = 0
        self.vertical_padding = 0
        self.init_in_head()
       
    def init_in_head(self):
        if self.parent.in_head is not None:
            self.in_head = self.parent.in_head
            return

        if self.node_is("html"):
            self.in_head = None
        else:    
            self.in_head = self.node_is("head")
    
    def self_rect(self):
        return  skia.Rect.MakeLTRB(self.x, self.y,
            self.x + self.width, self.y + self.height)    

    def paint(self):
        cmds = []
        cmds.extend(self.get_rectangels_cmds())
            
        return cmds 
    
    def get_rectangels_cmds(self):
        if not isinstance(self.node, Element):
            return []
        
        bgcolor = self.node.style.get("background-color", "transparent")
        rect_cmds = []

        predicates = {"li": lambda: self.node_is("li")}
        cmd_gen ={"li": lambda: self.get_bulletpoint_cmd()}

        for key in predicates:
            if predicates[key]():
                rect_cmds.append(cmd_gen[key]())

        if bgcolor != "transparent":
            rect_cmds.append(DrawRect(self.self_rect(), bgcolor))

        return rect_cmds
    
    def node_is(self, tag):
        return isinstance(self.node, Element) and self.node.tag == tag

    def get_bulletpoint_cmd(self):
        bullet_char = "•"
        parent_font = get_html_node_font(self.node)

        width = parent_font.measureText(bullet_char)
        line_height = linespace(parent_font)
        square_size = width  
        
        top_offset = (line_height - square_size) // 1.1
        x1, y1 = self.x, self.y + top_offset
        x2, y2 = x1 + square_size, y1 + square_size

        return DrawRect(skia.Rect.MakeLTRB(x1, y1, x2, y2), "black")
    
    def init_coordinates(self):
        self.x = self.parent.x
        self.width = self.parent.width if self.is_auto_property('width') else px_str_to_int(self.node.style["width"])
        self.init_y()
    
    def is_auto_property(self, property):
        return not has_px_ending(self.node.style[property])

    def init_y(self):
        if self.previous:
            y = self.previous.y + self.previous.height
        else:
            y = self.parent.y

        if self.is_toc_first_element():
            y += 0.5 *self.VSTEP
        
        self.y = y 

    def init_children(self):
        previous = None
        for child in self.node.children:
            next = BlockLayout(child, self, previous)
            self.children.append(next)
            previous = next
    
    def init_text_properties(self):
        self.init_cursor_x()
        self.only_uppercase = False
        self.current_tag = ''
        self.current_tag_class = ''
        self.preformat = False

    def init_cursor_x(self):
        self.cursor_x = self.VSTEP
        if self.node_is("li"):
            self.cursor_x += 0.5 * self.VSTEP
        

    def layout_text(self):
        self.init_text_properties()
        if not self.in_head:
            self.new_line()
            self.recurse(self.node)

    def calculate_hight(self,mode):
        if not self.is_auto_property('height'):
            self.height +=  px_str_to_int(self.node.style["height"])
            return
        
        self.height += sum([child.height for child in self.children])
        if len(self.children) > 0:
            self.height += self.get_child_vertical_distance()

    def layout(self):
        self.init_coordinates()
        mode = self.layout_mode()

        if mode == "block":
            self.init_children()
        else:
            self.layout_text()
            
        self.layout_children()

        self.calculate_hight(mode)

    def layout_children(self):
        i = 0
        while (i < len(self.children)):
            current_child = self.children[i]
            current_child.layout()
            i+= 1
        
        if i != 0:
            last_child = self.children[i-1]
            last_child.height += self.vertical_padding

    def layout_mode(self):
        if isinstance(self.node, Text):
            return "inline"
        elif any([isinstance(child, Element) and child.style['display'] == 'block'
                  for child in self.node.children]):
            return "block"
        elif self.node.children or (self.node.tag == "input" and not self.node.has_attribute("type", "hidden")):
            return "inline"
        else:
            return "block"

    def recurse(self, tree):
        if isinstance(tree, Text):
            if self.should_align_horizontal():
                self.cursor_x = self.get_centered_cursor_x(tree.text)
            for word in self.split_text(tree.text):
                self.word(tree, word)
        else:
            if tree.tag == "input" or tree.tag == "button":
                self.input(tree)
                return
            self.open_tag(tree)
            for child in tree.children:
                self.recurse(child)
            self.close_tag(tree)

    def word(self, node, word):
        if self.only_uppercase:
            word = word.upper()

        line = self.children[-1]
        previous_word = line.children[-1] if line.children else None
        text = TextLayout(node, word, line, previous_word)
        line.children.append(text)

    def new_line(self):
        last_line = self.children[-1] if self.children else None
        if last_line_is_empty(last_line):
            return

        new_line = LineLayout(self.node, self, last_line, self.cursor_x)
        self.children.append(new_line)

    def input(self, node):
        line = self.children[-1]
        previous_word = line.children[-1] if line.children else None
        if is_checkbox(node):
            input = CheckboxLayout(node, line, previous_word)
        else:
            input = InputLayout(node, line, previous_word)
        line.children.append(input)        

    def should_paint(self):
        return isinstance(self.node, Text) or \
            (self.node.tag != "input" and self.node.tag !=  "button")
    
    def handle_tag(self, element_node, tag_handlers):
        if element_node.tag in tag_handlers:
                tag_handlers[element_node.tag]()

        if "class" in element_node.attributes:
             self.current_tag_class = element_node.attributes["class"]
        else:
            self.current_tag_class = []
    
    def open_tag(self, element_node):
        opening_tag_handlers = {
            "br": self.new_line,
            "h1": lambda: (self.new_line(), setattr(self, 'current_tag', "h1")),
            "sup": lambda: (setattr(self, 'current_tag', "sup")),
            "abbr": lambda: (setattr(self, 'only_uppercase', True)),
            "pre": lambda: (setattr(self, 'preformat', True), setattr(self, 'vertical_padding', self.vertical_padding +self.DEFAULT_PADDING)),
            "p": lambda: (setattr(self, 'vertical_padding', self.vertical_padding + self.DEFAULT_PADDING))
        }
        self.handle_tag(element_node, opening_tag_handlers)

    def close_tag(self, element_node):
        closing_tag_handlers = {
            "h1": lambda: (setattr(self, 'current_tag', "")),
            "sup": lambda: (setattr(self, 'current_tag', "")),
            "abbr": lambda: (setattr(self, 'only_uppercase', False)),
            "pre": lambda: (setattr(self, 'preformat', False), setattr(self, 'vertical_padding', self.vertical_padding - self.DEFAULT_PADDING)),
        }
        self.handle_tag(element_node, closing_tag_handlers)

    def should_align_horizontal(self):
        return self.current_tag == 'h1' and "title" in self.current_tag_class

    def get_centered_cursor_x(self, text):
        font = get_html_node_font(self.node)
        w = font.measureText(text)
        white_space = self.width - w
        left_margin = white_space/2
        return left_margin
        
    def should_align_vertical(self):
        return self.current_tag == 'sup'
    
    def should_split_on_hypen(self, word, font):
        indexes = BlockLayout.get_soft_hyphen_positions(word)
        if len(indexes) == 0:
            return False
        
        min_break_index = indexes[0]
        min_word_split = word[:min_break_index] + "-"
        return not self.passed_horizontal_border(min_word_split, font)

    def get_soft_hyphen_positions(word):
        soft_hyphen = '\u00AD'
        indexes = [m.start() for m in re.finditer(soft_hyphen, word)]
        return indexes

    def split_on_hypen(self, word, font):
        indexes = BlockLayout.get_soft_hyphen_positions(word)
        last_valid_split_index = indexes[0]

        for split_index in indexes:
            first_split_part = word[:split_index] + "-"
            if not self.passed_horizontal_border(first_split_part, font):
                last_valid_split_index = split_index
            else:
                break
        
        before_split = word[:last_valid_split_index] + "-"
        after_split = word[last_valid_split_index:]
        return before_split, after_split

    def split_text(self, text):
        if not self.preformat:
            return text.split()

        words_spaces_new_line_regex = r'[^\s\n]+|[ ]+|\n'
        text_parts = re.findall(words_spaces_new_line_regex, text)
    
        return text_parts
    
    def is_toc_nav_element(self):
        return self.node_is("nav") and self.node.has_attribute("id","toc")
    
    def is_toc_list_element(self):
        return self.node_is('ul') and self.parent.is_toc_nav_element()

    def is_toc_first_element(self):
        return self.previous is None and self.parent.is_toc_list_element()
    
    def get_child_vertical_distance(self):
        return self.children[0].y - self.y
        