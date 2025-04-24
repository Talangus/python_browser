import skia
from window_layout.rect import Rect
from doc_layout.utils import parse_color, linespace
class DrawText:
    def __init__(self,x1, y1, text, font, color):
        self.rect = skia.Rect.MakeLTRB(
            x1, y1,
            x1 + font.measureText(text),
            y1 + linespace(font))
        self.top = y1
        self.left = x1
        self.text = text
        self.font = font
        self.color = color
        self.bottom = y1 + linespace(self.font)

    def execute(self, scroll, canvas):
        paint = skia.Paint(
            AntiAlias=True,
            Color=parse_color(self.color),
        )
        baseline = self.rect.top() - scroll \
            - self.font.getMetrics().fAscent
        canvas.drawString(self.text, float(self.rect.left()),
            baseline, self.font, paint)