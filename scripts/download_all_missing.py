#!/usr/bin/env python3
"""
下载所有缺失的蓝图和基石图标

用法:
  python download_all_missing.py [--output-dir DIR]
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://against-the-storm.fandom.com"
WIKI_IMAGE_BASE = "https://static.wikia.nocookie.net/against-the-storm/images"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# 缺失的蓝图（从之前的分析得出）
MISSING_BLUEPRINTS = [
    ("Beanery", "Beanery"),
    ("Explorer's Lodge", "Explorers_Lodge"),
    ("Farm Field", "Farm_Field"),
    ("Flawless Brewery", "Flawless_Brewery"),
    ("Forester's Hut", "Foresters_Hut"),
    ("Forum", "Forum"),
    ("Hallowed Herb Garden", "Hallowed_Herb_Garden"),
    ("Hallowed Small Farm", "Hallowed_Small_Farm"),
    ("Holy Market", "Holy_Market"),
    ("Holy Temple", "Holy_Temple"),
    ("Market", "Market"),
    ("Small Forager's Camp", "Small_Foragers_Camp"),
    ("Small Herbalist's Camp", "Small_Herbalists_Camp"),
    ("Small Trapper's Camp", "Small_Trappers_Camp"),
    ("Tea Doctor", "Tea_Doctor"),
    ("Teahouse", "Teahouse"),
    ("Tinctuary", "Tinctuary"),
]


def session():
    s = requests.Session()
    s.headers.update({
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    })
    return s


def slug(name: str) -> str:
    """Convert name to filename"""
    s = re.sub(r"[\s']+", "_", name)
    s = re.sub(r"[^a-zA-Z0-9_]", "", s)
    return s.lower().strip("_")


def to_full_image_url(thumb_url: str) -> str:
    """Convert thumbnail URL to full image URL"""
    if not thumb_url or "static.wikia.nocookie.net" not in thumb_url:
        return thumb_url
    return re.sub(r"/scale-to-width-down/\d+\?", "?", thumb_url)


def download_image(sess: requests.Session, url: str, out_path: Path, timeout: int = 15) -> bool:
    """Download image from URL"""
    try:
        r = sess.get(url, timeout=timeout)
        r.raise_for_status()
        out_path.write_bytes(r.content)
        return True
    except Exception as e:
        print(f"    FAIL: {e}", file=sys.stderr)
        return False


def download_blueprint(sess: requests.Session, name: str, wiki_name: str, output_dir: Path) -> bool:
    """Download a single blueprint icon"""
    # Try to get from wiki page
    try:
        r = sess.get(f"{BASE_URL}/wiki/{wiki_name}", timeout=30)
        if r.status_code != 200:
            print(f"  ✗ {name}: Page not found")
            return False
        
        soup = BeautifulSoup(r.text, "html.parser")
        
        # Find infobox image
        infobox = soup.find("aside", class_="portable-infobox")
        if infobox:
            img = infobox.find("img")
            if img:
                url = img.get("data-src") or img.get("src", "")
                if url:
                    if url.startswith("//"):
                        url = "https:" + url
                    url = to_full_image_url(url)
                    
                    filename = f"{slug(name)}.png"
                    out_path = output_dir / filename
                    
                    if download_image(sess, url, out_path):
                        print(f"  ✓ {name}")
                        return True
        
        print(f"  ✗ {name}: Image not found")
        return False
        
    except Exception as e:
        print(f"  ✗ {name}: {e}")
        return False


def download_cornerstones(sess: requests.Session, output_dir: Path) -> int:
    """Download all cornerstone icons"""
    print("\n=== Downloading Cornerstones ===")
    
    try:
        r = sess.get(f"{BASE_URL}/wiki/Cornerstone", timeout=30)
        r.raise_for_status()
    except Exception as e:
        print(f"Failed to fetch Cornerstone page: {e}")
        return 0
    
    soup = BeautifulSoup(r.text, "html.parser")
    tables = soup.find_all("table", class_="article-table")
    
    downloaded = 0
    failed = []
    
    for table in tables:
        rows = table.find_all("tr")
        
        for tr in rows[1:]:  # Skip header
            cells = tr.find_all(["td", "th"])
            if len(cells) < 2:
                continue
            
            name = cells[1].get_text(strip=True)
            if not name:
                continue
            
            img = cells[0].find("img")
            if not img:
                failed.append(name)
                continue
            
            url = img.get("data-src") or img.get("src", "")
            if not url or url.startswith("data:"):
                failed.append(name)
                continue
            
            if url.startswith("//"):
                url = "https:" + url
            url = to_full_image_url(url)
            
            filename = f"{slug(name)}.png"
            out_path = output_dir / filename
            
            if download_image(sess, url, out_path):
                downloaded += 1
                print(f"  ✓ {name}")
            else:
                failed.append(name)
    
    if failed:
        print(f"\n  Failed ({len(failed)}): {', '.join(failed[:5])}...")
    
    return downloaded


def main():
    parser = argparse.ArgumentParser(description="Download missing ATS icons")
    parser.add_argument("--output-dir", default=".", help="Output directory")
    parser.add_argument("--blueprints-only", action="store_true", help="Only download blueprints")
    parser.add_argument("--cornerstones-only", action="store_true", help="Only download cornerstones")
    args = parser.parse_args()
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    blueprints_dir = output_dir / "blueprints"
    cornerstones_dir = output_dir / "cornerstones"
    
    sess = session()
    
    total_downloaded = 0
    
    # Download blueprints
    if not args.cornerstones_only:
        blueprints_dir.mkdir(exist_ok=True)
        print("=== Downloading Missing Blueprints ===")
        
        for name, wiki_name in MISSING_BLUEPRINTS:
            download_blueprint(sess, name, wiki_name, blueprints_dir)
    
    # Download cornerstones
    if not args.blueprints_only:
        cornerstones_dir.mkdir(exist_ok=True)
        total_downloaded += download_cornerstones(sess, cornerstones_dir)
    
    print(f"\n=== Summary ===")
    print(f"Output directory: {output_dir.absolute()}")
    
    if not args.cornerstones_only:
        blueprint_count = len(list(blueprints_dir.glob("*.png")))
        print(f"Blueprints: {blueprint_count}")
    
    if not args.blueprints_only:
        cornerstone_count = len(list(cornerstones_dir.glob("*.png")))
        print(f"Cornerstones: {cornerstone_count}")
    
    print(f"\nNext steps:")
    print(f"  1. Copy blueprints to: backend/app/data/templates/blueprints/")
    print(f"  2. Copy cornerstones to: backend/app/data/templates/cornerstones/")


if __name__ == "__main__":
    main()
