from html_.source_html_parser import SourceHTMLParser
from html_.html_parser import HTMLParser

def get_html_parser(body, url):
    if url.is_view_source:
        return SourceHTMLParser(body)
    else:
        return HTMLParser(body)