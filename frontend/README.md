# 风暴之城蓝图助手 - 前端

Vue.js 3 + TypeScript + Element Plus 前端应用。

## 快速开始

### 1. 安装依赖

```bash
npm install
```

### 2. 启动开发服务器

```bash
npm run dev
```

应用将在 http://localhost:5173 启动

### 3. 构建生产版本

```bash
npm run build
```

构建产物将输出到 `dist/` 目录

## 功能特性

- 📸 截图上传（拖拽或点击）
- 🎯 蓝图推荐展示
- 📊 评分可视化
- 📜 历史记录管理
- 📱 响应式设计

## 项目结构

```
frontend/
├── src/
│   ├── components/          # Vue组件
│   │   ├── UploadComponent.vue
│   │   └── ResultsComponent.vue
│   ├── views/               # 页面视图
│   │   ├── HomeView.vue
│   │   ├── AnalyzeView.vue
│   │   └── HistoryView.vue
│   ├── router/              # 路由配置
│   │   └── index.ts
│   ├── services/            # API服务
│   │   └── api.ts
│   ├── App.vue              # 根组件
│   └── main.ts              # 应用入口
├── index.html
├── package.json
├── vite.config.ts
└── tsconfig.json
```

## 可用脚本

- `npm run dev` - 启动开发服务器
- `npm run build` - 构建生产版本
- `npm run preview` - 预览生产构建
- `npm run lint` - 运行ESLint检查
- `npm run test:unit` - 运行单元测试

## 环境变量

在 `.env` 文件中配置：

```
VITE_API_BASE_URL=http://localhost:8000
```

## 技术栈

- Vue 3 (Composition API)
- TypeScript
- Vite
- Element Plus
- Vue Router
- Axios

## 开发注意事项

- 确保后端API服务已启动（默认 http://localhost:8000）
- 使用 TypeScript 进行类型检查
- 遵循 Vue 3 Composition API 最佳实践
- 使用 Element Plus 组件库保持UI一致性

## API集成

前端通过 `src/services/api.ts` 与后端通信：

```typescript
import apiClient from '@/services/api'

// 分析截图
const response = await apiClient.post('/api/v1/analyze', formData)

// 获取历史
const response = await apiClient.get('/api/v1/history')
```

## 浏览器支持

- Chrome (最新版)
- Firefox (最新版)
- Safari (最新版)
- Edge (最新版)
