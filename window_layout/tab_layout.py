from window_layout.coordinate import Coordinate

class TabLayout:
    SCROLL_STEP = 100
    HSTEP = 13
    VSTEP = 18

    def __init__(self, tab):
        self.tab = tab
        self.height = tab.height
        self.width = tab.width
        self.scroll = 0 

    def update_size(self):
        self.height = self.tab.height
        self.width = self.tab.width

    def is_below_viewport(self, cmd):
        return cmd.rect.top > self.scroll + self.height
    
    def is_above_viewport(self,cmd, offset):
        return cmd.rect.bottom + self.VSTEP < self.scroll + offset

    def on_scrolldown(self, event):
        tmp_scroll = self.scroll + self.SCROLL_STEP
        max_scroll = self.get_max_scroll()
        if tmp_scroll > max_scroll:
            tmp_scroll = max_scroll
        
        self.scroll = tmp_scroll

    def get_max_scroll(self):
        page_bottom = self.tab.document.height

        if page_bottom <= self.height:
            max_scroll = 0
        else:
            max_scroll = page_bottom - self.height + 2*self.VSTEP
        
        return max_scroll
    
    def on_scrollup(self, event):
        tmp_scroll = self.scroll - self.SCROLL_STEP
        if tmp_scroll < 0:
            self.scroll = 0
        else:
            self.scroll = tmp_scroll
        
        
    def on_mouse_wheel(self, event):
        if event.delta > 0:
            self.on_scrollup(event)
        else:
            self.on_scrolldown(event)

    def handle_scrollbar(self, canvas):
        if not self.need_scrollbar():
            return
        
        top_left ,bottom_right = self.get_scrollbar_coordinates()
        canvas.create_rectangle(*top_left ,*bottom_right, fill="blue")

    def need_scrollbar(self):
        scrollbar_hight = self.get_scorllbar_hight()
        return scrollbar_hight < self.height
        
    def get_scrollbar_coordinates(self):
        bar_width = self.VSTEP*0.8
        bar_hight = self.get_scorllbar_hight()
        top_left = self.get_scrollbar_top_left()
        bottom_right = Coordinate(top_left.x + bar_width, top_left.y + bar_hight)

        return top_left ,bottom_right

    def get_scorllbar_hight(self):
        page_bottom = self.tab.document.height
        viewport_to_page_ratio = self.height / page_bottom
        scrollbar_hight = viewport_to_page_ratio * self.height
        fit_to_screen_hight = scrollbar_hight * 0.92
        return fit_to_screen_hight
        
    def get_scrollbar_top_left(self):
        page_bottom = self.tab.document.height
        scroll_to_bottom_ratio = self.scroll / page_bottom
        scroll_bar_top = scroll_to_bottom_ratio * self.height
        fit_to_screen_top = scroll_bar_top + 3
        top_left = Coordinate(self.width - self.VSTEP, fit_to_screen_top)
        return top_left