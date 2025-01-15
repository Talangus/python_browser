import os
import json
import time
from pathlib import Path
from urllib.parse import urlparse
from util.utils import *

CACHE_DIR = "cache"
CACHE_DISABLED = True

class CacheId:
    def __init__(self, url):
        self.host_key = generate_host_key(url.get_host(), url.get_port())

        path, file_name = split_pathname(url.get_path())
        if file_name == '':
            file_name = 'index.html@'
        self.file_name = file_name
        path = path[1:]
        self.path = path

        self.cache_path = os.path.join(CACHE_DIR, self.host_key, path)
        self.file_path = os.path.join(self.cache_path, self.file_name)

class Cache:
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(Cache, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        self.db_file_path = os.path.join(CACHE_DIR, 'cache_db.json')

        if not os.path.exists(CACHE_DIR):
            os.makedirs(CACHE_DIR)
            
        if not os.path.exists(self.db_file_path):
            with open(self.db_file_path, 'w') as f:
                json.dump({}, f)

        self.load_db()

    def load_db(self):
        with open(self.db_file_path, 'r') as f:
            self.db = json.load(f)

    def save_db(self):
        with open(self.db_file_path, 'w') as f:
            json.dump(self.db, f, indent=4)

    def save_to_cache(self, url, content):
        id = Cache.get_cache_id(url)
                
        os.makedirs(id.cache_path, exist_ok=True)
        
        with open(id.file_path, 'w') as f:
            f.write(content)
        
        if id.host_key not in self.db:
            self.db[id.host_key] = {}
        
        self.db[id.host_key][id.file_path] = {
            'valid_until': url.get_cache_max_age()
        }
        
        self.save_db()
    
    def load_from_cache(self, url):
        id = Cache.get_cache_id(url)

        with open(id.file_path, 'r') as file:
            content = file.read()

        return content
    
    def in_cache(self, url):
        if CACHE_DISABLED:
            return False
        
        id = Cache.get_cache_id(url)
        
        if id.host_key not in self.db:
            return False
        if id.file_path not in self.db[id.host_key]:
            return False
        
        file_entry = self.db[id.host_key][id.file_path]
        valid_until = file_entry['valid_until']
        if is_expired(valid_until):
            self.clean_cache_entry(id.host_key, id.file_path)
            return False
        
        return True

    def clean_cache_entry(self, host_key, file_path):
        del self.db[host_key][file_path]
        self.save_db()
        os.remove(file_path)

    def clear_expired_entries(self):
        for host_key in list(self.db.keys()):
            for file_path in list(self.db[host_key].keys()):
                file_entry = self.db[host_key][file_path]
                valid_until = file_entry['valid_until']

                if is_expired(valid_until):
                    self.clean_cache_entry(host_key, file_path)

    @staticmethod
    def get_cache_id(url):
        return CacheId(url)

cache = Cache()