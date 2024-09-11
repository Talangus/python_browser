from utils import *
from tag import Tag
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

class Layout:
    HSTEP = 13
    VSTEP = 18

    def __init__(self, tokens, width):
        self.display_list = []
        self.width = width
        self.cursor_x = Layout.HSTEP
        self.cursor_y = Layout.VSTEP
        self.weight = "normal"
        self.style = "roman"
        self.size = 12
        self.font_family = DEFAULT_FONT
        self.only_uppercase = False
        self.current_tag = ''
        self.current_tag_class = ''
        self.preformat = False
        self.line = []
        for tok in tokens:
            self.token(tok)
        self.flush()

    def flush(self):
        if not self.line: return
        metrics = [font.metrics() for x, word, font, y_align in self.line]
        max_ascent = max([metric["ascent"] for metric in metrics])
        baseline = self.cursor_y + 1.25 * max_ascent
        
        for x, word, font, y_align in self.line:
            if y_align:
                top_alignment = baseline - max_ascent
                y = top_alignment
            else:
                y = baseline - font.metrics("ascent")
            self.display_list.append((x, y, word, font))
            
        max_descent = max([metric["descent"] for metric in metrics])
        self.cursor_y = baseline + 1.25 * max_descent
        self.cursor_x = Layout.HSTEP
        self.line = []
            
    def token(self, tok):
        if isinstance(tok, Text):
            if self.should_align_horizontal():
                self.cursor_x = self.get_centered_cursor_x(tok.text)
            for word in self.split_text_token(tok):
                self.word(word)
        else: self.handle_tag(tok)

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

    def handle_tag(self, tok):
        tag_handlers = {
        "i": lambda: setattr(self, 'style', 'italic'),
        "/i": lambda: setattr(self, 'style', 'roman'),
        "b": lambda: setattr(self, 'weight', 'bold'),
        "/b": lambda: setattr(self, 'weight', 'normal'),
        "small": lambda: setattr(self, 'size', self.size - 2),
        "/small": lambda: setattr(self, 'size', self.size + 2),
        "big": lambda: setattr(self, 'size', self.size + 4),
        "/big": lambda: setattr(self, 'size', self.size - 4),
        "br": self.flush,
        "h1": lambda: (self.flush(), setattr(self, 'current_tag', "h1")),
        "/h1": lambda: (self.flush(), setattr(self, 'current_tag', "")),
        "sup": lambda: (setattr(self, 'current_tag', "sup"), setattr(self, 'size', 6)),
        "/sup": lambda: (setattr(self, 'current_tag', ""),setattr(self, 'size', 12)),
        "/p": lambda: (self.flush(), setattr(self, 'cursor_y', self.cursor_y + Layout.VSTEP)),
        "abbr": lambda: (setattr(self, 'size', self.size - 4), setattr(self, 'weight', 'bold'), setattr(self, 'only_uppercase', True)),
        "/abbr": lambda: (setattr(self, 'size', self.size + 4), setattr(self, 'weight', 'normal'), setattr(self, 'only_uppercase', False)),
        "pre": lambda: (setattr(self, 'preformat', True), setattr(self, 'font_family', "IBM Plex Mono")),
        "/pre": lambda: (self.flush(), setattr(self, 'preformat', False), setattr(self, 'font_family', DEFAULT_FONT))
        }

        if tok.tag in tag_handlers:
                tag_handlers[tok.tag]()

        if "class" in tok.attributes:
             self.current_tag_class = tok.attributes["class"]
        else:
            self.current_tag_class = []
             
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
        return self.cursor_x + w > self.width - Layout.HSTEP

    def should_split_on_hypen(self, word, font):
        indexes = Layout.get_soft_hyphen_positions(word)
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
        indexes = Layout.get_soft_hyphen_positions(word)
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

    def split_text_token(self, text_token):
        if not self.preformat:
            return text_token.text.split()

        words_spaces_new_line_regex = r'[^\s\n]+|[ ]+|\n'
        text_parts = re.findall(words_spaces_new_line_regex, text_token.text)
    
        return text_parts
        


    
         