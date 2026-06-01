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
┌─────────────┐       1:N       ┌─────────────┐       1:N       ┌─────────────────┐
│    User     │ ──────────────→ │   Camera    │ ──────────────→ │DetectionRecord  │
│             │                 │             │                 │                 │
│ • id        │                 │ • id        │                 │ • id            │
│ • username  │                 │ • name      │                 │ • user_id       │
│ • email     │                 │ • location  │                 │ • camera_id     │
│ • role      │                 │ • user_id   │                 │ • filename      │
│ • password  │                 │ • url       │                 │ • fall_detected │
└─────────────┘                 └─────────────┘                 └────────┬────────┘
        │                                                                 │
        │ 1:N                                                            │ 1:N
        ↓                                                                ↓
┌─────────────┐                                                  ┌─────────────┐
│   Alert     │                                                  │AlertRecord │
│             │                                                  │             │
│ • id        │                                                  │ • id        │
│ • user_id   │                                                  │ • detection_id│
│ • severity  │                                                  │ • behavior  │
│ • message   │                                                  │ • M1/M2/M3  │
└─────────────┘                                                  └─────────────┘
        │
        │ 1:N
        ↓
┌─────────────────────┐
│ConversationSession │
│                     │
│ • id                │
│ • user_id           │
│ • title             │
└──────────┬──────────┘
           │ 1:N
           ↓
┌─────────────────────┐
│ConversationHistory  │
│                     │
│ • id                │
│ • session_id        │
│ • role              │
│ • content           │
└─────────────────────┘
```

---

## 表结构详细设计

### 1. users 表 - 用户信息

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

**索引**：
- `idx_users_username` (username)
- `idx_users_email` (email)
- `idx_users_role` (role)

---

### 2. cameras 表 - 摄像头信息

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

**索引**：
- `idx_cameras_user_id` (user_id)
- `idx_cameras_status` (status)

---

### 3. detection_records 表 - 检测记录

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|-------|------|-----|-------|------|
| **id** | INTEGER | PRIMARY KEY, AUTO_INCREMENT | - | 记录ID |
| **user_id** | INTEGER | FOREIGN KEY | - | 用户ID |
| **camera_id** | INTEGER | FOREIGN KEY | NULL | 摄像头ID（可为空） |
| **filename** | VARCHAR(255) | - | - | 原始文件名 |
| **file_path** | VARCHAR(500) | - | - | 原始文件路径 |
| **output_path** | VARCHAR(500) | - | NULL | 输出文件路径 |
| **total_frames** | INTEGER | - | NULL | 总帧数 |
| **detected_frames** | INTEGER | - | NULL | 检测到事件的帧数 |
| **fall_detected** | BOOLEAN | - | NULL | 是否检测到跌倒 |
| **alert_count** | INTEGER | - | NULL | 告警数量 |
| **status** | VARCHAR(20) | - | 'pending' | 状态：pending/processing/completed/failed |
| **created_at** | DATETIME | - | CURRENT_TIMESTAMP | 创建时间 |
| **completed_at** | DATETIME | - | NULL | 完成时间 |

**索引**：
- `idx_detection_user_id` (user_id)
- `idx_detection_status` (status)
- `idx_detection_created_at` (created_at)

---

### 4. alert_records 表 - 告警详情记录

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

**索引**：
- `idx_alertrecord_detection_id` (detection_id)
- `idx_alertrecord_user_id` (user_id)
- `idx_alertrecord_acknowledged` (acknowledged)

---

### 5. alerts 表 - 告警通知

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|-------|------|-----|-------|------|
| **id** | INTEGER | PRIMARY KEY, AUTO_INCREMENT | - | 告警ID |
| **record_id** | INTEGER | FOREIGN KEY | - | 检测记录ID |
| **user_id** | INTEGER | FOREIGN KEY | - | 目标用户ID |
| **alert_type** | VARCHAR(50) | - | - | 告警类型 |
| **severity** | VARCHAR(20) | - | 'medium' | 严重程度：low/medium/high |
| **message** | TEXT | - | - | 告警消息 |
| **title** | VARCHAR(100) | - | '跌倒检测告警' | 告警标题 |
| **detection_type** | VARCHAR(50) | - | 'fall' | 检测类型 |
| **confidence** | FLOAT | - | 0.0 | 置信度 |
| **sent_to** | VARCHAR(200) | - | NULL | 发送目标 |
| **sent_at** | DATETIME | - | CURRENT_TIMESTAMP | 发送时间 |
| **acknowledged** | BOOLEAN | - | FALSE | 是否已确认 |
| **acknowledged_by** | INTEGER | FOREIGN KEY | NULL | 确认人ID |
| **acknowledged_at** | DATETIME | - | NULL | 确认时间 |
| **response_action** | TEXT | - | NULL | 响应动作 |

**索引**：
- `idx_alerts_user_id` (user_id)
- `idx_alerts_severity` (severity)
- `idx_alerts_acknowledged` (acknowledged)

---

### 6. system_config 表 - 系统配置

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|-------|------|-----|-------|------|
| **id** | INTEGER | PRIMARY KEY, AUTO_INCREMENT | - | 配置ID |
| **key** | VARCHAR(100) | UNIQUE | - | 配置键名 |
| **value** | TEXT | - | - | 配置值 |

---

### 7. conversation_sessions 表 - 对话会话

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|-------|------|-----|-------|------|
| **id** | INTEGER | PRIMARY KEY, AUTO_INCREMENT | - | 会话ID |
| **user_id** | VARCHAR(100) | NOT NULL | - | 用户ID或'admin' |
| **title** | VARCHAR(200) | NOT NULL | '新对话' | 会话标题 |
| **created_at** | DATETIME | - | CURRENT_TIMESTAMP | 创建时间 |
| **updated_at** | DATETIME | - | CURRENT_TIMESTAMP | 更新时间 |

**索引**：
- `idx_conversation_user_id` (user_id)

---

### 8. conversation_history 表 - 对话历史

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|-------|------|-----|-------|------|
| **id** | INTEGER | PRIMARY KEY, AUTO_INCREMENT | - | 消息ID |
| **session_id** | INTEGER | FOREIGN KEY, NOT NULL | - | 会话ID |
| **user_id** | VARCHAR(100) | NOT NULL | - | 用户ID |
| **role** | VARCHAR(20) | NOT NULL | - | 角色：user/assistant |
| **content** | TEXT | NOT NULL | - | 消息内容 |
| **timestamp** | DATETIME | - | CURRENT_TIMESTAMP | 时间戳 |

**索引**：
- `idx_history_session_id` (session_id)
- `idx_history_user_id` (user_id)

---

### 9. analysis_records 表 - 分析记录

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

**索引**：
- `idx_analysis_user_id` (user_id)
- `idx_analysis_status` (status)

---

## 数据库关系总结

| 关系 | 类型 | 说明 |
|-----|------|-----|
| User → Camera | 1:N | 一个用户可拥有多个摄像头 |
| User → DetectionRecord | 1:N | 一个用户可拥有多个检测记录 |
| User → Alert | 1:N | 一个用户可拥有多个告警 |
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
CREATE TABLE IF NOT EXISTS users (
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
CREATE TABLE IF NOT EXISTS cameras (
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
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 创建检测记录表
CREATE TABLE IF NOT EXISTS detection_records (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT,
  camera_id INT,
  filename VARCHAR(255),
  file_path VARCHAR(500),
  output_path VARCHAR(500),
  total_frames INT,
  detected_frames INT,
  fall_detected BOOLEAN,
  alert_count INT,
  status VARCHAR(20) DEFAULT 'pending',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  completed_at DATETIME,
  INDEX idx_detection_user_id (user_id),
  INDEX idx_detection_status (status),
  INDEX idx_detection_created_at (created_at),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (camera_id) REFERENCES cameras(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 创建告警详情表
CREATE TABLE IF NOT EXISTS alert_records (
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
  FOREIGN KEY (detection_id) REFERENCES detection_records(id) ON DELETE CASCADE,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 创建告警通知表
CREATE TABLE IF NOT EXISTS alerts (
  id INT AUTO_INCREMENT PRIMARY KEY,
  record_id INT,
  user_id INT,
  alert_type VARCHAR(50),
  severity VARCHAR(20) DEFAULT 'medium',
  message TEXT,
  title VARCHAR(100) DEFAULT '跌倒检测告警',
  detection_type VARCHAR(50) DEFAULT 'fall',
  confidence FLOAT DEFAULT 0.0,
  sent_to VARCHAR(200),
  sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  acknowledged BOOLEAN DEFAULT FALSE,
  acknowledged_by INT,
  acknowledged_at DATETIME,
  response_action TEXT,
  INDEX idx_alerts_user_id (user_id),
  INDEX idx_alerts_severity (severity),
  INDEX idx_alerts_acknowledged (acknowledged),
  FOREIGN KEY (record_id) REFERENCES detection_records(id) ON DELETE CASCADE,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (acknowledged_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 创建系统配置表
CREATE TABLE IF NOT EXISTS system_config (
  id INT AUTO_INCREMENT PRIMARY KEY,
  key VARCHAR(100) UNIQUE,
  value TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 创建对话会话表
CREATE TABLE IF NOT EXISTS conversation_sessions (
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
  FOREIGN KEY (session_id) REFERENCES conversation_sessions(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 创建分析记录表
CREATE TABLE IF NOT EXISTS analysis_records (
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
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

---

## 数据字典

### 枚举值定义

| 字段 | 枚举值 | 说明 |
|-----|-------|------|
| users.role | admin, user | 用户角色 |
| cameras.camera_type | rtsp, http, local | 摄像头类型 |
| cameras.status | online, offline | 摄像头状态 |
| detection_records.status | pending, processing, completed, failed | 检测状态 |
| alerts.severity | low, medium, high | 告警严重程度 |
| alerts.detection_type | fall, activity, unknown | 检测类型 |
| conversation_history.role | user, assistant | 消息角色 |

---

## 索引优化建议

### 查询优化

1. **用户登录查询**
   ```sql
   -- 优化前
   SELECT * FROM users WHERE username = 'xxx' AND password_hash = 'xxx';
   
   -- 索引优化
   CREATE INDEX idx_users_username_password ON users(username, password_hash);
   ```

2. **按用户查询检测记录**
   ```sql
   -- 优化前
   SELECT * FROM detection_records WHERE user_id = 1 ORDER BY created_at DESC LIMIT 20;
   
   -- 索引优化（已在表定义中）
   -- idx_detection_user_id, idx_detection_created_at
   ```

3. **未确认告警查询**
   ```sql
   -- 优化前
   SELECT * FROM alerts WHERE acknowledged = FALSE AND severity = 'high';
   
   -- 索引优化（已在表定义中）
   -- idx_alerts_severity, idx_alerts_acknowledged
   ```

### 复合索引建议

```sql
-- 联合索引：用户+创建时间（用于分页查询）
CREATE INDEX idx_detection_user_created ON detection_records(user_id, created_at DESC);

-- 联合索引：告警严重程度+确认状态（用于告警统计）
CREATE INDEX idx_alerts_severity_ack ON alerts(severity, acknowledged);

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
mysqldump -u username -p falldown_db users cameras > falldown_db_core_$(date +%Y%m%d).sql
```

---

## 安全注意事项

1. **密码存储**：密码必须使用 bcrypt 或类似算法哈希存储，禁止明文存储
2. **SQL注入**：使用 ORM 参数化查询，禁止字符串拼接
3. **敏感数据**：email、phone 等字段需要加密存储或脱敏处理
4. **备份加密**：数据库备份文件需要加密存储
5. **访问控制**：数据库用户权限最小化原则