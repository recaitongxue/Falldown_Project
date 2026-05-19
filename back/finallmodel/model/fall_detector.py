#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
跌倒检测系统核心模块 - 严格按照参考文件实现
整合：
1. infer_combined.py 的行为识别（GRU模型）
2. fallmodel/fall_detection_core.py 的跌倒检测（三重判定条件）

严格遵循：
- 行为识别使用 FallActionGRU 模型，输入为69维特征向量
- 跌倒检测使用三重判定条件（CGDD、BTD、SCDD）
- 骨骼标注使用14点模型
"""

import os
import cv2
import numpy as np
import torch
from collections import deque
from dataclasses import dataclass
from typing import Optional, Tuple, List, Dict
import math

# MediaPipe相关导入
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# 导入训练时使用的PoseExtractor和FallActionGRU
from pose_features import PoseExtractor, PoseFrameFeatures, FallRuleEngine, POSE_CONNECTIONS
from network import FallActionGRU
from config import ModelConfig, RuleConfig


# 行为类别定义
BEHAVIOR_CLASSES = ["empty", "standing", "sitting", "lying", "bending", "crawling", "falling"]
BEHAVIOR_CN_MAP = {
    "empty": "空帧",
    "standing": "站立",
    "sitting": "坐着",
    "lying": "躺卧",
    "bending": "弯腰",
    "crawling": "爬行",
    "falling": "跌倒"
}


@dataclass
class JointPoints:
    """关节点数据结构 - 基于论文的14点模型（与fallmodel一致）"""
    head: Tuple[float, float]
    shoulder_center: Tuple[float, float]
    right_shoulder: Tuple[float, float]
    right_elbow: Tuple[float, float]
    right_hand: Tuple[float, float]
    left_shoulder: Tuple[float, float]
    left_elbow: Tuple[float, float]
    left_hand: Tuple[float, float]
    right_hip: Tuple[float, float]
    right_knee: Tuple[float, float]
    right_ankle: Tuple[float, float]
    left_hip: Tuple[float, float]
    left_knee: Tuple[float, float]
    left_ankle: Tuple[float, float]

    def to_list(self) -> List:
        return [
            self.head, self.shoulder_center, self.right_shoulder, self.right_elbow,
            self.right_hand, self.left_shoulder, self.left_elbow, self.left_hand,
            self.right_hip, self.right_knee, self.right_ankle, self.left_hip,
            self.left_knee, self.left_ankle
        ]


@dataclass
class DetectionResult:
    """检测结果数据结构 - 严格参考fallmodel格式"""
    # 跌倒检测结果
    is_fall: bool
    cgdd_triggered: bool
    btd_triggered: bool
    scdd_triggered: bool
    center_gravity_speed: float
    body_tilt_angle: float
    contour_ratio: float
    confidence: float
    
    # 行为识别结果
    behavior: str
    behavior_confidence: float
    
    # 帧信息
    frame_number: int
    timestamp: float
    
    # 可视化相关
    joints: Optional[JointPoints] = None


class FallDetectionAlgorithm:
    """
    跌倒检测算法 - 严格参考fallmodel/fall_detection_core.py
    
    论文参数（来自参考论文）:
    - V_CRITICAL: 0.009 m/s (重心下降速度阈值)
    - THETA_CRITICAL: 45° (身体倾斜角度阈值)
    - P_CRITICAL: 1.0 (宽高比阈值)
    - T_CRITICAL: 10秒 (跌倒后报警延迟时间)
    """
    
    # 严格使用fallmodel的参数
    V_CRITICAL = 0.009
    THETA_CRITICAL = 45
    P_CRITICAL = 1.0
    T_CRITICAL = 10

    def __init__(self):
        self.frame_history = []
        self.fall_history = []
        self.history_size = 10
        self.alert_start_frame = None
        self.alert_triggered = False
        self.frame_idx = 0
        self.fps = 20.0

    def set_fps(self, fps: float):
        """设置帧率"""
        self.fps = fps

    def reset(self):
        """重置检测器状态"""
        self.frame_history = []
        self.fall_history = []
        self.alert_start_frame = None
        self.alert_triggered = False
        self.frame_idx = 0

    def calculate_center_of_gravity(self, joints: JointPoints) -> Tuple[float, float]:
        """计算重心位置（使用臀部中心）"""
        hip_l = joints.left_hip
        hip_r = joints.right_hip
        cg_x = (hip_l[0] + hip_r[0]) / 2
        cg_y = (hip_l[1] + hip_r[1]) / 2
        return (cg_x, cg_y)

    def calculate_leg_center(self, joints: JointPoints) -> Tuple[float, float]:
        """计算腿部中心位置（膝盖和脚踝的中点）"""
        left_knee = joints.left_knee
        left_ankle = joints.left_ankle
        leg_x = (left_knee[0] + left_ankle[0]) / 2
        leg_y = (left_knee[1] + left_ankle[1]) / 2
        return (leg_x, leg_y)

    def cgdd_check(self, frame_interval: int = 5) -> Tuple[bool, float]:
        """
        CGDD - 重心下降检测 (Center of Gravity Descent Detection)
        严格参考fallmodel的实现
        
        论文算法：检测间隔设置为每5个相邻帧检测1次，时间间隔约为0.25秒
        比较当前帧与frame_interval帧前的重心位置变化
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
        
        if delta_t <= 0:
            return False, 0.0

        # 计算重心下降速度（像素/秒）
        speed_px = abs(cg2[1] - cg1[1]) / delta_t
        
        # 转换为米/秒（假设图像高度约为1米）
        speed_mps = speed_px * 0.001

        triggered = speed_mps >= self.V_CRITICAL
        return triggered, speed_mps

    def btd_check(self, joints: JointPoints) -> Tuple[bool, float]:
        """
        BTD - 身体倾斜检测 (Body Tilt Detection)
        严格参考fallmodel的实现
        """
        head = joints.head
        leg_center = self.calculate_leg_center(joints)

        dx = abs(head[0] - leg_center[0])
        dy = abs(head[1] - leg_center[1])

        if dx < 1e-6:
            angle = 90.0
        else:
            angle = math.degrees(math.atan(dy / dx))

        # 角度越小表示越水平（跌倒状态）
        triggered = angle < self.THETA_CRITICAL
        return triggered, angle

    def scdd_check(self, bbox: Tuple[int, int, int, int]) -> Tuple[bool, float]:
        """
        SCDD - 外形轮廓变形检测 (Shape Contour Deformation Detection)
        严格参考fallmodel的实现
        """
        xmin, ymin, xmax, ymax = bbox
        width = xmax - xmin
        height = ymax - ymin

        if height < 1e-6:
            ratio = 0
        else:
            ratio = width / height

        triggered = ratio > self.P_CRITICAL
        return triggered, ratio

    def detect(self, frame: np.ndarray, joints: JointPoints) -> DetectionResult:
        """
        执行跌倒检测 - 严格参考fallmodel/fall_detection_core.py的实现
        三个条件都满足才判定为跌倒：
        1. CGDD: 重心下降速度 >= 0.009 m/s
        2. BTD: 身体倾斜角度 < 45°
        3. SCDD: 宽高比 > 1.0
        """
        self.frame_idx += 1
        
        # 严格按照fallmodel：先更新帧历史，再进行检测
        self.frame_history.append(joints)
        if len(self.frame_history) > self.history_size:
            self.frame_history.pop(0)
        
        # 计算边界框（使用所有有效关节点）
        points = joints.to_list()
        x_coords = [p[0] for p in points if p[0] > 0]
        y_coords = [p[1] for p in points if p[1] > 0]
        bbox = (min(x_coords), min(y_coords), max(x_coords), max(y_coords)) if x_coords and y_coords else (0, 0, 0, 0)

        # 执行三重检测（使用fallmodel的参数和检测顺序）
        cgdd_triggered, cg_speed = self.cgdd_check(5)
        btd_triggered, tilt_angle = self.btd_check(joints)
        scdd_triggered, contour_ratio = self.scdd_check(bbox)

        # 严格按照fallmodel：三个条件都满足才判定为跌倒
        is_fall = cgdd_triggered and btd_triggered and scdd_triggered

        # 更新跌倒历史用于计算置信度
        self.fall_history.append(1 if is_fall else 0)
        if len(self.fall_history) > 30:
            self.fall_history.pop(0)

        confidence = sum(self.fall_history) / len(self.fall_history) if self.fall_history else 0

        return DetectionResult(
            is_fall=is_fall,
            cgdd_triggered=cgdd_triggered,
            btd_triggered=btd_triggered,
            scdd_triggered=scdd_triggered,
            center_gravity_speed=cg_speed,
            body_tilt_angle=tilt_angle,
            contour_ratio=contour_ratio,
            confidence=confidence,
            behavior="unknown",
            behavior_confidence=0.0,
            frame_number=self.frame_idx,
            timestamp=self.frame_idx / self.fps,
            joints=joints
        )


class BehaviorRecognitionModel:
    """行为识别模型 - 严格参考infer_combined.py实现"""
    
    def __init__(self, model_path: str = None):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # 当前文件在 finallmodel/model/fall_detector.py
        current_dir = os.path.dirname(os.path.abspath(__file__))  # finallmodel/model
        
        # 设置默认模型路径 - 与infer_combined.py一致
        if model_path is None:
            model_path = os.path.join(current_dir, 'checkpoints/best_gru.pt')
        
        # 如果路径不存在，尝试finallmodel目录下的checkpoints
        if not os.path.exists(model_path):
            model_path = os.path.join(os.path.dirname(current_dir), 'checkpoints/best_gru.pt')
        
        self.model_path = model_path
        self.model = None
        self.sequence = deque(maxlen=24)  # 使用与训练时相同的序列长度
        self.min_sequence_len = 8
        self.class_names = BEHAVIOR_CLASSES
        
        print(f"尝试加载行为识别模型: {self.model_path}")
        if os.path.exists(model_path):
            self.load_model()
        else:
            print(f"警告：行为识别模型文件不存在: {model_path}")
    
    def load_model(self):
        """加载行为识别模型 - 与infer_combined.py完全一致"""
        try:
            self.model = FallActionGRU(
                input_size=33 * 2 + 3,  # 33*2 + 3 = 69维
                hidden_size=128,
                num_layers=2,
                num_classes=len(self.class_names),
                dropout=0.2,
            ).to(self.device)
            
            state = torch.load(self.model_path, map_location=self.device, weights_only=True)
            self.model.load_state_dict(state["state_dict"], strict=False)
            self.model.eval()
            print(f"行为识别模型加载成功: {self.model_path}")
            return True
        except Exception as e:
            print(f"加载行为识别模型失败: {e}")
            return False

    def extract_features(self, pose_features: PoseFrameFeatures) -> np.ndarray:
        """
        从PoseFrameFeatures提取特征向量（与infer_combined.py完全一致）
        特征向量格式: [33*2个归一化坐标 + cg_y + tilt_deg + wh_ratio] = 69维
        """
        # 关键点坐标 (33*2 = 66维)
        kp = pose_features.keypoints.astype(np.float32).reshape(-1)
        
        # 额外特征 (3维)
        extra = np.array(
            [
                float(pose_features.center_y),
                float(pose_features.tilt_deg) / 180.0,
                float(pose_features.wh_ratio),
            ],
            dtype=np.float32,
        )
        
        # 组合特征向量（66 + 3 = 69维）
        features = np.concatenate([kp, extra], axis=0)
        
        return features

    def recognize(self, pose_features: PoseFrameFeatures) -> Tuple[str, float]:
        """识别行为（与infer_combined.py完全一致）"""
        if self.model is None:
            return "unknown", 0.0
        
        try:
            features = self.extract_features(pose_features)
            self.sequence.append(features)
            
            # 当序列长度不足时，返回unknown
            if len(self.sequence) < self.min_sequence_len:
                return "unknown", 0.0
            
            # 构建输入张量（与infer_combined.py一致）
            x = torch.from_numpy(np.stack(list(self.sequence)).astype(np.float32))
            x = x.unsqueeze(0).to(self.device)
            
            with torch.no_grad():
                logits = self.model(x)
                prob = torch.softmax(logits, dim=1)[0].cpu().numpy()
                idx = int(prob.argmax())
                confidence = float(prob[idx])
                behavior = self.class_names[idx] if idx < len(self.class_names) else "unknown"
            
            # 增加置信度阈值过滤
            if confidence < 0.3:
                return "unknown", 0.0
            
            return behavior, confidence
        except Exception as e:
            print(f"行为识别失败: {e}")
            return "unknown", 0.0

    def reset(self):
        """重置序列"""
        self.sequence.clear()


class FallDetector:
    """
    综合跌倒检测系统
    严格整合：
    1. fallmodel的跌倒检测算法（三重判定条件）
    2. infer_combined.py的行为识别模型（GRU）
    """
    
    def __init__(self):
        # 使用训练时相同的PoseExtractor提取特征（用于行为识别）
        self.pose_extractor = PoseExtractor(min_det_conf=0.3, min_track_conf=0.3)
        self.fall_detector = FallDetectionAlgorithm()
        self.behavior_recognizer = BehaviorRecognitionModel()
        self.frame_idx = 0
        self.fps = 20.0
        self.alert_frames = deque(maxlen=60)
        print("检测器初始化完成")
    
    def set_fps(self, fps: float):
        """设置帧率"""
        self.fps = fps
        self.fall_detector.set_fps(fps)
    
    def reset(self):
        """重置检测器"""
        self.pose_extractor = PoseExtractor(min_det_conf=0.3, min_track_conf=0.3)
        self.fall_detector.reset()
        self.behavior_recognizer.reset()
        self.frame_idx = 0
        self.alert_frames.clear()
    
    def _get_joints_from_pose_features(self, pose_features: PoseFrameFeatures, frame_shape: Tuple[int, int]) -> JointPoints:
        """从PoseFrameFeatures转换为JointPoints（用于跌倒检测）"""
        h, w = frame_shape
        points = pose_features.keypoints * np.array([w, h])
        
        # 关键点索引定义
        NOSE = 0
        LEFT_SHOULDER = 11
        RIGHT_SHOULDER = 12
        LEFT_ELBOW = 13
        RIGHT_ELBOW = 14
        LEFT_WRIST = 15
        RIGHT_WRIST = 16
        LEFT_HIP = 23
        RIGHT_HIP = 24
        LEFT_KNEE = 25
        RIGHT_KNEE = 26
        LEFT_ANKLE = 27
        RIGHT_ANKLE = 28
        
        return JointPoints(
            head=(points[NOSE][0], points[NOSE][1]),
            shoulder_center=((points[LEFT_SHOULDER][0] + points[RIGHT_SHOULDER][0]) / 2, 
                           (points[LEFT_SHOULDER][1] + points[RIGHT_SHOULDER][1]) / 2),
            right_shoulder=(points[RIGHT_SHOULDER][0], points[RIGHT_SHOULDER][1]),
            right_elbow=(points[RIGHT_ELBOW][0], points[RIGHT_ELBOW][1]),
            right_hand=(points[RIGHT_WRIST][0], points[RIGHT_WRIST][1]),
            left_shoulder=(points[LEFT_SHOULDER][0], points[LEFT_SHOULDER][1]),
            left_elbow=(points[LEFT_ELBOW][0], points[LEFT_ELBOW][1]),
            left_hand=(points[LEFT_WRIST][0], points[LEFT_WRIST][1]),
            right_hip=(points[RIGHT_HIP][0], points[RIGHT_HIP][1]),
            right_knee=(points[RIGHT_KNEE][0], points[RIGHT_KNEE][1]),
            right_ankle=(points[RIGHT_ANKLE][0], points[RIGHT_ANKLE][1]),
            left_hip=(points[LEFT_HIP][0], points[LEFT_HIP][1]),
            left_knee=(points[LEFT_KNEE][0], points[LEFT_KNEE][1]),
            left_ankle=(points[LEFT_ANKLE][0], points[LEFT_ANKLE][1])
        )
    
    def detect_frame(self, frame: np.ndarray, mode: str = 'video') -> Dict:
        """
        检测单帧图像
        返回格式参考fallmodel的输出格式
        
        :param frame: BGR格式的图像帧
        :param mode: 'video' 用于视频序列检测，'image' 用于单帧实时检测
        """
        self.frame_idx += 1
        
        # 使用PoseExtractor提取特征（用于行为识别）
        # 根据模式选择不同的检测方式
        pose_features = self.pose_extractor.extract(frame, mode=mode)
        
        # 如果未检测到人体
        if pose_features is None:
            return {
                'status': 'no_person',
                'label': '未检测到人体',
                'is_fall': False,
                'M1': False,
                'M2': False,
                'M3': False,
                'center_gravity_speed': 0.0,
                'body_tilt_angle': 0.0,
                'contour_ratio': 0.0,
                'confidence': 0.0,
                'behavior': 'empty',
                'behavior_confidence': 0.0,
                'behavior_cn': '空帧',
                'frame_number': self.frame_idx,
                'timestamp': self.frame_idx / self.fps,
                'alert': False,
                'joints': {}
            }
        
        h, w = frame.shape[:2]
        
        # 从pose_features获取关节点（用于跌倒检测）
        joints = self._get_joints_from_pose_features(pose_features, (h, w))
        
        # 执行跌倒检测（使用fallmodel算法）
        fall_result = self.fall_detector.detect(frame, joints)
        
        # 执行行为识别（使用GRU模型，与infer_combined.py一致）
        behavior, behavior_conf = self.behavior_recognizer.recognize(pose_features)
        
        # 如果GRU模型返回unknown，使用简单规则判断
        if behavior == "unknown" or behavior_conf < 0.3:
            # 基于宽高比判断躺卧状态
            wh_ratio = pose_features.wh_ratio
            if wh_ratio > 1.0:
                behavior = "lying"
                behavior_conf = min(0.95, wh_ratio)
            else:
                behavior = "standing"
                behavior_conf = 0.6
        
        # 如果跌倒检测判定为跌倒，强制设置行为为跌倒
        if fall_result.is_fall:
            behavior = "falling"
            behavior_conf = min(1.0, behavior_conf + 0.3)
        
        # 更新行为到跌倒检测结果
        fall_result.behavior = behavior
        fall_result.behavior_confidence = behavior_conf
        
        # 报警判定：连续多帧检测到跌倒才触发报警
        self.alert_frames.append(1 if fall_result.is_fall else 0)
        alert_triggered = sum(self.alert_frames) >= len(self.alert_frames) * 0.7
        
        # 构建输出（参考fallmodel格式）
        result = {
            'status': 'detecting',
            'label': '跌倒' if bool(fall_result.is_fall) else '正常',
            'is_fall': bool(fall_result.is_fall),
            'M1': bool(fall_result.cgdd_triggered),
            'M2': bool(fall_result.btd_triggered),
            'M3': bool(fall_result.scdd_triggered),
            'center_gravity_speed': float(fall_result.center_gravity_speed),
            'body_tilt_angle': float(fall_result.body_tilt_angle),
            'contour_ratio': float(fall_result.contour_ratio),
            'confidence': float(fall_result.confidence),
            'behavior': str(fall_result.behavior),
            'behavior_confidence': float(fall_result.behavior_confidence),
            'behavior_cn': str(BEHAVIOR_CN_MAP.get(fall_result.behavior, fall_result.behavior)),
            'frame_number': int(self.frame_idx),
            'timestamp': float(self.frame_idx / self.fps),
            'alert': bool(alert_triggered),
            'joints': {
                'head': (float(joints.head[0]), float(joints.head[1])),
                'shoulder_center': (float(joints.shoulder_center[0]), float(joints.shoulder_center[1])),
                'right_shoulder': (float(joints.right_shoulder[0]), float(joints.right_shoulder[1])),
                'right_elbow': (float(joints.right_elbow[0]), float(joints.right_elbow[1])),
                'right_hand': (float(joints.right_hand[0]), float(joints.right_hand[1])),
                'left_shoulder': (float(joints.left_shoulder[0]), float(joints.left_shoulder[1])),
                'left_elbow': (float(joints.left_elbow[0]), float(joints.left_elbow[1])),
                'left_hand': (float(joints.left_hand[0]), float(joints.left_hand[1])),
                'right_hip': (float(joints.right_hip[0]), float(joints.right_hip[1])),
                'right_knee': (float(joints.right_knee[0]), float(joints.right_knee[1])),
                'right_ankle': (float(joints.right_ankle[0]), float(joints.right_ankle[1])),
                'left_hip': (float(joints.left_hip[0]), float(joints.left_hip[1])),
                'left_knee': (float(joints.left_knee[0]), float(joints.left_knee[1])),
                'left_ankle': (float(joints.left_ankle[0]), float(joints.left_ankle[1]))
            }
        }
        
        return result
    
    def detect_video(self, video_path: str, mode: str = 'fast', show_labels: bool = True, show_bboxes: bool = True, output_path: Optional[str] = None) -> Dict:
        """
        检测视频文件
        :param video_path: 输入视频路径
        :param mode: 检测模式 'fast' 或 'full'
        :param show_labels: 是否显示标签
        :param show_bboxes: 是否显示边界框
        :param output_path: 输出视频路径（可选），如果不提供则自动生成
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return {'success': False, 'error': '无法打开视频文件'}
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # 确保FPS有效
        if fps <= 0 or fps > 100:
            fps = 25
        
        self.set_fps(fps)
        
        # 准备输出视频
        if output_path:
            # 使用外部指定的输出路径
            output_dir = os.path.dirname(output_path)
            os.makedirs(output_dir, exist_ok=True)
        else:
            # 使用默认输出目录
            output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'outputs')
            os.makedirs(output_dir, exist_ok=True)
            name, ext = os.path.splitext(os.path.basename(video_path))
            # 强制使用.mp4扩展名
            output_path = os.path.join(output_dir, f"{name}_detected.mp4")
        
        output_video = output_path
        
        # 使用H.264编码（浏览器兼容）
        fourcc = cv2.VideoWriter_fourcc(*'avc1')
        out_writer = cv2.VideoWriter(output_video, fourcc, fps, (width, height))
        
        # 如果H.264失败，尝试其他编码
        if not out_writer.isOpened():
            print("H.264 encoding failed, trying mp4v...")
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out_writer = cv2.VideoWriter(output_video, fourcc, fps, (width, height))
        
        # 如果仍然失败，尝试MJPG
        if not out_writer.isOpened():
            print("mp4v encoding failed, trying MJPG...")
            fourcc = cv2.VideoWriter_fourcc(*'MJPG')
            out_writer = cv2.VideoWriter(output_video.replace('.mp4', '.avi'), fourcc, fps, (width, height))
            output_video = output_video.replace('.mp4', '.avi')
        
        results = []
        alerts = []
        frame_idx = 0
        detected_frames = 0
        fall_detected = False
        alert_count = 0
        
        skip_frames = 1
        if mode == 'fast' and fps > 15:
            skip_frames = 2
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_idx % skip_frames == 0:
                result = self.detect_frame(frame)
                results.append(result)
                
                if result['is_fall']:
                    detected_frames += 1
                    fall_detected = True
                
                if result.get('alert'):
                    alerts.append(result)
                    alert_count += 1
            
            frame = self.draw_result(frame, results[-1] if results else None)
            out_writer.write(frame)
            
            frame_idx += 1
            if frame_idx % 100 == 0:
                print(f"Processing frame {frame_idx}/{total_frames}")
        
        cap.release()
        out_writer.release()
        
        summary = {
            'success': True,
            'total_frames': total_frames,
            'detected_frames': detected_frames,
            'fall_detected': fall_detected,
            'alert_count': alert_count,
            'fps': float(fps),
            'duration': float(total_frames / fps),
            'mode': mode
        }
        
        return {
            'summary': summary,
            'frames': results,
            'alerts': alerts,
            'output_video': output_video
        }
    
    def detect_image(self, image_data: str) -> Dict:
        """
        检测单张图像
        """
        import base64
        import io
        from PIL import Image
        
        try:
            if image_data.startswith('data:image/'):
                image_data = image_data.split(',')[1]
            
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # 设置较高的帧率以提高检测灵敏度
            if self.fps != 30.0:
                self.set_fps(30.0)
            
            # 使用图像模式进行检测（适合实时单帧检测）
            result = self.detect_frame(frame, mode='image')
            return result
        except Exception as e:
            print(f"图像检测失败: {e}")
            import traceback
            traceback.print_exc()
            return {
                'status': 'error',
                'error': str(e),
                'label': '检测失败',
                'is_fall': False,
                'confidence': 0.0,
                'behavior': 'empty',
                'behavior_confidence': 0.0,
                'behavior_cn': '空帧',
                'joints': {}
            }
    
    def draw_result(self, frame: np.ndarray, result: Dict = None) -> np.ndarray:
        """
        在帧上绘制检测结果（参考fallmodel的可视化方式）
        使用PIL绘制中文，避免乱码问题
        """
        from PIL import Image, ImageDraw, ImageFont
        
        vis = frame.copy()
        h, w = vis.shape[:2]
        
        if result is None:
            return vis
        
        # 获取字体
        def get_font(font_size=20):
            # Windows字体路径（使用正确的Windows路径格式）
            font_paths = [
                "C:/Windows/Fonts/simhei.ttf",
                "C:\\Windows\\Fonts\\simhei.ttf",
                "C:/Windows/Fonts/msyh.ttc",
                "C:\\Windows\\Fonts\\msyh.ttc",
                "C:/Windows/Fonts/simsun.ttc",
                "C:\\Windows\\Fonts\\simsun.ttc",
                "C:/Windows/Fonts/simkai.ttf",
                "C:\\Windows\\Fonts\\simkai.ttf",
                "/Windows/Fonts/simhei.ttf",
                "/Windows/Fonts/msyh.ttc",
                "simhei.ttf",
                "msyh.ttc",
            ]
            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        return ImageFont.truetype(font_path, font_size)
                    except Exception as e:
                        print(f"加载字体失败 {font_path}: {e}")
                        continue
            print("警告：未找到中文字体，使用默认字体")
            return ImageFont.load_default()
        
        # 绘制骨骼姿态标注（先绘制，避免被文字覆盖）
        joints = result.get('joints', {})
        if joints:
            if result.get('alert'):
                skeleton_color = (0, 0, 255)
            elif result.get('is_fall'):
                skeleton_color = (0, 165, 255)
            else:
                skeleton_color = (0, 255, 0)
            
            points = [
                joints.get('head', (0, 0)),
                joints.get('shoulder_center', (0, 0)),
                joints.get('right_shoulder', (0, 0)),
                joints.get('right_elbow', (0, 0)),
                joints.get('right_hand', (0, 0)),
                joints.get('left_shoulder', (0, 0)),
                joints.get('left_elbow', (0, 0)),
                joints.get('left_hand', (0, 0)),
                joints.get('right_hip', (0, 0)),
                joints.get('right_knee', (0, 0)),
                joints.get('right_ankle', (0, 0)),
                joints.get('left_hip', (0, 0)),
                joints.get('left_knee', (0, 0)),
                joints.get('left_ankle', (0, 0))
            ]
            
            connections = [
                (0, 1), (1, 2), (2, 3), (3, 4),
                (1, 5), (5, 6), (6, 7),
                (1, 8), (8, 9), (9, 10),
                (1, 11), (11, 12), (12, 13)
            ]
            
            # 绘制关节点（使用更宽松的过滤条件）
            valid_points = []
            for idx, (x, y) in enumerate(points):
                # 检查坐标是否在有效范围内（大于0且小于图像尺寸）
                if x > 0 and y > 0 and x < w and y < h:
                    valid_points.append((idx, x, y))
                    cv2.circle(vis, (int(x), int(y)), 6, skeleton_color, -1)
                    # 绘制关节点序号
                    cv2.putText(vis, str(idx), (int(x)+8, int(y)+8), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
            
            # 绘制骨骼连接
            for start_idx, end_idx in connections:
                pt1 = points[start_idx]
                pt2 = points[end_idx]
                # 使用更宽松的过滤条件
                if pt1[0] > 0 and pt1[1] > 0 and pt2[0] > 0 and pt2[1] > 0:
                    if pt1[0] < w and pt1[1] < h and pt2[0] < w and pt2[1] < h:
                        cv2.line(vis, (int(pt1[0]), int(pt1[1])), (int(pt2[0]), int(pt2[1])), skeleton_color, 3)
            
            print(f"绘制了 {len(valid_points)} 个关节点")
        
        # 准备绘制中文文字（使用PIL）
        img_pil = Image.fromarray(cv2.cvtColor(vis, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img_pil)
        
        # 设置颜色和状态文字
        if result.get('alert'):
            text_color = (255, 0, 0)  # PIL使用RGB
            status_text = "ALERT: 跌倒告警!"
        elif result.get('is_fall'):
            text_color = (255, 165, 0)
            status_text = "WARNING: 疑似跌倒"
        else:
            text_color = (0, 255, 0)
            status_text = f"STATUS: {result.get('behavior_cn', '未知')}"
        
        # 绘制状态文字
        font_large = get_font(24)
        font_medium = get_font(16)
        font_small = get_font(14)
        
        draw.text((10, 10), status_text, font=font_large, fill=text_color)
        
        # 绘制行为识别结果
        if 'behavior_cn' in result:
            behavior_text = f"行为: {result['behavior_cn']} ({result.get('behavior_confidence', 0):.2f})"
            draw.text((10, 45), behavior_text, font=font_medium, fill=text_color)
        
        # 绘制检测条件状态（使用白色）
        white_color = (255, 255, 255)
        draw.text((10, 75), f"CGDD: {result.get('M1', False)}", font=font_small, fill=white_color)
        draw.text((10, 95), f"BTD: {result.get('M2', False)}", font=font_small, fill=white_color)
        draw.text((10, 115), f"SCDD: {result.get('M3', False)}", font=font_small, fill=white_color)
        
        # 绘制置信度
        draw.text((10, 135), f"置信度: {result.get('confidence', 0):.2f}", font=font_small, fill=white_color)
        
        # 转换回OpenCV格式
        vis = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
        
        return vis
