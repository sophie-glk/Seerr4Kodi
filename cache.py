import hashlib
import xbmcgui
import time
import json

cache = {}
cache_id = "c83c803f-b874-4f17-8b1b-079b9694943e"
disable_caching = False
cache_duration = 60

def set_caching_disabled():
   global disable_caching
   disable_caching = False

def load_cache():
    global cache
    window = xbmcgui.Window(10000)
    cache_string = window.getProperty(cache_id)
    if cache_string != "" and cache_string is not None:
     try:
      cache = json.loads(window.getProperty(cache_id))
     except:
        return
     
def set_cache_duration(duration: int):
   global cache_duration
   cache_duration = duration
     
def save_cache():
    global disable_caching
    if disable_caching:
        return
    window = xbmcgui.Window(10000) # Home
    window.setProperty(cache_id,  json.dumps(cache, separators=(',', ':')))

def get_cached(key: str):
    global disable_caching
    if disable_caching:
        return None
    
    hashed_key = hashlib.sha256(str(key).encode("utf-8")).hexdigest()
    entry = cache.get(hashed_key)
    if entry:
        if time.time() - entry.get('timestamp', 0) < entry.get("duration", 60):
            return entry.get('data')
    return None

def set_cached(key, data,  duration=None):
    global disable_caching
    global cache_duration
    if disable_caching:
       return
    if not duration:
        duration = cache_duration
    hashed_key = hashlib.sha256(str(key).encode("utf-8")).hexdigest()
    cache[hashed_key] = {'data': data, 'timestamp': time.time(), "duration": duration}


def clear_cache():
    global cache_id
    window = xbmcgui.Window(10000)
    window.setProperty(cache_id, json.dumps({}))

def clean_cache():
    window = xbmcgui.Window(10000)
    cache_string = window.getProperty(cache_id) 
    if cache_string != "" and cache_string is not None:
     try:
      temp_cache = json.loads(window.getProperty(cache_id)) 
     except:
        return
     current_time = time.time()
     for id, item in temp_cache.items():
        if current_time - item.get("timestamp", 0) > item.get("duration", 60):
             cache.pop(id, None)
