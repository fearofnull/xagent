"""
JSON Utilities Module

This module provides optimized JSON serialization/deserialization utilities.
Uses orjson for better performance when available, falls back to standard json.
"""

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Try to import orjson for better performance
try:
    import orjson
    HAS_ORJSON = True
    logger.info("Using orjson for optimized JSON serialization")
except ImportError:
    import json
    HAS_ORJSON = False
    logger.info("Using standard json library (install orjson for better performance)")


def dumps(obj: Any, indent: Optional[int] = None) -> str:
    """Serialize object to JSON string
    
    Args:
        obj: Object to serialize
        indent: Indentation level (for pretty printing)
        
    Returns:
        JSON string
    """
    if HAS_ORJSON:
        # orjson options
        option = 0
        if indent:
            option |= orjson.OPT_INDENT_2
        
        # orjson returns bytes, decode to str
        return orjson.dumps(obj, option=option).decode('utf-8')
    else:
        return json.dumps(obj, indent=indent, ensure_ascii=False)


def loads(s: str) -> Any:
    """Deserialize JSON string to object
    
    Args:
        s: JSON string
        
    Returns:
        Deserialized object
    """
    if HAS_ORJSON:
        return orjson.loads(s)
    else:
        return json.loads(s)


def dump(obj: Any, fp, indent: Optional[int] = None) -> None:
    """Serialize object to JSON file
    
    Args:
        obj: Object to serialize
        fp: File-like object
        indent: Indentation level (for pretty printing)
    """
    if HAS_ORJSON:
        # orjson doesn't have dump(), so we use dumps() and write
        option = 0
        if indent:
            option |= orjson.OPT_INDENT_2
        
        json_bytes = orjson.dumps(obj, option=option)
        fp.write(json_bytes.decode('utf-8'))
    else:
        json.dump(obj, fp, indent=indent, ensure_ascii=False)


def load(fp) -> Any:
    """Deserialize JSON file to object
    
    Args:
        fp: File-like object
        
    Returns:
        Deserialized object
    """
    if HAS_ORJSON:
        # Read file content and use loads()
        content = fp.read()
        if isinstance(content, str):
            content = content.encode('utf-8')
        return orjson.loads(content)
    else:
        return json.load(fp)


def jsonify_response(data: Any, status_code: int = 200) -> tuple:
    """Create Flask JSON response with optimized serialization
    
    Args:
        data: Data to serialize
        status_code: HTTP status code
        
    Returns:
        Tuple of (json_string, status_code, headers)
    """
    from flask import Response
    
    if HAS_ORJSON:
        # Use orjson for faster serialization
        json_bytes = orjson.dumps(data)
        return Response(
            json_bytes,
            status=status_code,
            mimetype='application/json'
        )
    else:
        # Use Flask's default jsonify
        from flask import jsonify
        return jsonify(data), status_code
