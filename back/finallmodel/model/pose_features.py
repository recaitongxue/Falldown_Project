import math
import os
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np

from config import RuleConfig


@dataclass
class PoseFrameFeatures:
    keypoints: np.ndarray
    bbox: Tuple[float, float, float, float]
    center_y: float
    tilt_deg: float
    wh_ratio: float
    # 新增关节角度
    elbow_angle: float  # 肘部角度
    knee_angle: float   # 膝盖角度
    hip_angle: float    # 臀部角度
    shoulder_angle: float  # 肩部角度
    # 新增身体特征
    body_height: float  # 身体高度
    body_width: float   # 身体宽度
    head_position: Tuple[float, float]  # 头部位置


# MediaPipe Pose 关键点索引定义
# 参考论文中的骨骼结构定义
NOSE = 0
LEFT_EYE_INNER = 1
LEFT_EYE = 2
LEFT_EYE_OUTER = 3
RIGHT_EYE_INNER = 4
RIGHT_EYE = 5
RIGHT_EYE_OUTER = 6
LEFT_EAR = 7
RIGHT_EAR = 8
MOUTH_LEFT = 9
MOUTH_RIGHT = 10
LEFT_SHOULDER = 11
RIGHT_SHOULDER = 12
LEFT_ELBOW = 13
RIGHT_ELBOW = 14
LEFT_WRIST = 15
RIGHT_WRIST = 16
LEFT_PINKY = 17
RIGHT_PINKY = 18
LEFT_INDEX = 19
RIGHT_INDEX = 20
LEFT_THUMB = 21
RIGHT_THUMB = 22
LEFT_HIP = 23
RIGHT_HIP = 24
LEFT_KNEE = 25
RIGHT_KNEE = 26
LEFT_ANKLE = 27
RIGHT_ANKLE = 28
LEFT_HEEL = 29
RIGHT_HEEL = 30
LEFT_FOOT_INDEX = 31
RIGHT_FOOT_INDEX = 32

# 关键点连接关系（用于绘制骨骼）
POSE_CONNECTIONS = [
    (NOSE, LEFT_EYE_INNER), (LEFT_EYE_INNER, LEFT_EYE), (LEFT_EYE, LEFT_EYE_OUTER), (LEFT_EYE_OUTER, LEFT_EAR),
    (NOSE, RIGHT_EYE_INNER), (RIGHT_EYE_INNER, RIGHT_EYE), (RIGHT_EYE, RIGHT_EYE_OUTER), (RIGHT_EYE_OUTER, RIGHT_EAR),
    (MOUTH_LEFT, MOUTH_RIGHT),
    (LEFT_SHOULDER, RIGHT_SHOULDER), (LEFT_SHOULDER, LEFT_ELBOW), (LEFT_ELBOW, LEFT_WRIST),
    (RIGHT_SHOULDER, RIGHT_ELBOW), (RIGHT_ELBOW, RIGHT_WRIST),
    (LEFT_WRIST, LEFT_PINKY), (LEFT_WRIST, LEFT_INDEX), (LEFT_INDEX, LEFT_THUMB),
    (RIGHT_WRIST, RIGHT_PINKY), (RIGHT_WRIST, RIGHT_INDEX), (RIGHT_INDEX, RIGHT_THUMB),
    (LEFT_SHOULDER, LEFT_HIP), (RIGHT_SHOULDER, RIGHT_HIP), (LEFT_HIP, RIGHT_HIP),
    (LEFT_HIP, LEFT_KNEE), (LEFT_KNEE, LEFT_ANKLE),
    (RIGHT_HIP, RIGHT_KNEE), (RIGHT_KNEE, RIGHT_ANKLE),
    (LEFT_ANKLE, LEFT_HEEL), (LEFT_HEEL, LEFT_FOOT_INDEX),
    (RIGHT_ANKLE, RIGHT_HEEL), (RIGHT_HEEL, RIGHT_FOOT_INDEX),
]


def calculate_angle(p1: np.ndarray, p2: np.ndarray, p3: np.ndarray) -> float:
    """计算三点形成的角度（p2为顶点）"""
    v1 = p1 - p2
    v2 = p3 - p2
    dot = np.dot(v1, v2)
    mag1 = np.linalg.norm(v1)
    mag2 = np.linalg.norm(v2)
    if mag1 == 0 or mag2 == 0:
        return 180.0
    cos_angle = dot / (mag1 * mag2)
    cos_angle = max(min(cos_angle, 1.0), -1.0)
    return float(np.degrees(np.arccos(cos_angle)))


class PoseExtractor:
    def __init__(self, min_det_conf: float = 0.3, min_track_conf: float = 0.3):
        # 设置默认模型路径 - 优先使用finallmodel目录下的模型
        # 当前文件在 finallmodel/model/pose_features.py
        # 模型文件在 finallmodel/pose_landmarker_lite.task
        current_dir = os.path.dirname(os.path.abspath(__file__))  # finallmodel/model
        parent_dir = os.path.dirname(current_dir)  # finallmodel
        
        model_path = os.path.join(parent_dir, 'pose_landmarker_lite.task')
        
        # 如果lite模型不存在，尝试full模型
        if not os.path.exists(model_path):
            model_path = os.path.join(parent_dir, 'pose_landmarker.task')
        
        # 如果仍然不存在，检查fallmodel目录
        if not os.path.exists(model_path):
            model_path = 'e:/fallmodel/pose_landmarker.task'
        
        # 如果仍然不存在，检查back目录
        if not os.path.exists(model_path):
            model_path = os.path.join(os.path.dirname(parent_dir), 'pose_landmarker.task')
        
        print(f"PoseExtractor使用模型: {model_path}")
        
        base_options = python.BaseOptions(model_asset_path=model_path)
        
        # 创建两个检测器：一个用于视频模式，一个用于图像模式
        video_options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            min_pose_detection_confidence=min_det_conf,
            min_tracking_confidence=min_track_conf,
            num_poses=1,
        )
        image_options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.IMAGE,
            min_pose_detection_confidence=min_det_conf,
            min_tracking_confidence=min_track_conf,
            num_poses=1,
        )
        
        self.video_detector = vision.PoseLandmarker.create_from_options(video_options)
        self.image_detector = vision.PoseLandmarker.create_from_options(image_options)
        self.frame_timestamp_ms = 0

    def extract(self, frame_bgr: np.ndarray, mode: str = 'video') -> Optional[PoseFrameFeatures]:
        """
        提取人体姿态特征
        :param frame_bgr: BGR格式的图像帧
        :param mode: 'video' 用于视频序列检测（带追踪），'image' 用于单帧图像检测
        """
        h, w = frame_bgr.shape[:2]
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        
        # 根据模式选择检测器
        if mode == 'image':
            # 图像模式：适合单帧实时检测
            result = self.image_detector.detect(mp_image)
        else:
            # 视频模式：适合视频序列检测（带追踪）
            self.frame_timestamp_ms += 50  # Assume ~20fps
            result = self.video_detector.detect_for_video(mp_image, self.frame_timestamp_ms)
        
        if not result.pose_landmarks or len(result.pose_landmarks) == 0:
            return None

        landmarks = result.pose_landmarks[0]
        points = np.array([[lm.x * w, lm.y * h, lm.visibility] for lm in landmarks], dtype=np.float32)
        valid = points[:, 2] > 0.1  # 降低可见性阈值
        
        # 至少需要检测到关键骨骼点 - 降低要求，只需要3个关键点
        required_points = [NOSE, LEFT_SHOULDER, RIGHT_SHOULDER, LEFT_HIP, RIGHT_HIP]
        if sum(valid[required_points]) < 3:
            return None
            
        xy = points[valid, :2]
        x1, y1 = np.min(xy, axis=0)
        x2, y2 = np.max(xy, axis=0)

        # 提取关键关节点
        l_shoulder = points[LEFT_SHOULDER, :2] if valid[LEFT_SHOULDER] else np.array([w/2, h/3])
        r_shoulder = points[RIGHT_SHOULDER, :2] if valid[RIGHT_SHOULDER] else np.array([w/2, h/3])
        l_hip = points[LEFT_HIP, :2] if valid[LEFT_HIP] else np.array([w/3, h/2])
        r_hip = points[RIGHT_HIP, :2] if valid[RIGHT_HIP] else np.array([2*w/3, h/2])
        head = points[NOSE, :2] if valid[NOSE] else np.array([w/2, h/4])
        l_knee = points[LEFT_KNEE, :2] if valid[LEFT_KNEE] else np.array([w/3, 2*h/3])
        r_knee = points[RIGHT_KNEE, :2] if valid[RIGHT_KNEE] else np.array([2*w/3, 2*h/3])
        l_ankle = points[LEFT_ANKLE, :2] if valid[LEFT_ANKLE] else np.array([w/3, h])
        r_ankle = points[RIGHT_ANKLE, :2] if valid[RIGHT_ANKLE] else np.array([2*w/3, h])
        l_elbow = points[LEFT_ELBOW, :2] if valid[LEFT_ELBOW] else l_shoulder
        r_elbow = points[RIGHT_ELBOW, :2] if valid[RIGHT_ELBOW] else r_shoulder
        l_wrist = points[LEFT_WRIST, :2] if valid[LEFT_WRIST] else l_elbow
        r_wrist = points[RIGHT_WRIST, :2] if valid[RIGHT_WRIST] else r_elbow

        # 计算重心（臀部中心）
        center_y = float((l_hip[1] + r_hip[1]) / 2.0 / h)
        
        # 计算身体倾斜角度（头部到腿部的角度）
        knee = (l_knee + r_knee) / 2.0
        ankle = (l_ankle + r_ankle) / 2.0
        leg_center = (knee + ankle) / 2.0
        dx = abs(head[0] - leg_center[0]) + 1e-6
        dy = abs(head[1] - leg_center[1])
        tilt_deg = float(math.degrees(math.atan2(dy, dx)))

        # 计算宽高比
        body_width = max(float(x2 - x1), 1.0)
        body_height = max(float(y2 - y1), 1.0)
        wh_ratio = body_width / body_height

        # 计算关节角度
        elbow_angle = calculate_angle(l_shoulder, l_elbow, l_wrist)
        knee_angle = calculate_angle(l_hip, l_knee, l_ankle)
        hip_angle = calculate_angle(l_shoulder, l_hip, l_knee)
        shoulder_angle = calculate_angle(l_hip, l_shoulder, l_elbow)

        return PoseFrameFeatures(
            keypoints=points[:, :2] / np.array([w, h], dtype=np.float32),
            bbox=(float(x1), float(y1), float(x2), float(y2)),
            center_y=center_y,
            tilt_deg=tilt_deg,
            wh_ratio=wh_ratio,
            elbow_angle=elbow_angle,
            knee_angle=knee_angle,
            hip_angle=hip_angle,
            shoulder_angle=shoulder_angle,
            body_height=body_height / h,
            body_width=body_width / w,
            head_position=(float(head[0] / w), float(head[1] / h)),
        )

    def draw_skeleton(self, frame: np.ndarray, feat: PoseFrameFeatures) -> np.ndarray:
        """在帧上绘制骨骼姿态标注"""
        h, w = frame.shape[:2]
        points = feat.keypoints * np.array([w, h])
        
        # 绘制骨骼连接
        for connection in POSE_CONNECTIONS:
            idx1, idx2 = connection
            p1 = points[idx1]
            p2 = points[idx2]
            cv2.line(frame, (int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1])), (0, 255, 0), 2)
        
        # 绘制关键点
        for i, point in enumerate(points):
            cv2.circle(frame, (int(point[0]), int(point[1])), 3, (0, 0, 255), -1)
        
        return frame


class FallRuleEngine:
    def __init__(self, cfg: RuleConfig):
        self.cfg = cfg
        self.history: Dict[str, list] = {
            "center_y": [], "tilt_deg": [], "wh_ratio": [], "fall_flag": [],
            "elbow_angle": [], "knee_angle": [], "hip_angle": [], "shoulder_angle": [],
            "body_height": [], "body_width": []
        }
        self.fall_start_frame: Optional[int] = None
        self.frame_idx = 0
        self.alert_triggered = False

    def update(self, feat: PoseFrameFeatures) -> Dict[str, float]:
        self.frame_idx += 1
        
        # 存储历史特征
        self.history["center_y"].append(feat.center_y)
        self.history["tilt_deg"].append(feat.tilt_deg)
        self.history["wh_ratio"].append(feat.wh_ratio)
        self.history["elbow_angle"].append(feat.elbow_angle)
        self.history["knee_angle"].append(feat.knee_angle)
        self.history["hip_angle"].append(feat.hip_angle)
        self.history["shoulder_angle"].append(feat.shoulder_angle)
        self.history["body_height"].append(feat.body_height)
        self.history["body_width"].append(feat.body_width)

        # 论文规则检测
        M1 = self._cgdd()  # 重心下降检测
        M2 = self._btd(feat.tilt_deg)  # 身体倾斜检测
        M3 = self._scdd(feat.wh_ratio)  # 形状变化检测
        M4 = self._jad(feat.elbow_angle, feat.knee_angle, feat.hip_angle)  # 关节角度检测
        M5 = self._bhd(feat.body_height)  # 身体高度检测
        
        # 综合判定：所有条件都满足才判定为跌倒
        fall_now = 1 if (M1 and M2 and M3 and M4 and M5) else 0
        self.history["fall_flag"].append(fall_now)

        if fall_now and self.fall_start_frame is None:
            self.fall_start_frame = self.frame_idx
            print(f"[检测] 满足跌倒条件! M1={M1}, M2={M2}, M3={M3}, M4={M4}, M5={M5}, 帧={self.frame_idx}")

        alert = 0
        if self.fall_start_frame is not None and not self._can_stand_up():
            elapsed = (self.frame_idx - self.fall_start_frame) / self.cfg.fps
            if elapsed >= self.cfg.t_cr_sec and not self.alert_triggered:
                alert = 1
                self.alert_triggered = True
                print(f"[告警] 跌倒确认! 持续躺卧超过 {self.cfg.t_cr_sec}秒")
            elif elapsed >= self.cfg.t_cr_sec:
                alert = 1  # 保持告警状态

        return {
            "M1": float(M1), "M2": float(M2), "M3": float(M3), 
            "M4": float(M4), "M5": float(M5),
            "fall_rule": float(fall_now), "alert": float(alert)
        }

    def _cgdd(self) -> int:
        """CGDD - Center of Gravity Drop Detection (重心下降检测)
        检测重心在短时间内的快速下降，这是跌倒的重要特征"""
        n = len(self.history["center_y"])
        gap = self.cfg.cgdd_frame_gap
        if n <= gap:
            return 0
        
        # 计算重心下降速度
        y1 = self.history["center_y"][-gap - 1]
        y2 = self.history["center_y"][-1]
        dt = gap / self.cfg.fps
        v = abs(y2 - y1) / max(dt, 1e-6)
        
        # 速度超过阈值表示快速下降
        return 1 if v >= self.cfg.v_cr else 0

    def _btd(self, tilt_deg: float) -> int:
        """BTD - Body Tilt Detection (身体倾斜检测)
        检测身体是否处于水平状态（跌倒后通常身体水平）"""
        # 倾斜角度小于阈值表示身体接近水平
        return 1 if tilt_deg < self.cfg.theta_cr_deg else 0

    def _scdd(self, wh_ratio: float) -> int:
        """SCDD - Shape Change Detection (形状变化检测)
        检测身体宽高比的变化，跌倒后身体变宽"""
        # 宽高比大于阈值表示身体呈水平姿态
        return 1 if wh_ratio >= self.cfg.p_cr else 0

    def _jad(self, elbow_angle: float, knee_angle: float, hip_angle: float) -> int:
        """JAD - Joint Angle Detection (关节角度检测)
        检测关节角度变化，跌倒时关节通常会伸直"""
        # 至少两个关节角度超过阈值（伸直状态）
        score = 0
        if elbow_angle > self.cfg.elbow_angle_cr:
            score += 1
        if knee_angle > self.cfg.knee_angle_cr:
            score += 1
        if hip_angle > self.cfg.hip_angle_cr:
            score += 1
        return 1 if score >= 2 else 0

    def _bhd(self, body_height: float) -> int:
        """BHD - Body Height Detection (身体高度检测)
        检测身体高度的变化，跌倒后身体高度显著降低"""
        if len(self.history["body_height"]) < 10:
            return 0
        
        # 计算平均历史高度
        avg_height = np.mean(self.history["body_height"][:-5])
        
        # 当前高度明显低于历史平均高度
        return 1 if body_height < avg_height * 0.7 else 0

    def _can_stand_up(self) -> bool:
        """检测是否已经站起来"""
        if len(self.history["wh_ratio"]) < self.cfg.cgdd_frame_gap:
            return False
        
        recent_p = np.mean(self.history["wh_ratio"][-self.cfg.cgdd_frame_gap:])
        recent_t = np.mean(self.history["tilt_deg"][-self.cfg.cgdd_frame_gap:])
        recent_h = np.mean(self.history["body_height"][-self.cfg.cgdd_frame_gap:])
        
        # 站起来的条件：宽高比小于1，倾斜角度大于阈值，身体高度恢复
        has_stood = (recent_p < 1.0) and (recent_t > self.cfg.theta_cr_deg)
        
        if has_stood and self.alert_triggered:
            print(f"[恢复] 检测到站立恢复，帧={self.frame_idx}")
            self.alert_triggered = False
            self.fall_start_frame = None
        
        return has_stood
