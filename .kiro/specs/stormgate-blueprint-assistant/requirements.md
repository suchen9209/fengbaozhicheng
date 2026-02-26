# 需求文档：风暴之城新手蓝图助手

## 简介

风暴之城新手蓝图助手是一个AI驱动的决策支持工具，用于帮助《风暴之城》(Stormgate)游戏玩家通过分析游戏截图来做出最优的蓝图选择。系统通过图像识别技术提取游戏状态信息，并基于多维度评分算法提供蓝图推荐。

## 术语表

- **System**: 风暴之城新手蓝图助手系统
- **User**: 使用该工具的《风暴之城》游戏玩家
- **Blueprint**: 游戏中的建筑蓝图，包含资源需求和产出信息
- **Game_State**: 从截图中提取的游戏状态信息，包括可用蓝图、资源库存和种族信息
- **Recognition_Box**: 用户可调整的识别区域框，用于标记截图中的关键信息区域
- **Recommendation_Engine**: 基于评分算法计算蓝图优先级的核心模块
- **Template_Matcher**: 使用OpenCV进行图标模板匹配的组件
- **OCR_Service**: 使用Tesseract进行文字和数字识别的服务
- **Analysis_Record**: 单次分析的历史记录，包含输入截图和推荐结果

## 需求

### 需求 1：截图上传与预处理

**用户故事：** 作为玩家，我想上传游戏截图并调整识别区域，以便系统能准确提取游戏状态信息。

#### 验收标准

1. WHEN User上传图片文件，THEN THE System SHALL验证文件格式为PNG、JPG或JPEG
2. WHEN 图片上传成功，THEN THE System SHALL在前端显示截图预览
3. THE System SHALL在预览图上叠加三个可调整的Recognition_Box（蓝图区域、资源区域、种族区域）
4. WHEN User拖动或调整Recognition_Box，THEN THE System SHALL实时更新框的坐标和尺寸
5. WHEN User确认识别区域，THEN THE System SHALL将截图和区域坐标发送到后端进行分析
6. IF 上传的文件大小超过10MB，THEN THE System SHALL拒绝上传并返回错误提示

### 需求 2：图像分析服务

**用户故事：** 作为系统，我需要从截图中准确识别游戏元素，以便提供可靠的推荐依据。

#### 验收标准

1. WHEN System接收到截图和Recognition_Box坐标，THEN THE Template_Matcher SHALL使用OpenCV模板匹配识别蓝图图标
2. WHEN 识别蓝图区域，THEN THE OCR_Service SHALL使用Tesseract提取蓝图名称文本
3. WHEN 识别资源区域，THEN THE OCR_Service SHALL提取资源数量的数字信息
4. WHEN 识别种族区域，THEN THE Template_Matcher SHALL匹配种族图标
5. THE System SHALL将识别结果组织为结构化的Game_State JSON对象
6. THE Game_State JSON SHALL包含字段：available_blueprints（可用蓝图列表）、resources（资源库存字典）、species（种族标识）
7. IF 模板匹配置信度低于0.7，THEN THE System SHALL在结果中标记该项为"不确定"
8. IF OCR识别失败，THEN THE System SHALL返回null值并记录错误日志

### 需求 3：蓝图数据管理

**用户故事：** 作为系统，我需要维护完整的蓝图数据库，以便进行准确的评分计算。

#### 验收标准

1. THE System SHALL从blueprints_data.json文件加载蓝图数据
2. WHEN 加载蓝图数据，THEN THE System SHALL验证每个蓝图包含必需字段：name、type、dlc、inputs、outputs、values、complexity、synergy
3. THE values字段 SHALL包含food、fuel、resolve三个评分（范围0-5）
4. THE complexity字段 SHALL为整数（范围1-5），表示生产链复杂度
5. THE synergy字段 SHALL包含species_preferences（种族偏好列表）和biome_bonuses（生物群系加成字典）
6. THE inputs和outputs字段 SHALL为字典，键为物品名称，值为数量
7. IF blueprints_data.json文件不存在或格式错误，THEN THE System SHALL返回错误并拒绝启动

### 需求 4：推荐引擎

**用户故事：** 作为玩家，我想获得基于当前游戏状态的蓝图推荐，以便做出最优决策。

#### 验收标准

1. WHEN Recommendation_Engine接收到Game_State和可用蓝图列表，THEN THE System SHALL为每个蓝图计算评分
2. THE 评分计算 SHALL包含基础价值分：food×10 + fuel×8 + resolve×12
3. WHEN 蓝图的species_preferences包含当前种族，THEN THE System SHALL为该蓝图加5分
4. WHEN 蓝图的inputs中某项资源在Game_State的resources中数量≥10，THEN THE System SHALL为该蓝图加3分
5. THE System SHALL从总分中减去complexity×4作为复杂度惩罚
6. WHEN 所有蓝图评分完成，THEN THE System SHALL按评分降序排列蓝图
7. THE System SHALL为每个推荐生成reasoning文本，说明加分和减分原因
8. THE System SHALL返回排名前5的蓝图推荐

### 需求 5：结果展示

**用户故事：** 作为玩家，我想清晰地看到推荐结果和评分理由，以便理解系统的推荐逻辑。

#### 验收标准

1. WHEN 推荐结果返回，THEN THE System SHALL在前端显示排名列表
2. WHEN 显示每个推荐，THEN THE System SHALL展示：蓝图名称、总评分、排名、reasoning文本
3. THE System SHALL使用颜色编码显示评分等级：≥80分为绿色，50-79分为黄色，<50分为灰色
4. WHEN User点击某个推荐，THEN THE System SHALL展开显示详细信息：inputs、outputs、values、complexity
5. THE System SHALL在结果页面显示识别到的Game_State信息（资源库存、种族）
6. WHEN 识别结果包含"不确定"项，THEN THE System SHALL在界面上显示警告图标和提示文本

### 需求 6：历史记录管理

**用户故事：** 作为玩家，我想查看过去的分析记录，以便追踪我的决策历史和游戏进展。

#### 验收标准

1. WHEN 分析完成，THEN THE System SHALL将Analysis_Record保存到SQLite数据库
2. THE Analysis_Record SHALL包含字段：id、timestamp、screenshot_path、game_state、recommendations、user_id
3. WHEN User请求历史记录，THEN THE System SHALL返回最近20条Analysis_Record
4. THE System SHALL按timestamp降序排列历史记录
5. WHEN User点击历史记录项，THEN THE System SHALL显示该次分析的完整结果
6. WHERE User已登录，THE System SHALL仅返回该User的历史记录
7. WHERE User未登录，THE System SHALL使用session_id关联匿名历史记录

### 需求 7：API接口

**用户故事：** 作为前端开发者，我需要清晰定义的API接口，以便与后端服务集成。

#### 验收标准

1. THE System SHALL提供POST /api/v1/analyze端点用于上传截图和识别区域
2. WHEN 调用/api/v1/analyze，THEN THE System SHALL接受multipart/form-data格式，包含image文件和boxes JSON
3. WHEN /api/v1/analyze处理成功，THEN THE System SHALL返回JSON响应，包含game_state和recommendations数组
4. THE System SHALL提供GET /api/v1/history端点用于获取历史记录
5. WHEN 调用/api/v1/history，THEN THE System SHALL接受可选的limit和offset查询参数
6. IF API请求失败，THEN THE System SHALL返回适当的HTTP状态码（400客户端错误，500服务器错误）和错误消息JSON
7. THE System SHALL在所有API响应中包含request_id字段用于追踪

### 需求 8：图像处理性能

**用户故事：** 作为玩家，我希望系统能快速处理截图，以便不影响游戏体验。

#### 验收标准

1. WHEN System处理单张截图，THEN THE System SHALL在5秒内返回分析结果
2. WHEN 执行模板匹配，THEN THE Template_Matcher SHALL使用多尺度匹配提高识别准确率
3. WHEN 执行OCR识别，THEN THE OCR_Service SHALL预处理图像（灰度化、二值化、降噪）
4. THE System SHALL缓存已加载的模板图像以减少重复加载时间
5. IF 处理时间超过5秒，THEN THE System SHALL返回超时错误并记录日志

### 需求 9：数据持久化

**用户故事：** 作为系统管理员，我需要可靠的数据存储，以便保证数据不丢失。

#### 验收标准

1. THE System SHALL使用SQLite数据库存储历史记录
2. WHEN System启动，THEN THE System SHALL自动创建必要的数据库表（如不存在）
3. THE System SHALL将上传的截图保存到本地文件系统的uploads目录
4. THE screenshot_path字段 SHALL存储相对路径，格式为：uploads/{timestamp}_{random_id}.{ext}
5. WHEN 保存Analysis_Record，THEN THE System SHALL使用事务确保数据一致性
6. THE System SHALL定期清理30天前的截图文件以节省存储空间

### 需求 10：错误处理与日志

**用户故事：** 作为开发者，我需要完善的错误处理和日志记录，以便快速定位和解决问题。

#### 验收标准

1. WHEN 发生异常，THEN THE System SHALL捕获异常并返回用户友好的错误消息
2. THE System SHALL记录所有错误到日志文件，包含timestamp、error_type、error_message、stack_trace
3. WHEN 图像识别失败，THEN THE System SHALL记录失败原因和识别参数
4. THE System SHALL使用不同日志级别：DEBUG（调试信息）、INFO（一般信息）、WARNING（警告）、ERROR（错误）
5. THE System SHALL将日志文件按日期轮转，保留最近7天的日志
6. IF 数据库连接失败，THEN THE System SHALL重试3次，每次间隔2秒

### 需求 11：部署与配置

**用户故事：** 作为运维人员，我需要简单的部署方式，以便快速搭建和维护系统。

#### 验收标准

1. THE System SHALL提供Docker Compose配置文件用于一键部署
2. THE Docker Compose配置 SHALL包含frontend、backend、nginx三个服务
3. THE System SHALL通过环境变量配置关键参数：数据库路径、上传目录、日志级别
4. WHEN 使用Docker部署，THEN THE System SHALL自动安装所有依赖（OpenCV、Tesseract、Python包）
5. THE System SHALL提供健康检查端点GET /api/v1/health
6. WHEN 调用/health端点，THEN THE System SHALL返回服务状态和版本信息

### 需求 12：前端交互体验

**用户故事：** 作为玩家，我希望界面操作流畅直观，以便快速完成分析流程。

#### 验收标准

1. WHEN User访问首页，THEN THE System SHALL显示上传区域和历史记录入口
2. THE System SHALL支持拖拽上传和点击选择文件两种方式
3. WHEN 图片上传中，THEN THE System SHALL显示进度条和百分比
4. WHEN 分析处理中，THEN THE System SHALL显示加载动画和"分析中..."提示
5. WHEN Recognition_Box被调整，THEN THE System SHALL显示当前框的像素坐标
6. THE System SHALL在移动端自适应显示，支持触摸操作调整Recognition_Box
7. WHEN 发生错误，THEN THE System SHALL使用Toast通知显示错误消息，3秒后自动消失
