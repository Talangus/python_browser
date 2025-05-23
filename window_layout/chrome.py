import skia

from doc_layout.utils import get_font, linespace
from window_layout.rect import Rect
from doc_layout.draw_text import DrawText
from doc_layout.draw_rect import DrawRect
from window_layout.draw_outline import DrawOutline
from window_layout.draw_line import DrawLine
from network.url import URL

PADLOCK_CHAR='\N{lock}'
CROSSMARK_CHAR = '\N{CROSS MARK}'
class Chrome:
    def __init__(self, browser):
        self.browser = browser
        self.padding = 5
        self.focus = None
        self.address_bar = ""
        
        self.init_tab_bar()
        self.init_url_bar()
        self.bottom = self.urlbar_bottom

    def raster(self, canvas):
            for cmd in self.paint():
                cmd.execute(canvas)    

    def init_tab_bar(self):
        self.font = get_font(20, "normal", "roman", "Arial")
        self.font_height = linespace(self.font)

        self.tabbar_top = 0
        self.tabbar_bottom = self.font_height + 2*self.padding
        plus_width = self.font.measureText("+") + 2*self.padding

        self.newtab_rect =  skia.Rect.MakeLTRB(
           self.padding, self.padding,
           self.padding + plus_width,
           self.padding + self.font_height)

    def init_url_bar(self):
        self.urlbar_top = self.tabbar_bottom
        self.urlbar_bottom = self.urlbar_top + self.font_height + 2*self.padding
        back_width = self.font.measureText("<") + 2*self.padding
        self.back_rect = skia.Rect.MakeLTRB(
            self.padding,
            self.urlbar_top + self.padding,
            self.padding + back_width,
            self.urlbar_bottom - self.padding)
        
        forward_width = self.font.measureText(">") + 2*self.padding
        self.forward_rect = skia.Rect.MakeLTRB(
            self.back_rect.right() + self.padding,
            self.urlbar_top + self.padding,
            self.back_rect.right() + self.padding + forward_width,
            self.urlbar_bottom - self.padding)

        self.address_rect = skia.Rect.MakeLTRB(
            self.forward_rect.right() + self.padding,
            self.urlbar_top + self.padding,
            self.browser.width - self.padding,
            self.urlbar_bottom - self.padding)
    
    def tab_rect(self, i):
        tabs_start = self.newtab_rect.right() + self.padding
        tab_width = self.font.measureText("Tab X") + 2*self.padding
        return skia.Rect.MakeLTRB(
            tabs_start + tab_width * i, self.tabbar_top,
            tabs_start + tab_width * (i + 1), self.tabbar_bottom)
    
    def paint(self):
        cmds = []
        self.paint_new_tab_button(cmds)
        self.paint_tabs(cmds)
        self.paint_back_button(cmds)
        self.paint_forward_button(cmds)
        self.paint_address_bar(cmds)

        return cmds

    def paint_new_tab_button(self, cmds):
        cmds.append(DrawOutline(self.newtab_rect, "black", 1))
        cmds.append(DrawText(
            self.newtab_rect.left() + self.padding,
            self.newtab_rect.top(),
            "+", self.font, "black"))
    
    def paint_tabs(self,cmds):
        for i, tab in enumerate(self.browser.tabs):
            bounds = self.tab_rect(i)
            cmds.append(DrawLine(
                bounds.left(), 0, bounds.left(), bounds.bottom(),
                "black", 1))
            cmds.append(DrawLine(
                bounds.right(), 0, bounds.right(), bounds.bottom(),
                "black", 1))
            cmds.append(DrawText(
                bounds.left() + self.padding, bounds.top() + self.padding,
                "Tab {}".format(i), self.font, "black"))
            
            if tab == self.browser.active_tab:
                cmds.append(DrawLine(
                    0, bounds.bottom(), bounds.left(), bounds.bottom(),
                    "black", 1))
                cmds.append(DrawLine(
                    bounds.right(), bounds.bottom(), self.browser.width, bounds.bottom(),
                    "black", 1))

    def paint_back_button(self, cmds):
        cmds.append(DrawOutline(self.back_rect, "black", 1))
        color = "black" if len(self.browser.active_tab.history) > 1 else "gray"
        cmds.append(DrawText(
            self.back_rect.left() + self.padding,
            self.back_rect.top(),
            "<", self.font, color))
        
    def paint_forward_button(self, cmds):
        cmds.append(DrawOutline(self.forward_rect, "black", 1))
        color = "black" if self.browser.active_tab.forward_stack else "gray"
        cmds.append(DrawText(
            self.forward_rect.left() + self.padding,
            self.forward_rect.top(),
            ">", self.font, color))


    def paint_address_bar(self, cmds):
        cmds.append(DrawOutline(self.address_rect, "black", 1))
        if self.focus == "address bar":
            cmds.append(DrawText(
                self.address_rect.left() + self.padding,
                self.address_rect.top(),
                self.address_bar, self.font, "black"))
            w = self.font.measureText(self.address_bar)
            cmds.append(DrawLine(
                self.address_rect.left() + self.padding + w,
                self.address_rect.top(),
                self.address_rect.left() + self.padding + w,
                self.address_rect.bottom(),
                "red", 1))
        else:
            w = 0
            if self.should_paint_padlock():
                cmds.extend(self.get_padlock_cmds())
                w = self.font.measureText(PADLOCK_CHAR) + self.padding

            url = str(self.browser.active_tab.url)
            cmds.append(DrawText(
                self.address_rect.left() + self.padding + w,
                self.address_rect.top(),
                url, self.font, "black"))

    def click(self, x, y):
        self.focus = None
        if self.newtab_rect.contains(x, y):
            self.browser.new_tab(URL("https://browser.engineering/"))
        elif self.back_rect.contains(x, y):
            self.browser.active_tab.go_back()
        elif self.forward_rect.contains(x, y):
            self.browser.active_tab.go_forward()
        elif self.address_rect.contains(x, y):
            self.focus = "address bar"
            self.address_bar = ""
        else:
            for i, tab in enumerate(self.browser.tabs):
                if self.tab_rect(i).contains(x, y):
                    self.browser.active_tab = tab
                    break

    def keypress(self, char):
        if self.focus == "address bar":
            self.address_bar += char
            return True
        
        return False

    def enter(self):
        if self.focus == "address bar":
            self.browser.active_tab.load(URL(self.address_bar))
            self.focus = None
            return True
        return False

    def backspace(self):
        if self.focus == "address bar" and len(self.address_bar) != 0:
            self.address_bar = self.address_bar[:-1]

    def blur(self):
        self.focus = None

    def should_paint_padlock(self):
        return self.browser.active_tab.url.scheme == 'https'
    
    def get_padlock_cmds(self):
        padlock_cmd = DrawText(
                self.address_rect.left() + self.padding,
                self.address_rect.top(),
                PADLOCK_CHAR, self.font, 'black')
        cmds = [padlock_cmd]
        
        if self.browser.active_tab.url.ssl_error:
            w = self.font.measureText(PADLOCK_CHAR)/4
            crossmark_cmd = DrawText(
                self.address_rect.left() + self.padding + 4,
                self.address_rect.top(),
                'X', self.font, 'red')
            cmds.append(crossmark_cmd)

        return cmds