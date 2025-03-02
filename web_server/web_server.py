import socket
import urllib.parse
ENTRIES = [ 'Pavel was here' ]

def handle_connection(conx):
    req = conx.makefile("rwb")
    reqline = req.readline().decode('utf8')
    method, url, version = reqline.split(" ", 2)
    print(method, url)
    assert method in ["GET", "POST"]
    headers = {}
    while True:
        line = req.readline().decode('utf8')
        if line == '\r\n': break
        header, value = line.split(":", 1)
        headers[header.casefold()] = value.strip()
        
    if 'content-length' in headers:
        length = int(headers['content-length'])
        body = req.read(length).decode('utf8')
    else:
        body = None

    status, body = do_request(method, url, headers, body)
    response = "HTTP/1.0 {}\r\n".format(status)
    response += "Content-Length: {}\r\n".format(
        len(body.encode("utf8")))
    response += "\r\n" + body
    conx.send(response.encode('utf8'))
    conx.close()

def do_request(method, url, headers, body):
    if method == "GET" and url == "/":
        return "200 OK", show_comments()
    elif method == "GET" and url == "/test.js":
        return "200 OK", open("test.js").read()
    elif method == "GET" and url == "/bubble.html":
        return "200 OK", open("bubble.html").read()
    elif method == "GET" and url == "/bubble.js":
        return "200 OK", open("bubble.js").read()
    elif method == "GET" and url == "/comment.css":
        return "200 OK", open("comment.css").read()
    elif method == "POST" and url == "/add":
        params = form_decode(body)
        return "200 OK", add_entry(params)
    else:
        return "404 Not Found", not_found(url, method)


    

def form_decode(body):
    params = {}
    for field in body.split("&"):
        name, value = field.split("=", 1)
        name = urllib.parse.unquote_plus(name)
        value = urllib.parse.unquote_plus(value)
        params[name] = value
    return params

def show_comments():
    out = "<!doctype html>"
    out +='<p>First line</p>'
    for entry in ENTRIES:
        out += "<p>" + entry + "</p>"
    
    
    out += "<form action=add method=post>"
    out +=   "<p><input name=guest></p>"
    out +=   "<p><input name=check type=checkbox></p>"
    out +=   "<p><button>Sign the book!</button></p>"
    out += "</form>"
    out += "<strong></strong>"
    out +='<p>last line</p>'
    out += "<div id=tal></div>"
    out += "<script src='test.js'></script>"
    out += "<link rel='stylesheet' href='comment.css'>"
    

    return out
    

def add_entry(params):
    if 'guest' in params:
        ENTRIES.append(params['guest'])
    if 'check' in params:
        ENTRIES.append(params['check'])
    return show_comments()

def not_found(url, method):
    out = "<!doctype html>"
    out += "<h1>{} {} not found!</h1>".format(method, url)
    return out

s = socket.socket(
    family=socket.AF_INET,
    type=socket.SOCK_STREAM,
    proto=socket.IPPROTO_TCP)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('', 8000))
s.listen()

while True:
    conx, addr = s.accept()
    handle_connection(conx)

