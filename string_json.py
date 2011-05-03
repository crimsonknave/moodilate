#!/usr/bin/env python2

# Taken from Stackoverflow
# http://stackoverflow.com/questions/4723535/how-to-decode-json-to-str-and-not-unicode-in-python-2-6

# overwrites the json decode of string objects to decode them as python strings instead of unicode objects
# To use simply:
# from string_json import json

import json
from json import decoder, scanner

from json.scanner import make_scanner
from _json import scanstring as c_scanstring

_CONSTANTS = json.decoder._CONSTANTS

py_make_scanner = scanner.py_make_scanner

def str_scanstring(*args, **kwargs):
  result = c_scanstring(*args, **kwargs)
  return str(result[0]), result[1]

json.decoder.scanstring = str_scanstring

class StrJSONDecoder(decoder.JSONDecoder):
  def __init__(self, encoding=None, object_hook=None, parse_float=None,
          parse_int=None, parse_constant=None, strict=True,
          object_pairs_hook=None):
    self.encoding = encoding
    self.object_hook = object_hook
    self.object_pairs_hook = object_pairs_hook
    self.parse_float = parse_float or float
    self.parse_int = parse_int or int
    self.parse_constant = parse_constant or _CONSTANTS.__getitem__
    self.strict = strict
    self.parse_object = decoder.JSONObject
    self.parse_array = decoder.JSONArray
    self.parse_string = str_scanstring
    self.scan_once = py_make_scanner(self)

_default_decoder = StrJSONDecoder(encoding=None, object_hook=None, object_pairs_hook=None)

json._default_decoder = _default_decoder



a = ('asdf', 'asd')
print a
print json.dumps(a)
print json.loads(json.dumps(a))
