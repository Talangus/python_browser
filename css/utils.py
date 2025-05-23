from util.utils import tree_to_list
from html_.element import Element
from css.css_parser import CSSParser

def get_css_links(node_list):
    links = []
    for node in node_list :
        if isinstance(node, Element) and node.tag == "link"\
        and node.attributes.get("rel") == "stylesheet"\
        and "href" in node.attributes:
            links.append(node.attributes["href"])
    return links

def get_css_rules(tab, url):
    rules = []
    node_list = tree_to_list(tab.nodes, [])
    rules.extend(get_external_css_rules(tab, node_list, url))
    rules.extend(get_inline_style_rules(node_list))
    
    return rules
            
def get_external_css_rules(tab, node_list, url):
    rules = []
    links = get_css_links(node_list)
    for link in links:
        style_url = url.resolve(link)
        if not tab.allowed_request(style_url):
                print("Blocked style", link, "due to CSP")
                continue
        try:
            _, body = style_url.request(tab)
            new_rules = CSSParser(body).parse()
            rules.extend(new_rules)
        except:
            continue
    
    return rules

def get_inline_style_rules(node_list):
    rules = []
    for node in node_list:
        if node.is_tag('style'):
            rules.extend(CSSParser(node.children[0].text).parse())
    return rules