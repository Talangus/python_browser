import base64
import gzip

from .socket_manager import socket_manager
from .cache import cache
from util.utils import *



class URL:
    DEFAULT_FILE_PATH="file:///Users/li016390/Desktop/challenges/browser/pages/test.html"
    SUPPORTED_SCHEME_PORTS={
        "http": 80,
        "https": 443, 
        "file": None, 
        "data":None,
        "view-source": None
        }
    DATA_URL_TYPES=["text"]
    
    def __init__(self, url):
        try:
            self.scheme, rest = URL.parse_scheme(url)

            if self.scheme == 'view-source':
                self.scheme, rest = URL.parse_scheme(rest)
                self.is_view_source = True
            else: self.is_view_source = False

            if self.scheme == 'data':
                self.process_data_scheme(rest)
                return
            
            self.host, rest = URL.parse_host(rest)

            self.host, self.port = URL.parse_port(self.host, self.scheme)
            self.is_malformed_url = False
        except:
            self.is_malformed_url = True
            self.is_view_source = False
            return 

        self.path = "/" + rest
        self.headers = {"Host": self.host,
                        "Connection": "keep-alive",
                        "User-Agent":"Tal_browser",
                        
                        "Accept": "*/*"}
        
        self.redirect_count = 0
        self.cache_max_age = None
    
    def __str__(self):
        port_part = ":" + str(self.port)
        if self.scheme == "https" and self.port == 443:
            port_part = ""
        if self.scheme == "http" and self.port == 80:
            port_part = ""
        return self.scheme + "://" + self.host + port_part + self.path

    #rfc2397#section-2
    def process_data_scheme(self, rest):
        self.data_is_base64 = False 
        type_and_encoding , self.data = rest.split(',', 1)

        if ';' in type_and_encoding:
            media_type, encoding = type_and_encoding.split(';')
            assert encoding == 'base64'
            self.data_is_base64 = True
        else:
            media_type = type_and_encoding

        if media_type == '':
            self.data_type = "text"
            self.data_subtype = "plain"
        else:
            self.data_type, self.data_subtype = media_type.split("/", 1)

        assert self.data_type in URL.DATA_URL_TYPES
    
    def request(self):
        if self.is_malformed_url:
            return " "

        if not self.need_socket():
            content = self.local_request_content()
            return content
        
        if cache.in_cache(self):
            content = cache.load_from_cache(self)
            return content
        
        s = self.get_socket()
                
        request = "GET {} HTTP/1.1\r\n".format(self.path)
        request += self.get_req_headers_string()
        request += "\r\n"

        s.send(request.encode("utf8"))
        response = s.makefile("rb")
                
        version, status, explanation = self.parse_status_line(response)
        response_headers = self.parse_response_headers(response)

        if self.is_chunked(response_headers):
            content = self.read_chunked_response(response)
        else:
            content_length = int(response_headers["content-length"])
            content = response.read(content_length)

        if self.is_gzip_encoded(response_headers):
            content = gzip.decompress(content)
            
        content = str(content, 'utf-8')

        if self.is_redirect(status):
            location = response_headers['location']
            return self.get_redirect_content(location)

        if self.should_cache_response(response_headers):
            cache.save_to_cache(self, content)
        
        return content

    def need_socket(self):
        return self.scheme in ["http", "https"]

    def local_request_content(self):
        if self.scheme == "file":
            with open(self.path, 'r') as file:
                content = file.read()
                return content
        
        if self.scheme == 'data':
            if self.data_is_base64:
                decoded_bytes = base64.b64decode(self.data)
                self.data = decoded_bytes.decode('utf-8')

        return self.data

    def get_socket(self):
        socket = socket_manager.get_socket(self.host, self.port)
        if self.scheme == "https" and not socket_manager.is_HTTPS_socket(self.host, self.port):
            socket = socket_manager.upgrade_to_https(self.host, self.port)

        return socket
    
    def get_req_headers_string(self):
        headers = ""
        for key,value in self.headers.items():
            headers += "{}: {}\r\n".format(key, value)
        return headers
    
    def parse_response_headers(self, response):
        response_headers = {}
        while True:
            line_bytes = response.readline()
            if line_bytes == b"\r\n": break
            line = read_utf8_line(line_bytes)
            header, value = line.split(":", 1)
            response_headers[header.casefold()] = value.strip()

        return response_headers
   
    def get_redirect_content(self, location):
        full_address = self.add_host_if_needed(location)

        new_url = URL(full_address)
        new_url.increase_redirect_count(self.redirect_count)

        return new_url.request()

    def add_host_if_needed(self,url):
        if self.is_relative_url(url):
            return self.scheme + "://" +  self.host + ":" + str(self.port) + url
        else:
            return url

    def increase_redirect_count(self, prev_count):
        prev_count +=1
        self.redirect_count = prev_count
        if self.redirect_count > 3:
            raise ValueError("Too many redirects")

    def should_cache_response(self, response_headers):
        if 'cache-control' not in response_headers:
            return False
        
        cache_control_value = response_headers['cache-control']
        if cache_control_value == 'no-store':
            return False
        
        self.cache_max_age =  self.parse_cache_max_age(cache_control_value)
        return self.cache_max_age != None

    def parse_cache_max_age(self, cache_control_value):
        directives = cache_control_value.split(',')
        for directive in directives:
            directive = directive.strip()
            if directive.startswith('max-age'):
                try:
                    max_age_value = int(directive.split('=')[1])
                    return generate_expiration_date(max_age_value)
                except (IndexError, ValueError):
                    return None
        return None

    def get_host(self):
        return self.host
    
    def get_port(self):
        return self.port
    
    def get_path(self):
        return self.path
    
    def get_cache_max_age(self):
        return self.cache_max_age
    
    def get_redirect_count(self):
        return self.redirect_count
    
    def resolve(self, url):
        if "://" in url: return URL(url)
        if not url.startswith("/"):
            dir, _ = self.path.rsplit("/", 1)
            while url.startswith("../"):
                _, url = url.split("/", 1)
                if "/" in dir:
                    dir, _ = dir.rsplit("/", 1)
            url = dir + "/" + url
        if url.startswith("//"):
            return URL(self.scheme + ":" + url)
        else:
            return URL(self.scheme + "://" + self.host + \
                       ":" + str(self.port) + url)
        
    @staticmethod
    def is_redirect(status):
        return status.startswith('3')
    
    @staticmethod
    def is_relative_url(url):
        return url.startswith('/')

    @staticmethod
    def parse_scheme(url):
        scheme, rest = url.split(":", 1)
        assert scheme in URL.SUPPORTED_SCHEME_PORTS

        return scheme, rest
    
    @staticmethod
    def parse_host(rest):
        rest = rest[2:] #remove protocol's //
        if "/" in rest:
            host, rest = rest.split("/", 1)
        else:
            host = rest
            rest = ""

        return host, rest
    
    @staticmethod
    def parse_port(host, scheme):
        if ":" in host:
            host, port = host.split(":", 1)
            port = int(port)
        else:
            port = URL.SUPPORTED_SCHEME_PORTS[scheme]

        return host, port
    
    @staticmethod
    def parse_status_line(response):
        line_bytes = response.readline()
        statusline = read_utf8_line(line_bytes)
        version, status, explanation = statusline.split(" ", 2)
        return version, status, explanation

    @staticmethod
    def is_gzip_encoded(response_headers):
        if "content-encoding" not in response_headers:
            return False
        return response_headers["content-encoding"] == "gzip"
    
    @staticmethod
    def is_chunked(response_headers):
        if "transfer-encoding" not in response_headers:
            return False
        return response_headers["transfer-encoding"] == "chunked"
    
    @staticmethod
    def read_chunked_response(response):
        content = b''
        while True:
            line_bytes = response.readline()
            line = read_utf8_line(line_bytes)
            chunk_length = int(line)
            if chunk_length == 0:
                response.readline()
                break
            content_line = response.read(chunk_length)
            content += remove_delimiter(content_line)
        return content

    @staticmethod
    def read_until_delimiter(response, delimiter):
        buffer = b''
        while True:
            data = response.read(1)
            if not data:
                break
            buffer += data
            if buffer.endswith(delimiter):
                break
        return buffer[:-len(delimiter)]

