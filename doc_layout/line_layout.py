from doc_layout.utils import split_on_object, get_object_index
class LineLayout:
    def __init__(self, node, parent, previous, x):
        self.node = node
        self.parent = parent
        self.previous = previous
        self.children = []
        self.x = x

    def layout_children(self):
        i = 0
        while (i < len(self.children)):
            current_child = self.children[i]
            current_child.layout()
            i+= 1

    def split_line(self, word):                
        before_split, after_split = split_on_object(self.children, word)
        self.children = before_split

        new_line = LineLayout(self.node, self.parent, self, self.x)
        new_line.children = after_split

        self.insert_to_parent(new_line)
        new_line.reset_children()
    
    def insert_to_parent(self, new_line):
        block_lines = self.parent.children
        self_index = get_object_index(block_lines, self)
        next_line_index = self_index + 1

        if next_line_index < len(block_lines):
            next_line = block_lines[next_line_index]
            next_line.previous = new_line

        block_lines.insert(next_line_index, new_line)

    def reset_children(self):
        first_word = self.children[0]
        first_word.previous = None

        for word in self.children:
            word.parent = self

    def layout(self):                                  
        self.width = self.parent.width
        # self.x = self.parent.x
        if self.previous:
            self.y = self.previous.y + self.previous.height
        else:
            self.y = self.parent.y + self.parent.vertical_padding
        self.layout_children()

        max_ascent = max([word.font.metrics("ascent") for word in self.children])
        baseline = self.y + 1.25 * max_ascent
        for word in self.children:
            word.y = baseline - word.font.metrics("ascent")
        max_descent = max([word.font.metrics("descent") for word in self.children])
        self.height = 1.25 * (max_ascent + max_descent) 

    def paint(self):
        return []