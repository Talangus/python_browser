import socket
import urllib.parse
import random
import html
from datetime import datetime, timedelta, timezone



ENTRIES = [ ('Pavel was here', "Pavel") ]
SESSIONS = {}
LOGINS = {
    "crashoverride": "0cool",
    "cerealkiller": "emmanuel",
    "tal":"1234",
    "":""
}


def handle_connection(conx):
    req = conx.makefile("rwb")
    reqline = req.readline().decode('utf8')
    method, url, version = reqline.split(" ", 2)
    print(method, url)
    assert method in ["GET", "POST"]
    headers = {}
    token = None
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

    if "cookie" in headers:
        token = headers["cookie"][len("token="):]
        
        if token is not None and token not in SESSIONS:
            token = None
        elif token in SESSIONS and "expires" in SESSIONS[token]:
            expires = SESSIONS[token]["expires"]
            if expires < datetime.now():
                del SESSIONS[token]
                token = None

    if token is None:
        token = str(random.random())[2:]
        expires = get_cookie_experation(timedelta(minutes=5))    

    if "referer" in headers:
        referer = headers["referer"]
        print(f"Referer is {referer}")

    session = SESSIONS.setdefault(token, {'expires': expires})
    status, body = do_request(session, method, url, headers, body)
    response = "HTTP/1.0 {}\r\n".format(status)
    response += "Content-Length: {}\r\n".format(
        len(body.encode("utf8")))
    if 'cookie' not in headers:
        expires_str = gen_expires_str(session)
        template = "Set-Cookie: token={}; SameSite=Lax; expires={}\r\n"
        response += template.format(token, expires_str)
    
    csp = "default-src http://localhost:8000 https://run.mocky.io"
    response += "Content-Security-Policy: {}\r\n".format(csp)
    response += "Access-Control-Allow-Origin: *\r\n"
    response += "Referrer-Policy: same-origin\r\n"

    response += "\r\n" + body
    conx.send(response.encode('utf8'))
    print("Cookie is: " + token)
    conx.close()

def do_request(session, method, url, headers, body):
    if method == "GET" and url == "/":
        return "200 OK", show_comments(session)
    elif method == "GET" and url == "/test.js":
        return "200 OK", open("test.js").read()
    elif method == "GET" and url == "/bubble.html":
        return "200 OK", open("bubble.html").read()
    elif method == "GET" and url == "/bubble.js":
        return "200 OK", open("bubble.js").read()
    elif method == "GET" and url == "/login":
        return "200 OK", login_form(session)
    elif method == "GET" and url == "/comment.css":
        return "200 OK", open("comment.css").read()
    elif method == "POST" and url == "/add":
        params = form_decode(body)
        return "200 OK", add_entry(session, params)
    elif method == "POST" and url == "/":
        params = form_decode(body)
        return do_login(session, params)
    else:
        return "404 Not Found", not_found(url, method)

def login_form(session):
    nonce = str(random.random())[2:]
    session["nonce"] = nonce
    body = "<!doctype html>"
    body += "<form action=/ method=post>"
    body += "<p>Username: <input name=username></p>"
    body += "<p>Password: <input name=password type=password></p>"
    body +=   "<input name=nonce type=hidden value=" + nonce + ">"
    body += "<p><button>Log in</button></p>"
    body += "</form>"
    body += "<strong></strong>"
    return body 
    
def do_login(session, params):
    if "nonce" not in session or "nonce" not in params: return
    if session["nonce"] != params["nonce"]: return
    username = params.get("username")
    password = params.get("password")
    if username in LOGINS and LOGINS[username] == password:
        session["user"] = username
        return "200 OK", show_comments(session)
    else:
        out = "<!doctype html>"
        out += "<h1>Invalid password for {}</h1>".format(username)
        return "401 Unauthorized", out


def form_decode(body):
    params = {}
    for field in body.split("&"):
        name, value = field.split("=", 1)
        name = urllib.parse.unquote_plus(name)
        value = urllib.parse.unquote_plus(value)
        params[name] = value
    return params

def show_comments(session):
    out = "<!doctype html>"
    out +='<p>First line</p>'
    for entry, who in ENTRIES:
        out += "<p>" + html.escape(entry) + "\n"
        out += "<i>by " + html.escape(who) + "</i></p>"
    
    
    if "user" in session:
        nonce = str(random.random())[2:]
        session["nonce"] = nonce
        out += "<h1>Hello, " + session["user"] + "</h1>"
        out += "<form action=add method=post>"
        out +=   "<p><input name=guest></p>"
        out +=   "<input name=nonce type=hidden value=" + nonce + ">"
        out +=   "<p><button>Sign the book!</button></p>"
        out += "</form>"
        out += "<script src='test.js'></script>"
        out += "<link rel='stylesheet' href='comment.css'>"
        out += "<strong></strong>"
    else:
        out += "<a href=/login>Sign in to write in the guest book</a>"

    out += "<script src=https://example.com/evil.js></script>" #csp test
    return out
    

def add_entry(session, params):
    if "user" not in session: return "<a href=/login>Sign in to write in the guest book</a>"
    if "nonce" not in session or "nonce" not in params: return
    if session["nonce"] != params["nonce"]: return
    if 'guest' in params:
        ENTRIES.append((params['guest'], session["user"]))
    return show_comments(session)

def not_found(url, method):
    out = "<!doctype html>"
    out += "<h1>{} {} not found!</h1>".format(method, url)
    return out

def gen_expires_str(session):
    return session['expires'].strftime("%a, %d-%b-%Y %H:%M:%S GMT")

def get_cookie_experation(delta = timedelta(minutes=1)):
    current_time = datetime.now()
    time_plus_delta = current_time + delta

    return time_plus_delta



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

