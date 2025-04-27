import tkinter
import argparse
import ctypes
import sdl2
import skia
import sys


from network.url import URL
from network.socket_manager import socket_manager 
from network.cache import cache
from tab import Tab
from window_layout.chrome import Chrome
from util.utils import *
from doc_layout.utils import parse_color


class Browser:
    def __init__(self):
        self.tabs = []
        self.active_tab = None
        self.width = 800
        self.height = 600
        self.sdl_window = sdl2.SDL_CreateWindow(b"Browser",
            sdl2.SDL_WINDOWPOS_CENTERED, sdl2.SDL_WINDOWPOS_CENTERED,
            self.width, self.height, sdl2.SDL_WINDOW_SHOWN | sdl2.SDL_WINDOW_RESIZABLE)
        self.root_surface = skia.Surface.MakeRaster(
            skia.ImageInfo.Make(
                self.width, self.height,
                ct=skia.kRGBA_8888_ColorType,
                at=skia.kUnpremul_AlphaType))
        if sdl2.SDL_BYTEORDER == sdl2.SDL_BIG_ENDIAN:
            self.RED_MASK = 0xff000000
            self.GREEN_MASK = 0x00ff0000
            self.BLUE_MASK = 0x0000ff00
            self.ALPHA_MASK = 0x000000ff
        else:
            self.RED_MASK = 0x000000ff
            self.GREEN_MASK = 0x0000ff00
            self.BLUE_MASK = 0x00ff0000
            self.ALPHA_MASK = 0xff000000
        self.canvas = self.root_surface.getCanvas()
        self.chrome = Chrome(self)
        self.focus = None

    def handle_scrolldown(self):
        self.active_tab.tab_layout.on_scrolldown()
        self.draw()

    def handle_scrollup(self):
        self.active_tab.tab_layout.on_scrollup()
        self.draw()

    def handle_click(self, e):
        if e.y < self.chrome.bottom:
            if self.focus == 'content':
                self.active_tab.blur()
            self.focus = None
            self.chrome.click(e.x, e.y)
        else:
            self.focus = 'content'
            self.chrome.blur()
            tab_y = e.y - self.chrome.bottom
            self.active_tab.click(e.x, tab_y)
        self.draw()

    def handle_middle_click(self, e):
        if e.y >= self.chrome.bottom:
            tab_y = e.y - self.chrome.bottom
            url = self.active_tab.get_clicked_url(e.x, tab_y)
            if url:
                self.new_tab(url)
                self.draw()

    def handle_mouse_wheel(self, e):
        self.active_tab.tab_layout.on_mouse_wheel(e)
        self.draw()

    def handle_resize(self, event):
        new_width = event.window.data1
        new_height = event.window.data2
        
        self.width = new_width
        self.height = new_height
        self.active_tab.on_resize(new_width, new_height)
        self.draw()

    def handle_key(self, char):
        # if len(e.char) == 0: return
        # if not (0x20 <= ord(e.char) < 0x7f): return

        if self.chrome.keypress(char):
            self.draw()
        elif self.focus == "content":
            self.active_tab.keypress(char)
            self.draw()

    def handle_enter(self):
        if self.chrome.enter():
            self.draw()
        elif self.focus == "content":
            self.active_tab.enter()
            self.draw()

    def handle_backspace(self):
        self.chrome.backspace()
        self.draw()

    def on_close(self):
        socket_manager.close_all()
        cache.clear_expired_entries()
        sdl2.SDL_DestroyWindow(self.sdl_window)

    def draw(self):
        sdl2.SDL_SetWindowTitle(self.sdl_window, self.active_tab.title.encode('utf-8'))
        self.canvas.clear(parse_color('white'))
        self.active_tab.draw(self.canvas, self.chrome.bottom)
        for cmd in self.chrome.paint():
            cmd.execute(0, self.canvas)
            
        skia_image = self.root_surface.makeImageSnapshot()
        skia_bytes = skia_image.tobytes()
        depth = 32 
        pitch = 4 * self.width
        sdl_surface = sdl2.SDL_CreateRGBSurfaceFrom(
            skia_bytes, self.width, self.height, depth, pitch,
            self.RED_MASK, self.GREEN_MASK,
            self.BLUE_MASK, self.ALPHA_MASK)
        rect = sdl2.SDL_Rect(0, 0, self.width, self.height)
        window_surface = sdl2.SDL_GetWindowSurface(self.sdl_window)
        sdl2.SDL_BlitSurface(sdl_surface, rect, window_surface, rect)
        sdl2.SDL_UpdateWindowSurface(self.sdl_window)

    def new_tab(self, url):
        new_tab = Tab(self.width, self.height - self.chrome.bottom)
        new_tab.load(url)
        self.active_tab = new_tab
        self.tabs.append(new_tab)
        self.draw()

def parse_arguments():
    parser = argparse.ArgumentParser(description="Simple python browser.")
    
    parser.add_argument("url",
        type=str,
        nargs="?",
        default=URL.DEFAULT_FILE_PATH, 
        help="The URL to process.")
    
    args = parser.parse_args()
    return args.url

def mainloop(browser):
    event = sdl2.SDL_Event()
    while True:
        while sdl2.SDL_PollEvent(ctypes.byref(event)) != 0:
            match event.type:
                case sdl2.SDL_QUIT:
                    browser.on_close()
                    sdl2.SDL_Quit()
                    sys.exit()
                case sdl2.SDL_MOUSEBUTTONUP:
                    if event.button.button == sdl2.SDL_BUTTON_LEFT:
                        browser.handle_click(event.button)
                    elif event.button.button == sdl2.SDL_BUTTON_MIDDLE:
                        browser.handle_middle_click(event)
                case sdl2.SDL_KEYDOWN:
                    if event.key.keysym.sym == sdl2.SDLK_RETURN:
                        browser.handle_enter()
                    elif event.key.keysym.sym == sdl2.SDLK_DOWN:
                        browser.handle_scrolldown()
                    elif event.key.keysym.sym == sdl2.SDLK_UP:
                        browser.handle_scrollup()
                    elif event.key.keysym.sym == sdl2.SDLK_BACKSPACE:
                        browser.handle_backspace()
                case sdl2.SDL_TEXTINPUT:
                    browser.handle_key(event.text.text.decode('utf8'))
                case sdl2.SDL_MOUSEWHEEL:
                    if event.wheel.y < 0:
                        browser.handle_scrolldown()
                    elif event.wheel.y > 0:
                        browser.handle_scrollup()
                case sdl2.SDL_WINDOWEVENT:
                    if event.window.event == sdl2.SDL_WINDOWEVENT_SIZE_CHANGED:
                        browser.handle_resize(event)

if __name__ == "__main__":
    sdl2.SDL_Init(sdl2.SDL_INIT_EVENTS)
    url_arg = parse_arguments()
    url = URL(url_arg)
    
    browser = Browser()
    browser.new_tab(url)
    mainloop(browser)