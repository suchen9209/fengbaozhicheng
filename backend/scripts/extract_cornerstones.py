#!/usr/bin/env python3
"""
Cornerstone template extraction tool

Extracts cornerstone icons from screenshots and saves them as templates.
Usage: python extract_cornerstones.py <screenshot_path> <cornerstone_name>
"""

import cv2
import numpy as np
import sys
import os
from pathlib import Path
import json


def get_all_cornerstones():
    """Load all cornerstones from data file."""
    data_path = Path(__file__).parent.parent / "app/data/ats_wiki/cornerstones.json"
    with open(data_path) as f:
        return json.load(f)


def extract_cornerstone_from_screenshot(image_path: str, cornerstone_name: str, output_dir: str = "app/data/templates/cornerstones"):
    """
    Extract a cornerstone icon from a screenshot.
    
    The user should provide a screenshot showing the cornerstone selection UI,
    and specify which cornerstone to extract.
    """
    img = cv2.imread(image_path)
    if img is None:
        print(f"Error: Cannot load image from {image_path}")
        return False
    
    height, width = img.shape[:2]
    print(f"Image loaded: {width}x{height}")
    
    # Cornerstones typically appear in the center of the screen
    # in a card format similar to blueprints
    # Try to extract from the center area
    center_x, center_y = width // 2, height // 2
    
    # Cornerstone icons are usually in an octagon frame, similar to blueprints
    icon_size = 150
    x1 = center_x - icon_size//2
    y1 = center_y - icon_size//2
    x2 = center_x + icon_size//2
    y2 = center_y + icon_size//2
    
    icon = img[y1:y2, x1:x2]
    
    # Resize to standard 128x128
    resized = cv2.resize(icon, (128, 128), interpolation=cv2.INTER_LANCZOS4)
    
    # Save
    slug = cornerstone_name.lower().replace(' ', '_').replace("'", '').replace('-', '_')
    output_path = os.path.join(output_dir, f"{slug}.png")
    
    os.makedirs(output_dir, exist_ok=True)
    cv2.imwrite(output_path, resized)
    
    print(f"Extracted '{cornerstone_name}' -> {output_path}")
    print(f"Icon size: {resized.shape}")
    
    return True


def list_missing_templates():
    """List cornerstones that don't have templates yet."""
    template_dir = Path("app/data/templates/cornerstones")
    existing = set(f.stem for f in template_dir.glob("*.png"))
    
    cornerstones = get_all_cornerstones()
    missing = []
    
    for cs in cornerstones:
        slug = cs['name'].lower().replace(' ', '_').replace("'", '').replace('-', '_')
        if slug not in existing:
            missing.append(cs['name'])
    
    print(f"\n=== Cornerstone Template Collection Progress ===")
    print(f"Existing: {len(existing)} / {len(cornerstones)}")
    print(f"Missing: {len(missing)}")
    
    if missing:
        print(f"\nMissing templates (first 30):")
        for name in missing[:30]:
            print(f"  - {name}")
        if len(missing) > 30:
            print(f"  ... and {len(missing) - 30} more")
    
    return missing


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python extract_cornerstones.py --list              # Show missing templates")
        print("  python extract_cornerstones.py <image> <name>      # Extract specific cornerstone")
        sys.exit(1)
    
    if sys.argv[1] == "--list":
        list_missing_templates()
    else:
        if len(sys.argv) < 3:
            print("Error: Please provide cornerstone name")
            sys.exit(1)
        
        image_path = sys.argv[1]
        cornerstone_name = sys.argv[2]
        extract_cornerstone_from_screenshot(image_path, cornerstone_name)
