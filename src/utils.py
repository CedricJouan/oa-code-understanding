import re

def format_name(filename):
    transformed = re.sub(r'[^a-zA-Z0-9_-]', '_', filename)    
    transformed = transformed[:64]

    return transformed