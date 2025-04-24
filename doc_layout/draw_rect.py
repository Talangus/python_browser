import skia
from window_layout.rect import Rect
from doc_layout.utils import parse_color
class DrawRect:
    def __init__(self, rect, color, outline=""):
        self.rect = rect
        self.color = color
        self.outline = outline

    def execute(self, scroll, canvas):
        paint = skia.Paint(
            Color=parse_color(self.color),
        )
        canvas.drawRect(self.rect.makeOffset(0, -scroll), paint)