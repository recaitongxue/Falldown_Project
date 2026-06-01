# 跌倒检测系统后端服务

## 项目概述

本项目是一个基于 Flask 的跌倒检测系统后端服务，提供视频检测、实时图像检测、AI智能分析、用户管理等功能。系统集成了深度学习模型和规则引擎，实现高精度的跌倒事件检测。

---

## 技术架构

### 技术栈

| 分类 | 技术 | 版本 | 用途 |
|-----|------|-----|------|
| 语言 | Python | 3.8+ | 后端开发 |
| 框架 | Flask | 2.0+ | Web服务 |
| 数据库 | MySQL | 8.0+ | 数据存储 |
| ORM | Flask-SQLAlchemy | 3.0+ | 数据库操作 |
| 迁移 | Flask-Migrate | 4.0+ | 数据库迁移 |
| 深度学习 | PyTorch | 2.0+ | 行为识别模型 |
| 骨骼检测 | MediaPipe | 0.10+ | 人体关键点检测 |
| AI智能体 | Ollama | 0.10+ | 本地LLM支持 |
| 视频处理 | OpenCV | 4.5+ | 视频帧处理 |

### 架构设计

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        后端系统架构                                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌──────────────┐    HTTP    ┌──────────────┐    RPC    ┌──────────┐   │
│   │   前端应用    │ ─────────→ │   Flask API   │ ─────────→│  Ollama  │   │
│   │   (Vue.js)   │            │    网关层     │            │  AI智能体 │   │
│   └──────────────┘            └──────────────┘            └──────────┘   │
│                                       │                                  │
│          ┌─────────────────────────────┼─────────────────────────────┐    │
│          ▼                             ▼                             ▼    │
│   ┌──────────────┐            ┌──────────────┐            ┌──────────┐   │
│   │  用户认证    │            │  视频检测    │            │  模型推理 │   │
│   │   模块       │            │   模块       │            │   模块    │   │
│   └──────────────┘            └──────────────┘            └──────────┘   │
│                                       │                                  │
│                                       ▼                                  │
│                          ┌──────────────────┐                           │
│                          │   MySQL 数据库    │                           │
│                          └──────────────────┘                           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 核心模块

| 模块 | 功能说明 | 文件位置 |
|-----|---------|---------|
| **app.py** | Flask主应用，路由定义，请求处理 | `back/app.py` |
| **config.py** | 配置管理，环境变量加载 | `back/config.py` |
| **ai_agent.py** | AI智能体，风险分析，对话管理 | `back/ai_agent.py` |
| **fall_detector.py** | 跌倒检测核心引擎 | `back/finallmodel/model/fall_detector.py` |
| **network.py** | GRU行为识别网络 | `back/finallmodel/model/network.py` |
| **pose_features.py** | MediaPipe骨骼特征提取 | `back/finallmodel/model/pose_features.py` |

---

## 目录结构

```
back/
├── finallmodel/              # 跌倒检测模型模块
│   ├── model/                # 模型核心代码
│   │   ├── __init__.py
│   │   ├── config.py         # 模型配置
│   │   ├── network.py        # GRU网络结构
│   │   ├── pose_features.py  # 骨骼特征提取
│   │   ├── fall_detector.py  # 跌倒检测器
│   │   ├── train.py          # 模型训练脚本
│   │   └── dataset_loader.py # 数据集加载器
│   ├── dataset/              # 训练数据集
│   ├── checkpoints/          # 模型权重
│   └── README.md             # 模型说明文档
├── uploads/                  # 上传文件存储
├── outputs/                  # 检测结果输出
├── app.py                    # Flask主应用
├── config.py                 # 系统配置
├── ai_agent.py               # AI智能体模块
├── .env                      # 环境变量配置
└── requirements.txt          # 依赖列表
```

---

## 安装与配置

### 1. 环境要求

```bash
# Python 3.8+
python --version  # 检查版本

# 安装依赖
pip install -r requirements.txt
```

### 2. 数据库配置

创建 MySQL 数据库：

```sql
CREATE DATABASE falldown_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'falldown_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON falldown_db.* TO 'falldown_user'@'localhost';
FLUSH PRIVILEGES;
```

### 3. 环境变量配置

创建 `.env` 文件：

```env
# 数据库配置
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=falldown_user
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=falldown_db

# Ollama配置（可选）
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen3:1.7b
OLLAMA_ENABLED=true

# 应用配置
SECRET_KEY=fall_detection_secret_key_2025

# 规则配置（基于论文参数）
RULE_FPS=20.0
RULE_CGDD_FRAME_GAP=10
RULE_V_CR=0.015
RULE_THETA_CR_DEG=60.0
RULE_P_CR=0.7
RULE_T_CR_SEC=15.0
```

### 4. 数据库迁移

```bash
# 初始化迁移
flask db init

# 创建迁移脚本
flask db migrate -m "Initial migration"

# 应用迁移
flask db upgrade
```

### 5. 启动服务

```bash
# 开发模式
python app.py

# 或使用 Flask CLI
flask run --host 0.0.0.0 --port 5000

# 生产模式（建议使用Gunicorn）
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

---

## 数据库模型

### 核心数据表

| 表名 | 功能 | 关键字段 |
|-----|------|---------|
| **users** | 用户信息 | id, username, email, role, phone |
| **cameras** | 摄像头管理 | id, name, location, url, user_id, status |
| **detection_records** | 检测记录 | id, user_id, camera_id, filename, fall_detected |
| **alert_records** | 告警详情 | id, detection_id, frame_number, behavior, M1/M2/M3 |
| **alerts** | 告警通知 | id, user_id, alert_type, severity, acknowledged |
| **conversation_sessions** | AI对话会话 | id, user_id, title, created_at |
| **conversation_history** | 对话历史 | id, session_id, role, content |
| **analysis_records** | 分析记录 | id, user_id, status, ai_analysis |

### 数据模型关系

```
User 1:N Camera       (用户拥有多个摄像头)
User 1:N DetectionRecord (用户拥有多个检测记录)
DetectionRecord 1:N AlertRecord (检测记录包含多个告警)
DetectionRecord 1:N Alert (检测记录触发多个告警通知)
ConversationSession 1:N ConversationHistory (会话包含多条对话)
```

---

## API 接口

### 1. 视频检测

**POST** `/api/detect/file`

```json
{
  "filepath": "/path/to/video.mp4",
  "user_id": 1,
  "mode": "fast",
  "show_labels": true,
  "show_bboxes": true
}
```

**响应**：

```json
{
  "status": "ok",
  "summary": {
    "total_frames": 1000,
    "detected_frames": 50,
    "fall_detected": true,
    "alert_count": 5
  },
  "output_video": "uuid_detected.mp4",
  "alerts": [...],
  "record_id": 123,
  "ai_analysis": {...}
}
```

### 2. 实时图像检测

**POST** `/api/detect`

```json
{
  "image": "base64_encoded_image"
}
```

**响应**：

```json
{
  "success": true,
  "label": "跌倒",
  "confidence": 0.95,
  "behavior": "falling",
  "behavior_cn": "跌倒",
  "is_fall": true,
  "M1": true,
  "M2": true,
  "M3": false,
  "center_gravity_speed": 0.02,
  "body_tilt_angle": 35.5,
  "contour_ratio": 1.2,
  "alert": true
}
```

### 3. 用户认证

| 接口 | 方法 | 说明 |
|-----|------|-----|
| `/api/user/register` | POST | 用户注册 |
| `/api/user/login` | POST | 用户登录 |
| `/api/auth/register` | POST | 兼容路径 |
| `/api/auth/login` | POST | 兼容路径 |

### 4. AI智能体

| 接口 | 方法 | 说明 |
|-----|------|-----|
| `/api/ai/chat` | POST | AI对话 |
| `/api/ai/history` | GET | 获取对话历史 |
| `/api/ai/clear` | POST | 清除对话历史 |
| `/api/ai/status` | GET | 获取AI状态 |
| `/api/ai/report` | GET | 生成分析报告 |

### 5. 检测历史

| 接口 | 方法 | 说明 |
|-----|------|-----|
| `/api/history` | GET | 获取检测历史列表 |
| `/api/history/{id}` | GET | 获取检测记录详情 |
| `/api/analysis/records` | GET | 分页获取分析记录 |
| `/api/analysis/record/{id}` | DELETE | 删除分析记录 |

### 6. 告警管理

| 接口 | 方法 | 说明 |
|-----|------|-----|
| `/api/alerts` | GET | 获取告警列表 |
| `/api/alerts/{id}/acknowledge` | POST | 确认告警 |
| `/api/alerts/clear` | POST | 清空所有告警 |

### 7. 视频流

| 接口 | 方法 | 说明 |
|-----|------|-----|
| `/api/video/stream/{filename}` | GET | 流式播放视频 |
| `/api/download/video/{filename}` | GET | 下载视频文件 |

### 8. 系统状态

| 接口 | 方法 | 说明 |
|-----|------|-----|
| `/api/health` | GET | 健康检查 |
| `/api/statistics` | GET | 获取统计数据 |

---

## 跌倒检测算法

系统采用 **三重判定条件**（参考论文《基于深度学习的人体姿势跌倒检测算法》）：

### 条件1：CGDD - 重心下降检测

检测人体重心在短时间内的快速下降：

```python
V_CRITICAL = 0.015  # 重心下降速度阈值 (m/s)
```

### 条件2：BTD - 身体倾斜检测

检测身体是否处于水平状态：

```python
THETA_CRITICAL = 60.0  # 倾斜角度阈值 (度)
```

### 条件3：SCDD - 形状变化检测

检测人体外接矩形的宽高比变化：

```python
P_CRITICAL = 0.7  # 宽高比阈值
```

### 综合判定

三个条件**全部满足**才判定为跌倒：

```python
is_fall = cgdd_triggered and btd_triggered and scdd_triggered
```

---

## 行为识别模型

### GRU网络结构

```python
class FallActionGRU(nn.Module):
    def __init__(self, input_size=69, hidden_size=128, num_layers=2, num_classes=7):
        self.gru = nn.GRU(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            bidirectional=True,
            dropout=0.3
        )
        self.cls = nn.Sequential(
            nn.LayerNorm(256),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(128, num_classes)
        )
```

### 行为类别

| 索引 | 类别 | 说明 |
|-----|------|-----|
| 0 | empty | 空帧（无人） |
| 1 | standing | 站立 |
| 2 | sitting | 坐着 |
| 3 | lying | 躺卧 |
| 4 | bending | 弯腰 |
| 5 | crawling | 爬行 |
| 6 | falling | 跌倒 |

---

## AI智能体功能

### 风险分析

基于检测结果计算风险评分：

```python
risk = 0.0
if fall_detected: risk += 0.6
if alert: risk += 0.3
if M1 and M2: risk += 0.1
```

### 风险等级

| 风险评分 | 等级 | 建议 |
|---------|------|-----|
| > 0.7 | 高风险 | 立即检查人员状态，启动紧急救援 |
| 0.4-0.7 | 中风险 | 增加监控频率，观察状态变化 |
| < 0.4 | 低风险 | 保持正常监控 |

### 对话功能

支持自然语言交互，可回答：
- 系统状态查询
- 风险分析报告
- 检测历史查询
- 技术支持问题
- 日常对话

---

## 使用示例

### Python客户端

```python
import requests
import base64

# 视频检测
response = requests.post('http://localhost:5000/api/detect/file', json={
    'filepath': '/uploads/test.mp4',
    'user_id': 1,
    'mode': 'fast'
})
print(response.json())

# 实时图像检测
with open('frame.jpg', 'rb') as f:
    image_data = base64.b64encode(f.read()).decode('utf-8')
    
response = requests.post('http://localhost:5000/api/detect', json={
    'image': image_data
})
print(response.json())

# AI对话
response = requests.post('http://localhost:5000/api/ai/chat', json={
    'message': '当前系统风险如何？',
    'user_id': 'admin'
})
print(response.json())
```

### cURL命令

```bash
# 视频检测
curl -X POST http://localhost:5000/api/detect/file \
  -H "Content-Type: application/json" \
  -d '{"filepath": "/uploads/test.mp4", "user_id": 1}'

# 实时检测
curl -X POST http://localhost:5000/api/detect \
  -H "Content-Type: application/json" \
  -d '{"image": "base64_encoded_image"}'

# AI对话
curl -X POST http://localhost:5000/api/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "帮我分析一下今天的检测结果", "user_id": "admin"}'
```

---

## 配置参数说明

### 规则配置（`config.py`）

| 参数 | 默认值 | 说明 |
|-----|-------|------|
| `fps` | 20.0 | 视频帧率 |
| `cgdd_frame_gap` | 10 | 重心检测帧间隔 |
| `v_cr` | 0.015 | 重心下降速度阈值 |
| `theta_cr_deg` | 60.0 | 身体倾斜角度阈值 |
| `p_cr` | 0.7 | 轮廓变形比例阈值 |
| `t_cr_sec` | 15.0 | 报警延迟时间 |

### 模型配置

| 参数 | 默认值 | 说明 |
|-----|-------|------|
| `hidden_size` | 128 | GRU隐藏层维度 |
| `num_layers` | 2 | GRU层数 |
| `dropout` | 0.3 | Dropout比例 |
| `sequence_length` | 16 | 输入序列长度 |

---

## 部署建议

### 生产环境配置

1. **使用 Gunicorn 作为 WSGI 服务器**

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 --timeout 120 app:app
```

2. **使用 Nginx 作为反向代理**

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_connect_timeout 60;
        proxy_send_timeout 60;
        proxy_read_timeout 60;
    }
    
    location /api/video/stream {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Range $http_range;
        proxy_set_header If-Range $http_if_range;
        proxy_set_header Host $host;
        proxy_buffering off;
        proxy_cache off;
        chunked_transfer_encoding on;
    }
}
```

3. **启用 HTTPS**

```bash
# 使用 Certbot 配置 SSL
certbot --nginx -d your-domain.com
```

---

## 注意事项

1. **视频文件处理**：系统会自动修复MP4文件使其支持流式播放（需要安装ffmpeg）
2. **中文文件名**：系统支持中文文件名上传和处理
3. **模型加载**：跌倒检测模型首次加载可能需要较长时间（约10-30秒）
4. **Ollama支持**：AI智能体功能需要安装Ollama并启动服务
5. **性能优化**：建议使用GPU加速模型推理（需安装CUDA）

---

## 技术特点

1. **双路检测融合**：深度学习行为识别 + 规则引擎判定
2. **实时处理**：支持视频流实时检测
3. **鲁棒性强**：多条件验证避免误报
4. **可配置性**：所有检测参数均可调整
5. **AI增强**：集成Ollama提供智能分析和对话功能
6. **完整API**：提供RESTful API支持前端集成