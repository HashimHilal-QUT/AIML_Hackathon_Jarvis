from typing import Union
from werkzeug.datastructures import FileStorage

def validate_json_file(file: FileStorage) -> Union[bool, str]:
    """Validate uploaded JSON file"""
    if not file or file.filename == '':
        return "No file provided"
    
    if not file.filename.endswith('.json'):
        return "File must be JSON format"
        
    return True
