# 模板图来源说明（与官方一致、截图更好处理）

蓝图/种族识别依赖 `backend/app/data/templates/` 下的图标。为和**游戏内 UI 一致**、截图时更好识别，优先使用官方或与游戏内一致的图源。

---

## 1. 官方渠道一览

| 来源 | 说明 | 是否与游戏一致 | 备注 |
|------|------|----------------|------|
| **Hooded Horse 官方 Wiki** | [wiki.hoodedhorse.com/Against_the_Storm](https://wiki.hoodedhorse.com/wiki/Against_the_Storm/)：List of Buildings、Buildings、Blueprints、Species 等；使用 Module:SpriteFinder 显示游戏内小图标 | ✅ 与游戏资源同源 | 官方维护，图标应和游戏一致；需能访问该站 |
| **游戏内截图裁剪** | 在游戏蓝图/种族选择界面截图，按图标格子裁剪成单张图 | ✅ 完全一致 | 推荐：和实际截图 UI 一致，识别最准 |
| **Fandom Wiki** | [against-the-storm.fandom.com](https://against-the-storm.fandom.com/wiki/)：非官方，各页表格图标尺寸/格式不统一（117/128/256 等，部分 WebP） | ⚠️ 近似 | 当前默认抓取源；下载后需运行 `normalize_template_images.py` |
| **游戏资源文件** | Steam：`steamapps/common/Against the Storm`；Unity 资源在 AssetBundle 等 | ✅ 一致 | 需用 Asset Studio 等工具打开、导出贴图；步骤较多 |

---

## 2. 推荐做法（和官方一致、截图好处理）

### 方案 A：从官方 Wiki 抓取（与游戏同源，推荐用脚本）

- **一键抓取**：在项目根目录执行  
  `python scripts/download_official_wiki_images.py`  
  会从 [List of Buildings](https://wiki.hoodedhorse.com/wiki/Against_the_Storm/List_of_Buildings) 与 [Species](https://wiki.hoodedhorse.com/wiki/Against_the_Storm/Species) 解析表格，按建筑名/种族名下载图标到 `backend/app/data/templates/blueprints/` 与 `species/`，文件名与现有一致（建筑 slug、种族小写英文）。  
  若出现 **403 Forbidden**，多为站点对当前 IP 限流，请在本地网络再试，或改用方案 A 的手动保存。
- **手动**：浏览器打开上述页面，右键图标 → “图片另存为”，按命名规则放到对应目录（见下）。
- 下载后执行一次 `python scripts/normalize_template_images.py` 统一尺寸与格式。

### 方案 B：游戏内截图裁剪（最准）

1. 进入游戏，打开**蓝图选择界面**（或种族选择界面）。
2. 截一张完整界面图（分辨率固定、UI 缩放一致更好）。
3. 按界面上的**图标格子**裁剪：每个建筑/种族一格，保存为单张图。
4. 命名与现有模板一致（建筑：`woodcutters_camp.png` 等 slug；种族：`human.png`, `beaver.png` 等），放入 `templates/blueprints/` 或 `templates/species/`。
5. 运行一次归一化，统一尺寸与格式：
   ```bash
   python scripts/normalize_template_images.py
   ```

这样得到的模板与**你截图时的游戏 UI 完全一致**，识别最稳。

### 方案 C：继续用 Fandom + 归一化

- 使用现有 `scripts/download_ats_wiki_images.py` 从 Fandom 抓图。
- 抓取后**务必**执行：
  ```bash
  python scripts/normalize_template_images.py   # 可选 --backup
  ```
- 归一化后尺寸与格式统一，识别会明显改善，但仍非官方图源。

---

## 3. 模板命名规则（与代码一致）

- **建筑**：英文名转 slug，如 `Woodcutters' Camp` → `woodcutters_camp.png`；见 `backend/app/data/blueprints_data_ats.json` 或 `scripts/build_ats_blueprints_data.py` 中的建筑列表。
- **种族**：小写英文，如 `human.png`, `beaver.png`, `harpy.png`, `lizard.png`, `fox.png`。

替换或新增文件后，若需统一尺寸，再运行一次 `normalize_template_images.py` 即可。

---

## 4. 参考链接

- 官方 Wiki 首页: https://wiki.hoodedhorse.com/wiki/Against_the_Storm/
- 官方建筑列表: https://wiki.hoodedhorse.com/wiki/Against_the_Storm/List_of_Buildings
- 官方 Modding 文档: https://wiki.hoodedhorse.com/wiki/Against_the_Storm/Modding
- Fandom（非官方）: https://against-the-storm.fandom.com/wiki/
- Thunderstore（ATS 模组，无专用“图标导出”工具）: https://thunderstore.io/c/against-the-storm/
