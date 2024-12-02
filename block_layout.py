from utils import *
from element import Element
from draw_text import DrawText
from draw_rect import DrawRect
import tkinter.font

FONTS = {}
DEFAULT_FONT_FAMILY = "Arial"
DEFAULT_WEIGHT = "normal"
DEFAULT_STYLE= "roman"
DEFAULT_SIZE = 12

def get_font(size, weight, style, family):
        key = (size, weight, style, family)
        if key not in FONTS:
            font = tkinter.font.Font(size=size, weight=weight,
                slant=style, family=family)
            label = tkinter.Label(font=font)
            FONTS[key] = (font, label)
        return FONTS[key][0]

def get_default_font():
    return get_font(DEFAULT_SIZE,DEFAULT_WEIGHT,DEFAULT_STYLE, DEFAULT_FONT_FAMILY)

BLOCK_ELEMENTS = [
    "html", "body", "article", "section", "nav", "aside",
    "h1", "h2", "h3", "h4", "h5", "h6", "hgroup", "header",
    "footer", "address", "p", "hr", "pre", "blockquote",
    "ol", "ul", "menu", "li", "dl", "dt", "dd", "figure",
    "figcaption", "main", "div", "table", "form", "fieldset",
    "legend", "details", "summary"
]

class BlockLayout:
    HSTEP = 13
    VSTEP = 18

    def __init__(self, node, parent, previous):
        self.node = node
        self.parent = parent
        self.previous = previous
        self.children = []
        self.display_list = []
        self.x = None
        self.y = None
        self.width = None
        self.height = None
        self.init_in_head()

        if self.is_toc_nav_element():
            self.add_toc_text()

    def init_in_head(self):
        if self.parent.in_head is not None:
            self.in_head = self.parent.in_head
            return

        if self.node_is("html"):
            self.in_head = None
        else:    
            self.in_head = self.node_is("head")
        

    def paint(self):
        cmds = []
        cmds.extend(self.get_rectangels_cmds())
        cmds.extend(self.get_text_cmds())
            
        return cmds 
    
    def get_text_cmds(self):
        cmds = []
        if self.layout_mode() == "inline":
            for x, y, word, font in self.display_list:
                    cmds.append(DrawText(x, y, word, font))
        return cmds

    def get_rectangels_cmds(self):
        if not isinstance(self.node, Element):
            return []
        
        x2 = self.x + self.width
        y2 = self.y + self.height
        rect_cmds = []

        predicates = {"pre_element": lambda: self.node_is("pre"),
                    "link_bar": lambda: self.node_is("nav") and self.node.has_class("links"),
                    "li": lambda: self.node_is("li"),
                    "toc": lambda: self.is_toc_nav_element()}
        cmd_gen ={"pre_element":lambda: DrawRect(self.x, self.y, x2, y2, "gray"),
                  "link_bar": lambda: DrawRect(self.x, self.y, x2, y2, "light gray"),
                  "li": lambda: self.get_bulletpoint_cmd(),
                  "toc": lambda: DrawRect(self.x, self.y, x2, y2, "gray")}

        for key in predicates:
            if predicates[key]():
                rect_cmds.append(cmd_gen[key]())

        return rect_cmds
    
    def node_is(self, tag):
        return isinstance(self.node, Element) and self.node.tag == tag

    def get_bulletpoint_cmd(self):
        bullet_char = "•"
        default_font = get_default_font()

        width = default_font.measure(bullet_char)
        ascent = default_font.metrics("ascent")  
        descent = default_font.metrics("descent")  
        line_height = ascent + descent  
        square_size = width  
        
        top_offset = (line_height - square_size) // 2
        x1, y1 = self.x, self.y + top_offset
        x2, y2 = x1 + square_size, y1 + square_size

        return DrawRect(x1, y1, x2, y2, "white")
    
    def init_coordinates(self):
        self.x = self.parent.x
        self.width = self.parent.width
        self.init_y()

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
        self.cursor_y = 0
        self.weight = DEFAULT_WEIGHT
        self.style = DEFAULT_STYLE
        self.size = DEFAULT_SIZE
        self.font_family = DEFAULT_FONT_FAMILY
        self.only_uppercase = False
        self.current_tag = ''
        self.current_tag_class = ''
        self.preformat = False

    def init_cursor_x(self):
        if self.node_is("li"):
            self.cursor_x = self.VSTEP
        else:
            self.cursor_x = 0

    def init_cursor_y(self):
        if self.is_toc_first_element():
            self.cursor_y = self.VSTEP
        else:
            self.cursor_y = 0
          

    def layout_text(self):
        self.init_text_properties()
        if not self.in_head:
            self.line = []
            self.recurse(self.node)
            self.flush()

    def calculate_hight(self,mode):
        if mode == "block":
            self.height = sum([child.height for child in self.children])
            
            if len(self.children) > 0:
                self.height += self.get_child_vertical_distance()

        else: self.height = self.cursor_y

    def layout(self):
        self.init_coordinates()
        mode = self.layout_mode()

        if mode == "block":
            self.init_children()
        else:
            self.layout_text()
            
        for child in self.children:
            child.layout()

        self.calculate_hight(mode)
        
    def layout_mode(self):
        if isinstance(self.node, Text):
            return "inline"
        elif any([isinstance(child, Element) and child.tag in BLOCK_ELEMENTS
                  for child in self.node.children]):
            return "block"
        elif self.node.children:
            return "inline"
        else:
            return "block"

    def recurse(self, tree):
        if isinstance(tree, Text):
            if self.should_align_horizontal():
                self.cursor_x = self.get_centered_cursor_x(tree.text)
            for word in self.split_text(tree.text):
                self.word(word)
        else:
            self.open_tag(tree)
            for child in tree.children:
                self.recurse(child)
            self.close_tag(tree)

    def flush(self):
        if not self.line: return
        metrics = [font.metrics() for x, word, font, y_align in self.line]
        max_ascent = max([metric["ascent"] for metric in metrics])
        baseline = self.cursor_y + 1.25 * max_ascent
        
        for rel_x, word, font, y_align in self.line:
            x = self.x + rel_x
            y = self.y
            
            if y_align:
                top_alignment = baseline - max_ascent
                y += top_alignment
            else:
                y += baseline - font.metrics("ascent")
            self.display_list.append((x, y, word, font))
            
        max_descent = max([metric["descent"] for metric in metrics])
        self.cursor_y = baseline + 1.25 * max_descent
        self.cursor_x = 0
        self.line = []
            
    def word(self, word):
        if word == "\n":
            self.flush()
            return
        
        font = get_font(self.size, self.weight, self.style, self.font_family)
        if self.only_uppercase:
            word = word.upper()
        w = font.measure(word)

        if self.passed_horizontal_border(word, font):
            if self.should_split_on_hypen(word, font):
                before_split, after_split = self.split_on_hypen(word, font)
                self.line.append((self.cursor_x, before_split, font, self.should_align_vertical()))
                self.flush()
                self.word(after_split)
                return
            else: self.flush()

        self.line.append((self.cursor_x, word, font, self.should_align_vertical()))
        self.cursor_x += w + font.measure(" ")

    def handle_tag(self, element_node, tag_handlers):
        if element_node.tag in tag_handlers:
                tag_handlers[element_node.tag]()

        if "class" in element_node.attributes:
             self.current_tag_class = element_node.attributes["class"]
        else:
            self.current_tag_class = []
    
    def open_tag(self, element_node):
        opening_tag_handlers = {
            "i": lambda: setattr(self, 'style', 'italic'),
            "b": lambda: setattr(self, 'weight', 'bold'),
            "small": lambda: setattr(self, 'size', self.size - 2),
            "big": lambda: setattr(self, 'size', self.size + 4),
            "br": self.flush,
            "h1": lambda: (self.flush(), setattr(self, 'current_tag', "h1")),
            "sup": lambda: (setattr(self, 'current_tag', "sup"), setattr(self, 'size', 6)),
            "abbr": lambda: (setattr(self, 'size', self.size - 4), setattr(self, 'weight', 'bold'), setattr(self, 'only_uppercase', True)),
            "pre": lambda: (setattr(self, 'preformat', True), setattr(self, 'font_family', "IBM Plex Mono")),
        }
        self.handle_tag(element_node, opening_tag_handlers)

    def close_tag(self, element_node):
        closing_tag_handlers = {
            "i": lambda: setattr(self, 'style', 'roman'),
            "b": lambda: setattr(self, 'weight', 'normal'),
            "small": lambda: setattr(self, 'size', self.size + 2),
            "big": lambda: setattr(self, 'size', self.size - 4),
            "h1": lambda: (self.flush(), setattr(self, 'current_tag', "")),
            "sup": lambda: (setattr(self, 'current_tag', ""), setattr(self, 'size', 12)),
            "p": lambda: (self.flush(), setattr(self, 'cursor_y', self.cursor_y + BlockLayout.VSTEP)),
            "abbr": lambda: (setattr(self, 'size', self.size + 4), setattr(self, 'weight', 'normal'), setattr(self, 'only_uppercase', False)),
            "pre": lambda: (self.flush(), setattr(self, 'preformat', False), setattr(self, 'font_family', DEFAULT_FONT_FAMILY)),
        }
        self.handle_tag(element_node, closing_tag_handlers)

    def should_align_horizontal(self):
        return self.current_tag == 'h1' and "title" in self.current_tag_class

    def get_centered_cursor_x(self, text):
        font = get_font(self.size, self.weight, self.style, self.font_family)
        w = font.measure(text)
        white_space = self.width - w
        left_margin = white_space/2
        return left_margin
        
    def should_align_vertical(self):
        return self.current_tag == 'sup'
    
    def passed_horizontal_border(self, word ,font):
        if self.preformat:
            return False
        w = font.measure(word)
        return self.cursor_x + w > self.width 

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
    
    def add_toc_text(self):
        if len(self.node.children) > 0:
            first = self.node.children[0]
            if not isinstance(first, Text) or (isinstance(first, Text) and first.text != '\n  Table Of Content\n'):
                self.node.children.insert(0,Text('\n  Table Of Content\n', self.node))
        