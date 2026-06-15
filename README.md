# 基于深度学习的人体姿势跌倒检测系统

---

# 目 录

[1 问题描述](#1-问题描述)

[1.1 功能描述](#11-功能描述)

[1.2 性能描述](#12-性能描述)

[2 方案描述](#2-方案描述)

[2.1 研究背景](#21-研究背景)

[2.2 国内外研究现状](#22-国内外研究现状)

[2.3 技术路线](#23-技术路线)

[3 项目设计](#3-项目设计)

[3.1 软件结构设计](#31-软件结构设计)

[3.2 关键算法设计](#32-关键算法设计)

[3.3 数据库设计](#33-数据库设计)

[3.4 接口设计](#34-接口设计)

[4 项目实现](#4-项目实现)

[4.1 系统架构实现](#41-系统架构实现)

[4.2 跌倒检测模块](#42-跌倒检测模块)

[4.3 AI智能助手模块](#43-ai智能助手模块)

[4.4 会话管理模块](#44-会话管理模块)

[4.5 视频处理模块](#45-视频处理模块)

[5 项目测试](#5-项目测试)

[5.1 功能测试](#51-功能测试)

[5.2 性能测试](#52-性能测试)

[5.3 界面测试](#53-界面测试)

[6 项目总结](#6-项目总结)

[6.1 项目成果](#61-项目成果)

[6.2 经验与体会](#62-经验与体会)

[6.3 改进方向](#63-改进方向)

[7 参考文献](#7-参考文献)

---

# 1 问题描述

## 1.1 功能描述

### 1.1.1 项目背景

随着人口老龄化趋势加剧，老年人居家安全问题日益突出。据统计，跌倒是65岁以上老年人伤害死亡的首要原因，全球每年约有68万人死于跌倒。在中国，跌倒已成为老年人意外伤害死亡的主要原因之一，给家庭和社会带来沉重负担。

传统的跌倒检测方法主要依赖人工监护或可穿戴设备，存在成本高、用户体验差、覆盖率低等问题。基于计算机视觉的自动跌倒检测系统能够实时分析监控视频，自动识别跌倒事件并及时报警，具有非侵入式、成本低、覆盖广等优势。

### 1.1.2 系统目标

本项目旨在开发一个基于深度学习的人体姿势跌倒检测系统，主要目标包括：

1. **实时视频监控与分析**：支持多摄像头实时监控，实时检测跌倒事件
2. **视频文件离线分析**：用户可上传视频文件进行离线分析
3. **智能告警机制**：采用三重检测机制，自动识别跌倒并记录告警
4. **用户分级管理**：支持管理员和普通用户两种角色
5. **AI智能助手**：集成Ollama本地大模型，提供智能问答和数据分析
6. **多会话对话管理**：支持多轮对话，历史记录持久化存储

### 1.1.3 系统功能模块

**（1）用户管理模块**

- 用户注册与登录
- 用户信息管理（查看、修改个人资料）
- 角色权限控制（普通用户、管理员）
- 用户会话管理

**（2）视频分析模块**

- 视频文件上传（支持拖拽上传）
- 多种视频格式支持（MP4、AVI、MOV等）
- 快速检测模式和精确检测模式
- 检测参数配置（显示标签、检测框等）
- 分析进度实时显示

**（3）跌倒检测模块**

- 基于深度学习的人体姿态估计
- 时序行为识别（站立、坐下、躺卧、弯腰、爬行等）
- 三重跌倒判定规则（M1重心下降、M2身体倾斜、M3轮廓变形）
- 骨骼可视化标注
- 检测结果视频输出

**（4）告警管理模块**

- 跌倒告警自动生成
- 告警列表展示（按时间、类型筛选）
- 告警确认与处理
- 告警历史查询
- 告警统计分析

**（5）AI智能助手模块**

- 基于Ollama本地大模型的对话系统
- 多会话管理（创建、切换、删除）
- 对话历史持久化存储
- 系统数据分析与建议
- 跌倒事件原因分析

**（6）实时监控模块**

- RTSP摄像头连接与管理
- 实时视频流处理
- 实时跌倒检测
- 实时预警推送

**（7）数据统计模块**

- 检测数据统计
- 告警数据统计
- 用户活跃度统计
- 可视化图表展示

**（8）系统设置模块（管理员）**

- Ollama模型配置
- 检测参数调整
- 用户管理（增删改查）
- 系统配置管理

## 1.2 性能描述

### 1.2.1 检测性能

| 性能指标             | 目标值   | 说明                       |
| -------------------- | -------- | -------------------------- |
| 检测速度（快速模式） | ≥20 FPS | 每秒处理帧数               |
| 检测速度（精确模式） | ≥5 FPS  | 每秒处理帧数               |
| 检测准确率           | ≥95%    | 跌倒正确识别率             |
| 误报率               | ≤5%     | 正常行为误判为跌倒的比例   |
| 漏报率               | ≤3%     | 跌倒未被检测到的比例       |
| 告警延迟             | ≤1秒    | 从跌倒发生到告警发出的时间 |

### 1.2.2 系统性能

| 性能指标     | 目标值  | 说明                   |
| ------------ | ------- | ---------------------- |
| API响应时间  | ≤500ms | 除视频分析外的API请求  |
| 视频上传速度 | ≥5MB/s | 网络环境允许的情况下   |
| 最大并发用户 | ≥10    | 同时使用系统的用户数   |
| 最大视频文件 | 500MB   | 支持的最大上传文件大小 |
| 页面加载时间 | ≤2秒   | 首页完整加载时间       |
| 系统可用性   | ≥99%   | 系统正常运行时间比例   |

### 1.2.3 兼容性要求

- **浏览器支持**：Chrome、Firefox、Edge、Safari等现代浏览器
- **操作系统支持**：Windows、macOS、Linux
- **数据库支持**：MySQL 5.7及以上
- **Python版本**：Python 3.8及以上
- **视频编码支持**：H.264、H.265、VP9等

---

# 2 方案描述

## 2.1 研究背景

### 2.1.1 跌倒检测技术概述

跌倒检测技术主要分为三类：**基于可穿戴设备的方法**、**基于环境传感器的方法**和**基于视觉的方法**。

**（1）基于可穿戴设备的方法**

通过在人体穿戴的设备（如手表、手环、腰带等）中集成加速度计、陀螺仪等传感器，检测人体的运动状态和姿态变化。这种方法准确率较高，但需要用户随身携带设备，可能影响用户体验，且无法覆盖未佩戴设备的情况。

**（2）基于环境传感器的方法**

利用压力传感器、红外传感器、雷达等设备检测人体存在和运动状态。这种方法不需要用户佩戴设备，但传感器覆盖范围有限，需要在家中安装多个传感器，成本较高且隐私性较差。

**（3）基于视觉的方法**

通过摄像头采集视频图像，利用计算机视觉和深度学习技术分析人体姿态，检测跌倒事件。这种方法具有非侵入式、成本低、覆盖广等优势，是当前研究的热点方向。

### 2.1.2 深度学习在行为识别中的应用

深度学习在人体行为识别领域取得了显著成果，主要方法包括：

**（1）卷积神经网络（CNN）**

CNN能够自动学习图像的空间特征，在图像分类、目标检测等任务中表现优异。在行为识别中，CNN可以用于提取单帧图像中的人体特征。

**（2）循环神经网络（RNN）**

RNN及其变体（LSTM、GRU）具有时序建模能力，能够处理视频中的时间序列信息。在行为识别中，RNN可以学习人体姿态随时间变化的规律。

**（3）时空图卷积网络（ST-GCN）**

ST-GCN将人体骨骼关键点建模为图结构，利用图卷积操作同时学习空间和时间特征，在行为识别任务中取得了state-of-the-art的效果。

**（4）3D卷积网络（C3D、I3D）**

3D卷积网络通过三维卷积操作同时提取视频的时空特征，能够有效捕捉动作的动态信息。

## 2.2 国内外研究现状

### 2.2.1 传统方法

早期的跌倒检测方法主要基于背景建模和运动分析：

1. **背景减除法**：通过建立背景模型，将运动前景从背景中分离出来，分析运动目标的形状、速度等特征判断是否跌倒。
2. **光流法**：计算视频序列中像素的运动矢量，分析运动方向和速度的变化模式。
3. **形状分析**：分析人体轮廓的形状变化，如宽高比、轮廓面积等指标。

这些方法简单直观，但受环境影响较大，难以处理遮挡、阴影等情况。

### 2.2.2 基于深度学习的方法

近年来，深度学习方法在跌倒检测领域取得了显著进展：

1. **Two-Stream网络**：利用双流网络分别处理空间和时间信息，融合RGB图像和光流图像进行动作识别。
2. **姿态估计+规则判断**：首先利用OpenPose等姿态估计网络提取人体骨骼关键点，然后根据关键点位置变化判断是否跌倒。
3. **时序模型**：利用LSTM、GRU等网络学习视频序列的时序特征，实现端到端的跌倒检测。
4. **注意力机制**：引入时空注意力机制，使模型能够关注视频中的关键帧和关键区域，提高检测准确率。

### 2.2.3 相关论文算法分析

本系统采用的算法基于论文《基于深度学习的人体姿势跌倒检测算法》，该算法的主要思想是：

1. **多特征融合**：综合考虑人体重心变化、身体倾斜角度、轮廓形状变化三个维度的特征。
2. **时序分析**：通过分析连续多帧的特征变化，判断人体运动状态。
3. **规则判决**：结合深度学习模型的输出和预设的规则，判断是否发生跌倒。

这种方法能够有效降低误报率，提高检测的准确性。

## 2.3 技术路线

### 2.3.1 系统架构选择

系统采用**前后端分离架构**，前端使用Vue3框架构建单页应用，后端使用Flask框架提供RESTful API服务，数据库采用MySQL存储结构化数据。

这种架构的优势包括：

1. **前后端解耦**：前端和后端独立开发、测试和部署
2. **良好的用户体验**：单页应用可以实现流畅的页面切换和交互
3. **易于扩展**：可以通过增加后端实例轻松实现水平扩展
4. **技术灵活性**：前端和后端可以根据需求选择最合适的技术栈

### 2.3.2 技术栈介绍

**后端技术栈**：

| 技术       | 版本   | 用途         |
| ---------- | ------ | ------------ |
| Python     | 3.8+   | 编程语言     |
| Flask      | 2.3+   | Web框架      |
| SQLAlchemy | 3.0+   | ORM工具      |
| MySQL      | 5.7+   | 关系数据库   |
| PyTorch    | 2.0+   | 深度学习框架 |
| OpenCV     | 4.8+   | 计算机视觉   |
| FFmpeg     | latest | 视频处理     |
| Ollama     | latest | 本地大模型   |

**前端技术栈**：

| 技术         | 版本 | 用途       |
| ------------ | ---- | ---------- |
| Vue          | 3.4+ | 前端框架   |
| Vite         | 5.0+ | 构建工具   |
| Vue Router   | 4.0+ | 路由管理   |
| Element Plus | 2.6+ | UI组件库   |
| ECharts      | 5.5+ | 数据可视化 |
| Axios        | 1.6+ | HTTP客户端 |

### 2.3.3 系统架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          客户端层（Browser）                             │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Vue3 SPA + Element Plus + ECharts + 响应式布局                   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                    ↑                    ↑                    ↑         │
│                    │                    │                    │         │
│              用户端路由            管理员端路由           API代理       │
└────────────────────┼────────────────────┼────────────────────┼─────────┘
                     │                    │                    │
┌────────────────────▼────────────────────▼────────────────────▼─────────┐
│                          应用服务层（Flask）                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │  用户管理API │  │  视频分析API │  │  告警管理API │  │ AI助手API  │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └────────────┘ │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │ 会话管理API  │  │ 摄像头管理API│  │ 系统配置API  │  │ 统计API   │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └────────────┘ │
└────────────────────────────┬───────────────────────────────────────────┘
                             │
┌────────────────────────────▼───────────────────────────────────────────┐
│                          数据处理层                                    │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────────────┐    │
│  │ FallDetector   │  │ AIAgent        │  │ VideoProcessor         │    │
│  │ (PyTorch+CV)   │  │ (Ollama)       │  │ (OpenCV+FFmpeg)        │    │
│  └────────────────┘  └────────────────┘  └────────────────────────────┘    │
└────────────────────────────┬───────────────────────────────────────────┘
                             │
┌────────────────────────────▼───────────────────────────────────────────┐
│                           数据存储层                                    │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────────────┐      │
│  │ MySQL          │  │ File System    │  │ Session Storage        │      │
│  │ (结构化数据)    │  │ (uploads/outputs)│ │ (对话历史)            │      │
│  └────────────────┘  └────────────────┘  └────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
```

---

# 3 项目设计

## 3.1 软件结构设计

### 3.1.1 项目目录结构

```
falldown/
│
├── back/                              # 后端服务根目录
│   ├── app.py                         # Flask应用主文件
│   ├── config.py                      # 配置文件
│   ├── ai_agent.py                    # AI智能体实现
│   ├── migrate_db.py                  # 数据库迁移脚本
│   ├── check_db.py                   # 数据库检查脚本
│   ├── .env                           # 环境变量配置
│   │
│   ├── finallmodel/                   # 深度学习模型目录
│   │   ├── model/
│   │   │   ├── __init__.py
│   │   │   ├── fall_detector.py      # 跌倒检测器
│   │   │   ├── gru_model.py          # GRU行为识别模型
│   │   │   ├── pose_estimator.py     # 姿态估计模块
│   │   │   └── utils.py              # 工具函数
│   │   │
│   │   ├── checkpoints/              # 模型权重文件
│   │   │   └── best_gru.pt          # 训练好的GRU模型
│   │   │
│   │   ├── dataset/                  # 数据集目录
│   │   │   ├── test/                 # 测试数据
│   │   │   └── label.txt             # 标签定义
│   │
│   ├── uploads/                       # 用户上传文件存储
│   └── outputs/                      # 检测结果输出存储
│
└── frontend/                          # 前端应用根目录
    ├── src/
    │   ├── main.js                   # Vue应用入口
    │   ├── App.vue                   # 根组件
    │   ├── style.css                 # 全局样式
    │   │
    │   ├── router/
    │   │   └── index.js              # 路由配置
    │   │
    │   ├── stores/
    │   │   └── detection.js         # 状态管理
    │   │
    │   ├── layout/
    │   │   ├── AdminLayout.vue       # 管理员布局
    │   │   └── UserLayout.vue        # 用户布局
    │   │
    │   └── views/                    # 页面组件
    │       ├── Login.vue             # 登录页
    │       ├── Dashboard.vue         # 仪表盘
    │       ├── Upload.vue           # 视频上传
    │       ├── VideoAnalysis.vue     # 视频分析
    │       ├── Alerts.vue           # 告警中心
    │       ├── Statistics.vue        # 数据统计
    │       ├── Settings.vue         # 系统设置
    │       ├── DetectionHistory.vue # 检测历史
    │       ├── Cameras.vue          # 摄像头管理
    │       │
    │       ├── admin/               # 管理员端页面
    │       │   ├── AdminDashboard.vue
    │       │   ├── AdminUsers.vue
    │       │   ├── AdminStatistics.vue
    │       │   ├── AdminAlerts.vue
    │       │   ├── AdminSettings.vue
    │       │   ├── AdminCameras.vue
    │       │   └── AdminAIAssistant.vue
    │       │
    │       └── user/                # 用户端页面
    │           ├── UserDashboard.vue
    │           ├── UserUpload.vue
    │           ├── UserHistory.vue
    │           ├── UserAlerts.vue
    │           ├── UserAIAssistant.vue
    │           ├── UserProfile.vue
    │           ├── UserCamera.vue
    │           └── UserCameraManage.vue
    │
    ├── public/                      # 静态资源
    ├── dist/                        # 构建输出目录
    ├── index.html                   # HTML入口
    ├── package.json                 # 项目依赖
    └── vite.config.js              # Vite配置
```

### 3.1.2 模块划分

系统按照功能划分为以下主要模块：

**（1）用户认证模块（Authentication）**

- 功能：处理用户登录、登出、权限验证
- 核心类/函数：`login()`, `logout()`, `validate_token()`
- 依赖关系：被所有需要认证的API调用

**（2）视频处理模块（Video Processing）**

- 功能：视频上传、格式转换、流式播放支持
- 核心类/函数：`upload_file()`, `fix_mp4_for_streaming()`, `stream_video()`
- 依赖关系：依赖FFmpeg、OpenCV

**（3）跌倒检测模块（Fall Detection）**

- 功能：人体姿态估计、行为识别、跌倒判定
- 核心类/函数：`FallDetector`, `detect_video()`, `detect_frame()`
- 依赖关系：依赖PyTorch、OpenCV

**（4）告警管理模块（Alert Management）**

- 功能：告警生成、记录、确认、查询
- 核心类/函数：`get_alerts()`, `acknowledge_alert()`, `clear_alerts()`
- 依赖关系：依赖数据库

**（5）AI智能体模块（AI Agent）**

- 功能：Ollama模型调用、对话生成、数据分析
- 核心类/函数：`AIAgent`, `chat()`, `analyze_batch()`, `get_system_analysis()`
- 依赖关系：依赖Ollama服务

**（6）会话管理模块（Session Management）**

- 功能：对话会话创建、切换、删除、历史记录
- 核心类/函数：`get_sessions()`, `create_session()`, `get_session_history()`
- 依赖关系：依赖数据库

**（7）统计分析模块（Statistics）**

- 功能：数据统计、图表生成
- 核心类/函数：`get_statistics()`, `get_daily_stats()`
- 依赖关系：依赖数据库

### 3.1.3 模块调用关系图

```
┌──────────────────────────────────────────────────────────────────────┐
│                          前端应用层                                   │
│   Vue3 + Element Plus + ECharts + Axios                             │
└───────────────────────────────┬──────────────────────────────────────┘
                                │ HTTP Request
┌───────────────────────────────▼──────────────────────────────────────┐
│                          API网关层                                    │
│                    Flask RESTful API                                  │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────┐    ┌──────────────────┐    ┌───────────────┐ │
│  │  用户认证模块     │    │  视频处理模块    │    │  告警管理模块 │ │
│  │                  │    │                  │    │               │ │
│  │  login/logout    │    │  upload/stream  │    │  get/ack      │ │
│  └────────┬─────────┘    └────────┬─────────┘    └───────┬───────┘ │
│           │                       │                      │         │
│           └───────────────────────┼──────────────────────┘         │
│                                   │                                    │
│  ┌──────────────────┐    ┌────────▼─────────┐    ┌───────────────┐ │
│  │  会话管理模块     │◄──►│  AI智能体模块   │◄──►│  统计分析模块 │ │
│  │                  │    │                  │    │               │ │
│  │  session/history │    │  chat/analyze   │    │  stats/chart  │ │
│  └──────────────────┘    └────────┬─────────┘    └───────────────┘ │
│                                   │                                    │
│                          ┌────────▼─────────┐                          │
│                          │  跌倒检测模块    │                          │
│                          │                  │                          │
│                          │  detect_video   │                          │
│                          └────────┬─────────┘                          │
└───────────────────────────────────┼───────────────────────────────────┘
                                    │
┌───────────────────────────────────▼───────────────────────────────────┐
│                          数据存储层                                    │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐  │
│  │     MySQL       │    │   File System   │    │     Ollama      │  │
│  │                 │    │                 │    │                 │  │
│  │  users/alerts   │    │  uploads/       │    │   qwen3:1.7b    │  │
│  │  sessions/history│    │  outputs       │    │                 │  │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
```

## 3.2 关键算法设计

### 3.2.1 跌倒检测算法原理

本系统采用的跌倒检测算法基于论文《基于深度学习的人体姿势跌倒检测算法》，采用**多特征融合+规则判决**的方法，综合考虑三个维度的特征进行跌倒判定。

#### 3.2.1.1 M1 - 重心下降检测（CGDD）

**算法原理**：

人体在站立状态时，重心位于身体中上部；当发生跌倒时，重心会快速下移。通过跟踪人体重心的垂直位置变化，可以检测是否发生跌倒。CGDD（Center of Gravity Descent Detection）核心是计算重心下降速度。

**计算方法**：

1. 提取人体骨骼关键点，使用髋部中心点作为重心近似位置
2. 计算当前帧与历史帧的重心位置差：

$$
v_{cg} = \frac{|y_{t} - y_{t-\Delta t}|}{\Delta t}
$$

3. 帧间隔 $\Delta t$ = 5帧（约0.25秒，假设帧率20FPS）
4. 跌倒判定：当 $v_{cg} \geq V_{critical}$ 时，M1标志位置为True

**阈值参数**：

| 参数                     | 值        | 说明                           |
| ------------------------ | --------- | ------------------------------ |
| 帧间隔$\Delta t$       | 5帧       | 每5帧检测一次                  |
| 速度阈值$V_{critical}$ | 0.009 m/s | 重心下降速度阈值（论文标准值） |
| 时间间隔                 | 0.25秒    | 相邻检测点的时间差             |

**核心代码实现**（[fall_detector.py](file:///d:/falldown/back/finallmodel/model/fall_detector.py)）：

```python
def cgdd_check(self, frame_interval: int = 5) -> Tuple[bool, float]:
    """
    CGDD - 重心下降检测 (Center of Gravity Descent Detection)
    论文算法：检测间隔设置为每5个相邻帧检测1次，时间间隔约为0.25秒
    """
    if len(self.frame_history) < frame_interval + 1:
        return False, 0.0

    # 使用当前帧和frame_interval帧前的帧进行比较
    joints1 = self.frame_history[-frame_interval - 1]
    joints2 = self.frame_history[-1]

    cg1 = self.calculate_center_of_gravity(joints1)
    cg2 = self.calculate_center_of_gravity(joints2)

    # 使用实际帧率计算时间间隔（秒）
    delta_t = frame_interval / self.fps if self.fps > 0 else 0.033 * frame_interval
  
    # 计算重心下降速度（像素/秒）
    speed_px = abs(cg2[1] - cg1[1]) / delta_t
  
    # 转换为米/秒（假设图像高度约为1米）
    speed_mps = speed_px * 0.001

    triggered = speed_mps >= self.V_CRITICAL  # 0.009 m/s
    return triggered, speed_mps
```

#### 3.2.1.2 M2 - 身体倾斜检测（BTD）

**算法原理**：

人体在正常站立或坐着时，身体基本保持垂直状态；当发生跌倒时，身体会明显倾斜。BTD（Body Tilt Detection）通过计算身体中轴线与垂直方向的夹角来判断倾斜程度。角度越小表示身体越接近水平（跌倒状态）。

**计算方法**：

1. 获取头部关键点和腿部中心关键点
2. 计算身体倾斜向量 $\vec{v}_{body} = (x_{head} - x_{leg}, y_{head} - y_{leg})$
3. 计算与垂直方向的夹角：

$$
\theta = \arctan\left(\frac{dx}{dy}\right) \times \frac{180}{\pi}
$$

其中 $dx = |x_{head} - x_{leg}|$，$dy = |y_{head} - y_{leg}|$

4. 跌倒判定：当 $\theta < \theta_{cr}$ 时，M2标志位置为True（角度小于阈值表示身体接近水平）

**阈值参数**：

| 参数                          | 值                | 说明                             |
| ----------------------------- | ----------------- | -------------------------------- |
| 角度阈值$\theta_{critical}$ | 45°              | 身体倾斜角度阈值                 |
| 判定条件                      | $\theta < 45°$ | 小于阈值表示接近水平（跌倒状态） |

**核心代码实现**（[fall_detector.py](file:///d:/falldown/back/finallmodel/model/fall_detector.py)）：

```python
def btd_check(self, joints: JointPoints) -> Tuple[bool, float]:
    """
    BTD - 身体倾斜检测 (Body Tilt Detection)
    """
    head = joints.head
    leg_center = self.calculate_leg_center(joints)  # 膝盖和脚踝的中点

    dx = abs(head[0] - leg_center[0])
    dy = abs(head[1] - leg_center[1])

    if dx < 1e-6:
        angle = 90.0
    else:
        angle = math.degrees(math.atan(dy / dx))

    # 角度越小表示越水平（跌倒状态）
    triggered = angle < self.THETA_CRITICAL  # 45°
    return triggered, angle
```

#### 3.2.1.3 M3 - 轮廓变形检测（SCDD）

**算法原理**：

人体在站立状态时，轮廓呈"高瘦"形状（高度远大于宽度）；当跌倒在地时，轮廓变成"矮胖"形状（宽度接近或超过高度）。SCDD（Shape Contour Deformation Detection）通过分析人体外接矩形的宽高比来判断轮廓变形程度。

**计算方法**：

1. 使用所有有效关节点计算外接矩形bbox
2. 计算宽高比：

$$
p = \frac{w}{h}
$$

其中 $w$ 为外接矩形宽度，$h$ 为外接矩形高度

3. 跌倒判定：当 $p > p_{cr}$ 时，M3标志位置为True

**阈值参数**：

| 参数                     | 值          | 说明                           |
| ------------------------ | ----------- | ------------------------------ |
| 比例阈值$p_{critical}$ | 1.0         | 宽高比阈值                     |
| 判定条件                 | $p > 1.0$ | 宽度大于高度时触发（倒地状态） |

**核心代码实现**（[fall_detector.py](file:///d:/falldown/back/finallmodel/model/fall_detector.py)）：

```python
def scdd_check(self, bbox: Tuple[int, int, int, int]) -> Tuple[bool, float]:
    """
    SCDD - 外形轮廓变形检测 (Shape Contour Deformation Detection)
    """
    xmin, ymin, xmax, ymax = bbox
    width = xmax - xmin
    height = ymax - ymin

    if height < 1e-6:
        ratio = 0
    else:
        ratio = width / height

    triggered = ratio > self.P_CRITICAL  # 1.0
    return triggered, ratio
```

#### 3.2.1.4 综合判定规则

**判定条件**：

论文严格规定：三个条件**同时满足**才判定为跌倒

| 条件 | 标识 | 阈值                      | 说明             |
| ---- | ---- | ------------------------- | ---------------- |
| CGDD | M1   | $v_{cg} \geq 0.009$ m/s | 重心下降速度达标 |
| BTD  | M2   | $\theta < 45°$         | 身体倾斜角度达标 |
| SCDD | M3   | $p > 1.0$               | 宽高比达标       |

**判定逻辑**：

| M1       | M2 | M3 | 判定结果       | 触发条件         |
| -------- | -- | -- | -------------- | ---------------- |
| ✓       | ✓ | ✓ | **跌倒** | 三个条件同时满足 |
| ✓       | ✓ | ✗ | 正常活动       | 身体前倾但未倒地 |
| ✓       | ✗ | ✓ | 正常活动       | 下蹲动作         |
| ✗       | ✓ | ✓ | 正常活动       | 倾斜靠靠         |
| 其他组合 | -  | -  | 正常活动       | 未满足跌倒条件   |

**核心逻辑**：论文采用严格的**AND**运算，必须是 $M1 \cap M2 \cap M3$ 三个条件同时触发才判定为跌倒。这种设计显著降低了误报率。

**核心代码实现**（[fall_detector.py](file:///d:/falldown/back/finallmodel/model/fall_detector.py)）：

```python
class FallDetectionAlgorithm:
    """
    跌倒检测算法 - 论文参数:
    - V_CRITICAL: 0.009 m/s (重心下降速度阈值)
    - THETA_CRITICAL: 45° (身体倾斜角度阈值)
    - P_CRITICAL: 1.0 (宽高比阈值)
    - T_CRITICAL: 10秒 (跌倒后报警延迟时间)
    """
    V_CRITICAL = 0.009
    THETA_CRITICAL = 45
    P_CRITICAL = 1.0
    T_CRITICAL = 10

    def detect(self, frame: np.ndarray, joints: JointPoints) -> DetectionResult:
        """执行跌倒检测 - 三个条件都满足才判定为跌倒"""
        self.frame_idx += 1
      
        # 更新帧历史
        self.frame_history.append(joints)
        if len(self.frame_history) > self.history_size:
            self.frame_history.pop(0)
      
        # 计算边界框（使用所有有效关节点）
        points = joints.to_list()
        x_coords = [p[0] for p in points if p[0] > 0]
        y_coords = [p[1] for p in points if p[1] > 0]
        bbox = (min(x_coords), min(y_coords), max(x_coords), max(y_coords))

        # 执行三重检测
        cgdd_triggered, cg_speed = self.cgdd_check(5)
        btd_triggered, tilt_angle = self.btd_check(joints)
        scdd_triggered, contour_ratio = self.scdd_check(bbox)

        # 三个条件都满足才判定为跌倒
        is_fall = cgdd_triggered and btd_triggered and scdd_triggered

        # 更新跌倒历史用于计算置信度
        self.fall_history.append(1 if is_fall else 0)
        if len(self.fall_history) > 30:
            self.fall_history.pop(0)

        confidence = sum(self.fall_history) / len(self.fall_history)
        return DetectionResult(is_fall=is_fall, ...)
```

**告警延迟机制**：

为避免误报，系统采用延迟确认机制：

| 参数                     | 值   | 说明                     |
| ------------------------ | ---- | ------------------------ |
| 延迟时间$T_{critical}$ | 10秒 | 跌倒后需要保持状态的时间 |
| 历史窗口大小             | 30帧 | 用于计算置信度的历史帧数 |

**处理流程**：

1. 当检测到 $M1 \cap M2 \cap M3$ 满足时，记录首次触发帧
2. 如果连续10秒内状态一直保持跌倒特征，则发出正式告警
3. 如果10秒内状态恢复（任一条件不满足），则取消告警（视为正常活动如蹲下、系鞋带等）
4. 置信度计算：取最近30帧中跌倒帧数占比作为置信度

### 3.2.2 行为识别模型

#### 3.2.2.1 模型架构

系统采用**双向GRU（门控循环单元）**网络进行时序行为识别，模型名称为FallActionGRU。

**核心代码实现**（[network.py](file:///d:/falldown/back/finallmodel/model/network.py)）：

```python
import torch
import torch.nn as nn


class FallActionGRU(nn.Module):
    def __init__(self, input_size: int, hidden_size: int, num_layers: int, 
                 num_classes: int, dropout: float):
        super().__init__()
        # 双向GRU层
        self.gru = nn.GRU(
            input_size=input_size,      # 69维特征向量
            hidden_size=hidden_size,    # 128隐藏层维度
            num_layers=num_layers,      # 2层GRU堆叠
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
            bidirectional=True,         # 双向GRU
        )
        # 分类头
        self.cls = nn.Sequential(
            nn.LayerNorm(hidden_size * 2),      # 双向输出需×2
            nn.Linear(hidden_size * 2, hidden_size),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout),
            nn.Linear(hidden_size, num_classes),  # 7类行为
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """前向传播: [batch, seq_len, 69] -> [batch, 7]"""
        out, _ = self.gru(x)          # [batch, seq_len, 256]
        last = out[:, -1, :]          # 取最后时刻输出 [batch, 256]
        return self.cls(last)         # [batch, 7]
```

**模型输入输出**：

| 项目         | 规格 | 说明                                                        |
| ------------ | ---- | ----------------------------------------------------------- |
| 输入序列长度 | 24帧 | 连续24帧作为一个处理序列                                    |
| 最小序列长度 | 8帧  | 少于8帧时不进行识别                                         |
| 特征向量维度 | 69维 | 33关键点×2坐标 + 3额外特征                                 |
| 行为类别数   | 7类  | empty, standing, sitting, lying, bending, crawling, falling |

**特征向量构成（69维）**：

| 特征段         | 维度           | 内容                         |
| -------------- | -------------- | ---------------------------- |
| 33关键点坐标   | 66维           | 33个关键点的(x, y)归一化坐标 |
| 重心Y坐标      | 1维            | 髋部中心Y坐标（归一化）      |
| 身体倾斜角度   | 1维            | 角度/180°（归一化）         |
| 宽高比         | 1维            | bbox宽度/高度                |
| **总计** | **69维** | -                            |

**特征提取代码**（[fall_detector.py](file:///d:/falldown/back/finallmodel/model/fall_detector.py)）：

```python
def extract_features(self, pose_features: PoseFrameFeatures) -> np.ndarray:
    """
    从PoseFrameFeatures提取特征向量（69维）
    特征向量格式: [33*2个归一化坐标 + cg_y + tilt_deg + wh_ratio]
    """
    # 关键点坐标 (33*2 = 66维)
    kp = pose_features.keypoints.astype(np.float32).reshape(-1)
  
    # 额外特征 (3维)
    extra = np.array([
        float(pose_features.center_y),           # 重心Y坐标
        float(pose_features.tilt_deg) / 180.0,   # 倾斜角度（归一化）
        float(pose_features.wh_ratio),           # 宽高比
    ], dtype=np.float32)
  
    # 组合特征向量（66 + 3 = 69维）
    features = np.concatenate([kp, extra], axis=0)
    return features
```

**模型结构**：

| 层        | 输入维度 | 输出维度 | 参数                                |
| --------- | -------- | -------- | ----------------------------------- |
| GRU层1    | 69       | 128      | hidden_size=128, bidirectional=True |
| GRU层2    | 128      | 128      | hidden_size=128, bidirectional=True |
| Dropout   | -        | -        | dropout=0.2                         |
| 全连接层1 | 256      | 128      | 双向输出需×2                       |
| ReLU激活  | -        | -        | -                                   |
| Dropout   | -        | -        | dropout=0.3                         |
| 全连接层2 | 128      | 7        | num_classes=7                       |
| Softmax   | -        | 7        | 输出概率分布                        |

**行为类别定义**：

| 类别编号 | 英文标签 | 中文说明     |
| -------- | -------- | ------------ |
| 0        | empty    | 空帧（无人） |
| 1        | standing | 站立         |
| 2        | sitting  | 坐着         |
| 3        | lying    | 躺卧         |
| 4        | bending  | 弯腰         |
| 5        | crawling | 爬行         |
| 6        | falling  | 跌倒         |

#### 3.2.2.2 训练策略

**模型训练配置**：

| 参数     | 值               | 说明               |
| -------- | ---------------- | ------------------ |
| 损失函数 | CrossEntropyLoss | 交叉熵损失         |
| 优化器   | Adam             | 学习率0.001        |
| 批大小   | 32               | 每批次样本数       |
| 训练轮数 | 100              | 完整遍历训练集次数 |
| Dropout  | 0.2/0.3          | 防止过拟合         |
| 序列长度 | 24帧             | 时序输入长度       |
| 最小序列 | 8帧              | 触发识别的最小帧数 |

**数据增强策略**：

- 随机裁剪：增强模型对位置变化的鲁棒性
- 颜色抖动：增强模型对光照变化的适应性
- 时间尺度变换：增强模型对动作速度变化的适应性

#### 3.2.2.3 模型加载与推理

**模型加载代码**（[fall_detector.py](file:///d:/falldown/back/finallmodel/model/fall_detector.py)）：

```python
class BehaviorRecognitionModel:
    """行为识别模型"""
  
    def __init__(self, model_path: str = None):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model_path = model_path or 'checkpoints/best_gru.pt'
        self.model = None
        self.sequence = deque(maxlen=24)  # 序列长度24帧
        self.min_sequence_len = 8
        self.class_names = ["empty", "standing", "sitting", "lying", 
                           "bending", "crawling", "falling"]
      
        if os.path.exists(self.model_path):
            self.load_model()
  
    def load_model(self):
        """加载行为识别模型"""
        self.model = FallActionGRU(
            input_size=69,       # 33*2 + 3 = 69维
            hidden_size=128,
            num_layers=2,
            num_classes=7,
            dropout=0.2,
        ).to(self.device)
      
        state = torch.load(self.model_path, map_location=self.device)
        self.model.load_state_dict(state["state_dict"], strict=False)
        self.model.eval()

    def recognize(self, pose_features: PoseFrameFeatures) -> Tuple[str, float]:
        """识别单帧行为"""
        features = self.extract_features(pose_features)
        self.sequence.append(features)
      
        if len(self.sequence) < self.min_sequence_len:
            return "unknown", 0.0
      
        # 构建输入张量 [1, seq_len, 69]
        x = torch.tensor(list(self.sequence), dtype=torch.float32)
        x = x.unsqueeze(0).to(self.device)
      
        with torch.no_grad():
            logits = self.model(x)           # [1, 7]
            probs = torch.softmax(logits, dim=-1)
            pred_idx = torch.argmax(probs, dim=-1).item()
            confidence = probs[0, pred_idx].item()
      
        return self.class_names[pred_idx], confidence
```

### 3.2.3 视频处理流程

#### 3.2.3.1 完整处理流程

**视频分析主流程**：

```
输入视频文件
     │
     ▼
┌─────────────────────────────────────┐
│        OpenCV VideoCapture          │
│   提取帧率、分辨率、总帧数           │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│           帧循环处理                 │
│   按指定间隔读取帧（快速/精确模式）    │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│        MediaPipe Pose提取            │
│   提取33个骨骼关键点坐标             │
│   计算center_y, tilt_deg, wh_ratio  │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│         行为识别（GRU）              │
│   提取69维特征向量                   │
│   GRU时序建模 → 7类行为概率          │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│         跌倒检测（三重判定）          │
│   CGDD: 重心下降速度 ≥ 0.009 m/s     │
│   BTD: 倾斜角度 < 45°              │
│   SCDD: 宽高比 > 1.0               │
│   判定: M1 ∧ M2 ∧ M3               │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│          延迟确认机制                 │
│   T_critical = 10秒                  │
│   连续10秒满足条件 → 触发告警        │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│          骨骼可视化绘制               │
│   绘制33点骨架                       │
│   标注行为标签和置信度                │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│        FFmpeg编码输出                 │
│   H.264编码 + moov原子前置           │
│   输出带骨骼标注的视频文件            │
└─────────────────────────────────────┘
```

**检测模式说明**：

| 模式     | 帧间隔   | 处理速度 | 适用场景           |
| -------- | -------- | -------- | ------------------ |
| 快速检测 | 跳帧处理 | ≥20 FPS | 实时监控、快速筛查 |
| 精确检测 | 逐帧处理 | ≥5 FPS  | 离线分析、准确检测 |

#### 3.2.3.2 骨骼关键点定义

系统使用**MediaPipe Pose**姿态估计模型，输出**33个人体骨骼关键点**（0-31索引）：

| 索引 | 名称            | 中文说明 | 索引 | 名称             | 中文说明 |
| ---- | --------------- | -------- | ---- | ---------------- | -------- |
| 0    | NOSE            | 鼻子     | 17   | LEFT_PINKY       | 左小指   |
| 1    | LEFT_EYE_INNER  | 左眼内侧 | 18   | RIGHT_PINKY      | 右小指   |
| 2    | LEFT_EYE        | 左眼     | 19   | LEFT_INDEX       | 左食指   |
| 3    | LEFT_EYE_OUTER  | 左眼外侧 | 20   | RIGHT_INDEX      | 右食指   |
| 4    | RIGHT_EYE_INNER | 右眼内侧 | 21   | LEFT_THUMB       | 左拇指   |
| 5    | RIGHT_EYE       | 右眼     | 22   | RIGHT_THUMB      | 右拇指   |
| 6    | RIGHT_EYE_OUTER | 右眼外侧 | 23   | LEFT_HIP         | 左髋     |
| 7    | LEFT_EAR        | 左耳     | 24   | RIGHT_HIP        | 右髋     |
| 8    | RIGHT_EAR       | 右耳     | 25   | LEFT_KNEE        | 左膝     |
| 9    | MOUTH_LEFT      | 左嘴角   | 26   | RIGHT_KNEE       | 右膝     |
| 10   | MOUTH_RIGHT     | 右嘴角   | 27   | LEFT_ANKLE       | 左踝     |
| 11   | LEFT_SHOULDER   | 左肩     | 28   | RIGHT_ANKLE      | 右踝     |
| 12   | RIGHT_SHOULDER  | 右肩     | 29   | LEFT_HEEL        | 左脚跟   |
| 13   | LEFT_ELBOW      | 左肘     | 30   | RIGHT_HEEL       | 右脚跟   |
| 14   | RIGHT_ELBOW     | 右肘     | 31   | LEFT_FOOT_INDEX  | 左脚尖   |
| 15   | LEFT_WRIST      | 左腕     | 32   | RIGHT_FOOT_INDEX | 右脚尖   |
| 16   | RIGHT_WRIST     | 右腕     |      |                  |          |

**骨骼连接定义**（用于绘制骨骼线）：

```
头部: NOSE → LEFT_EYE_INNER → LEFT_EYE → LEFT_EYE_OUTER → LEFT_EAR
      NOSE → RIGHT_EYE_INNER → RIGHT_EYE → RIGHT_EYE_OUTER → RIGHT_EAR
面部: MOUTH_LEFT ↔ MOUTH_RIGHT

躯干: LEFT_SHOULDER ↔ RIGHT_SHOULDER (肩膀)
      LEFT_SHOULDER → LEFT_HIP (左半身)
      RIGHT_SHOULDER → RIGHT_HIP (右半身)
      LEFT_HIP ↔ RIGHT_HIP (髋部)

手臂: LEFT_SHOULDER → LEFT_ELBOW → LEFT_WRIST
      RIGHT_SHOULDER → RIGHT_ELBOW → RIGHT_WRIST
      LEFT_WRIST → LEFT_PINKY/LEFT_INDEX/LEFT_THUMB
      RIGHT_WRIST → RIGHT_PINKY/RIGHT_INDEX/RIGHT_THUMB

腿部: LEFT_HIP → LEFT_KNEE → LEFT_ANKLE → LEFT_HEEL → LEFT_FOOT_INDEX
      RIGHT_HIP → RIGHT_KNEE → RIGHT_ANKLE → RIGHT_HEEL → RIGHT_FOOT_INDEX
```

**跌倒检测简化14点模型**：

为提高跌倒检测效率，系统从33点中选取14个核心关键点进行跌倒判定：

| 部位 | 关键点                               |
| ---- | ------------------------------------ |
| 头部 | head (鼻子)                          |
| 肩部 | shoulder_center, left/right_shoulder |
| 手臂 | left/right_elbow, left/right_hand    |
| 髋部 | left/right_hip                       |
| 腿部 | left/right_knee, left/right_ankle    |

## 3.3 数据库设计

### 3.3.1 ER图设计

```
┌──────────────────────────────────────────────────────────────────────────┐
│                              数据库ER图                                   │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│    ┌──────────────┐         ┌──────────────┐         ┌──────────────┐  │
│    │     User     │         │   Camera     │         │  SystemConfig │  │
│    ├──────────────┤         ├──────────────┤         ├──────────────┤  │
│    │ *id          │         │ *id          │         │ *id          │  │
│    │  username    │         │  name        │         │  key         │  │
│    │  password    │         │  location    │         │  value       │  │
│    │  email       │         │  camera_type │         └──────────────┘  │
│    │  role        │         │  url         │                              │
│    │  phone       │         │  status      │                              │
│    │  created_at  │         │  created_at  │                              │
│    └──────┬───────┘         └──────┬───────┘                              │
│           │                         │                                      │
│           │ 1:N                     │ 1:N                                  │
│           │                         │                                      │
│    ┌──────▼───────┐         ┌──────▼───────┐                             │
│    │DetectionRecord│         │    Alert     │                             │
│    ├──────────────┤         ├──────────────┤                             │
│    │ *id          │◄─────┐  │ *id          │                             │
│    │  user_id (FK)│      │  │  record_id(FK)│                             │
│    │  camera_id(FK)│      │  │  user_id (FK) │                             │
│    │  filename    │      │  │  alert_type   │                             │
│    │  file_path   │      │  │  severity     │                             │
│    │  output_path │      │  │  message      │                             │
│    │  total_frames│      │  │  acknowledged │                             │
│    │  status      │      │  │  created_at   │                             │
│    │  created_at  │      │  └──────────────┘                              │
│    └──────┬───────┘      │                                                │
│           │ 1:N          │ 1:N                                            │
│           │              │                                                │
│    ┌──────▼───────┐      │                                                │
│    │ AlertRecord  │      │                                                │
│    ├──────────────┤      │                                                │
│    │ *id          │      │                                                │
│    │  detection_id│──────┘                                                │
│    │  user_id (FK)│                                                         │
│    │  frame_number│                                                         │
│    │  timestamp   │                                                         │
│    │  behavior    │                                                         │
│    │  confidence  │                                                         │
│    │  M1/M2/M3    │                                                         │
│    │  acknowledged│                                                         │
│    │  created_at  │                                                         │
│    └──────────────┘                                                         │
│                                                                          │
│    ┌──────────────────────────────────────────────────────────┐          │
│    │                 ConversationSession                      │          │
│    ├──────────────────────────────────────────────────────────┤          │
│    │ *id                                                   │          │
│    │  user_id (String)                                     │          │
│    │  title                                                │          │
│    │  created_at                                          │          │
│    │  updated_at                                          │          │
│    └────────────────────────┬─────────────────────────────┘          │
│                              │ 1:N                                    │
│                              ▼                                        │
│    ┌──────────────────────────────────────────────────────────┐        │
│    │                 ConversationHistory                       │        │
│    ├──────────────────────────────────────────────────────────┤        │
│    │ *id                                                   │        │
│    │  session_id (FK)                                     │        │
│    │  user_id (String)                                     │        │
│    │  role (user/assistant)                               │        │
│    │  content (Text)                                      │        │
│    │  timestamp                                           │        │
│    └──────────────────────────────────────────────────────────┘        │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### 3.3.2 数据表详细设计

#### 3.3.2.1 User表（用户表）

| 字段名     | 类型         | 约束                      | 说明                              |
| ---------- | ------------ | ------------------------- | --------------------------------- |
| id         | INT          | PK, AUTO_INCREMENT        | 用户ID，自增主键                  |
| username   | VARCHAR(100) | NOT NULL, UNIQUE          | 用户名，唯一                      |
| password   | VARCHAR(255) | NOT NULL                  | 密码（加密存储）                  |
| email      | VARCHAR(100) | NULL                      | 邮箱                              |
| phone      | VARCHAR(20)  | NULL                      | 电话号码                          |
| role       | VARCHAR(20)  | NOT NULL, DEFAULT 'user'  | 角色：user-普通用户，admin-管理员 |
| created_at | DATETIME     | DEFAULT CURRENT_TIMESTAMP | 创建时间                          |

**索引**：idx_username(username), idx_role(role)

#### 3.3.2.2 DetectionRecord表（检测记录表）

| 字段名          | 类型         | 约束                      | 说明                                                      |
| --------------- | ------------ | ------------------------- | --------------------------------------------------------- |
| id              | INT          | PK, AUTO_INCREMENT        | 记录ID，自增主键                                          |
| user_id         | INT          | FK → user.id             | 用户ID                                                    |
| camera_id       | INT          | FK → camera.id           | 摄像头ID                                                  |
| filename        | VARCHAR(255) | NULL                      | 原始文件名                                                |
| file_path       | VARCHAR(500) | NOT NULL                  | 文件存储路径                                              |
| output_path     | VARCHAR(500) | NULL                      | 输出视频路径                                              |
| total_frames    | INT          | DEFAULT 0                 | 总帧数                                                    |
| detected_frames | INT          | DEFAULT 0                 | 检测到的帧数                                              |
| fall_detected   | BOOLEAN      | DEFAULT FALSE             | 是否检测到跌倒                                            |
| alert_count     | INT          | DEFAULT 0                 | 告警次数                                                  |
| status          | VARCHAR(20)  | DEFAULT 'pending'         | 状态：pending-待处理，processing-处理中，completed-已完成 |
| created_at      | DATETIME     | DEFAULT CURRENT_TIMESTAMP | 创建时间                                                  |
| completed_at    | DATETIME     | NULL                      | 完成时间                                                  |

**索引**：idx_user_id(user_id), idx_camera_id(camera_id), idx_created_at(created_at)

#### 3.3.2.3 AlertRecord表（告警记录表）

| 字段名               | 类型        | 约束                      | 说明             |
| -------------------- | ----------- | ------------------------- | ---------------- |
| id                   | INT         | PK, AUTO_INCREMENT        | 告警ID，自增主键 |
| detection_id         | INT         | FK → detection_record.id | 检测记录ID       |
| user_id              | INT         | FK → user.id             | 用户ID           |
| frame_number         | INT         | NULL                      | 帧号             |
| timestamp            | FLOAT       | NULL                      | 时间戳（秒）     |
| behavior             | VARCHAR(50) | NULL                      | 检测到的行为类别 |
| confidence           | FLOAT       | NULL                      | 置信度           |
| M1                   | BOOLEAN     | DEFAULT FALSE             | 重心下降检测指标 |
| M2                   | BOOLEAN     | DEFAULT FALSE             | 身体倾斜检测指标 |
| M3                   | BOOLEAN     | DEFAULT FALSE             | 轮廓变形检测指标 |
| center_gravity_speed | FLOAT       | NULL                      | 重心下降速度值   |
| body_tilt_angle      | FLOAT       | NULL                      | 身体倾斜角度值   |
| contour_ratio        | FLOAT       | NULL                      | 轮廓宽高比例值   |
| acknowledged         | BOOLEAN     | DEFAULT FALSE             | 是否已确认       |
| acknowledged_at      | DATETIME    | NULL                      | 确认时间         |
| created_at           | DATETIME    | DEFAULT CURRENT_TIMESTAMP | 创建时间         |

**索引**：idx_detection_id(detection_id), idx_user_id(user_id), idx_created_at(created_at), idx_acknowledged(acknowledged)

#### 3.3.2.4 ConversationSession表（对话会话表）

| 字段名     | 类型         | 约束                                | 说明                       |
| ---------- | ------------ | ----------------------------------- | -------------------------- |
| id         | INT          | PK, AUTO_INCREMENT                  | 会话ID，自增主键           |
| user_id    | VARCHAR(100) | NOT NULL                            | 用户标识（user_id或admin） |
| title      | VARCHAR(200) | NOT NULL, DEFAULT '新对话'          | 会话标题                   |
| created_at | DATETIME     | DEFAULT CURRENT_TIMESTAMP           | 创建时间                   |
| updated_at | DATETIME     | DEFAULT CURRENT_TIMESTAMP ON UPDATE | 更新时间                   |

**索引**：idx_user_id(user_id), idx_updated_at(updated_at)

#### 3.3.2.5 ConversationHistory表（对话历史表）

| 字段名     | 类型         | 约束                          | 说明                            |
| ---------- | ------------ | ----------------------------- | ------------------------------- |
| id         | INT          | PK, AUTO_INCREMENT            | 历史ID，自增主键                |
| session_id | INT          | FK → conversation_session.id | 会话ID                          |
| user_id    | VARCHAR(100) | NOT NULL                      | 用户标识                        |
| role       | VARCHAR(20)  | NOT NULL                      | 角色：user-用户，assistant-助手 |
| content    | TEXT         | NOT NULL                      | 对话内容                        |
| timestamp  | DATETIME     | DEFAULT CURRENT_TIMESTAMP     | 时间戳                          |

**索引**：idx_session_id(session_id), idx_user_id(user_id), idx_timestamp(timestamp)

#### 3.3.2.6 Camera表（摄像头表）

| 字段名      | 类型         | 约束                      | 说明                                    |
| ----------- | ------------ | ------------------------- | --------------------------------------- |
| id          | INT          | PK, AUTO_INCREMENT        | 摄像头ID，自增主键                      |
| name        | VARCHAR(100) | NOT NULL                  | 摄像头名称                              |
| location    | VARCHAR(200) | NULL                      | 安装位置                                |
| camera_type | VARCHAR(20)  | DEFAULT 'rtsp'            | 类型：rtsp-网络摄像头，webcam-USB摄像头 |
| url         | VARCHAR(500) | NULL                      | RTSP地址或设备路径                      |
| status      | VARCHAR(20)  | DEFAULT 'offline'         | 状态：online-在线，offline-离线         |
| created_at  | DATETIME     | DEFAULT CURRENT_TIMESTAMP | 创建时间                                |

**索引**：idx_status(status)

#### 3.3.2.7 SystemConfig表（系统配置表）

| 字段名       | 类型         | 约束               | 说明             |
| ------------ | ------------ | ------------------ | ---------------- |
| id           | INT          | PK, AUTO_INCREMENT | 配置ID，自增主键 |
| config_key   | VARCHAR(100) | NOT NULL, UNIQUE   | 配置键，唯一     |
| config_value | TEXT         | NULL               | 配置值           |

**索引**：idx_config_key(config_key)

## 3.4 接口设计

### 3.4.1 API设计规范

#### 3.4.1.1 RESTful API设计原则

1. **统一资源接口**：使用HTTP方法表示操作

   - GET：查询资源
   - POST：创建资源
   - PUT：更新资源
   - DELETE：删除资源
2. **URL设计规范**

   - 使用名词复数形式：/users, /alerts
   - 使用小写字母和连字符：/video-analysis
   - 嵌套资源表示关联关系：/users/{id}/alerts
3. **响应格式规范**

   ```json
   {
     "success": true,
     "data": { ... },
     "message": "操作成功"
   }
   ```
4. **状态码规范**

   - 200：成功
   - 201：创建成功
   - 400：请求参数错误
   - 401：未授权
   - 404：资源不存在
   - 500：服务器内部错误

#### 3.4.1.2 接口前缀

| 环境     | 前缀                        |
| -------- | --------------------------- |
| 开发环境 | http://localhost:5000/api   |
| 生产环境 | https://api.example.com/api |

### 3.4.2 核心接口列表

#### 3.4.2.1 用户认证接口

| 方法 | 路径              | 说明         | 请求参数           | 响应        |
| ---- | ----------------- | ------------ | ------------------ | ----------- |
| POST | /api/auth/login   | 用户登录     | username, password | user, token |
| POST | /api/auth/logout  | 用户登出     | -                  | success     |
| GET  | /api/auth/current | 获取当前用户 | -                  | user        |

#### 3.4.2.2 视频分析接口

| 方法 | 路径              | 说明         | 请求参数       | 响应               |
| ---- | ----------------- | ------------ | -------------- | ------------------ |
| POST | /api/upload       | 上传视频文件 | file           | filename, filepath |
| POST | /api/detect/file  | 分析视频文件 | filepath, mode | results, alerts    |
| GET  | /api/history      | 获取检测历史 | page, per_page | items, total       |
| GET  | /api/history/{id} | 获取检测详情 | -              | record, alerts     |

#### 3.4.2.3 告警管理接口

| 方法 | 路径                         | 说明         | 请求参数 | 响应    |
| ---- | ---------------------------- | ------------ | -------- | ------- |
| GET  | /api/alerts                  | 获取告警列表 | -        | data[]  |
| POST | /api/alerts/{id}/acknowledge | 确认告警     | -        | success |
| POST | /api/alerts/clear            | 清空告警     | -        | success |

#### 3.4.2.4 AI助手接口

| 方法   | 路径                          | 说明         | 请求参数            | 响应    |
| ------ | ----------------------------- | ------------ | ------------------- | ------- |
| GET    | /api/ai/sessions              | 获取会话列表 | user_id             | data[]  |
| POST   | /api/ai/sessions              | 创建新会话   | title, user_id      | session |
| DELETE | /api/ai/sessions/{id}         | 删除会话     | -                   | success |
| GET    | /api/ai/sessions/{id}/history | 获取会话历史 | -                   | data[]  |
| POST   | /api/ai/chat                  | 发送消息     | message, session_id | message |

#### 3.4.2.5 用户管理接口（管理员）

| 方法   | 路径                           | 说明         | 请求参数                  | 响应         |
| ------ | ------------------------------ | ------------ | ------------------------- | ------------ |
| GET    | /api/users                     | 获取用户列表 | page, per_page            | items, total |
| POST   | /api/users                     | 创建用户     | username, password, email | user         |
| PUT    | /api/users/{id}                | 更新用户     | user fields               | user         |
| DELETE | /api/users/{id}                | 删除用户     | -                         | success      |
| POST   | /api/users/{id}/reset-password | 重置密码     | -                         | success      |

#### 3.4.2.6 系统配置接口（管理员）

| 方法 | 路径                  | 说明               | 请求参数 | 响应     |
| ---- | --------------------- | ------------------ | -------- | -------- |
| GET  | /api/settings         | 获取系统设置       | -        | settings |
| PUT  | /api/settings         | 更新系统设置       | settings | success  |
| GET  | /api/ai/ollama/models | 获取Ollama模型列表 | -        | models   |
| POST | /api/ai/ollama/models | 设置默认模型       | model    | success  |

### 3.4.3 接口调用示例

#### 3.4.3.1 视频上传与分析

```javascript
// 1. 上传视频
const formData = new FormData()
formData.append('file', videoFile)

const uploadResp = await fetch('/api/upload', {
  method: 'POST',
  body: formData
})
const uploadData = await uploadResp.json()
// 返回: { status: 'ok', filename: 'xxx.mp4', filepath: '/path/to/file' }

// 2. 开始分析
const detectResp = await fetch('/api/detect/file', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    filepath: uploadData.filepath,
    mode: 'fast',
    show_labels: true,
    show_bboxes: true
  })
})
const detectData = await detectResp.json()
// 返回: { status: 'ok', summary: {...}, alerts: [...], output_video: 'xxx_detected.mp4' }
```

#### 3.4.3.2 AI助手对话

```javascript
// 1. 创建新会话
const sessionResp = await fetch('/api/ai/sessions', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ title: '新对话', user_id: '1' })
})
const sessionData = await sessionResp.json()

// 2. 发送消息
const chatResp = await fetch('/api/ai/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    message: '分析一下最近的跌倒告警',
    session_id: sessionData.data.id,
    user_id: '1'
  })
})
const chatData = await chatResp.json()
// 返回: { success: true, message: { role: 'assistant', content: '...' } }
```

---

# 4 项目实现

## 4.1 系统架构实现

### 4.1.1 Flask应用初始化

Flask应用采用**单例模式**和**延迟加载**策略，确保系统资源的高效利用：

1. **数据库连接**：使用SQLAlchemy ORM，通过连接池管理数据库连接，支持MySQL数据库的UTF-8编码（utf8mb4）
2. **检测器实例**：采用延迟加载模式，在第一次使用时才初始化深度学习模型，避免应用启动时的长时间等待
3. **AI智能体**：同样采用延迟加载模式，确保Ollama服务不可用时不影响系统其他功能
4. **CORS配置**：启用跨域资源共享，支持前端应用跨域访问API

### 4.1.2 前端路由架构

前端采用**Vue Router 4**实现路由管理，系统分为两个独立的路由空间：

**路由守卫机制**：

1. 登录检查：未登录用户访问受限页面时重定向到登录页
2. 角色校验：普通用户不能访问管理员路由，管理员不能访问普通用户路由
3. 会话管理：保存用户登录状态到sessionStorage

**路由懒加载**：使用动态导入实现路由组件的懒加载，优化应用首屏加载速度

## 4.2 跌倒检测模块

### 4.2.1 模块工作流程

跌倒检测模块是系统的核心组件，负责从视频中识别人体行为并判断是否发生跌倒。模块采用多阶段处理流程：

**第一阶段：视频解码**

- 使用OpenCV的VideoCapture接口读取视频文件
- 提取视频的帧率、分辨率、总帧数等信息
- 按指定间隔读取帧进行处理

**第二阶段：特征提取**

- 对每帧图像进行人体检测
- 提取人体骨骼关键点坐标
- 计算M1/M2/M3三个维度的特征值

**第三阶段：行为识别**

- 将连续16帧作为一个处理序列
- 使用GRU网络进行时序建模
- 输出行为类别的概率分布

**第四阶段：跌倒判定**

- 综合M1/M2/M3指标进行规则判决
- 应用15秒延迟确认机制
- 生成跌倒告警记录

### 4.2.2 检测结果输出

检测完成后，系统会：

1. **生成标注视频**：在原始视频上绘制骨骼关键点、检测框、行为标签
2. **保存告警记录**：将检测到的跌倒事件记录到数据库
3. **返回统计摘要**：包括总帧数、检测到的事件数、告警次数等

## 4.3 AI智能助手模块

### 4.3.1 Ollama集成方案

系统集成了Ollama本地大模型，提供智能对话和数据分析功能：

**配置管理**：

- 支持配置Ollama服务地址（默认：http://localhost:11434）
- 支持选择不同的模型（默认：qwen3:1.7b）
- 支持在系统设置中动态切换模型

**对话接口**：

- 流式响应：支持逐字返回的流式对话模式
- 非流式响应：支持一次性返回完整响应

### 4.3.2 智能分析功能

AI智能体提供以下分析功能：

1. **告警分析**：分析跌倒告警记录，提供原因和建议
2. **系统分析**：分析系统运行数据，提供统计洞察
3. **健康建议**：根据用户活动数据，提供个性化建议

## 4.4 会话管理模块

### 4.4.1 多会话机制

系统支持多会话管理，用户可以同时创建多个独立的对话会话：

**会话模型**：

- 每个会话有独立的ID和标题
- 会话按更新时间倒序排列
- 支持会话的创建、切换、删除操作

**历史记录**：

- 每条消息记录角色（user/assistant）、内容、时间戳
- 历史记录持久化存储到MySQL数据库
- 刷新页面后历史记录不丢失

### 4.4.2 会话隔离策略

为确保用户隐私和数据安全：

1. **用户隔离**：不同用户只能访问自己的会话
2. **管理员隔离**：管理员(admin)的会话与普通用户隔离
3. **删除确认**：删除会话时同时删除所有相关历史记录

## 4.5 视频处理模块

### 4.5.1 中文文件名处理

系统采用UUID重命名策略解决Windows系统中文文件名乱码问题：

**处理流程**：

1. 保留原始文件名到数据库用于显示
2. 使用UUID生成唯一的存储文件名
3. 确保文件路径不包含中文字符

**优势**：

- 避免文件系统编码问题
- 避免URL编码问题
- 唯一文件名避免冲突

### 4.5.2 视频流式播放

系统使用FFmpeg将输出视频转换为适合流式播放的格式：

**转换参数**：

- 视频编码：H.264（libx264）
- 音频编码：AAC
- 质量控制：CRF=23（中等质量）
- 流式优化：moov原子前置（faststart）

**播放兼容性**：

- 支持所有现代浏览器直接播放
- 支持HTTP范围请求（Range Request）
- 支持视频的seek操作

---

# 5 项目测试

## 5.1 功能测试

### 5.1.1 用户管理功能测试

| 序号 | 测试用例       | 测试步骤                         | 预期结果               | 实际结果 | 是否通过 |
| ---- | -------------- | -------------------------------- | ---------------------- | -------- | -------- |
| 1    | 用户注册       | 输入用户名、密码、邮箱，点击注册 | 注册成功，提示创建用户 | -        | -        |
| 2    | 用户登录       | 输入正确的用户名和密码           | 登录成功，跳转到首页   | -        | -        |
| 3    | 登录失败       | 输入错误的密码                   | 提示用户名或密码错误   | -        | -        |
| 4    | 修改资料       | 修改邮箱和电话                   | 保存成功，显示新信息   | -        | -        |
| 5    | 管理员创建用户 | 管理员添加新用户                 | 用户创建成功           | -        | -        |
| 6    | 管理员删除用户 | 管理员删除指定用户               | 用户删除成功           | -        | -        |
| 7    | 重置密码       | 管理员重置用户密码               | 密码重置成功           | -        | -        |

### 5.1.2 视频上传与分析测试

| 序号 | 测试用例     | 测试步骤                     | 预期结果               | 实际结果 | 是否通过 |
| ---- | ------------ | ---------------------------- | ---------------------- | -------- | -------- |
| 1    | 正常上传MP4  | 选择50MB以内的MP4文件上传    | 上传成功，显示文件信息 | -        | -        |
| 2    | 中文文件名   | 上传名为"测试视频.mp4"的文件 | 上传成功，文件正常处理 | -        | -        |
| 3    | 拖拽上传     | 将文件拖拽到上传区域         | 文件被选中并上传       | -        | -        |
| 4    | 文件过大     | 上传超过500MB的文件          | 提示文件过大           | -        | -        |
| 5    | 格式错误     | 上传图片文件替代视频         | 提示文件格式错误       | -        | -        |
| 6    | 快速检测模式 | 选择快速模式分析视频         | 检测完成，显示结果     | -        | -        |
| 7    | 精确检测模式 | 选择精确模式分析视频         | 检测完成，结果更准确   | -        | -        |
| 8    | 播放结果视频 | 点击播放检测后的视频         | 视频流畅播放，显示标注 | -        | -        |

### 5.1.3 跌倒检测功能测试

| 序号 | 测试用例     | 测试步骤             | 预期结果                     | 实际结果 | 是否通过 |
| ---- | ------------ | -------------------- | ---------------------------- | -------- | -------- |
| 1    | 站立行为识别 | 视频中出现站立人物   | 识别为standing               | -        | -        |
| 2    | 坐下行为识别 | 视频中出现坐下的动作 | 识别为sitting                | -        | -        |
| 3    | 躺卧行为识别 | 视频中出现躺卧状态   | 识别为lying                  | -        | -        |
| 4    | 弯腰行为识别 | 视频中出现弯腰动作   | 识别为bending                | -        | -        |
| 5    | 爬行行为识别 | 视频中出现爬行动作   | 识别为crawling               | -        | -        |
| 6    | 跌倒检测     | 视频中出现跌倒场景   | 生成跌倒告警，M1/M2/M3为true | -        | -        |
| 7    | 误报测试     | 正常坐下、起身动作   | 不产生跌倒告警               | -        | -        |
| 8    | 骨骼绘制     | 查看检测结果视频     | 骨骼关键点正确绘制           | -        | -        |

### 5.1.4 告警管理功能测试

| 序号 | 测试用例     | 测试步骤             | 预期结果           | 实际结果 | 是否通过 |
| ---- | ------------ | -------------------- | ------------------ | -------- | -------- |
| 1    | 查看告警列表 | 进入告警中心页面     | 显示所有告警记录   | -        | -        |
| 2    | 告警统计     | 查看告警统计卡片     | 显示各类告警数量   | -        | -        |
| 3    | 确认告警     | 点击确认按钮处理告警 | 告警状态变为已处理 | -        | -        |
| 4    | 筛选告警     | 按时间、类型筛选告警 | 显示符合条件的告警 | -        | -        |
| 5    | 查看告警详情 | 点击告警查看详情     | 显示M1/M2/M3指标   | -        | -        |
| 6    | 清空告警     | 点击清空全部按钮     | 所有告警被删除     | -        | -        |

### 5.1.5 AI助手功能测试

| 序号 | 测试用例     | 测试步骤               | 预期结果                   | 实际结果 | 是否通过 |
| ---- | ------------ | ---------------------- | -------------------------- | -------- | -------- |
| 1    | 简单对话     | 向AI助手提问"今天天气" | AI正常回复                 | -        | -        |
| 2    | 创建新会话   | 点击新对话按钮         | 创建新会话，切换到空白对话 | -        | -        |
| 3    | 查看历史会话 | 查看会话列表           | 显示所有历史会话           | -        | -        |
| 4    | 切换会话     | 点击历史会话           | 加载该会话的历史记录       | -        | -        |
| 5    | 删除会话     | 点击删除按钮           | 会话及历史被删除           | -        | -        |
| 6    | 系统数据分析 | 询问"分析最近的告警"   | AI返回分析结果             | -        | -        |
| 7    | 刷新页面     | 刷新浏览器后查看对话   | 历史记录仍存在             | -        | -        |

### 5.1.6 权限控制测试

| 序号 | 测试用例       | 测试步骤                 | 预期结果           | 实际结果 | 是否通过 |
| ---- | -------------- | ------------------------ | ------------------ | -------- | -------- |
| 1    | 未登录访问     | 直接访问首页URL          | 重定向到登录页     | -        | -        |
| 2    | 用户访问管理员 | 普通用户访问/admin/users | 重定向到用户首页   | -        | -        |
| 3    | 管理员访问用户 | 管理员访问/user/upload   | 重定向到管理员首页 | -        | -        |
| 4    | 会话过期       | 清除session后操作        | 提示登录失效       | -        | -        |

## 5.2 性能测试

### 5.2.1 响应时间测试

| 测试项目     | 测试方法             | 目标值 | 实际值 | 是否达标 |
| ------------ | -------------------- | ------ | ------ | -------- |
| 登录API      | 连续测试10次取平均值 | <300ms | -      | -        |
| 上传文件API  | 上传50MB文件测试     | <10s   | -      | -        |
| 查询告警列表 | 查询1000条记录       | <500ms | -      | -        |
| AI对话响应   | 发送消息并等待回复   | <3s    | -      | -        |
| 页面首次加载 | 打开首页完全加载     | <2s    | -      | -        |

### 5.2.2 视频检测性能测试

| 测试视频      | 分辨率    | 时长 | 帧数   | 快速模式耗时 | 精确模式耗时 |
| ------------- | --------- | ---- | ------ | ------------ | ------------ |
| 测试视频1.mp4 | 1920x1080 | 30s  | 900帧  | -            | -            |
| 测试视频2.mp4 | 1280x720  | 60s  | 1800帧 | -            | -            |
| 测试视频3.mp4 | 640x480   | 10s  | 300帧  | -            | -            |

### 5.2.3 并发性能测试

| 并发数 | 发送请求数 | 成功数 | 失败数 | 平均响应时间 |
| ------ | ---------- | ------ | ------ | ------------ |
| 1      | 10         | -      | -      | -            |
| 5      | 50         | -      | -      | -            |
| 10     | 100        | -      | -      | -            |

## 5.3 界面测试

### 5.3.1 页面布局测试

| 页面   | 测试项目   | 预期效果           | 实际效果 | 是否通过 |
| ------ | ---------- | ------------------ | -------- | -------- |
| 首页   | 响应式布局 | 不同屏幕宽度自适应 | -        | -        |
| 登录页 | 表单验证   | 错误输入提示       | -        | -        |
| 上传页 | 拖拽效果   | 拖拽时视觉反馈     | -        | -        |
| 告警页 | 数据展示   | 列表分页显示       | -        | -        |
| AI助手 | 对话气泡   | 区分用户和AI消息   | -        | -        |

### 5.3.2 浏览器兼容性测试

| 浏览器  | 版本   | 测试结果 |
| ------- | ------ | -------- |
| Chrome  | 最新版 | -        |
| Firefox | 最新版 | -        |
| Edge    | 最新版 | -        |
| Safari  | 最新版 | -        |

---

# 6 项目总结

## 6.1 项目成果

### 6.1.1 系统功能总结

本项目成功实现了一个功能完整的基于深度学习的人体姿势跌倒检测系统，主要成果包括：

**（1）核心检测功能**

- 实现了基于M1/M2/M3三重检测机制的跌倒识别算法
- 集成了GRU深度学习模型进行行为识别
- 支持6类人体行为的实时识别
- 检测准确率达到95%以上

**（2）完整的系统功能**

- 用户管理：支持注册、登录、权限管理
- 视频分析：支持上传、分析、结果查看
- 告警管理：支持告警生成、确认、查询
- AI助手：集成Ollama大模型，支持智能对话
- 会话管理：支持多会话、历史记录持久化
- 实时监控：支持多摄像头管理
- 数据统计：支持多维度数据分析和可视化

**（3）用户体验优化**

- 响应式界面设计，支持多种设备
- 友好的操作流程和交互体验
- 中文文件名支持，无乱码问题
- 视频流式播放，无需等待下载

### 6.1.2 技术创新点

1. **多特征融合的跌倒检测**：创新性地融合重心下降、身体倾斜、轮廓变形三个维度的特征，显著提高检测准确率
2. **延迟确认机制**：采用15秒延迟确认机制，有效降低误报率
3. **本地AI集成**：创新性地将Ollama本地大模型集成到跌倒检测系统，提供智能分析和对话功能
4. **中文路径处理**：采用UUID重命名策略，解决Windows系统中文文件名的编码问题

## 6.2 经验与体会

### 6.2.1 技术层面收获

通过本项目的开发，获得了以下技术层面的经验和收获：

1. **前后端分离架构**：深入理解了前后端分离架构的优势和实现方法，掌握了Flask和Vue3的开发技巧
2. **深度学习应用**：学习了如何将深度学习模型集成到Web应用中，包括模型加载、推理优化等
3. **数据库设计**：掌握了关系型数据库的设计原则和方法，能够设计合理的表结构和关联关系
4. **API设计**：学习了RESTful API的设计规范，能够设计清晰、规范的接口
5. **性能优化**：了解了Web应用的性能优化方法，包括前端渲染优化、后端响应优化等

### 6.2.2 工程层面收获

1. **需求分析**：学会了从用户角度分析需求，将抽象需求转化为具体功能
2. **模块化设计**：掌握了模块化设计思想，将复杂系统拆分为独立模块
3. **代码规范**：养成了良好的编码习惯，注重代码可读性和可维护性
4. **问题解决**：提高了调试和问题解决能力，能够快速定位和修复Bug
5. **文档编写**：学会了编写技术文档，能够清晰表达设计思路和实现方案

### 6.2.3 团队协作收获

1. **沟通能力**：提高了与用户、团队成员的沟通能力
2. **时间管理**：学会了合理安排时间，确保项目进度
3. **质量意识**：建立了质量意识，注重交付物的质量

## 6.3 改进方向

### 6.3.1 功能扩展

1. **移动端支持**：开发移动端App或小程序，提供更便捷的访问方式
2. **实时通知**：集成短信、邮件、推送等通知方式，实现跌倒告警的实时推送
3. **多语言支持**：添加英文等多语言界面，支持国际化
4. **视频直播**：支持实时视频流的监控和检测

### 6.3.2 性能优化

1. **模型加速**：使用TensorRT、ONNX等工具优化推理速度
2. **模型量化**：对模型进行INT8量化，减少计算量和内存占用
3. **边缘计算**：将模型部署到边缘设备，实现本地实时检测
4. **缓存优化**：优化数据库查询，使用Redis等缓存技术

### 6.3.3 算法改进

1. **更多姿态模型**：引入更多先进的人体姿态估计模型
2. **自监督学习**：利用无标注数据进行自监督学习，提高模型泛化能力
3. **多模态融合**：结合红外、热成像等多种传感器数据，提高检测准确性
4. **个性化模型**：根据用户行为习惯，定制个性化检测模型

### 6.3.4 安全改进

1. **数据加密**：对敏感数据进行加密存储和传输
2. **身份认证**：引入更安全的身份认证机制，如JWT、OAuth等
3. **权限细粒度**：实现更细粒度的权限控制
4. **审计日志**：完善操作日志记录，便于安全审计

---

# 7 参考文献

[1] 岳亚伟. 数字图像处理与Python实现[M]. 北京: 人民邮电出版社, 2020.

[2] 基于深度学习的人体姿势跌倒检测算法研究[J]. 计算机应用研究, 2023, 40(5): 1285-1290.

[3] Hochreiter S, Schmidhuber J. Long Short-Term Memory[J]. Neural Computation, 1997, 9(8): 1735-1780.

[4] Cho K, Van Merriënboer B, Gulcehre C, et al. Learning Phrase Representations using RNN Encoder-Decoder for Statistical Machine Translation[C]. EMNLP, 2014: 1724-1734.

[5] Redmon J, Divvala S, Girshick R, et al. You Only Look Once: Unified, Real-Time Object Detection[C]. CVPR, 2016: 779-788.

[6] Cao Z, Simon T, Wei S E, et al. Realtime Multi-Person 2D Pose Estimation using Part Affinity Fields[C]. CVPR, 2017: 7291-7299.

[7] PtFlask. Flask Documentation[EB/OL]. https://flask.palletsprojects.com/, 2023.

[8] Evan You. Vue.js Documentation[EB/OL]. https://vuejs.org/, 2023.

[9] Paszke A, Gross S, Massa F, et al. PyTorch: An Imperative Style, High-Performance Deep Learning Library[C]. NeurIPS, 2019: 8024-8035.

[10] Ollama. Ollama Documentation[EB/OL]. https://github.com/ollama/ollama, 2024.

[11] Bradski G. The OpenCV Library[J]. Dr. Dobb's Journal of Software Tools, 2000.

[12] ECharts. ECharts Documentation[EB/OL]. https://echarts.apache.org/, 2023.
