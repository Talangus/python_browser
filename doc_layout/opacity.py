import skia

class Opacity:
    def __init__(self, opacity, children):
        self.opacity = opacity
        self.children = children
        self.rect = skia.Rect.MakeEmpty()
        for cmd in self.children:
            self.rect.join(cmd.rect)

    def execute(self, canvas):
        paint = skia.Paint(
            Alphaf=self.opacity
        )
        canvas.saveLayer(None, paint)
        for cmd in self.children:
            cmd.execute(canvas)
        canvas.restore()