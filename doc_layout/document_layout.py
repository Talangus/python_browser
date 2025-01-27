from doc_layout.block_layout import BlockLayout

class DocumentLayout:
    HSTEP = 13
    VSTEP = 18
    
    def __init__(self, node, width):
        self.node = node
        self.parent = None
        self.children = []
        self.x = None
        self.y = None
        self.width = width - 2 * self.HSTEP
        self.height = None
        self.in_head = None
        

    def layout(self):
        child = BlockLayout(self.node, self, None)
        self.children.append(child)
        self.x = self.HSTEP
        self.y = 0
        child.layout()
        self.height = child.height

    def paint(self):
        return []
    
    def node_is(self, tag):
        return self.node.tag == tag
    
    def is_toc_list_element(self):
        return False