# 蓝图数据与推荐逻辑说明

## 推荐逻辑（已就绪）

推荐引擎对「当前可选蓝图」逐条打分并排序，使用的字段：

| 字段 | 用途 |
|------|------|
| **values** (food/fuel/resolve) | 基础价值分：food×10 + fuel×8 + resolve×12 |
| **synergy.species_preferences** | 当前种族在偏好列表则 +5 分 |
| **inputs** | 资源充足（≥10）时每项 +3 分 |
| **complexity** | 惩罚：complexity×4 |

总分 = 基础价值 + 种族协同 + 资源分 - 复杂度惩罚。**所有在 `blueprints_data_ats.json` 里且名字与识别结果一致的建筑都会参与比较和推荐**，没有逻辑缺口。

## 当前数据来源

- **建筑列表与分类**：来自 `ats_wiki/buildings.json`（Fandom Wiki 抓取），再与 `templates/blueprints/*.png` 取交集，只保留有模板图的 31 栋。
- **values（食物/燃料/决心）**：由 `scripts/build_ats_blueprints_data.py` 按**类型 + 建筑名**推断，例如：
  - Camps：fuel 3, resolve 2, food 0
  - Cookhouse/Bakery：food 4
  - Brewery/Cellar：resolve 4
  - Brick Oven/Smokehouse：fuel 4
  - City（Bath/Tavern/Temple 等）：resolve 4
- **complexity**：按分类固定（Camps=1, Food_Production=2, City_Buildings=2, Industry=3），便于区分优先级。
- **inputs / outputs**：来自 Fandom Wiki 分类页（Camps、Food_Production、City_Buildings、Industry）表格的 **Cost**、**Produces**/Goods Produced，由 `scripts/scrape_building_details.py` 抓取并写入 `ats_wiki/building_details.json`；`build_ats_blueprints_data.py` 生成蓝图时优先使用该文件，无记录时退回按分类占位。
- **synergy.species_preferences**：来自上述分类页的 **Workers** 列（如 Woodcutters' Camp → Beavers，Forager's Camp → Humans）；无或仅 "Any" 时视为全种族。

## 能否「对比推荐」？

- **能**。31 栋建筑都具备上述必填字段，推荐接口会对传入的 `available_blueprints` 列表逐条打分、排序并返回 top-k。
- **区分度**：同一局里不同蓝图之间的分数会因 values（食物/燃料/决心侧重）、complexity（营地 1 vs 工业 3）、以及你当前资源和种族而产生差异，排序结果会有实际意义。
- **精度**：若要和游戏内真实价值、配方、种族偏好完全一致，需要从游戏或官方 Wiki 引入**每栋建筑的 inputs/outputs/values/种族偏好**再写回 `blueprints_data_ats.json`（或扩展 build 脚本的数据源）。

## 重新生成蓝图数据

**推荐顺序**：先抓建筑详情与配方，再生成蓝图数据。

```bash
# 1）抓取 Wiki 基础数据（建筑列表、物资列表等）
python scripts/scrape_ats_wiki.py

# 2）抓取每栋建筑的 Cost / Produces / Workers（inputs、outputs、species_preferences）
python scripts/scrape_building_details.py

# 3）抓取配方：每栋建筑能造什么、所需资源及数量、制作时间、评级（可选，稍慢）
python scripts/scrape_recipes.py

# 4）根据 ats_wiki + templates 生成蓝图 JSON（会使用 building_details.json）
python scripts/build_ats_blueprints_data.py
```

---

## 配方数据（每栋建筑能造什么、所需资源、数量、时间）

由 `scripts/scrape_recipes.py` 从 Fandom 抓取：

- **Recipes 总表**：https://against-the-storm.fandom.com/wiki/Recipes（Product、Building、Rating、Duration、Input 1/2）
- **各建筑子页**：如 /wiki/Bakery、/wiki/Cookhouse 等页的 Recipes 表（Produced、Grade、Production Time、Ingredients）

**输出文件**（均在 `ats_wiki/` 下）：

| 文件 | 说明 |
|------|------|
| **recipes.json** | 配方扁平列表：每项含 `product`、`output_amount`、`building`、`rating`、`duration_seconds`、`inputs`（资源名→数量） |
| **recipes_by_building.json** | 按建筑名分组：`{ "Bakery": [ {...}, ... ], "Cookhouse": [ ... ], ... }`，便于查「某建筑能造什么」 |

用途：前端展示「该建筑可生产列表、每条配方所需资源与数量、制作时间」；或后续推荐逻辑按真实配方算资源需求。仅需总表时可加 `--skip-pages` 跳过各建筑子页（更快）。
