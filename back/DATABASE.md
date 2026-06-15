# 跌倒检测系统 - 数据库设计文档

## 概述

本文档详细描述跌倒检测系统的数据库设计，包括表结构、字段定义、数据关系和索引设计。

---

## 数据库环境

| 项目 | 描述 |
|-----|------|
| **数据库类型** | MySQL 8.0+ |
| **字符集** | utf8mb4 |
| **排序规则** | utf8mb4_unicode_ci |
| **数据库名称** | falldown_db |
| **ORM框架** | Flask-SQLAlchemy 3.0+ |

---

## 实体关系图 (ERD)

```
┌─────────────┐       1:N       ┌─────────────┐       1:N       ┌─────────────────────┐
│    User     │ ──────────────→ │   Camera    │ ──────────────→ │  DetectionRecord    │
│             │                 │             │                 │                     │
│ • id        │                 │ • id        │                 │ • id                │
│ • username  │                 │ • name      │                 │ • user_id          │
│ • email     │                 │ • location  │                 │ • camera_id        │
│ • role      │                 │ • url       │                 │ • filename         │
│ • password  │                 │ • user_id   │                 │ • file_path        │
│ • phone     │                 │ • status    │                 │ • screenshot_path  │
└─────────────┘                 └─────────────┘                 └──────────┬──────────┘
        │                                                                   │
        │ 1:N                                                              │ 1:N
        ↓                                                                  ↓
┌─────────────┐                                                    ┌─────────────┐
│ AlertRecord │                                                    │    Alert    │
│             │                                                    │             │
│ • id        │                                                    │ • id        │
│ • detection_id│                                                  │ • record_id │
│ • user_id   │                                                    │ • user_id   │
│ • M1/M2/M3  │                                                    │ • severity  │
│ • behavior  │                                                    │ • message   │
└─────────────┘                                                    └─────────────┘
        │
        │ 1:N
        ↓
┌─────────────────────┐       1:N       ┌─────────────────────┐
│ConversationSession │ ──────────────→ │ ConversationHistory │
│                     │                 │                     │
│ • id               │                 │ • id                │
│ • user_id          │                 │ • session_id        │
│ • title            │                 │ • role              │
└─────────────────────┘                 │ • content          │
                                         └─────────────────────┘

        1:N
        ↓
┌─────────────────────┐
│  AnalysisRecord    │
│                     │
│ • id                │
│ • user_id           │
│ • input_path        │
│ • output_path       │
│ • status            │
│ • fall_detected     │
└─────────────────────┘
```

---

## 表结构详细设计

### 1. user 表 - 用户信息

**对应模型**: `User` (app.py:119)

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|-------|------|-----|-------|------|
| **id** | INTEGER | PRIMARY KEY, AUTO_INCREMENT | - | 用户ID |
| **username** | VARCHAR(80) | UNIQUE, NOT NULL | - | 用户名 |
| **email** | VARCHAR(120) | UNIQUE, NOT NULL | - | 邮箱地址 |
| **password_hash** | VARCHAR(512) | - | - | 密码哈希值 |
| **role** | VARCHAR(20) | - | 'user' | 角色：admin/user |
| **phone** | VARCHAR(20) | - | NULL | 手机号码 |
| **created_at** | DATETIME | - | CURRENT_TIMESTAMP | 创建时间 |
| **last_login** | DATETIME | - | NULL | 最后登录时间 |
| **is_active** | BOOLEAN | - | TRUE | 是否活跃 |

**索引**:
- `idx_users_username` (username)
- `idx_users_email` (email)
- `idx_users_role` (role)

---

### 2. camera 表 - 摄像头信息

**对应模型**: `Camera` (app.py:143)

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|-------|------|-----|-------|------|
| **id** | INTEGER | PRIMARY KEY, AUTO_INCREMENT | - | 摄像头ID |
| **name** | VARCHAR(100) | NOT NULL | - | 摄像头名称 |
| **location** | VARCHAR(200) | - | NULL | 安装位置 |
| **camera_type** | VARCHAR(20) | - | 'rtsp' | 类型：rtsp/http/local |
| **url** | VARCHAR(500) | - | NULL | 视频流地址 |
| **is_active** | BOOLEAN | - | TRUE | 是否启用 |
| **user_id** | INTEGER | FOREIGN KEY | - | 所属用户ID |
| **created_at** | DATETIME | - | CURRENT_TIMESTAMP | 创建时间 |
| **last_check** | DATETIME | - | NULL | 最后检查时间 |
| **status** | VARCHAR(20) | - | 'offline' | 状态：online/offline |
| **resolution** | VARCHAR(20) | - | NULL | 分辨率 |
| **fps** | INTEGER | - | NULL | 帧率 |

**索引**:
- `idx_cameras_user_id` (user_id)
- `idx_cameras_status` (status)

---

### 3. detection_record 表 - 检测记录

**对应模型**: `DetectionRecord` (app.py:175)

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|-------|------|-----|-------|------|
| **id** | INTEGER | PRIMARY KEY, AUTO_INCREMENT | - | 记录ID |
| **user_id** | INTEGER | FOREIGN KEY | - | 用户ID |
| **camera_id** | INTEGER | FOREIGN KEY | NULL | 摄像头ID |
| **filename** | VARCHAR(255) | - | - | 原始文件名 |
| **file_path** | VARCHAR(500) | - | - | 原始文件路径 |
| **output_path** | VARCHAR(500) | - | NULL | 输出文件路径 |
| **screenshot_path** | VARCHAR(500) | - | NULL | 跌倒截图路径 |
| **total_frames** | INTEGER | - | NULL | 总帧数 |
| **detected_frames** | INTEGER | - | NULL | 检测到事件的帧数 |
| **fall_detected** | BOOLEAN | - | NULL | 是否检测到跌倒 |
| **alert_count** | INTEGER | - | NULL | 告警数量 |
| **status** | VARCHAR(20) | - | 'pending' | 状态：pending/processing/completed/failed |
| **label** | VARCHAR(50) | - | NULL | 检测标签 |
| **confidence** | FLOAT | - | NULL | 置信度 |
| **behavior** | VARCHAR(50) | - | NULL | 行为类型 |
| **detected_at** | DATETIME | - | NULL | 检测时间 |
| **created_at** | DATETIME | - | CURRENT_TIMESTAMP | 创建时间 |
| **completed_at** | DATETIME | - | NULL | 完成时间 |

**索引**:
- `idx_detection_user_id` (user_id)
- `idx_detection_status` (status)
- `idx_detection_created_at` (created_at)

---

### 4. alert_record 表 - 告警详情记录

**对应模型**: `AlertRecord` (app.py:221)

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|-------|------|-----|-------|------|
| **id** | INTEGER | PRIMARY KEY, AUTO_INCREMENT | - | 记录ID |
| **detection_id** | INTEGER | FOREIGN KEY | - | 所属检测记录ID |
| **user_id** | INTEGER | FOREIGN KEY | - | 用户ID |
| **frame_number** | INTEGER | - | - | 帧序号 |
| **timestamp** | FLOAT | - | - | 时间戳（秒） |
| **behavior** | VARCHAR(50) | - | - | 行为类型 |
| **confidence** | FLOAT | - | - | 置信度 |
| **M1** | BOOLEAN | - | FALSE | 条件1：重心下降触发 |
| **M2** | BOOLEAN | - | FALSE | 条件2：身体倾斜触发 |
| **M3** | BOOLEAN | - | FALSE | 条件3：形状变化触发 |
| **center_gravity_speed** | FLOAT | - | NULL | 重心下降速度 |
| **body_tilt_angle** | FLOAT | - | NULL | 身体倾斜角度（度） |
| **contour_ratio** | FLOAT | - | NULL | 轮廓宽高比 |
| **acknowledged** | BOOLEAN | - | FALSE | 是否已确认 |
| **acknowledged_at** | DATETIME | - | NULL | 确认时间 |
| **created_at** | DATETIME | - | CURRENT_TIMESTAMP | 创建时间 |

**索引**:
- `idx_alertrecord_detection_id` (detection_id)
- `idx_alertrecord_user_id` (user_id)
- `idx_alertrecord_acknowledged` (acknowledged)

---

### 5. alert 表 - 告警通知

**对应模型**: `Alert` (app.py:263)

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|-------|------|-----|-------|------|
| **id** | INTEGER | PRIMARY KEY, AUTO_INCREMENT | - | 告警ID |
| **record_id** | INTEGER | FOREIGN KEY | - | 检测记录ID |
| **user_id** | INTEGER | FOREIGN KEY | - | 目标用户ID |
| **alert_type** | VARCHAR(50) | - | - | 告警类型 |
| **severity** | VARCHAR(20) | - | NULL | 严重程度：low/medium/high |
| **message** | TEXT | - | - | 告警消息 |
| **title** | VARCHAR(100) | - | NULL | 告警标题 |
| **detection_type** | VARCHAR(50) | - | NULL | 检测类型 |
| **confidence** | FLOAT | - | NULL | 置信度 |
| **sent_to** | VARCHAR(200) | - | NULL | 发送目标 |
| **sent_at** | DATETIME | - | CURRENT_TIMESTAMP | 发送时间 |
| **acknowledged** | BOOLEAN | - | FALSE | 是否已确认 |
| **acknowledged_by** | INTEGER | FOREIGN KEY | NULL | 确认人ID |
| **acknowledged_at** | DATETIME | - | NULL | 确认时间 |
| **response_action** | TEXT | - | NULL | 响应动作 |

**索引**:
- `idx_alerts_user_id` (user_id)
- `idx_alerts_severity` (severity)
- `idx_alerts_acknowledged` (acknowledged)

---

### 6. conversation_session 表 - 对话会话

**对应模型**: `ConversationSession` (app.py:315)

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|-------|------|-----|-------|------|
| **id** | INTEGER | PRIMARY KEY, AUTO_INCREMENT | - | 会话ID |
| **user_id** | VARCHAR(100) | NOT NULL | - | 用户ID或'admin' |
| **title** | VARCHAR(200) | NOT NULL | '新对话' | 会话标题 |
| **created_at** | DATETIME | - | CURRENT_TIMESTAMP | 创建时间 |
| **updated_at** | DATETIME | - | CURRENT_TIMESTAMP | 更新时间 |

**索引**:
- `idx_conversation_user_id` (user_id)

---

### 7. conversation_history 表 - 对话历史

**对应模型**: `ConversationHistory` (app.py:333)

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|-------|------|-----|-------|------|
| **id** | INTEGER | PRIMARY KEY, AUTO_INCREMENT | - | 消息ID |
| **session_id** | INTEGER | FOREIGN KEY, NOT NULL | - | 会话ID |
| **user_id** | VARCHAR(100) | NOT NULL | - | 用户ID |
| **role** | VARCHAR(20) | NOT NULL | - | 角色：user/assistant |
| **content** | TEXT | NOT NULL | - | 消息内容 |
| **timestamp** | DATETIME | - | CURRENT_TIMESTAMP | 时间戳 |

**索引**:
- `idx_history_session_id` (session_id)
- `idx_history_user_id` (user_id)

---

### 8. analysis_record 表 - 分析记录

**对应模型**: `AnalysisRecord` (app.py:353)

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|-------|------|-----|-------|------|
| **id** | INTEGER | PRIMARY KEY, AUTO_INCREMENT | - | 记录ID |
| **user_id** | INTEGER | FOREIGN KEY, NOT NULL | - | 用户ID |
| **original_filename** | VARCHAR(255) | NOT NULL | - | 原始文件名 |
| **processed_filename** | VARCHAR(255) | - | NULL | 处理后文件名 |
| **input_path** | VARCHAR(500) | NOT NULL | - | 输入路径 |
| **output_path** | VARCHAR(500) | - | NULL | 输出路径 |
| **file_type** | VARCHAR(20) | NOT NULL | - | 文件类型 |
| **status** | VARCHAR(20) | - | 'processing' | 状态 |
| **total_frames** | INTEGER | - | 0 | 总帧数 |
| **detected_frames** | INTEGER | - | 0 | 检测帧数 |
| **fall_detected** | BOOLEAN | - | FALSE | 是否检测到跌倒 |
| **alert_count** | INTEGER | - | 0 | 告警数量 |
| **ai_analysis** | TEXT | - | NULL | AI分析结果 |
| **created_at** | DATETIME | - | CURRENT_TIMESTAMP | 创建时间 |
| **completed_at** | DATETIME | - | NULL | 完成时间 |

**索引**:
- `idx_analysis_user_id` (user_id)
- `idx_analysis_status` (status)

---

## 数据库关系总结

| 关系 | 类型 | 说明 |
|-----|------|------|
| User → Camera | 1:N | 一个用户可拥有多个摄像头 |
| User → DetectionRecord | 1:N | 一个用户可拥有多个检测记录 |
| User → AlertRecord | 1:N | 一个用户可拥有多个告警详情记录 |
| User → Alert | 1:N | 一个用户可拥有多个告警通知 |
| User → AnalysisRecord | 1:N | 一个用户可拥有多个分析记录 |
| Camera → DetectionRecord | 1:N | 一个摄像头可有多个检测记录 |
| DetectionRecord → AlertRecord | 1:N | 一个检测记录可有多个告警详情 |
| DetectionRecord → Alert | 1:N | 一个检测记录可触发多个告警通知 |
| ConversationSession → ConversationHistory | 1:N | 一个会话可有多条消息 |

---

## 数据库初始化 SQL

```sql
-- 创建数据库
CREATE DATABASE IF NOT EXISTS falldown_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

-- 使用数据库
USE falldown_db;

-- 创建用户表
CREATE TABLE IF NOT EXISTS user (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(80) NOT NULL UNIQUE,
  email VARCHAR(120) NOT NULL UNIQUE,
  password_hash VARCHAR(512),
  role VARCHAR(20) DEFAULT 'user',
  phone VARCHAR(20),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  last_login DATETIME,
  is_active BOOLEAN DEFAULT TRUE,
  INDEX idx_users_username (username),
  INDEX idx_users_email (email),
  INDEX idx_users_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 创建摄像头表
CREATE TABLE IF NOT EXISTS camera (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  location VARCHAR(200),
  camera_type VARCHAR(20) DEFAULT 'rtsp',
  url VARCHAR(500),
  is_active BOOLEAN DEFAULT TRUE,
  user_id INT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  last_check DATETIME,
  status VARCHAR(20) DEFAULT 'offline',
  resolution VARCHAR(20),
  fps INT,
  INDEX idx_cameras_user_id (user_id),
  INDEX idx_cameras_status (status),
  FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 创建检测记录表
CREATE TABLE IF NOT EXISTS detection_record (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT,
  camera_id INT,
  filename VARCHAR(255),
  file_path VARCHAR(500),
  output_path VARCHAR(500),
  screenshot_path VARCHAR(500),
  total_frames INT,
  detected_frames INT,
  fall_detected BOOLEAN,
  alert_count INT,
  status VARCHAR(20) DEFAULT 'pending',
  label VARCHAR(50),
  confidence FLOAT,
  behavior VARCHAR(50),
  detected_at DATETIME,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  completed_at DATETIME,
  INDEX idx_detection_user_id (user_id),
  INDEX idx_detection_status (status),
  INDEX idx_detection_created_at (created_at),
  FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
  FOREIGN KEY (camera_id) REFERENCES camera(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 创建告警详情表
CREATE TABLE IF NOT EXISTS alert_record (
  id INT AUTO_INCREMENT PRIMARY KEY,
  detection_id INT,
  user_id INT,
  frame_number INT,
  timestamp FLOAT,
  behavior VARCHAR(50),
  confidence FLOAT,
  M1 BOOLEAN DEFAULT FALSE,
  M2 BOOLEAN DEFAULT FALSE,
  M3 BOOLEAN DEFAULT FALSE,
  center_gravity_speed FLOAT,
  body_tilt_angle FLOAT,
  contour_ratio FLOAT,
  acknowledged BOOLEAN DEFAULT FALSE,
  acknowledged_at DATETIME,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_alertrecord_detection_id (detection_id),
  INDEX idx_alertrecord_user_id (user_id),
  INDEX idx_alertrecord_acknowledged (acknowledged),
  FOREIGN KEY (detection_id) REFERENCES detection_record(id) ON DELETE CASCADE,
  FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 创建告警通知表
CREATE TABLE IF NOT EXISTS alert (
  id INT AUTO_INCREMENT PRIMARY KEY,
  record_id INT,
  user_id INT,
  alert_type VARCHAR(50),
  severity VARCHAR(20),
  message TEXT,
  title VARCHAR(100),
  detection_type VARCHAR(50),
  confidence FLOAT,
  sent_to VARCHAR(200),
  sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  acknowledged BOOLEAN DEFAULT FALSE,
  acknowledged_by INT,
  acknowledged_at DATETIME,
  response_action TEXT,
  INDEX idx_alerts_user_id (user_id),
  INDEX idx_alerts_severity (severity),
  INDEX idx_alerts_acknowledged (acknowledged),
  FOREIGN KEY (record_id) REFERENCES detection_record(id) ON DELETE CASCADE,
  FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
  FOREIGN KEY (acknowledged_by) REFERENCES user(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 创建对话会话表
CREATE TABLE IF NOT EXISTS conversation_session (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id VARCHAR(100) NOT NULL,
  title VARCHAR(200) NOT NULL DEFAULT '新对话',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_conversation_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 创建对话历史表
CREATE TABLE IF NOT EXISTS conversation_history (
  id INT AUTO_INCREMENT PRIMARY KEY,
  session_id INT NOT NULL,
  user_id VARCHAR(100) NOT NULL,
  role VARCHAR(20) NOT NULL,
  content TEXT NOT NULL,
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_history_session_id (session_id),
  INDEX idx_history_user_id (user_id),
  FOREIGN KEY (session_id) REFERENCES conversation_session(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 创建分析记录表
CREATE TABLE IF NOT EXISTS analysis_record (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  original_filename VARCHAR(255) NOT NULL,
  processed_filename VARCHAR(255),
  input_path VARCHAR(500) NOT NULL,
  output_path VARCHAR(500),
  file_type VARCHAR(20) NOT NULL,
  status VARCHAR(20) DEFAULT 'processing',
  total_frames INT DEFAULT 0,
  detected_frames INT DEFAULT 0,
  fall_detected BOOLEAN DEFAULT FALSE,
  alert_count INT DEFAULT 0,
  ai_analysis TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  completed_at DATETIME,
  INDEX idx_analysis_user_id (user_id),
  INDEX idx_analysis_status (status),
  FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

---

## 数据字典

### 枚举值定义

| 字段 | 枚举值 | 说明 |
|-----|-------|------|
| user.role | admin, user | 用户角色 |
| camera.camera_type | rtsp, http, local | 摄像头类型 |
| camera.status | online, offline | 摄像头状态 |
| detection_record.status | pending, processing, completed, failed | 检测状态 |
| alert.severity | low, medium, high | 告警严重程度 |
| alert.detection_type | fall, activity, unknown | 检测类型 |
| conversation_history.role | user, assistant | 消息角色 |
| analysis_record.status | processing, completed, failed | 分析状态 |

---

## 索引优化建议

### 查询优化

1. **用户登录查询**
   ```sql
   -- 优化前
   SELECT * FROM user WHERE username = 'xxx' AND password_hash = 'xxx';

   -- 索引优化
   CREATE INDEX idx_users_username_password ON user(username, password_hash);
   ```

2. **按用户查询检测记录**
   ```sql
   -- 优化前
   SELECT * FROM detection_record WHERE user_id = 1 ORDER BY created_at DESC LIMIT 20;

   -- 索引优化（已在表定义中）
   -- idx_detection_user_id, idx_detection_created_at
   ```

3. **未确认告警查询**
   ```sql
   -- 优化前
   SELECT * FROM alert WHERE acknowledged = FALSE AND severity = 'high';

   -- 索引优化（已在表定义中）
   -- idx_alerts_severity, idx_alerts_acknowledged
   ```

### 复合索引建议

```sql
-- 联合索引：用户+创建时间（用于分页查询）
CREATE INDEX idx_detection_user_created ON detection_record(user_id, created_at DESC);

-- 联合索引：告警严重程度+确认状态（用于告警统计）
CREATE INDEX idx_alerts_severity_ack ON alert(severity, acknowledged);

-- 联合索引：会话+时间（用于对话历史查询）
CREATE INDEX idx_history_session_timestamp ON conversation_history(session_id, timestamp DESC);
```

---

## 数据备份策略

### 备份频率

| 类型 | 频率 | 保留周期 |
|-----|------|---------|
| 每日增量备份 | 每天 02:00 | 7天 |
| 每周全量备份 | 每周日 02:00 | 30天 |
| 每月归档备份 | 每月1号 02:00 | 永久 |

### 备份命令示例

```bash
# 全量备份
mysqldump -u username -p falldown_db > falldown_db_backup_$(date +%Y%m%d).sql

# 压缩备份
mysqldump -u username -p falldown_db | gzip > falldown_db_backup_$(date +%Y%m%d).sql.gz

# 备份特定表
mysqldump -u username -p falldown_db user camera detection_record > falldown_db_core_$(date +%Y%m%d).sql
```

---

## 代码中的模型定义

以下是 `app.py` 中的实际模型定义（供开发参考）：

```python
# app.py:119
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(512))
    role = db.Column(db.String(20), default='user')
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)

# app.py:143
class Camera(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200))
    camera_type = db.Column(db.String(20), default='rtsp')
    url = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, default=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)
    last_check = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='offline')
    resolution = db.Column(db.String(20))
    fps = db.Column(db.Integer)

# app.py:175
class DetectionRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    camera_id = db.Column(db.Integer, db.ForeignKey('camera.id'))
    filename = db.Column(db.String(255))
    file_path = db.Column(db.String(500))
    output_path = db.Column(db.String(500))
    screenshot_path = db.Column(db.String(500))  # 跌倒截图路径
    total_frames = db.Column(db.Integer)
    detected_frames = db.Column(db.Integer)
    fall_detected = db.Column(db.Boolean)
    alert_count = db.Column(db.Integer)
    status = db.Column(db.String(20), default='pending')
    label = db.Column(db.String(50))
    confidence = db.Column(db.Float)
    behavior = db.Column(db.String(50))
    detected_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)
    completed_at = db.Column(db.DateTime)

# app.py:221
class AlertRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    detection_id = db.Column(db.Integer, db.ForeignKey('detection_record.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    frame_number = db.Column(db.Integer)
    timestamp = db.Column(db.Float)
    behavior = db.Column(db.String(50))
    confidence = db.Column(db.Float)
    M1 = db.Column(db.Boolean)  # 重心下降检测
    M2 = db.Column(db.Boolean)  # 身体倾斜检测
    M3 = db.Column(db.Boolean)  # 形状变化检测
    center_gravity_speed = db.Column(db.Float)
    body_tilt_angle = db.Column(db.Float)
    contour_ratio = db.Column(db.Float)
    acknowledged = db.Column(db.Boolean, default=False)
    acknowledged_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)

# app.py:263
class Alert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    record_id = db.Column(db.Integer, db.ForeignKey('detection_record.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    alert_type = db.Column(db.String(50))
    severity = db.Column(db.String(20))
    message = db.Column(db.Text)
    title = db.Column(db.String(100))
    detection_type = db.Column(db.String(50))
    confidence = db.Column(db.Float)
    sent_to = db.Column(db.String(200))
    sent_at = db.Column(db.DateTime, default=datetime.datetime.now)
    acknowledged = db.Column(db.Boolean, default=False)
    acknowledged_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    acknowledged_at = db.Column(db.DateTime)
    response_action = db.Column(db.Text)

# app.py:315
class ConversationSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(200), nullable=False, default='新对话')
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

# app.py:333
class ConversationHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('conversation_session.id'), nullable=False)
    user_id = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'user' or 'assistant'
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.now)

# app.py:353
class AnalysisRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    processed_filename = db.Column(db.String(255))
    input_path = db.Column(db.String(500), nullable=False)
    output_path = db.Column(db.String(500))
    file_type = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='processing')
    total_frames = db.Column(db.Integer, default=0)
    detected_frames = db.Column(db.Integer, default=0)
    fall_detected = db.Column(db.Boolean, default=False)
    alert_count = db.Column(db.Integer, default=0)
    ai_analysis = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)
    completed_at = db.Column(db.DateTime)
```