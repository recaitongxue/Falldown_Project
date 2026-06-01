# 跌倒检测系统项目汇报

## 一、项目概述

### 1.1 项目背景

随着人口老龄化加剧，老年人跌倒已成为重大公共安全问题。据统计，跌倒是65岁以上老年人意外伤害死亡的首要原因。及时准确的跌倒检测对于降低伤害程度、提高救援效率具有重要意义。

本项目开发了一套基于深度学习与多规则融合的智能跌倒检测系统，融合了骨骼姿态识别、时序行为分析、多维度规则判定等前沿技术，实现了高准确率的跌倒检测与实时告警。

### 1.2 项目目标

- 实现高准确率的跌倒行为识别与检测
- 提供实时视频流分析与告警功能
- 构建完整的用户管理、摄像头管理与数据记录体系
- 集成AI智能体，提供风险分析与对话交互能力
- 支持多场景应用：家庭监护、养老院、医院等

---

## 二、技术架构

### 2.1 系统架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           前端展示层 (Vue.js)                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐   │
│  │   用户端界面     │  │   管理端界面     │  │     AI助手界面           │   │
│  │  - 实时监控     │  │  - 用户管理     │  │   - 风险分析对话         │   │
│  │  - 摄像头管理   │  │  - 摄像头管理   │  │   - 报告生成            │   │
│  │  - 视频上传     │  │  - 数据统计     │  │   - 智能问答            │   │
│  │  - 检测历史     │  │  - 告警中心     │  │                         │   │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          Flask 后端服务层                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐   │
│  │   REST API      │  │   WebSocket     │  │     AI 智能体           │   │
│  │  - /api/upload  │  │  - 实时通信     │  │   - Ollama + Qwen3     │   │
│  │  - /api/detect │  │  - 状态推送     │  │   - 风险分析            │   │
│  │  - /api/cameras│  │                 │  │   - 对话生成            │   │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
┌─────────────────────────────────┐  ┌─────────────────────────────────┐
│      跌倒检测引擎                │  │        数据库层                 │
│  ┌───────────────────────────┐  │  │  ┌───────────────────────────┐  │
│  │   FallActionGRU 模型      │  │  │  │  MySQL 8.0               │  │
│  │   行为识别（7类行为）     │  │  │  │  - users表                │  │
│  │   输入：69维特征向量      │  │  │  │  - cameras表              │  │
│  │   输出：行为类别+置信度   │  │  │  │  - detection_records表    │  │
│  └───────────────────────────┘  │  │  │  - alert_records表        │  │
│  ┌───────────────────────────┐  │  │  │  - alerts表               │  │
│  │   FallRuleEngine 规则引擎 │  │  │  │  - analysis_records表     │  │
│  │   五重判定算法            │  │  │  │  - conversations会话表     │  │
│  │   M1:重心下降检测         │  │  │  │                           │  │
│  │   M2:身体倾斜检测         │  │  │  └───────────────────────────┘  │
│  │   M3:形状变化检测         │  │  └─────────────────────────────────┘
│  │   M4:关节角度检测         │  │
│  │   M5:身体高度检测         │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │   PoseExtractor 骨骼提取   │  │
│  │   MediaPipe 33关键点      │  │
│  │   生成69维特征向量        │  │
│  └───────────────────────────┘  │
└─────────────────────────────────┘
```

### 2.2 技术栈

| 层次 | 技术选型 | 说明 |
|------|----------|------|
| 前端框架 | Vue.js 3 + Element Plus | 现代化响应式UI框架 |
| 后端框架 | Flask | 轻量级Python Web框架 |
| 深度学习 | PyTorch | 神经网络训练与推理 |
| 姿态识别 | MediaPipe Pose | Google开源33点骨骼检测 |
| 数据库 | MySQL 8.0 | 关系型数据存储 |
| AI智能体 | Ollama + 动态模型 | 本地部署大语言模型 |
| 视频处理 | OpenCV | 视频流处理与分析 |

---

## 三、骨骼检测模块

### 3.1 MediaPipe 33点骨骼检测

系统采用Google的MediaPipe Pose模型进行人体骨骼检测，可精确识别33个人体关键点：

| 编号 | 关键点名称 | 描述 | 编号 | 关键点名称 | 描述 |
|------|-----------|------|------|-----------|------|
| 0 | NOSE | 鼻子 | 17 | LEFT_PINKY | 左小指 |
| 1-3 | LEFT_EYE_* | 左眼系列 | 18 | RIGHT_PINKY | 右小指 |
| 4-6 | RIGHT_EYE_* | 右眼系列 | 19-21 | LEFT_INDEX/THUMB | 左手系列 |
| 7-8 | EARS | 耳朵 | 22 | RIGHT_INDEX | 右手食指 |
| 9-10 | MOUTH | 嘴巴 | 23 | RIGHT_THUMB | 右手拇指 |
| 11 | LEFT_SHOULDER | 左肩 | 24 | LEFT_HIP | 左髋关节 |
| 12 | RIGHT_SHOULDER | 右肩 | 25 | LEFT_KNEE | 左膝关节 |
| 13 | LEFT_ELBOW | 左肘关节 | 26 | LEFT_ANKLE | 左踝关节 |
| 14 | RIGHT_ELBOW | 右肘关节 | 27 | RIGHT_ANKLE | 右踝关节 |
| 15-16 | WRISTS | 手腕 | 28-32 | FEET | 脚部系列 |

### 3.2 骨骼连接关系

```python
POSE_CONNECTIONS = [
    # 头部连接
    (NOSE, LEFT_EYE_INNER), (LEFT_EYE_INNER, LEFT_EYE), 
    (LEFT_EYE, LEFT_EYE_OUTER), (LEFT_EYE_OUTER, LEFT_EAR),
    (NOSE, RIGHT_EYE_INNER), (RIGHT_EYE_INNER, RIGHT_EYE),
    (RIGHT_EYE, RIGHT_EYE_OUTER), (RIGHT_EYE_OUTER, RIGHT_EAR),
    (MOUTH_LEFT, MOUTH_RIGHT),
    
    # 上肢连接
    (LEFT_SHOULDER, RIGHT_SHOULDER),
    (LEFT_SHOULDER, LEFT_ELBOW), (LEFT_ELBOW, LEFT_WRIST),
    (RIGHT_SHOULDER, RIGHT_ELBOW), (RIGHT_ELBOW, RIGHT_WRIST),
    
    # 躯干连接
    (LEFT_SHOULDER, LEFT_HIP), (RIGHT_SHOULDER, RIGHT_HIP),
    (LEFT_HIP, RIGHT_HIP),
    
    # 下肢连接
    (LEFT_HIP, LEFT_KNEE), (LEFT_KNEE, LEFT_ANKLE),
    (RIGHT_HIP, RIGHT_KNEE), (RIGHT_KNEE, RIGHT_ANKLE),
    
    # 脚部连接
    (LEFT_ANKLE, LEFT_HEEL), (LEFT_HEEL, LEFT_FOOT_INDEX),
    (RIGHT_ANKLE, RIGHT_HEEL), (RIGHT_HEEL, RIGHT_FOOT_INDEX),
]
```

---

## 四、特征提取模块

### 4.1 特征向量构成

系统从MediaPipe 33点骨骼数据中提取69维特征向量作为行为识别模型的输入：

```
69维特征向量 = 66维坐标特征 + 3维额外特征

66维坐标特征：
  - 33个关键点的X坐标 (33维)
  - 33个关键点的Y坐标 (33维)

3维额外特征：
  - center_y：重心Y坐标归一化值
  - tilt_deg/180：身体倾斜角度归一化值
  - wh_ratio：身体宽高比
```

### 4.2 核心特征计算

```python
# 重心Y坐标（臀部中心）
center_y = (left_hip[1] + right_hip[1]) / 2.0 / image_height

# 身体倾斜角度（头部到腿部的角度）
dx = abs(head[0] - leg_center[0]) + 1e-6
dy = abs(head[1] - leg_center[1])
tilt_deg = arctan(dy / dx)  # 弧度转角度

# 宽高比（用于检测身体形状变化）
body_width = xmax - xmin
body_height = ymax - ymin
wh_ratio = body_width / body_height

# 关节角度计算
def calculate_angle(p1, p2, p3):
    """计算三点形成的角度（p2为顶点）"""
    v1 = p1 - p2
    v2 = p3 - p2
    cos_angle = dot(v1, v2) / (|v1| * |v2|)
    return arccos(cos_angle) * 180 / pi
```

### 4.3 特征数据类型

| 特征类型 | 维度 | 描述 | 范围 |
|----------|------|------|------|
| keypoints.x | 33 | 33个关键点X坐标归一化值 | [0, 1] |
| keypoints.y | 33 | 33个关键点Y坐标归一化值 | [0, 1] |
| center_y | 1 | 重心Y坐标归一化值 | [0, 1] |
| tilt_deg/180 | 1 | 倾斜角度归一化值 | [0, 1] |
| wh_ratio | 1 | 宽高比 | [0, ∞) |
| **总计** | **69** | | |

---

## 五、行为识别模型

### 5.1 FallActionGRU 网络架构

本项目采用双向GRU（门控循环单元）神经网络进行时序行为识别，网络结构如下：

```python
class FallActionGRU(nn.Module):
    def __init__(self, input_size=69, hidden_size=128, 
                 num_layers=2, num_classes=7, dropout=0.2):
        super().__init__()
        self.gru = nn.GRU(
            input_size=69,        # 输入维度：69维特征向量
            hidden_size=128,      # 隐藏层维度：128
            num_layers=2,         # 循环层数：2层
            batch_first=True,     # 输入格式：(batch, seq, feature)
            dropout=0.2 if num_layers > 1 else 0,  # 层间dropout
            bidirectional=True   # 双向GRU
        )
        self.cls = nn.Sequential(
            nn.LayerNorm(128 * 2),  # 层归一化（双向输出256维）
            nn.Linear(256, 128),    # 全连接层
            nn.ReLU(inplace=True),  # ReLU激活
            nn.Dropout(0.2),        # Dropout正则化
            nn.Linear(128, 7),      # 输出层：7类行为
        )
```

### 5.2 模型参数配置

| 参数名称 | 配置值 | 说明 |
|----------|--------|------|
| input_size | 69 | 输入特征维度 |
| hidden_size | 128 | GRU隐藏层维度 |
| num_layers | 2 | GRU层数 |
| dropout | 0.2 | Dropout比例 |
| bidirectional | True | 双向GRU |
| sequence_length | 24 | 输入序列长度（帧数） |
| num_classes | 7 | 行为类别数 |

### 5.3 行为类别定义

| 类别编号 | 英文名称 | 中文名称 | 描述 |
|----------|----------|----------|------|
| 0 | empty | 空帧 | 未检测到人体 |
| 1 | standing | 站立 | 正常站立姿态 |
| 2 | sitting | 坐着 | 坐姿状态 |
| 3 | lying | 躺卧 | 躺下或趴着 |
| 4 | bending | 弯腰 | 弯腰或蹲下 |
| 5 | crawling | 爬行 | 爬行姿态 |
| 6 | falling | 跌倒 | 跌倒进行中 |

### 5.4 模型训练配置

| 配置项 | 参数值 |
|--------|--------|
| 优化器 | Adam |
| 学习率 | 0.001 |
| 权重衰减 | 0.0001 |
| 批量大小 | 8 |
| 训练轮次 | 20 |
| 序列长度 | 24帧 |
| 步长(stride) | 6帧 |
| 设备 | CUDA/CPU |
| 检查点目录 | checkpoints/ |

---

## 六、跌倒检测算法

### 6.1 双重检测机制概述

系统采用双重跌倒检测机制：

```
┌──────────────────────────────────────────────────────────────┐
│                    跌倒检测双重机制                            │
├──────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              FallActionGRU 行为识别模型                   │ │
│  │   输入：24帧时序特征（69维/帧）→ 输出：7类行为概率         │ │
│  │   关键类别：lying（躺卧）、falling（跌倒）                 │ │
│  └─────────────────────────────────────────────────────────┘ │
│                           │                                  │
│                           ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │        FallDetectionAlgorithm 三重判定算法                 │ │
│  │   M1: CGDD 重心下降检测 (0.009 m/s)                      │ │
│  │   M2: BTD  身体倾斜检测 (45°)                           │ │
│  │   M3: SCDD 形状变化检测 (宽高比>1.0)                     │ │
│  └─────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

> **说明**：`infer_combined.py` 中定义的五重判定算法（额外包含JAD关节角度检测和BHD身体高度检测）为离线推理版本，目前前后端系统实际使用的是上述三重判定算法。

### 6.2 跌倒判定算法（FallDetectionAlgorithm）

系统使用的跌倒检测算法，包含3个核心判定条件：

| 判定条件 | 英文缩写 | 阈值参数 | 判定逻辑 |
|----------|----------|----------|----------|
| 重心下降检测 | CGDD | V_CRITICAL = 0.009 m/s | 重心下降速度 ≥ 阈值 |
| 身体倾斜检测 | BTD | THETA_CRITICAL = 45° | 身体倾斜角度 < 阈值 |
| 形状变化检测 | SCDD | P_CRITICAL = 1.0 | 宽高比 > 阈值 |

**判定规则**：三个条件**同时满足**才判定为跌倒

> **说明**：五重判定算法（FallRuleEngine）定义在 `infer_combined.py` 离线推理脚本中，目前前后端系统实际使用的是上述三重判定算法。

```python
class FallDetectionAlgorithm:
    V_CRITICAL = 0.009      # 重心下降速度阈值 (m/s)
    THETA_CRITICAL = 45     # 身体倾斜角度阈值 (度)
    P_CRITICAL = 1.0        # 宽高比阈值
    T_CRITICAL = 10         # 跌倒后报警延迟时间 (秒)

    def detect(self, frame, joints):
        # CGDD: 重心下降检测
        cgdd_triggered, cg_speed = self.cgdd_check(5)
        
        # BTD: 身体倾斜检测
        btd_triggered, tilt_angle = self.btd_check(joints)
        
        # SCDD: 形状变化检测
        scdd_triggered, contour_ratio = self.scdd_check(bbox)
        
        # 三重条件同时满足才判定为跌倒
        is_fall = cgdd_triggered and btd_triggered and scdd_triggered
```

#### 6.2.1 CGDD 重心下降检测

```python
def cgdd_check(self, frame_interval=5):
    """
    CGDD - Center of Gravity Descent Detection
    检测重心在短时间内的快速下降
    """
    if len(self.frame_history) < frame_interval + 1:
        return False, 0.0
    
    # 比较当前帧与frame_interval帧前的重心位置
    joints1 = self.frame_history[-frame_interval - 1]
    joints2 = self.frame_history[-1]
    
    cg1 = self.calculate_center_of_gravity(joints1)
    cg2 = self.calculate_center_of_gravity(joints2)
    
    # 计算时间间隔
    delta_t = frame_interval / self.fps
    
    # 计算重心下降速度（像素/秒）→ 转换为米/秒
    speed_mps = abs(cg2[1] - cg1[1]) / delta_t * 0.001
    
    # 速度超过阈值表示快速下降
    triggered = speed_mps >= self.V_CRITICAL  # 0.009 m/s
    return triggered, speed_mps
```

#### 6.2.2 BTD 身体倾斜检测

```python
def btd_check(self, joints):
    """
    BTD - Body Tilt Detection
    检测身体是否处于水平状态（跌倒后通常身体接近水平）
    """
    head = joints.head
    leg_center = self.calculate_leg_center(joints)
    
    dx = abs(head[0] - leg_center[0])
    dy = abs(head[1] - leg_center[1])
    
    # 计算身体倾斜角度
    if dx < 1e-6:
        angle = 90.0  # 垂直状态
    else:
        angle = arctan(dy / dx)  # 弧度转角度
    
    # 角度越小表示越水平（跌倒状态）
    triggered = angle < self.THETA_CRITICAL  # 45度
    return triggered, angle
```

#### 6.2.3 SCDD 形状变化检测

```python
def scdd_check(self, bbox):
    """
    SCDD - Shape Contour Deformation Detection
    检测身体宽高比的变化
    """
    xmin, ymin, xmax, ymax = bbox
    width = xmax - xmin
    height = ymax - ymin
    
    if height < 1e-6:
        ratio = 0
    else:
        ratio = width / height
    
    # 宽高比大于阈值表示身体呈水平姿态
    triggered = ratio > self.P_CRITICAL  # 1.0
    return triggered, ratio
```

### 6.3 跌倒判定流程图

```
                    ┌─────────────────┐
                    │  接收视频帧      │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ MediaPipe骨骼   │
                    │ 检测33个关键点   │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  提取69维特征   │
                    │  (66+3特征)     │
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              │                              │
              ▼                              ▼
    ┌─────────────────┐          ┌─────────────────┐
    │ FallActionGRU   │          │ FallDetection   │
    │   行为识别模型    │          │ Algorithm      │
    │  (24帧序列)     │          │ 三重判定        │
    └────────┬────────┘          │ M1:重心下降     │
             │                   │ M2:身体倾斜     │
             │   lying/falling   │ M3:形状变化     │
             │         │        └────────┬────────┘
             └─────────┼─────────────────┘
                       │
                       ▼
             ┌─────────────────┐
             │   融合判定       │
             │  行为识别+规则   │
             └────────┬────────┘
                       │
         ┌─────────────┴─────────────┐
         │                           │
         ▼                           ▼
┌─────────────────┐       ┌─────────────────┐
│  连续跌倒帧≥70% │       │   未满足跌倒条件  │
│  → 触发告警     │       │   → 继续监控     │
└─────────────────┘       └─────────────────┘
```

---

## 七、AI智能体模块

### 7.1 系统架构

AI智能体基于Ollama平台构建，动态获取用户部署的大语言模型：

```
┌─────────────────────────────────────────────────────────────┐
│                     AI 智能体系统                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌─────────────────────────────────────────────────────┐  │
│   │              Ollama 本地推理平台                      │  │
│   │  ┌─────────────────────────────────────────────────┐ │  │
│   │  │           动态模型加载                           │ │  │
│   │  │  - 自动检测Ollama部署的所有模型                  │ │  │
│   │  │  - 支持Qwen、Llama、Gemma等多种模型              │ │  │
│   │  │  - 本地部署，数据隐私安全                        │ │  │
│   │  │  - 无网络依赖，离线可用                          │ │  │
│   │  └─────────────────────────────────────────────────┘ │  │
│   └─────────────────────────────────────────────────────┘  │
│                             │                               │
│                             ▼                               │
│   ┌─────────────────────────────────────────────────────┐  │
│   │              AIAgent 智能体类                        │  │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │  │
│   │  │ 风险分析    │  │ 报告生成    │  │ 对话生成    │  │  │
│   │  │ analyze_    │  │ generate_   │  │ chat        │  │  │
│   │  │ behavior()  │  │ report()    │  │ ()          │  │  │
│   │  └─────────────┘  └─────────────┘  └─────────────┘  │  │
│   └─────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**模型配置说明**：
- 默认配置：`qwen3:1.7b`（在 `config.py` 中定义）
- 实际运行时：自动调用 `/api/tags` 接口获取用户Ollama部署的所有可用模型
- 模型选择：根据用户部署的模型动态适应

### 7.2 核心功能

#### 7.2.1 风险分析

```python
def analyze_behavior(self, result, context=None):
    """分析行为并计算风险等级"""
    risk = 0.0
    
    # 基础风险因子
    if result.get('fall_detected'):
        risk += 0.6
    if result.get('alert'):
        risk += 0.3
    if result.get('M1') and result.get('M2'):
        risk += 0.1
    
    # 近期跌倒频率
    recent = list(self.behavior_history)[-10:]
    if len(recent) >= 5:
        fall_count = sum(1 for r in recent if r['result'].get('fall_detected'))
        if fall_count >= 3:
            risk += 0.2
    
    self.risk_score = min(1.0, risk)
    
    return {
        'risk_level': self.risk_score,
        'risk_label': 'high' if risk > 0.7 else 'medium' if risk > 0.4 else 'low',
        'recommendation': self._get_recommendation(risk, result),
        'pattern_detected': self._detect_pattern(recent)
    }
```

#### 7.2.2 批量风险分析

```python
def analyze_batch(self, results):
    """批量分析检测结果"""
    fall_count = sum(1 for r in results if r.get('fall_detected'))
    alert_count = sum(1 for r in results if r.get('alert'))
    total = len(results)
    
    risk = 0.0
    if fall_count > total * 0.3:
        risk += 0.5
    if alert_count > total * 0.2:
        risk += 0.3
    
    avg_confidence = sum(r.get('confidence', 0) for r in results) / total
    if avg_confidence > 0.8:
        risk += 0.2
    
    risk = min(1.0, risk)
    
    return {
        "risk_level": risk,
        "risk_label": "high" if risk > 0.7 else "medium" if risk > 0.4 else "low",
        "recommendations": [...],
        "statistics": {
            "total_frames": total,
            "fall_frames": fall_count,
            "alert_frames": alert_count,
            "avg_confidence": avg_confidence
        }
    }
```

#### 7.2.3 智能对话

```python
def chat(self, message, user_id=None):
    """与用户进行智能对话"""
    # 优先使用Ollama生成回复
    if ollama_available:
        response = self._generate_ollama_response(message, history, context_key)
    else:
        response = self._generate_response(message, history)
    
    return response

def _generate_ollama_response(self, message, history, context_key='default'):
    """使用Qwen3:1.7b生成响应"""
    system_prompt = f"""你是一个智能AI助手，可以回答各种问题。

当前系统上下文（跌倒检测系统）：
- 当前风险等级：{risk_level}
- 近期跌倒事件：{fall_events}次
- 系统建议：{' '.join(recommendations)}

你的能力：
1. 分析跌倒风险并提供专业建议
2. 回答用户关于系统功能的问题
3. 帮助用户理解检测结果
4. 提供友好的技术支持
5. 回答各种通用问题
"""
    # 构建对话历史并调用Ollama API
    ollama_messages = [
        {"role": "system", "content": system_prompt},
        ...history_messages...
        {"role": "user", "content": message}
    ]
    
    response = self._call_ollama(ollama_messages)
    return response
```

### 7.3 AI智能体能力矩阵

| 功能类型 | 描述 | 技术实现 |
|----------|------|----------|
| 风险评估 | 实时计算当前风险等级 | 规则+统计模型 |
| 行为分析 | 分析近期行为模式 | 时序分析 |
| 报告生成 | 生成综合分析报告 | 模板+数据聚合 |
| 智能问答 | 回答用户各类问题 | Ollama动态模型 |
| 建议生成 | 提供个性化建议 | 规则引擎 |
| 状态监控 | 监控长期风险趋势 | 统计分析 |

---

## 八、数据库设计

### 8.1 ER实体关系图

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│      User       │       │     Camera      │       │     Alert       │
│   ┌─────────┐   │       │   ┌─────────┐   │       │   ┌─────────┐   │
│   │ id (PK) │◄──┼───────┼──►│user_id  │   │       │   │ id (PK) │   │
│   │username │   │       │   │ id (PK) │◄──┼───────┼──►│user_id  │   │
│   │ email   │   │       │   │  name   │   │       │   │record_id│   │
│   │ password│   │       │   │location │   │       │   │severity │   │
│   │  role   │   │       │   │  url    │   │       │   │ message │   │
│   └─────────┘   │       │   │status   │   │       │   └─────────┘   │
└────────┬────────┘       └────────┬────────┘       └────────┬────────┘
         │                         │                         │
         │    ┌─────────────────────┤                         │
         │    │                     │                         │
         ▼    ▼                     ▼                         ▼
┌───────────────────────────────────────────────────────────────────────┐
│                      DetectionRecord                                  │
│   ┌─────────────────────────────────────────────────────────────────┐ │
│   │ id (PK) │ user_id (FK) │ camera_id (FK) │ filename │ fall_detected│ │
│   │ total_frames │ detected_frames │ alert_count │ status │ created_at │ │
│   └─────────────────────────────────────────────────────────────────┘ │
│                              │                                        │
│                              │ 1:N                                    │
│                              ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────┐ │
│   │                      AlertRecord                                 │ │
│   │ id (PK) │ detection_id (FK) │ user_id (FK) │ frame_number │ M1 │ │
│   │ M2 │ M3 │ center_gravity_speed │ body_tilt_angle │ contour_ratio│ │
│   └─────────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────────┘

┌─────────────────┐       ┌─────────────────────────┐
│ConversationSession│     │  ConversationHistory    │
│   ┌─────────────┐ │       │   ┌─────────────────┐   │
│   │ id (PK)     │─┼───────┼──►│ session_id(FK) │   │
│   │ user_id     │ │       │   │ id (PK)        │   │
│   │ title       │ │       │   │ role           │   │
│   │ created_at  │ │       │   │ content        │   │
│   └─────────────┘ │       │   │ timestamp      │   │
└───────────────────┘       │   └─────────────────┘   │
                            └─────────────────────────┘

┌─────────────────┐
│ AnalysisRecord  │
│   ┌───────────┐ │
│   │ id (PK)  │ │
│   │ user_id  │ │
│   │input_path│ │
│   │output_path│
│   │file_type │ │
│   │ai_analysis│
│   └───────────┘ │
└─────────────────┘
```

### 8.2 数据库表结构

#### 8.2.1 用户表 (users)

```sql
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) NOT NULL UNIQUE,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(512),
    role VARCHAR(20) DEFAULT 'user',
    phone VARCHAR(20),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME,
    is_active BOOLEAN DEFAULT TRUE,
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户信息表';
```

#### 8.2.2 摄像头表 (cameras)

```sql
CREATE TABLE cameras (
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
    description TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_camera_type (camera_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='摄像头信息表';
```

#### 8.2.3 检测记录表 (detection_records)

```sql
CREATE TABLE detection_records (
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
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (camera_id) REFERENCES cameras(id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_camera_id (camera_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    INDEX idx_fall_detected (fall_detected)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='检测记录表';
```

#### 8.2.4 告警记录表 (alert_records)

```sql
CREATE TABLE alert_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    detection_id INT,
    user_id INT,
    frame_number INT,
    timestamp FLOAT,
    behavior VARCHAR(50),
    confidence FLOAT,
    M1 BOOLEAN,
    M2 BOOLEAN,
    M3 BOOLEAN,
    center_gravity_speed FLOAT,
    body_tilt_angle FLOAT,
    contour_ratio FLOAT,
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (detection_id) REFERENCES detection_records(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_detection_id (detection_id),
    INDEX idx_user_id (user_id),
    INDEX idx_acknowledged (acknowledged),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='告警记录表';
```

#### 8.2.5 告警表 (alerts)

```sql
CREATE TABLE alerts (
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
    FOREIGN KEY (record_id) REFERENCES detection_records(id) ON DELETE SET NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (acknowledged_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_record_id (record_id),
    INDEX idx_severity (severity),
    INDEX idx_acknowledged (acknowledged),
    INDEX idx_sent_at (sent_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='告警通知表';
```

#### 8.2.6 系统配置表 (system_config)

```sql
CREATE TABLE system_config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    `key` VARCHAR(100) NOT NULL UNIQUE,
    value TEXT,
    INDEX idx_key (`key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统配置表';
```

#### 8.2.7 对话会话表 (conversation_sessions)

```sql
CREATE TABLE conversation_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL,
    title VARCHAR(200) NOT NULL DEFAULT '新对话',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='对话会话表';
```

#### 8.2.8 对话历史表 (conversation_history)

```sql
CREATE TABLE conversation_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id INT NOT NULL,
    user_id VARCHAR(100) NOT NULL,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES conversation_sessions(id) ON DELETE CASCADE,
    INDEX idx_session_id (session_id),
    INDEX idx_user_id (user_id),
    INDEX idx_timestamp (timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='对话历史表';
```

#### 8.2.9 分析记录表 (analysis_records)

```sql
CREATE TABLE analysis_records (
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
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_file_type (file_type),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='分析记录表';
```

### 8.3 数据库关系说明

| 关系 | 说明 |
|------|------|
| User → Camera | 一对多关系，一个用户可以创建多个摄像头 |
| User → DetectionRecord | 一对多关系，一个用户可以有多条检测记录 |
| User → AlertRecord | 一对多关系，一个用户可以收到多条告警记录 |
| Camera → DetectionRecord | 一对多关系，一个摄像头可以有多个检测记录 |
| DetectionRecord → AlertRecord | 一对多关系，一个检测记录可以有多个告警帧 |
| DetectionRecord → Alert | 一对多关系到一对多关系到告警通知 |
| ConversationSession → ConversationHistory | 一对多关系，一个会话可以包含多条历史 |
| User → AnalysisRecord | 一对多关系，一个用户可以有多条分析记录 |

---

## 九、系统功能

### 9.1 用户端功能

#### 9.1.1 实时监控

- **本地摄像头实时检测**：使用浏览器MediaDevices API访问本地摄像头
- **骨骼姿态标注**：实时显示33点骨骼检测结果
- **行为识别**：实时显示7类行为识别结果及置信度
- **三重判定显示**：实时显示M1/M2/M3判定状态
- **录制功能**：支持录制检测视频
- **截图功能**：支持一键保存当前帧

#### 9.1.2 摄像头管理

- **查看我的摄像头**：用户只能查看自己创建的摄像头
- **添加摄像头**：支持本地摄像头、RTSP、HTTP三种类型
- **编辑/删除摄像头**：用户可修改或删除自己创建的摄像头
- **实时视频流**：查看摄像头的实时画面

#### 9.1.3 视频上传分析

- **视频上传**：支持MP4、AVI、MOV、MKV格式
- **批量上传**：支持多文件同时上传
- **分析进度**：实时显示分析进度
- **结果展示**：显示检测摘要、跌倒事件、AI风险分析
- **视频下载**：支持下载分析后的视频

#### 9.1.4 检测历史

- **记录查询**：查看历史检测记录
- **详情查看**：查看每条记录的详细信息
- **告警确认**：对告警进行确认处理

#### 9.1.5 AI助手

- **风险咨询**：询问当前风险等级
- **功能咨询**：了解系统功能
- **状态查询**：查询系统监控状态
- **智能问答**：回答各类问题

### 9.2 管理端功能

#### 9.2.1 用户管理

- **用户列表**：查看所有注册用户
- **用户信息编辑**：修改用户角色、状态
- **启用/禁用用户**：管理用户账户状态

#### 9.2.2 摄像头管理

- **全局摄像头列表**：查看所有用户的摄像头
- **摄像头信息**：查看位置、创建者、状态等信息
- **权限管理**：管理员可管理所有摄像头
- **注意**：管理员端仅显示摄像头信息，不显示其他用户的实时视频

#### 9.2.3 告警中心

- **告警列表**：查看所有用户的告警
- **告警确认**：对告警进行确认
- **告警统计**：按类型、严重程度统计

#### 9.2.4 数据统计

- **检测统计**：总检测数、跌倒事件数、告警数
- **用户统计**：活跃用户数、新增用户数
- **摄像头统计**：在线摄像头数、离线摄像头数
- **趋势分析**：按日/周/月统计

#### 9.2.5 AI助手（管理）

- **系统风险分析**：分析全局风险等级
- **批量报告生成**：生成综合报告
- **智能对话**：与管理功能集成

---

## 十、项目总结

### 10.1 技术创新点

1. **双重检测机制**：融合深度学习行为识别与多规则判定，提高检测准确率
2. **69维特征向量**：基于MediaPipe 33点提取丰富的空间与运动特征
3. **双向GRU时序建模**：利用双向记忆能力捕捉长时序依赖关系
4. **五重跌倒判定规则**：从多个维度综合判断跌倒行为
5. **本地AI部署**：基于Ollama实现本地智能分析，支持动态加载用户部署的各种大语言模型

### 10.2 系统优势

| 优势 | 说明 |
|------|------|
| 高准确率 | 双重机制互补，有效降低误报和漏报 |
| 实时性强 | 支持实时视频流分析与告警 |
| 隐私安全 | 本地AI部署，数据不外传 |
| 跨平台 | 支持多种摄像头类型和部署方式 |
| 可扩展 | 模块化设计，易于功能扩展 |
| 用户友好 | 提供Web界面和AI对话，易于使用 |

### 10.3 技术指标

| 指标 | 参数 |
|------|------|
| 骨骼关键点 | 33个（MediaPipe Pose） |
| 特征向量维度 | 69维 |
| 行为类别数 | 7类 |
| GRU隐藏层维度 | 128 |
| GRU层数 | 2层 |
| 序列长度 | 24帧 |
| 跌倒判定条件 | 3重（M1/M2/M3：CGDD/BTD/SCDD） |
| AI模型 | Ollama动态模型（默认qwen3:1.7b） |

### 10.4 应用场景

- **家庭监护**：独居老人跌倒检测与告警
- **养老院**：集中看护场景下的实时监控
- **医院**：病房患者安全监护
- **公共场所**：商场、车站等易跌倒区域监控

---

## 附录

### A. 代码仓库结构

```
d:\falldown\
├── back\                          # 后端代码
│   ├── app.py                     # Flask应用主文件
│   ├── config.py                  # 配置文件
│   ├── ai_agent.py               # AI智能体
│   ├── finallmodel\              # 跌倒检测模型
│   │   ├── model\
│   │   │   ├── fall_detector.py  # 跌倒检测核心
│   │   │   ├── network.py        # GRU网络定义
│   │   │   ├── pose_features.py  # 特征提取
│   │   │   ├── config.py         # 模型配置
│   │   │   ├── dataset_loader.py # 数据集加载
│   │   │   ├── train.py         # 训练脚本
│   │   │   └── infer_combined.py # 推理脚本
│   │   └── checkpoints\          # 模型权重
│   │       └── best_gru.pt
│   └── ...
├── frontend\                      # 前端代码
│   ├── src\
│   │   ├── views\               # 页面组件
│   │   ├── router\             # 路由配置
│   │   ├── stores\             # 状态管理
│   │   └── ...
│   └── ...
└── PPT项目汇报报告.md              # 本文档
```

### B. API接口一览

| 接口 | 方法 | 描述 |
|------|------|------|
| /api/upload | POST | 上传视频文件 |
| /api/detect/file | POST | 视频文件检测 |
| /api/detect | POST | 图像实时检测 |
| /api/cameras | GET/POST | 摄像头列表/添加 |
| /api/cameras/{id} | GET/PUT/DELETE | 摄像头CRUD |
| /api/user/cameras | GET | 当前用户的摄像头 |
| /api/alerts | GET | 告警列表 |
| /api/chat | POST | AI对话 |

---

*文档版本：v1.0*
*最后更新：2026-06-01*
