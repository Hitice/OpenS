# app/utils.py
from flask import jsonify
from html import escape
import re

def sanitize(text):
    if not text:
        return ""
    text = re.sub(r'<[^>]*>', '', str(text))  # remove tags HTML
    return escape(text.strip())

def sanitize_dict(d):
    return {k: sanitize(v) for k, v in d.items()}