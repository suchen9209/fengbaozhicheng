# 基石图标收集指南

由于Wiki网站有Cloudflare保护，服务器无法直接抓取。请按以下步骤手动获取：

## 方法1：从Fandom Wiki手动下载

1. 访问 https://against-the-storm.fandom.com/wiki/Cornerstone
2. 在浏览器中按 F12 打开开发者工具
3. 切换到 Console 标签
4. 粘贴以下代码：

```javascript
// 提取所有基石图标
const images = document.querySelectorAll('table.article-table img');
const cornerstones = [];

images.forEach(img => {
    const row = img.closest('tr');
    const nameCell = row.querySelector('td:nth-child(2)');
    if (nameCell) {
        const name = nameCell.textContent.trim();
        const src = img.src;
        if (name && src && !src.includes('data:image')) {
            cornerstones.push({name, src});
        }
    }
});

console.log(JSON.stringify(cornerstones, null, 2));
```

5. 复制输出的JSON
6. 使用以下Python脚本下载：

```python
import json
import requests
import os

cornerstones = [...]  # 粘贴刚才复制的JSON
output_dir = "backend/app/data/templates/cornerstones"
os.makedirs(output_dir, exist_ok=True)

for cs in cornerstones:
    name = cs['name'].lower().replace(' ', '_').replace("'", '').replace('-', '_')
    url = cs['src'].replace('/thumb/', '/').split('.png/')[0] + '.png'
    
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code == 200:
            with open(f"{output_dir}/{name}.png", 'wb') as f:
                f.write(r.content)
            print(f"✓ Downloaded: {name}")
    except Exception as e:
        print(f"✗ Failed: {name} - {e}")
```

## 方法2：从游戏文件提取（推荐）

如果你有游戏本体：

1. 找到游戏安装目录
2. 进入 `Against the Storm_Data/StreamingAssets/`
3. 搜索包含 "Cornerstone" 的文件夹
4. 图标通常在 `Sprites` 或 `Icons` 子文件夹中
5. 复制所有 cornerstone 图标到 `backend/app/data/templates/cornerstones/`

## 方法3：逐个截图提取

使用我之前创建的提取脚本：

```bash
python scripts/extract_all_from_screenshot.py <screenshot_path>
```

每当你在游戏中看到基石选择界面时，截图并用此工具提取。

## 验证下载

下载完成后，运行：

```bash
python scripts/extract_cornerstones.py --list
```

查看收集进度。
