# 跌倒检测系统前端

## 项目概述

本项目是一个基于 Vue 3 的跌倒检测系统前端应用，采用现代化的 UI 设计，提供用户端和管理员端两种角色的完整功能。

---

## 技术栈

| 分类 | 技术 | 版本 | 说明 |
|-----|------|-----|------|
| 框架 | Vue | 3.4+ | 前端框架 |
| 路由 | Vue Router | 4.3+ | 路由管理 |
| 状态管理 | Pinia | 2.1+ | 全局状态管理 |
| UI组件 | Element Plus | 2.6+ | 组件库 |
| HTTP客户端 | Axios | 1.6+ | 网络请求 |
| 图表 | ECharts | 5.5+ | 数据可视化 |
| 构建工具 | Vite | 5.1+ | 构建工具 |

---

## 目录结构

```
frontend/
├── src/
│   ├── layout/              # 布局组件
│   │   ├── UserLayout.vue   # 用户端布局
│   │   └── AdminLayout.vue  # 管理员端布局
│   ├── views/               # 页面组件
│   │   ├── Login.vue        # 登录页面
│   │   ├── Dashboard.vue    # 仪表盘（通用）
│   │   ├── Upload.vue       # 上传页面（通用）
│   │   ├── Alerts.vue       # 告警页面（通用）
│   │   ├── AIAssistant.vue  # AI助手（通用）
│   │   ├── admin/           # 管理员端页面
│   │   │   ├── AdminDashboard.vue
│   │   │   ├── AdminUsers.vue
│   │   │   ├── AdminCameras.vue
│   │   │   ├── AdminStatistics.vue
│   │   │   ├── AdminAlerts.vue
│   │   │   ├── AdminSettings.vue
│   │   │   └── AdminAIAssistant.vue
│   │   └── user/            # 用户端页面
│   │       ├── UserDashboard.vue
│   │       ├── UserUpload.vue
│   │       ├── UserHistory.vue
│   │       ├── UserAlerts.vue
│   │       ├── UserProfile.vue
│   │       ├── UserCamera.vue
│   │       ├── UserCameraManage.vue
│   │       └── UserAIAssistant.vue
│   ├── router/              # 路由配置
│   │   └── index.js
│   ├── stores/              # Pinia状态管理
│   │   └── detection.js
│   ├── App.vue              # 根组件
│   ├── main.js              # 入口文件
│   └── style.css            # 全局样式
├── index.html               # HTML模板
├── package.json             # 依赖配置
├── vite.config.js           # Vite配置
└── README.md                # 项目说明
```

---

## 安装与运行

### 1. 安装依赖

```bash
# 安装依赖
npm install

# 或使用 yarn
yarn install
```

### 2. 开发模式

```bash
# 启动开发服务器
npm run dev

# 访问地址
# http://localhost:3000
```

### 3. 生产构建

```bash
# 构建生产版本
npm run build

# 预览构建结果
npm run preview
```

---

## 页面结构

### 用户端页面

| 页面 | 路由 | 功能说明 |
|-----|------|---------|
| **仪表盘** | `/user` | 展示检测统计概览 |
| **视频上传** | `/user/upload` | 上传视频进行检测 |
| **检测历史** | `/user/history` | 查看检测记录 |
| **告警管理** | `/user/alerts` | 查看个人告警 |
| **AI助手** | `/user/ai-assistant` | 智能对话助手 |
| **个人中心** | `/user/profile` | 修改个人信息 |
| **摄像头** | `/user/camera` | 摄像头实时监控 |
| **摄像头管理** | `/user/cameras` | 管理摄像头列表 |

### 管理员端页面

| 页面 | 路由 | 功能说明 |
|-----|------|---------|
| **仪表盘** | `/admin` | 系统总览和统计 |
| **用户管理** | `/admin/users` | 管理系统用户 |
| **摄像头管理** | `/admin/cameras` | 查看所有摄像头（仅显示信息，不可查看实时视频） |
| **统计分析** | `/admin/statistics` | 系统数据统计 |
| **告警管理** | `/admin/alerts` | 全局告警管理 |
| **系统设置** | `/admin/settings` | 系统配置 |
| **AI助手** | `/admin/ai-assistant` | 管理员AI助手 |

### 通用页面

| 页面 | 路由 | 功能说明 |
|-----|------|---------|
| **登录** | `/login` | 用户登录 |
| **测试** | `/test` | 测试页面（无需登录） |

---

## 路由配置

### 路由守卫

系统实现了完整的路由权限控制：

```javascript
router.beforeEach((to, from, next) => {
  const user = sessionStorage.getItem('user') ? JSON.parse(sessionStorage.getItem('user')) : null
  
  // 测试页面和登录页面无需登录
  if (to.path === '/test' || to.path === '/login') {
    next()
    return
  }
  
  // 需要登录的页面
  if (!user) {
    next('/login')
    return
  }
  
  // 权限校验
  const isAdmin = user.role === 'admin'
  const isAdminRoute = to.path.startsWith('/admin')
  const isUserRoute = to.path.startsWith('/user')
  
  // 管理员访问管理员路由
  if (isAdminRoute && isAdmin) {
    next()
    return
  }
  
  // 用户访问用户路由
  if (isUserRoute && !isAdmin) {
    next()
    return
  }
  
  // 重定向到对应角色的首页
  next(isAdmin ? '/admin' : '/user')
})
```

### 路由结构

```
/                           → 重定向到 /login
/login                      → 登录页面
/test                       → 测试页面
/user                       → 用户端仪表盘
/user/upload                → 视频上传
/user/history               → 检测历史
/user/alerts                → 个人告警
/user/ai-assistant          → AI助手
/user/profile               → 个人中心
/user/camera                → 摄像头监控
/user/cameras               → 摄像头管理
/admin                      → 管理员仪表盘
/admin/users                → 用户管理
/admin/cameras              → 摄像头管理（仅显示信息）
/admin/statistics           → 统计分析
/admin/alerts               → 告警管理
/admin/settings             → 系统设置
/admin/ai-assistant         → 管理员AI助手
```

---

## 状态管理

### Pinia Store

系统使用 Pinia 管理全局状态：

```javascript
// src/stores/detection.js
import { defineStore } from 'pinia'

export const useDetectionStore = defineStore('detection', {
  state: () => ({
    currentUser: null,
    detectionResults: [],
    alerts: [],
    statistics: {},
    isLoading: false
  }),
  
  actions: {
    setUser(user) {
      this.currentUser = user
      sessionStorage.setItem('user', JSON.stringify(user))
    },
    
    clearUser() {
      this.currentUser = null
      sessionStorage.removeItem('user')
    },
    
    setDetectionResults(results) {
      this.detectionResults = results
    },
    
    setAlerts(alerts) {
      this.alerts = alerts
    },
    
    setStatistics(stats) {
      this.statistics = stats
    }
  },
  
  getters: {
    isAdmin: (state) => state.currentUser?.role === 'admin',
    hasAlerts: (state) => state.alerts.length > 0
  }
})
```

---

## API 调用配置

### Axios 配置

前端使用 Axios 与后端 API 进行通信：

```javascript
import axios from 'axios'

// 创建 axios 实例
const api = axios.create({
  baseURL: 'http://localhost:5000/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json;charset=utf-8'
  }
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    const user = sessionStorage.getItem('user')
    if (user) {
      // 可在此添加认证信息
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => response.data,
  error => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)
```

### 主要 API 调用

| API 端点 | 方法 | 说明 |
|---------|------|-----|
| `/api/user/login` | POST | 用户登录 |
| `/api/user/register` | POST | 用户注册 |
| `/api/detect/file` | POST | 视频检测 |
| `/api/detect` | POST | 实时图像检测 |
| `/api/history` | GET | 获取检测历史 |
| `/api/alerts` | GET | 获取告警列表 |
| `/api/ai/chat` | POST | AI对话 |
| `/api/statistics` | GET | 获取统计数据 |
| `/api/video/stream/{filename}` | GET | 视频流式播放 |

---

## 核心功能

### 1. 用户认证

- 支持用户名/密码登录
- 角色区分（用户/管理员）
- 登录状态持久化（sessionStorage）

### 2. 视频检测

- 支持视频文件上传
- 实时显示检测进度
- 展示检测结果和告警信息
- 支持检测视频回放

### 3. 实时监控

- 摄像头列表管理
- 实时视频预览（仅用户端）
- 跌倒检测告警推送

### 4. 告警管理

- 告警列表展示
- 告警确认功能
- 告警统计分析

### 5. AI智能助手

- 自然语言对话
- 风险分析报告
- 检测结果解读

### 6. 数据统计

- 检测记录统计
- 告警趋势分析
- 用户行为分析

---

## 权限控制

### 用户端权限

| 功能 | 权限 | 说明 |
|-----|------|-----|
| 查看个人摄像头 | ✅ | 可查看自己创建的摄像头 |
| 查看摄像头实时视频 | ✅ | 可查看自己摄像头的实时视频 |
| 上传视频检测 | ✅ | 可上传视频进行检测 |
| 查看个人检测历史 | ✅ | 可查看自己的检测记录 |
| 查看个人告警 | ✅ | 可查看自己的告警通知 |

### 管理员端权限

| 功能 | 权限 | 说明 |
|-----|------|-----|
| 查看所有用户 | ✅ | 可查看系统所有用户 |
| 查看所有摄像头 | ✅ | 可查看所有摄像头信息 |
| 查看摄像头实时视频 | ❌ | **不可查看**实时视频，仅显示摄像头信息 |
| 管理用户 | ✅ | 可管理系统用户 |
| 查看全局告警 | ✅ | 可查看所有告警 |
| 系统设置 | ✅ | 可配置系统参数 |

---

## 界面设计

### 布局结构

```
┌──────────────────────────────────────────────┐
│  ┌──────────────┐  ┌──────────────────────┐  │
│  │   Logo       │  │       顶部导航        │  │
│  │   侧边栏     │  │   (面包屑/用户信息)   │  │
│  │   菜单       │  ├──────────────────────┤  │
│  │              │  │                      │  │
│  │              │  │      主内容区域       │  │
│  │              │  │                      │  │
│  │              │  │                      │  │
│  └──────────────┘  └──────────────────────┘  │
└──────────────────────────────────────────────┘
```

### 颜色主题

| 元素 | 颜色 |
|-----|------|
| 主色调 | #409EFF |
| 成功 | #67C23A |
| 警告 | #E6A23C |
| 危险 | #F56C6C |
| 信息 | #909399 |

---

## 构建配置

### Vite 配置

```javascript
// vite.config.js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true
      }
    }
  }
})
```

---

## 开发规范

### 组件命名

- 页面组件：`PascalCase.vue`（如 `UserDashboard.vue`）
- 布局组件：`PascalCaseLayout.vue`（如 `UserLayout.vue`）
- 通用组件：`PascalCase.vue`

### 代码风格

- 使用 ES6+ 语法
- 使用 Composition API
- 变量命名：`camelCase`
- 组件命名：`PascalCase`
- 常量命名：`UPPER_CASE`

### 注释规范

- 组件注释：描述组件功能
- 方法注释：描述方法作用、参数、返回值
- 复杂逻辑注释：解释业务逻辑

---

## 部署说明

### 开发环境

```bash
# 启动前端开发服务器
npm run dev

# 启动后端服务（需在 back 目录执行）
python app.py
```

### 生产环境

```bash
# 构建前端
npm run build

# 将 dist 目录部署到静态服务器
# 推荐使用 Nginx 作为反向代理
```

### Nginx 配置示例

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # 前端静态文件
    location / {
        root /path/to/frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }
    
    # API 代理
    location /api {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 注意事项

1. **跨域配置**：确保后端服务配置了正确的 CORS 策略
2. **端口配置**：前端默认端口为 3000，后端默认端口为 5000
3. **管理员权限**：管理员端无法查看摄像头实时视频，仅显示摄像头信息
4. **登录状态**：登录状态存储在 sessionStorage，关闭浏览器后需要重新登录
5. **视频播放**：检测结果视频使用流式播放，需要后端支持 HTTP Range 请求

---

## 技术特点

1. **Vue 3 Composition API**：使用现代化的组合式 API
2. **Element Plus**：美观的 UI 组件库
3. **Pinia**：轻量级状态管理
4. **响应式设计**：支持多种屏幕尺寸
5. **权限控制**：完整的角色权限管理
6. **模块化架构**：清晰的代码组织结构