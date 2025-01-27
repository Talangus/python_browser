from html_.source_html_parser import SourceHTMLParser
from html_.html_parser import HTMLParser
from html_.text import Text
from util.utils import tree_to_list


def get_html_parser(body, url):
    if url.is_view_source:
        return SourceHTMLParser(body)
    else:
        return HTMLParser(body)
    
def get_html_title(tree):
    head = tree.children[0]
    
    for node in head.children:
        if node.tag == 'title':
            if len(node.children) != 0 and isinstance(node.children[0], Text):
                text_node = node.children[0]
                return text_node.text
            

    return ''    