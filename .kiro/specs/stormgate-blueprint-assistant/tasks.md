# 实现计划：风暴之城新手蓝图助手

## 概述

本实现计划将风暴之城新手蓝图助手分解为离散的编码任务。系统采用前后端分离架构，后端使用Python + FastAPI，前端使用Vue.js + TypeScript。实现将按照数据层 → 业务逻辑层 → API层 → 前端层的顺序进行，确保每个步骤都可以增量验证。

## 任务

- [x] 1. 项目初始化和基础设施
  - 创建项目目录结构（backend/、frontend/、data/、tests/）
  - 配置Python虚拟环境和依赖（requirements.txt：FastAPI、OpenCV、Pytesseract、SQLAlchemy、Hypothesis）
  - 配置前端项目（Vue 3 + Vite + TypeScript + Element Plus）
  - 创建Docker Compose配置文件（backend、frontend、nginx服务）
  - 配置日志系统（Python logging，按日期轮转）
  - _需求：11.1, 11.2, 11.3_

- [ ] 2. 数据层实现
  - [x] 2.1 创建蓝图数据模型和JSON加载器
    - 定义Blueprint数据类（name、type、dlc、inputs、outputs、values、complexity、synergy）
    - 实现blueprints_data.json加载和验证逻辑
    - 添加数据验证：values范围0-5，complexity范围1-5
    - _需求：3.1, 3.2, 3.3, 3.4, 3.5, 3.6_
  
  - [ ]* 2.2 编写蓝图数据验证的属性测试
    - **属性 7：蓝图数据验证**
    - **验证需求：3.2, 3.3, 3.4, 3.5, 3.6**
  
  - [x] 2.3 创建SQLite数据库模型和迁移
    - 定义analysis_records表结构（id、timestamp、screenshot_path、game_state_json、recommendations_json、user_id、session_id）
    - 创建索引（timestamp、user_id、session_id）
    - 实现数据库初始化逻辑
    - _需求：9.1, 9.2_
  
  - [x] 2.4 实现HistoryService历史记录服务
    - 实现save_record方法（带事务）
    - 实现get_records方法（支持limit、offset、user_id、session_id过滤）
    - 实现get_record_by_id方法
    - 实现delete_record方法
    - 实现cleanup_old_records方法（删除30天前记录）
    - _需求：6.1, 6.2, 6.3, 6.4, 6.5, 9.6_
  
  - [ ]* 2.5 编写历史记录服务的属性测试
    - **属性 17：分析记录持久化**
    - **验证需求：6.1, 6.2**
    - **属性 18：历史记录排序**
    - **验证需求：6.4**
    - **属性 19：用户记录隔离**
    - **验证需求：6.6, 6.7**

- [ ] 3. 检查点 - 数据层验证
  - 确保所有数据层测试通过，数据库可以正常初始化和操作

- [ ] 4. 图像处理模块实现
  - [x] 4.1 实现TemplateMatcher模板匹配器
    - 实现load_templates方法（加载模板到缓存）
    - 实现match_template方法（单模板匹配，支持多尺度）
    - 实现match_multiple方法（多模板匹配）
    - 实现_multi_scale_match私有方法（尺度：0.8, 0.9, 1.0, 1.1, 1.2）
    - _需求：2.1, 2.4_
  
  - [ ]* 4.2 编写模板匹配的属性测试
    - **属性 4：模板匹配通用性**
    - **验证需求：2.1, 2.4**
  
  - [x] 4.3 实现OCRService OCR服务
    - 实现extract_text方法（支持中文简体+英文）
    - 实现extract_number方法（提取数字）
    - 实现_preprocess_image方法（灰度化、二值化、降噪）
    - 配置Tesseract路径（支持环境变量）
    - _需求：2.2, 2.3_
  
  - [ ]* 4.4 编写OCR服务的属性测试
    - **属性 5：OCR文本提取**
    - **验证需求：2.2, 2.3**
  
  - [x] 4.5 实现ImageAnalysisService图像分析服务
    - 实现analyze_screenshot主方法（协调识别流程）
    - 实现_extract_blueprints方法（从蓝图区域提取列表）
    - 实现_extract_resources方法（从资源区域提取字典）
    - 实现_extract_species方法（从种族区域识别）
    - 返回GameState对象（包含置信度）
    - _需求：2.1, 2.2, 2.3, 2.4, 2.5, 2.6_
  
  - [ ]* 4.6 编写游戏状态结构化的属性测试
    - **属性 6：游戏状态结构化**
    - **验证需求：2.5, 2.6**

- [ ] 5. 推荐引擎实现
  - [x] 5.1 实现RecommendationEngine推荐引擎
    - 实现_calculate_base_value_score方法（food×10 + fuel×8 + resolve×12）
    - 实现_calculate_synergy_score方法（种族匹配+5分）
    - 实现_calculate_resource_score方法（充足资源每个+3分）
    - 实现_calculate_complexity_penalty方法（complexity×4）
    - 实现_calculate_score方法（组合所有评分）
    - 实现_generate_reasoning方法（生成评分理由文本）
    - 实现generate_recommendations方法（排序并返回top_k）
    - _需求：4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8_
  
  - [ ]* 5.2 编写评分计算的属性测试
    - **属性 8：基础价值分计算**
    - **验证需求：4.2**
    - **属性 9：种族协同加分**
    - **验证需求：4.3**
    - **属性 10：资源充足加分**
    - **验证需求：4.4**
    - **属性 11：复杂度惩罚计算**
    - **验证需求：4.5**
  
  - [ ]* 5.3 编写推荐排序的属性测试
    - **属性 12：推荐排序正确性**
    - **验证需求：4.6, 4.8**
    - **属性 13：评分理由生成**
    - **验证需求：4.7**

- [ ] 6. 检查点 - 业务逻辑验证
  - 确保图像处理和推荐引擎测试通过，可以生成正确的推荐结果

- [ ] 7. 后端API实现
  - [x] 7.1 创建FastAPI应用和中间件
    - 初始化FastAPI应用
    - 配置CORS中间件（允许前端跨域）
    - 配置请求ID中间件（为每个请求生成request_id）
    - 配置异常处理器（捕获并返回友好错误）
    - _需求：7.6, 10.1_
  
  - [x] 7.2 实现POST /api/v1/analyze端点
    - 定义请求模型（AnalyzeRequest：image、boxes、session_id）
    - 实现文件验证（格式PNG/JPG/JPEG，大小≤10MB）
    - 保存上传的截图到uploads目录（格式：uploads/{timestamp}_{random_id}.{ext}）
    - 调用ImageAnalysisService分析截图
    - 调用RecommendationEngine生成推荐
    - 调用HistoryService保存记录
    - 返回响应（request_id、game_state、recommendations、record_id）
    - _需求：1.1, 1.5, 1.6, 7.1, 7.2, 7.3, 7.7, 9.3, 9.4_
  
  - [ ]* 7.3 编写分析API的属性测试
    - **属性 1：文件验证完整性**
    - **验证需求：1.1, 1.6**
    - **属性 14：分析API响应结构**
    - **验证需求：7.3, 7.7**
    - **属性 20：截图文件保存**
    - **验证需求：9.3, 9.4**
  
  - [x] 7.4 实现GET /api/v1/history端点
    - 定义查询参数（limit、offset、session_id、user_id）
    - 调用HistoryService.get_records
    - 返回响应（request_id、total、limit、offset、records）
    - _需求：7.4, 7.5_
  
  - [ ]* 7.5 编写历史API的属性测试
    - **属性 15：历史API参数处理**
    - **验证需求：7.5**
  
  - [x] 7.6 实现GET /api/v1/health健康检查端点
    - 检查数据库连接状态
    - 检查OCR服务可用性
    - 检查模板加载状态
    - 返回服务状态和版本信息
    - _需求：11.5, 11.6_
  
  - [x] 7.7 实现错误处理和日志记录
    - 配置全局异常处理器（ImageProcessingError、ValidationError、SQLAlchemyError）
    - 实现数据库重试机制（最多3次，间隔2秒）
    - 配置日志记录（ERROR、WARNING、INFO级别）
    - 记录所有API请求和错误
    - _需求：10.1, 10.2, 10.3, 10.4, 10.5, 10.6_
  
  - [ ]* 7.8 编写错误处理的属性测试
    - **属性 16：API错误响应**
    - **验证需求：7.6**
    - **属性 22：异常捕获和友好错误**
    - **验证需求：10.1**
    - **属性 23：错误日志记录**
    - **验证需求：10.2, 10.3**
    - **属性 24：数据库重试机制**
    - **验证需求：10.6**

- [ ] 8. 前端组件实现
  - [x] 8.1 创建UploadComponent上传组件
    - 实现文件选择和拖拽上传UI
    - 实现validateFile方法（格式和大小验证）
    - 实现uploadFile方法（显示进度条）
    - 实现错误处理（显示Toast通知）
    - _需求：1.1, 1.2, 1.6, 12.1, 12.2, 12.3_
  
  - [x] 8.2 创建RecognitionBoxComponent识别框组件
    - 实现Canvas初始化（加载图片）
    - 实现三个识别框的绘制（blueprints、resources、species）
    - 实现鼠标事件处理（拖动、调整大小）
    - 实现坐标显示（实时更新x、y、width、height）
    - 实现getBoxCoordinates方法（返回所有框坐标）
    - _需求：1.3, 1.4, 12.5_
  
  - [ ]* 8.3 编写识别框组件的属性测试
    - **属性 2：识别框坐标更新**
    - **验证需求：1.4**
    - **属性 26：识别框坐标显示**
    - **验证需求：12.5**
  
  - [x] 8.4 创建ResultsComponent结果展示组件
    - 实现推荐列表显示（名称、评分、排名、reasoning）
    - 实现评分颜色编码（≥80绿色、50-79黄色、<50灰色）
    - 实现详情展开功能（显示inputs、outputs、values、complexity）
    - 实现游戏状态显示（resources、species）
    - 实现低置信度警告显示（警告图标和提示）
    - _需求：5.1, 5.2, 5.3, 5.4, 5.5, 5.6_
  
  - [ ]* 8.5 编写结果展示组件的属性测试
    - **属性 25：推荐结果展示完整性**
    - **验证需求：5.2, 5.3**
  
  - [x] 8.6 创建HistoryComponent历史记录组件
    - 实现fetchHistory方法（调用GET /api/v1/history）
    - 实现历史记录列表显示（时间、截图缩略图）
    - 实现分页功能（limit、offset）
    - 实现记录详情查看（点击显示完整分析结果）
    - 实现deleteRecord方法（可选功能）
    - _需求：6.3, 6.4, 6.5_
  
  - [x] 8.7 实现前端错误处理和加载状态
    - 实现Toast通知组件（3秒自动消失）
    - 实现加载动画（上传中、分析中）
    - 实现错误消息显示（网络错误、API错误）
    - _需求：12.3, 12.4, 12.7_
  
  - [ ]* 8.8 编写前端交互的属性测试
    - **属性 3：分析请求触发**
    - **验证需求：1.5**
    - **属性 27：错误通知显示**
    - **验证需求：12.7**

- [ ] 9. 前端路由和主应用
  - [x] 9.1 配置Vue Router
    - 创建路由：/ (首页)、/analyze (分析页)、/history (历史页)
    - 实现路由导航
    - _需求：12.1_
  
  - [x] 9.2 创建主应用组件
    - 集成UploadComponent、RecognitionBoxComponent、ResultsComponent
    - 实现完整的分析流程（上传 → 调整识别框 → 确认 → 显示结果）
    - 实现session_id管理（localStorage）
    - _需求：1.2, 1.3, 1.4, 1.5_
  
  - [x] 9.3 实现响应式设计
    - 配置移动端适配（媒体查询）
    - 实现触摸事件支持（识别框调整）
    - _需求：12.6_

- [ ] 10. 检查点 - 端到端功能验证
  - 确保前后端集成正常，完整流程可以运行

- [ ] 11. 测试数据和模板准备
  - [ ] 11.1 创建blueprints_data.json
    - 添加至少20个核心蓝图数据
    - 包含多种类型（生产建筑、军事建筑、特殊建筑）
    - 包含不同种族偏好和复杂度
    - _需求：3.1_
  
  - [ ] 11.2 准备模板图像
    - 收集蓝图图标模板（至少20个）
    - 收集种族图标模板（人类、精灵、兽人等）
    - 保存到templates目录
    - _需求：2.1, 2.4_
  
  - [ ] 11.3 创建测试截图
    - 准备多个测试截图（不同分辨率、不同游戏状态）
    - 保存到tests/fixtures目录
    - _需求：2.1, 2.2, 2.3_

- [ ] 12. 集成测试和E2E测试
  - [ ]* 12.1 编写API集成测试
    - 测试POST /api/v1/analyze完整流程
    - 测试GET /api/v1/history查询功能
    - 测试GET /api/v1/health健康检查
    - 测试错误场景（无效文件、识别失败、数据库错误）
  
  - [ ]* 12.2 编写前端E2E测试（使用Playwright）
    - 测试上传截图流程
    - 测试调整识别框
    - 测试查看推荐结果
    - 测试查看历史记录

- [ ] 13. 部署配置和文档
  - [x] 13.1 完善Docker配置
    - 配置后端Dockerfile（安装OpenCV、Tesseract依赖）
    - 配置前端Dockerfile（构建生产版本）
    - 配置nginx.conf（反向代理、静态文件服务）
    - 配置环境变量（.env.example）
    - _需求：11.1, 11.2, 11.3, 11.4_
  
  - [x] 13.2 编写README文档
    - 项目介绍和功能说明
    - 安装和运行指南（Docker Compose一键启动）
    - API文档（端点、请求、响应格式）
    - 开发指南（本地开发、测试运行）
  
  - [ ] 13.3 配置CI/CD
    - 配置GitHub Actions或GitLab CI
    - 运行linting（flake8、ESLint）
    - 运行类型检查（mypy、TypeScript）
    - 运行所有测试（单元、属性、集成）
    - 生成覆盖率报告

- [ ] 14. 最终检查点
  - 确保所有测试通过（单元测试覆盖率≥80%）
  - 确保所有属性测试运行100次迭代
  - 确保Docker Compose可以一键启动
  - 确保文档完整且准确

## 注意事项

- 标记为`*`的任务是可选的测试任务，可以跳过以加快MVP开发
- 每个任务都引用了具体的需求编号，便于追溯
- 检查点任务确保增量验证，及时发现问题
- 属性测试必须配置为运行最少100次迭代
- 所有属性测试必须包含注释，引用设计文档中的属性编号
