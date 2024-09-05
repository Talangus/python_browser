from utils import *
from tag import Tag
import tkinter.font

FONTS = {}

def get_font(size, weight, style):
        key = (size, weight, style)
        if key not in FONTS:
            font = tkinter.font.Font(size=size, weight=weight,
                slant=style)
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
        self.current_tag = ''
        self.current_tag_class = ''
        self.line = []
        for tok in tokens:
            self.token(tok)
        self.flush()

    def flush(self):
        if not self.line: return
        metrics = [font.metrics() for x, word, font in self.line]
        max_ascent = max([metric["ascent"] for metric in metrics])
        baseline = self.cursor_y + 1.25 * max_ascent
        
        for x, word, font in self.line:
            y = baseline - font.metrics("ascent")
            self.display_list.append((x, y, word, font))
            
        max_descent = max([metric["descent"] for metric in metrics])
        self.cursor_y = baseline + 1.25 * max_descent
        self.cursor_x = Layout.HSTEP
        self.line = []
            
    def token(self, tok):
        if isinstance(tok, Text):
            if self.should_center_text():
                self.cursor_x = self.get_centered_cursor_x(tok.text)
            for word in tok.text.split():
                self.word(word)
        else: self.handle_tag(tok)

    def word(self, word):
        font = get_font(self.size, self.weight, self.style)
        w = font.measure(word)
        if self.cursor_x + w > self.width - Layout.HSTEP:
            self.flush()
        self.line.append((self.cursor_x, word, font))
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
        "/p": lambda: (self.flush(), setattr(self, 'cursor_y', self.cursor_y + Layout.VSTEP))
        }

        if tok.tag in tag_handlers:
                tag_handlers[tok.tag]()

        if "class" in tok.attributes:
             self.current_tag_class = tok.attributes["class"]
        else:
            self.current_tag_class = []
             
    def should_center_text(self):
        return self.current_tag == 'h1' and "title" in self.current_tag_class

    def get_centered_cursor_x(self, text):
        font = get_font(self.size, self.weight, self.style)
        w = font.measure(text)
        white_space = self.width - w
        left_margin = white_space/2
        return left_margin
        
         
          
    
         