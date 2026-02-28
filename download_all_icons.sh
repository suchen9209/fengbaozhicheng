#!/bin/bash
# 一键下载所有缺失图标（蓝图 + 基石）

echo "=== Against the Storm 图标完整下载工具 ==="
echo ""
echo "将下载:"
echo "  - 19个缺失的蓝图"
echo "  - 123个基石"
echo ""

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "错误: 需要先安装 Python 3"
    exit 1
fi

# 创建临时目录
mkdir -p /tmp/ats_icons
cd /tmp/ats_icons

# 复制Python脚本
cat > download.py << 'PYEOF'
#!/usr/bin/env python3
"""下载所有缺失的图标"""

import re
import sys
from pathlib import Path
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://against-the-storm.fandom.com"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"

MISSING_BLUEPRINTS = [
    ("Beanery", "Beanery"),
    ("Explorer's Lodge", "Explorer's_Lodge"),
    ("Farm Field", "Farm_Field"),
    ("Forester's Hut", "Forester's_Hut"),
    ("Forum", "Forum"),
    ("Hallowed Herb Garden", "Hallowed_Herb_Garden"),
    ("Hallowed Small Farm", "Hallowed_Small_Farm"),
    ("Holy Market", "Holy_Market"),
    ("Holy Temple", "Holy_Temple"),
    ("Market", "Market"),
    ("Small Forager's Camp", "Small_Forager's_Camp"),
    ("Small Herbalist's Camp", "Small_Herbalist's_Camp"),
    ("Small Trapper's Camp", "Small_Trapper's_Camp"),
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

def slug(name):
    s = re.sub(r"[\s']+", "_", name)
    s = re.sub(r"[^a-zA-Z0-9_]", "", s)
    return s.lower().strip("_")

def to_full_image_url(thumb_url):
    if not thumb_url or "static.wikia.nocookie.net" not in thumb_url:
        return thumb_url
    return re.sub(r"/scale-to-width-down/\d+\?", "?", thumb_url)

def download_image(sess, url, out_path):
    try:
        r = sess.get(url, timeout=15)
        r.raise_for_status()
        out_path.write_bytes(r.content)
        return True
    except Exception as e:
        return False

def download_blueprint(sess, name, wiki_name, output_dir):
    try:
        r = sess.get(f"{BASE_URL}/wiki/{wiki_name}", timeout=30)
        if r.status_code != 200:
            print(f"  ✗ {name}")
            return False
        
        soup = BeautifulSoup(r.text, "html.parser")
        infobox = soup.find("aside", class_="portable-infobox")
        if infobox:
            img = infobox.find("img")
            if img:
                url = img.get("data-src") or img.get("src", "")
                if url:
                    if url.startswith("//"):
                        url = "https:" + url
                    url = to_full_image_url(url)
                    
                    out_path = output_dir / f"{slug(name)}.png"
                    if download_image(sess, url, out_path):
                        print(f"  ✓ {name}")
                        return True
        
        print(f"  ✗ {name}")
        return False
    except Exception as e:
        print(f"  ✗ {name}: {e}")
        return False

def download_cornerstones(sess, output_dir):
    try:
        r = sess.get(f"{BASE_URL}/wiki/Cornerstone", timeout=30)
        r.raise_for_status()
    except Exception as e:
        print(f"  ✗ Cornerstone page: {e}")
        return 0
    
    soup = BeautifulSoup(r.text, "html.parser")
    tables = soup.find_all("table", class_="article-table")
    
    downloaded = 0
    for table in tables:
        for tr in table.find_all("tr")[1:]:
            cells = tr.find_all(["td", "th"])
            if len(cells) < 2:
                continue
            
            name = cells[1].get_text(strip=True)
            if not name:
                continue
            
            img = cells[0].find("img")
            if not img:
                continue
            
            url = img.get("data-src") or img.get("src", "")
            if not url or url.startswith("data:"):
                continue
            
            if url.startswith("//"):
                url = "https:" + url
            url = to_full_image_url(url)
            
            out_path = output_dir / f"{slug(name)}.png"
            if download_image(sess, url, out_path):
                downloaded += 1
                print(f"  ✓ {name}")
    
    return downloaded

def main():
    sess = session()
    
    # Download blueprints
    blueprints_dir = Path("blueprints")
    blueprints_dir.mkdir(exist_ok=True)
    
    print("=== 下载缺失的蓝图 ===")
    for name, wiki_name in MISSING_BLUEPRINTS:
        download_blueprint(sess, name, wiki_name, blueprints_dir)
    
    # Download cornerstones
    cornerstones_dir = Path("cornerstones")
    cornerstones_dir.mkdir(exist_ok=True)
    
    print("\n=== 下载基石 ===")
    count = download_cornerstones(sess, cornerstones_dir)
    
    print(f"\n=== 完成 ===")
    print(f"蓝图: {len(list(blueprints_dir.glob('*.png')))} 个")
    print(f"基石: {len(list(cornerstones_dir.glob('*.png')))} 个")
    print(f"\n保存位置: {Path('.').absolute()}")

if __name__ == "__main__":
    main()
PYEOF

# 安装依赖
echo "安装依赖..."
pip3 install requests beautifulsoup4 -q 2>/dev/null

# 运行下载
echo ""
echo "开始下载..."
python3 download.py

echo ""
echo "=== 下载完成 ==="
echo ""
echo "图标已保存到: /tmp/ats_icons/"
echo ""
echo "下一步:"
echo "  1. 复制蓝图到项目:"
echo "     cp -r /tmp/ats_icons/blueprints/* /path/to/project/backend/app/data/templates/blueprints/"
echo ""
echo "  2. 复制基石到项目:"
echo "     cp -r /tmp/ats_icons/cornerstones/* /path/to/project/backend/app/data/templates/cornerstones/"
