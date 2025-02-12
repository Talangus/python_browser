from util.utils import tree_to_list
from html_.element import Element


def get_external_scripts(tree):
    script_urls = []
    node_list = tree_to_list(tree, [])
    for node in node_list:
        if isinstance(node, Element) and node.tag == "script"\
                and "src" in node.attributes:
            script_urls.append(node.attributes["src"])

    return script_urls    

    