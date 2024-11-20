from utils import *
from element import Element
import tkinter.font

FONTS = {}
DEFAULT_FONT = "Arial"
def get_font(size, weight, style, family):
        key = (size, weight, style, family)
        if key not in FONTS:
            font = tkinter.font.Font(size=size, weight=weight,
                slant=style, family=family)
            label = tkinter.Label(font=font)
            FONTS[key] = (font, label)
        return FONTS[key][0]

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
        
    def paint(self):
        return self.display_list    
    
    def layout(self):
        self.x = self.parent.x
        self.width = self.parent.width

        if self.previous:
            self.y = self.previous.y + self.previous.height
        else:
            self.y = self.parent.y

        mode = self.layout_mode()
        if mode == "block":
            previous = None
            for child in self.node.children:
                next = BlockLayout(child, self, previous)
                self.children.append(next)
                previous = next
        else:
            self.cursor_x = 0
            self.cursor_y = 0
            self.weight = "normal"
            self.style = "roman"
            self.size = 12
            self.font_family = DEFAULT_FONT
            self.only_uppercase = False
            self.current_tag = ''
            self.current_tag_class = ''
            self.preformat = False

            self.line = []
            self.recurse(self.node)
            self.flush()
        
        for child in self.children:
            child.layout()

        if mode == "block":
            self.height = sum([child.height for child in self.children])
        else: self.height = self.cursor_y


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
            "pre": lambda: (self.flush(), setattr(self, 'preformat', False), setattr(self, 'font_family', DEFAULT_FONT)),
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
        


    
         