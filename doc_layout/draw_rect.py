from window_layout.rect import Rect
class DrawRect:
    def __init__(self, rect, color, outline=""):
        self.rect = rect
        self.color = color
        self.outline = outline

    def execute(self, scroll, canvas):
        canvas.create_rectangle(
            self.rect.left, self.rect.top - scroll,
            self.rect.right, self.rect.bottom - scroll,
            width=0 if self.outline == "" else 1,
            outline=self.outline,
            fill=self.color)