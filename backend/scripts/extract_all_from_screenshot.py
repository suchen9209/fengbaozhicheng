#!/usr/bin/env python3
"""
Interactive Screenshot Extractor for Against the Storm

Extracts Blueprints, Cornerstones, and Species icons from game screenshots.
Usage: python extract_all_from_screenshot.py <screenshot_path>
"""

import cv2
import numpy as np
import sys
import os
from pathlib import Path


def save_template(image, name, category):
    """Save extracted icon as template"""
    output_dir = Path(f"app/data/templates/{category}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Resize to standard 128x128
    resized = cv2.resize(image, (128, 128), interpolation=cv2.INTER_LANCZOS4)
    
    slug = name.lower().replace(' ', '_').replace("'", '').replace('-', '_')
    output_path = output_dir / f"{slug}.png"
    
    cv2.imwrite(str(output_path), resized)
    print(f"  ✓ Saved: {output_path}")
    return output_path


def extract_from_blueprint_ui(img):
    """Extract blueprint icons from blueprint selection UI"""
    height, width = img.shape[:2]
    
    # Blueprint UI typically has 4 cards in center-bottom
    # Cards are at roughly: x: 560-2000, y: 420-1020 for 2560x1440
    
    card_width = 360
    start_x = 560
    start_y = 420
    
    # Relative positions of icons within cards (from previous extraction)
    icon_rel_x1 = 150
    icon_rel_y1 = 180
    icon_rel_x2 = 230
    icon_rel_y2 = 250
    
    extracted = []
    
    for i in range(4):
        card_x = start_x + i * card_width
        x1 = card_x + icon_rel_x1
        y1 = start_y + icon_rel_y1
        x2 = card_x + icon_rel_x2
        y2 = start_y + icon_rel_y2
        
        icon = img[y1:y2, x1:x2]
        extracted.append(icon)
    
    return extracted


def extract_from_cornerstone_ui(img):
    """Extract cornerstone icons from cornerstone selection UI"""
    height, width = img.shape[:2]
    
    # Cornerstone UI is similar to blueprint UI
    # Usually 3 cornerstones to choose from
    # Try to detect based on UI layout
    
    # Common positions for cornerstone cards
    # Center of screen, slightly lower
    center_y = height // 2
    
    # Extract center region
    region = img[int(height*0.3):int(height*0.7), int(width*0.2):int(width*0.8)]
    
    # TODO: Detect specific card positions
    # For now, return the center region for manual inspection
    return [region]


def extract_species_icons(img):
    """Extract species icons from left sidebar"""
    height, width = img.shape[:2]
    
    # Species icons are on the left side
    # x: 10-130, y: 100-500
    species_region = img[100:500, 10:130]
    
    # Three species stacked vertically
    # Each ~80 pixels tall
    icons = []
    for i, center_y in enumerate([40, 160, 280]):
        y1 = center_y - 30
        y2 = center_y + 30
        x1 = 30
        x2 = 90
        
        icon = species_region[y1:y2, x1:x2]
        icons.append(icon)
    
    return icons


def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_all_from_screenshot.py <screenshot_path>")
        print("")
        print("This tool extracts game icons from Against the Storm screenshots.")
        print("It can detect:")
        print("  - Blueprint selection UI (4 blueprints)")
        print("  - Cornerstone selection UI (3 cornerstones)")
        print("  - Species icons (3 species)")
        sys.exit(1)
    
    image_path = sys.argv[1]
    img = cv2.imread(image_path)
    
    if img is None:
        print(f"Error: Cannot load image from {image_path}")
        sys.exit(1)
    
    height, width = img.shape[:2]
    print(f"Loaded image: {width}x{height}")
    print("")
    
    # Detect UI type based on visual features
    # For now, ask user what type of screenshot this is
    
    print("What type of screenshot is this?")
    print("1. Blueprint selection (声望奖励 - 4 blueprints)")
    print("2. Cornerstone selection (基石选择 - 3 cornerstones)")
    print("3. Main game (species sidebar visible)")
    print("4. Extract all possible")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        print("\nExtracting blueprints...")
        icons = extract_from_blueprint_ui(img)
        
        print(f"\nFound {len(icons)} blueprint icons.")
        print("Enter names for each blueprint (in order left-to-right):")
        
        names = [
            input("  Blueprint 1 (leftmost): ").strip(),
            input("  Blueprint 2: ").strip(),
            input("  Blueprint 3: ").strip(),
            input("  Blueprint 4 (rightmost): ").strip(),
        ]
        
        for icon, name in zip(icons, names):
            if name:
                save_template(icon, name, "blueprints")
    
    elif choice == "2":
        print("\nExtracting cornerstones...")
        icons = extract_from_cornerstone_ui(img)
        
        print(f"\nFound {len(icons)} region(s) with possible cornerstones.")
        print("Note: Cornerstone extraction requires manual specification of card positions.")
        print("This feature is not fully automated yet.")
    
    elif choice == "3":
        print("\nExtracting species...")
        icons = extract_species_icons(img)
        
        print(f"\nFound {len(icons)} species icons.")
        print("Enter names for each species (top to bottom):")
        
        names = [
            input("  Species 1 (top): ").strip(),
            input("  Species 2 (middle): ").strip(),
            input("  Species 3 (bottom): ").strip(),
        ]
        
        for icon, name in zip(icons, names):
            if name:
                save_template(icon, name, "species")
    
    elif choice == "4":
        print("\nAttempting to extract all...")
        # Try all extractors
        pass
    
    print("\nDone!")


if __name__ == "__main__":
    main()
