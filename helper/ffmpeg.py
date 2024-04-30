import time
import os
import asyncio
from PIL import Image
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser


async def fix_thumb(thumb):
    # Default width and height to zero
    width = 0
    height = 0
    if thumb is None:
        return width, height, None
    
    try:
        # Create a parser for the given thumbnail
        parser = createParser(thumb)
        if parser is None:
            raise Exception("Failed to create parser for the thumbnail.")
        
        # Extract metadata
        metadata = extractMetadata(parser)
        if not metadata:
            raise Exception("Failed to extract metadata from the thumbnail.")
        
        if metadata.has("width"):
            width = metadata.get("width")
        if metadata.has("height"):
            height = metadata.get("height")
        
        # Open the image and convert to RGB format
        with Image.open(thumb) as img:
            img = img.convert("RGB")
            
            # Resize image to original dimensions
            resized_img = img.resize((width, height))
            
            # Save the resized image in JPEG format
            resized_img.save(thumb, "JPEG")
        
    except Exception as e:
        print(f"Error fixing thumbnail: {e}")
        thumb = None  # Return None in case of failure
    
    return width, height, thumb
    
