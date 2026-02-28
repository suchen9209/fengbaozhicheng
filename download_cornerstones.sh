#!/bin/bash
# 一键下载基石图标脚本

echo "=== Against the Storm 基石图标下载工具 ==="
echo ""

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "错误: 需要先安装 Python 3"
    echo "下载地址: https://www.python.org/downloads/"
    exit 1
fi

# 创建临时目录
mkdir -p /tmp/ats_cornerstones
cd /tmp/ats_cornerstones

# 创建Python脚本
cat > download.py << 'PYEOF'
#!/usr/bin/env python3
import re
import json
import requests
from pathlib import Path
from bs4 import BeautifulSoup

BASE_URL = "https://against-the-storm.fandom.com"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"

def session():
    s = requests.Session()
    s.headers.update({
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    })
    return s

def slug(name: str) -> str:
    return re.sub(r"[^\w]", "_", name).lower().strip("_")

def main():
    sess = session()
    output_dir = Path("cornerstones")
    output_dir.mkdir(exist_ok=True)
    
    print("正在获取基石页面...")
    r = sess.get(f"{BASE_URL}/wiki/Cornerstone", timeout=30)
    r.raise_for_status()
    
    soup = BeautifulSoup(r.text, "html.parser")
    tables = soup.find_all("table", class_="article-table")
    print(f"找到 {len(tables)} 个表格")
    
    downloaded = []
    failed = []
    
    for table in tables:
        rows = table.find_all("tr")
        
        for tr in rows[1:]:
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
            
            # 获取高清版本
            url = re.sub(r"/scale-to-width-down/\d+", "", url)
            
            try:
                r = sess.get(url, timeout=15)
                r.raise_for_status()
                
                filepath = output_dir / f"{slug(name)}.png"
                filepath.write_bytes(r.content)
                
                downloaded.append(name)
                print(f"✓ {name}")
                
            except Exception as e:
                failed.append(name)
                print(f"✗ {name}")
    
    print(f"\n=== 下载完成 ===")
    print(f"成功: {len(downloaded)}")
    print(f"失败: {len(failed)}")
    print(f"\n图标保存在: {output_dir.absolute()}")
    
    if failed:
        print(f"\n失败的基石:")
        for name in failed[:10]:
            print(f"  - {name}")

if __name__ == "__main__":
    main()
PYEOF

# 安装依赖
echo "安装依赖..."
pip3 install requests beautifulsoup4 -q

# 运行下载脚本
echo "开始下载基石图标..."
python3 download.py

# 显示结果
echo ""
echo "下载的图标:"
ls -la cornerstones/ | head -20

echo ""
echo "=== 下一步 ==="
echo "1. 图标已下载到: /tmp/ats_cornerstones/cornerstones/"
echo "2. 复制到项目目录:"
echo "   cp -r /tmp/ats_cornerstones/cornerstones/* /path/to/project/backend/app/data/templates/cornerstones/"
