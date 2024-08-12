import os
import re
from datetime import datetime, timedelta
from pathlib import Path


class CustomError(Exception):
    pass

DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

def generate_host_key(host, port):
        return host + ':' + str(port)

def split_pathname(pathname):
    directory_path, file_name = os.path.split(pathname)
    return directory_path, file_name
        
def generate_expiration_date(seconds):
    now = datetime.now()
    delta = timedelta(seconds=seconds)
    future_time = now + delta
    future_time_str = future_time.strftime(DATE_FORMAT)

    return future_time_str

def is_expired(time_str):
     valid_until = datetime.strptime(time_str, DATE_FORMAT)
     now = datetime.now()

     return valid_until < now

def read_utf8_line(line_bytes):
    text_and_newline = line_bytes.decode('utf-8')
    text = text_and_newline[:-2]

    return text

def remove_delimiter(content):
    delimiter_length = len('\r\n')
    return content[:-delimiter_length]

def get_emoji_png_path(code_point_hex):
    emoji_dir = "./openmoji-618x618-color"
    filename = f"{code_point_hex}.png"
    path = Path(os.path.join(emoji_dir, filename))

    return path

