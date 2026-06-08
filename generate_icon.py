#!/usr/bin/env python3
"""
Generate a simple icon file for the system tray
"""
from PIL import Image, ImageDraw

def create_icon():
    """Create a simple monitor icon and save as .ico"""
    # Create a 64x64 image
    width = 64
    height = 64
    image = Image.new('RGBA', (width, height), color=(0, 0, 0, 0))  # Transparent background
    dc = ImageDraw.Draw(image)
    
    # Draw a simple monitor-like shape
    # Monitor body
    dc.rectangle([16, 16, 48, 48], fill='#4a90e2', outline='#357ab8', width=2)
    # Monitor stand
    dc.rectangle([28, 48, 36, 56], fill='#4a90e2')
    # Screen glare
    dc.rectangle([20, 20, 28, 28], fill=(255, 255, 255, 128))
    
    # Save as ICO with multiple sizes
    icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64)]
    image.save('resources/icon.ico', format='ICO', sizes=icon_sizes)
    print("Icon saved to resources/icon.ico")

if __name__ == "__main__":
    create_icon()