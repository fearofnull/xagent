"""
Compression Module

This module provides response compression middleware for Flask.
Supports gzip compression for API responses to reduce bandwidth usage.
"""

import gzip
import logging
from io import BytesIO
from flask import Flask, request, Response
from functools import wraps

logger = logging.getLogger(__name__)


def configure_compression(app: Flask, min_size: int = 500, compression_level: int = 6):
    """Configure response compression for Flask app
    
    Args:
        app: Flask application instance
        min_size: Minimum response size in bytes to compress (default: 500)
        compression_level: Gzip compression level 1-9 (default: 6)
    """
    
    @app.after_request
    def compress_response(response: Response) -> Response:
        """Compress response if appropriate
        
        Args:
            response: Flask response object
            
        Returns:
            Compressed or original response
        """
        # Check if client accepts gzip encoding
        accept_encoding = request.headers.get('Accept-Encoding', '')
        if 'gzip' not in accept_encoding.lower():
            return response
        
        # Don't compress if already compressed
        if response.headers.get('Content-Encoding') == 'gzip':
            return response
        
        # Don't compress if response is too small
        if response.content_length is not None and response.content_length < min_size:
            return response
        
        # Don't compress non-text content types (images, videos, etc.)
        content_type = response.headers.get('Content-Type', '')
        compressible_types = [
            'text/',
            'application/json',
            'application/javascript',
            'application/xml',
            'application/x-javascript'
        ]
        
        if not any(ct in content_type for ct in compressible_types):
            return response
        
        # Don't compress streaming responses
        if response.is_streamed:
            return response
        
        # Compress response data
        try:
            # Get response data
            data = response.get_data()
            
            # Skip if data is empty
            if not data:
                return response
            
            # Compress data
            gzip_buffer = BytesIO()
            with gzip.GzipFile(
                mode='wb',
                compresslevel=compression_level,
                fileobj=gzip_buffer
            ) as gzip_file:
                gzip_file.write(data)
            
            compressed_data = gzip_buffer.getvalue()
            
            # Only use compressed version if it's actually smaller
            if len(compressed_data) < len(data):
                response.set_data(compressed_data)
                response.headers['Content-Encoding'] = 'gzip'
                response.headers['Content-Length'] = len(compressed_data)
                
                # Calculate compression ratio
                ratio = (1 - len(compressed_data) / len(data)) * 100
                logger.debug(
                    f"Compressed response: {len(data)} -> {len(compressed_data)} bytes "
                    f"({ratio:.1f}% reduction)"
                )
            
            # Add Vary header to indicate response varies by encoding
            response.headers['Vary'] = 'Accept-Encoding'
            
        except Exception as e:
            logger.warning(f"Failed to compress response: {e}")
            # Return original response on error
        
        return response
    
    logger.info(
        f"Response compression configured: min_size={min_size}B, "
        f"level={compression_level}"
    )


def compress_json(data: dict, compression_level: int = 6) -> bytes:
    """Compress JSON data with gzip
    
    Args:
        data: Dictionary to compress
        compression_level: Gzip compression level 1-9
        
    Returns:
        Compressed bytes
    """
    import json
    
    # Serialize to JSON
    json_str = json.dumps(data, ensure_ascii=False)
    json_bytes = json_str.encode('utf-8')
    
    # Compress
    gzip_buffer = BytesIO()
    with gzip.GzipFile(
        mode='wb',
        compresslevel=compression_level,
        fileobj=gzip_buffer
    ) as gzip_file:
        gzip_file.write(json_bytes)
    
    return gzip_buffer.getvalue()


def decompress_json(compressed_data: bytes) -> dict:
    """Decompress gzipped JSON data
    
    Args:
        compressed_data: Compressed bytes
        
    Returns:
        Deserialized dictionary
    """
    import json
    
    # Decompress
    gzip_buffer = BytesIO(compressed_data)
    with gzip.GzipFile(mode='rb', fileobj=gzip_buffer) as gzip_file:
        json_bytes = gzip_file.read()
    
    # Deserialize
    json_str = json_bytes.decode('utf-8')
    return json.loads(json_str)
