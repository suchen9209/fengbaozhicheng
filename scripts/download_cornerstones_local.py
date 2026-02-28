#!/usr/bin/env python3
"""
本地抓取基石图标（需要在本地运行，因为服务器被Cloudflare屏蔽）

用法：
  1. 将本脚本复制到你的电脑
  2. 安装依赖: pip install requests beautifulsoup4
  3. 运行: python download_cornerstones_local.py
  4. 将下载的图标复制到 backend/app/data/templates/cornerstones/
"""

import re
import json
import requests
from pathlib import Path
from bs4 import BeautifulSoup

BASE_URL = "https://against-the-storm.fandom.com"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

def session():
    s = requests.Session()
    s.headers.update({
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    })
    return s

def slug(name: str) -> str:
    """Convert name to filename"""
    return re.sub(r"[^\w]", "_", name).lower().strip("_")

def download_cornerstones():
    """Download all cornerstone icons from Fandom wiki"""
    sess = session()
    output_dir = Path("cornerstones")
    output_dir.mkdir(exist_ok=True)
    
    print("Fetching Cornerstone page...")
    r = sess.get(f"{BASE_URL}/wiki/Cornerstone", timeout=30)
    r.raise_for_status()
    
    soup = BeautifulSoup(r.text, "html.parser")
    
    # Find the cornerstone table
    tables = soup.find_all("table", class_="article-table")
    print(f"Found {len(tables)} tables")
    
    downloaded = []
    failed = []
    
    for table in tables:
        rows = table.find_all("tr")
        print(f"\nProcessing table with {len(rows)} rows...")
        
        for tr in rows[1:]:  # Skip header
            cells = tr.find_all(["td", "th"])
            if len(cells) < 2:
                continue
            
            # Get name from second cell
            name = cells[1].get_text(strip=True)
            if not name:
                continue
            
            # Find image in first cell
            img = cells[0].find("img")
            if not img:
                failed.append(name)
                continue
            
            # Get image URL
            url = img.get("data-src") or img.get("src", "")
            if not url or url.startswith("data:"):
                failed.append(name)
                continue
            
            if url.startswith("//"):
                url = "https:" + url
            
            # Convert to full size URL
            url = re.sub(r"/scale-to-width-down/\d+", "", url)
            url = url.replace("?cb=", "?format=png&cb=")
            
            # Download
            try:
                r = sess.get(url, timeout=15)
                r.raise_for_status()
                
                filename = f"{slug(name)}.png"
                filepath = output_dir / filename
                filepath.write_bytes(r.content)
                
                downloaded.append(name)
                print(f"  ✓ {name}")
                
            except Exception as e:
                failed.append(name)
                print(f"  ✗ {name}: {e}")
    
    print(f"\n=== Summary ===")
    print(f"Downloaded: {len(downloaded)}")
    print(f"Failed: {len(failed)}")
    
    if failed:
        print(f"\nFailed items:")
        for name in failed[:10]:
            print(f"  - {name}")
    
    print(f"\nIcons saved to: {output_dir.absolute()}")
    print(f"Copy these files to: backend/app/data/templates/cornerstones/")

if __name__ == "__main__":
    download_cornerstones()
