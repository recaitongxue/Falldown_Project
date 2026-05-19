import argparse
import base64
import json
import os
import uuid
import threading
import time
from datetime import datetime, timedelta
from collections import deque
from functools import wraps

import cv2
import numpy as np
import torch
from flask import Flask, jsonify, request, send_from_directory, session, send_file, make_response
import re
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from PIL import Image, ImageDraw, ImageFont
import mediapipe as mp

app = Flask(__name__, static_folder='../frontend/dist', static_url_path='/')
app.secret_key = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fall_detection.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = 'uploads'
CORS(app, supports_credentials=True)

db = SQLAlchemy(app)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='user')
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "role": self.role,
            "email": self.email,
            "phone": self.phone,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "is_active": self.is_active
        }


class Camera(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200))
    camera_type = db.Column(db.String(20), default='rtsp')
    url = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, default=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_check = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='offline')

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "location": self.location,
            "camera_type": self.camera_type,
            "url": self.url,
            "is_active": self.is_active,
            "user_id": self.user_id,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class DetectionRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    event_type = db.Column(db.String(50))
    detected_class = db.Column(db.String(50))
    confidence = db.Column(db.Float)
    m1_triggered = db.Column(db.Boolean, default=False)
    m2_triggered = db.Column(db.Boolean, default=False)
    m3_triggered = db.Column(db.Boolean, default=False)
    fall_detected = db.Column(db.Boolean, default=False)
    alert_triggered = db.Column(db.Boolean, default=False)
    video_path = db.Column(db.String(500))
    camera_id = db.Column(db.Integer, db.ForeignKey('camera.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    alert_sent = db.Column(db.Boolean, default=False)
    alert_method = db.Column(db.String(50))

    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "event_type": self.event_type,
            "detected_class": self.detected_class,
            "confidence": self.confidence,
            "M1": self.m1_triggered,
            "M2": self.m2_triggered,
            "M3": self.m3_triggered,
            "fall_detected": self.fall_detected,
            "alert": self.alert_triggered,
            "video_path": self.video_path,
            "camera_id": self.camera_id,
            "user_id": self.user_id
        }


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
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    acknowledged = db.Column(db.Boolean, default=False)
    acknowledged_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    acknowledged_at = db.Column(db.DateTime)
    response_action = db.Column(db.Text)

    def to_dict(self):
        user = User.query.get(self.user_id) if self.user_id else None
        return {
            "id": self.id,
            "record_id": self.record_id,
            "user_id": self.user_id,
            "username": user.username if user else None,
            "alert_type": self.alert_type,
            "severity": self.severity,
            "message": self.message,
            "title": self.title or "跌倒检测告警",
            "detection_type": self.detection_type or "fall",
            "confidence": self.confidence or 0.0,
            "sent_to": self.sent_to,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "acknowledged": self.acknowledged,
            "acknowledged_by": self.acknowledged_by,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "timestamp": self.sent_at.isoformat() if self.sent_at else None
        }


class SystemConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True)
    value = db.Column(db.Text)

    def to_dict(self):
        return {"key": self.key, "value": self.value}


class AnalysisRecord(db.Model):
    """分析记录表"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    processed_filename = db.Column(db.String(255))
    input_path = db.Column(db.String(500), nullable=False)
    output_path = db.Column(db.String(500))
    file_type = db.Column(db.String(20), nullable=False)  # video, image
    status = db.Column(db.String(20), default='processing')  # processing, completed, failed
    total_frames = db.Column(db.Integer, default=0)
    detected_frames = db.Column(db.Integer, default=0)
    fall_detected = db.Column(db.Boolean, default=False)
    alert_count = db.Column(db.Integer, default=0)
    ai_analysis = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "original_filename": self.original_filename,
            "processed_filename": self.processed_filename,
            "input_path": self.input_path,
            "output_path": self.output_path,
            "file_type": self.file_type,
            "status": self.status,
            "total_frames": self.total_frames,
            "detected_frames": self.detected_frames,
            "fall_detected": self.fall_detected,
            "alert_count": self.alert_count,
            "ai_analysis": self.ai_analysis,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }


class AIAgent:
    def __init__(self):
        self.is_running = False
        self.alert_callbacks = []
        self.behavior_history = deque(maxlen=100)
        self.risk_score = 0.0
        self.fall_patterns = []
        self.normal_patterns = []
        self.conversation_context = {}
        # Ollama配置
        self.ollama_host = "http://localhost:11434"
        self.ollama_model = "qwen3:1.7b"
        self.ollama_enabled = True
        self.ollama_available = self._check_ollama()
    
    def _check_ollama(self):
        """检查Ollama服务是否可用"""
        try:
            import requests
            resp = requests.get(f"{self.ollama_host}/api/tags", timeout=5)
            return resp.status_code == 200
        except Exception:
            return False
    
    def set_ollama_config(self, host=None, model=None):
        """设置Ollama配置"""
        if host:
            self.ollama_host = host
        if model:
            self.ollama_model = model
        self.ollama_available = self._check_ollama()
        return self.ollama_available
    
    def get_ollama_models(self):
        """获取Ollama可用模型列表"""
        try:
            import requests
            resp = requests.get(f"{self.ollama_host}/api/tags", timeout=5)
            if resp.status_code == 200:
                return resp.json().get('models', [])
        except Exception as e:
            print(f"Error fetching Ollama models: {e}")
        return []
    
    def _call_ollama(self, messages):
        """调用Ollama API"""
        try:
            import requests
            data = {
                "model": self.ollama_model,
                "messages": messages,
                "stream": False
            }
            resp = requests.post(f"{self.ollama_host}/api/chat", json=data, timeout=60)
            if resp.status_code == 200:
                return resp.json().get('message', {}).get('content', '')
            else:
                print(f"Ollama API error: {resp.status_code}")
                return ""
        except Exception as e:
            print(f"Error calling Ollama: {e}")
            return ""

    def register_alert_callback(self, callback):
        self.alert_callbacks.append(callback)

    def analyze_behavior(self, result, context=None):
        self.behavior_history.append({
            'timestamp': datetime.utcnow(),
            'result': result,
            'context': context
        })

        risk = 0.0
        if result.get('fall_detected'):
            risk += 0.6
        if result.get('alert'):
            risk += 0.3
        if result.get('M1') and result.get('M2'):
            risk += 0.1

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

    def _get_recommendation(self, risk, result):
        if risk > 0.7:
            return "高风险！立即检查人员状态，建议启动紧急救援流程"
        elif risk > 0.4:
            return "中度风险，增加监控频率，观察人员状态变化"
        else:
            return "风险较低，保持正常监控"

    def _detect_pattern(self, recent):
        if len(recent) < 5:
            return None

        statuses = [r['result'].get('detected_class', 'unknown') for r in recent]
        if statuses.count('lying') >= 3:
            return "长时间躺卧"
        if statuses.count('bending') >= 4:
            return "频繁弯腰"
        return None

    def generate_report(self):
        history = list(self.behavior_history)
        if not history:
            return {"summary": "暂无数据", "patterns": [], "risk_trend": "stable"}

        fall_events = [h for h in history if h['result'].get('fall_detected')]
        return {
            "total_events": len(history),
            "fall_events": len(fall_events),
            "avg_risk": sum(self.risk_score for _ in history) / len(history),
            "risk_trend": "increasing" if self.risk_score > 0.5 else "stable",
            "patterns": [self._detect_pattern(history[i:i+5]) for i in range(0, len(history)-5, 5)],
            "recommendations": self._generate_recommendations(history)
        }

    def _generate_recommendations(self, history):
        recommendations = []
        fall_count = sum(1 for h in history if h['result'].get('fall_detected'))
        if fall_count > 10:
            recommendations.append("近期跌倒事件较多，建议检查环境安全性")
        if self.risk_score > 0.6:
            recommendations.append("当前风险等级较高，需要重点关注")
        return recommendations

    def analyze_batch(self, results):
        if not results:
            return {"risk_level": 0, "risk_label": "low", "recommendations": []}
        
        fall_count = sum(1 for r in results if r.get('fall_detected'))
        alert_count = sum(1 for r in results if r.get('alert'))
        total = len(results)
        
        risk = 0.0
        if fall_count > total * 0.3:
            risk += 0.5
        if alert_count > total * 0.2:
            risk += 0.3
        
        avg_confidence = sum(r.get('confidence', 0) for r in results) / total if total > 0 else 0
        if avg_confidence > 0.8:
            risk += 0.2
        
        risk = min(1.0, risk)
        
        recommendations = []
        if risk > 0.7:
            recommendations.append("检测到大量跌倒事件，建议立即检查")
            recommendations.append("可能存在安全隐患，需要人工干预")
        elif risk > 0.4:
            recommendations.append("检测到部分异常行为，建议加强监控")
            recommendations.append("关注后续行为变化")
        
        return {
            "risk_level": risk,
            "risk_label": "high" if risk > 0.7 else "medium" if risk > 0.4 else "low",
            "recommendations": recommendations,
            "statistics": {
                "total_frames": total,
                "fall_frames": fall_count,
                "alert_frames": alert_count,
                "avg_confidence": avg_confidence
            }
        }

    def chat(self, message, user_id=None):
        context_key = user_id or 'default'
        if context_key not in self.conversation_context:
            self.conversation_context[context_key] = []

        self.conversation_context[context_key].append({
            'role': 'user',
            'content': message,
            'timestamp': datetime.utcnow()
        })

        history = list(self.behavior_history)[-5:]
        
        # 优先使用Ollama
        if self.ollama_enabled and self.ollama_available:
            response = self._generate_ollama_response(message, history)
        else:
            response = self._generate_response(message, history)

        self.conversation_context[context_key].append({
            'role': 'assistant',
            'content': response,
            'timestamp': datetime.utcnow()
        })

        return response
    
    def _generate_ollama_response(self, message, history):
        """使用Ollama生成响应"""
        # 获取系统状态信息
        report = self.generate_report()
        risk_level = report.get('risk_label', 'low')
        fall_events = report.get('fall_events', 0)
        recommendations = report.get('recommendations', [])
        
        # 构建系统提示词
        system_prompt = f"""你是一个跌倒检测系统的AI助手。

系统状态信息：
- 当前风险等级：{risk_level}
- 近期跌倒事件：{fall_events}次
- 系统建议：{' '.join(recommendations)}

你的任务是：
1. 分析跌倒风险并提供建议
2. 回答用户关于系统功能的问题
3. 帮助用户理解检测结果
4. 提供友好的技术支持

请用中文回答，保持专业且友好。
"""
        
        # 构建消息历史
        ollama_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ]
        
        response = self._call_ollama(ollama_messages)
        
        # 如果Ollama调用失败，使用备用响应
        if not response:
            return self._generate_response(message, history)
        
        return response

    def _generate_response(self, message, history):
        """备用响应生成器（当Ollama不可用时）"""
        message_lower = message.lower()

        if any(kw in message_lower for kw in ['风险', 'risk', '分析']):
            report = self.generate_report()
            return f"当前系统风险评估：{report.get('risk_trend', '稳定')}\n近期跌倒事件：{report.get('fall_events', 0)}次\n建议：{' '.join(report.get('recommendations', ['保持监控']))}"

        if any(kw in message_lower for kw in ['帮助', 'help', '功能']):
            return "我可以帮助您：\n1. 分析跌倒风险\n2. 查看检测历史\n3. 管理摄像头\n4. 生成报告\n5. 回答系统相关问题"

        if any(kw in message_lower for kw in ['状态', 'status', '情况']):
            return f"当前监控状态：\n- 风险等级：{'高' if self.risk_score > 0.6 else '中' if self.risk_score > 0.3 else '低'}\n- 待处理告警：{sum(1 for h in history if h['result'].get('alert') and not h['result'].get('acknowledged'))}条"

        return f"我已收到您的问题：{message}\n当前系统运行正常，如有需要请随时提问。"


class FallDetectionSystem:
    def __init__(self, ckpt_path="checkpoints/best_gru.pt", device_name="cpu"):
        self.device = torch.device(device_name if torch.cuda.is_available() else "cpu")
        self.model_cfg = ModelConfig(device=self.device)
        self.rule_cfg = RuleConfig(
            fps=20.0,
            cgdd_frame_gap=10,
            v_cr=0.015,
            theta_cr_deg=60.0,
            p_cr=0.7,
            t_cr_sec=15.0
        )

        try:
            from network import FallActionGRU
            self.model = FallActionGRU(
                input_size=33 * 2 + 3,
                hidden_size=self.model_cfg.hidden_size,
                num_layers=self.model_cfg.num_layers,
                num_classes=len(self.model_cfg.class_names),
                dropout=self.model_cfg.dropout,
            ).to(self.device)

            if os.path.exists(ckpt_path):
                state = torch.load(ckpt_path, map_location=self.device, weights_only=True)
                self.model.load_state_dict(state["state_dict"], strict=False)
                print(f"Model loaded from {ckpt_path}")
            self.model.eval()
        except Exception as e:
            print(f"Model loading error: {e}")
            self.model = None

        self.pose = PoseExtractor()
        self.rule = FallRuleEngine(self.rule_cfg)
        self.seq = deque(maxlen=self.model_cfg.sequence_length)
        self.class_names = self.model_cfg.class_names

    def reset(self):
        self.seq.clear()
        self.rule = FallRuleEngine(self.rule_cfg)

    def process_frame(self, frame):
        feat = self.pose.extract(frame)

        if feat is None:
            return frame, {
                "status": "no_person",
                "detected_class": "未检测到人体",
                "confidence": 0.0,
                "M1": False, "M2": False, "M3": False,
                "fall_detected": False, "alert": False
            }

        vec = np.concatenate([
            feat.keypoints.reshape(-1).astype(np.float32),
            np.array([feat.center_y, feat.tilt_deg / 180.0, feat.wh_ratio], dtype=np.float32),
        ], axis=0)
        self.seq.append(vec)

        rule_result = self.rule.update(feat)
        M1, M2, M3 = bool(rule_result["M1"]), bool(rule_result["M2"]), bool(rule_result["M3"])
        rule_fall = rule_result["fall_rule"]
        alert = rule_result["alert"]

        detected_class = "unknown"
        class_prob = 0.0

        if self.model and len(self.seq) == self.model_cfg.sequence_length:
            x = torch.from_numpy(np.stack(self.seq).astype(np.float32)).unsqueeze(0).to(self.device)
            with torch.no_grad():
                logits = self.model(x)
                prob = torch.softmax(logits, dim=1)[0].cpu().numpy()
                idx = int(prob.argmax())
                class_prob = float(prob[idx])
                detected_class = self.class_names[idx] if idx < len(self.class_names) else str(idx)

        # 综合模型预测和规则引擎的结果
        model_fall_score = 0.0
        if detected_class == "lying" and class_prob > 0.5:
            model_fall_score = class_prob
        elif detected_class == "bending" and class_prob > 0.7:
            model_fall_score = class_prob * 0.5
        
        # 模型预测权重更高
        combined_fall = (model_fall_score * 0.7 + rule_fall * 0.3)

        if alert > 0.5:
            color = (0, 0, 255)
            status_text = "ALERT: 跌倒告警!"
        elif combined_fall > 0.6:
            color = (0, 165, 255)
            status_text = "WARNING: 疑似跌倒"
        else:
            color = (0, 255, 0)
            status_text = f"STATUS: {detected_class}"

        frame = draw_text_cn(frame, status_text, 20, 40, color, 32)
        frame = draw_text_cn(frame, f"行为: {detected_class} ({class_prob:.2f})", 20, 80, color, 26)
        frame = draw_text_cn(frame, f"M1(重心): {'是' if M1 else '否'}", 20, 115, color, 22)
        frame = draw_text_cn(frame, f"M2(倾斜): {'是' if M2 else '否'}", 20, 145, color, 22)
        frame = draw_text_cn(frame, f"M3(变形): {'是' if M3 else '否'}", 20, 175, color, 22)

        return frame, {
            "status": "detecting",
            "detected_class": detected_class,
            "confidence": class_prob,
            "M1": M1, "M2": M2, "M3": M3,
            "fall_detected": combined_fall > 0.5,
            "alert": alert > 0.5
        }


def get_font(font_size=20):
    font_paths = [
        r"C:\Windows\Fonts\simhei.ttf",
        r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\msyh.ttf",
        r"C:\Windows\Fonts\simsun.ttc",
        r"C:\Windows\Fonts\simkai.ttf",
        "simhei.ttf",
        "msyh.ttc",
    ]
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                return ImageFont.truetype(font_path, font_size)
            except:
                continue
    return ImageFont.load_default()


def draw_text_cn(frame, text, x, y, color=(0, 255, 0), font_size=20):
    font = get_font(font_size)
    img_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    # 添加黑色边框使文字更清晰可见
    for dx in [-2, -1, 0, 1, 2]:
        for dy in [-2, -1, 0, 1, 2]:
            if dx != 0 or dy != 0:
                draw.text((x + dx, y + dy), text, font=font, fill=(0, 0, 0))
    draw.text((x, y), text, font=font, fill=(color[2], color[1], color[0]))
    return cv2.cvtColor(np.array(img_pil), cv2.COLOR_BGR2RGB)


def fix_mp4_for_streaming(input_path):
    """修复MP4文件使其支持流式播放（重新编码为H.264并移动moov atom到文件开头）"""
    import subprocess
    import os
    
    # 检查是否有ffmpeg可用
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=5)
        if result.returncode != 0:
            raise FileNotFoundError("ffmpeg not found")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("ffmpeg not available, skipping video transcoding")
        return
    
    # 使用ffmpeg重新编码视频为H.264格式（浏览器兼容），并将moov atom移到开头
    temp_path = input_path + ".temp.mp4"
    try:
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-c:v', 'libx264',
            '-crf', '23',
            '-preset', 'fast',
            '-c:a', 'aac',
            '-movflags', 'faststart',
            '-y',
            temp_path
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=120)
        if result.returncode == 0:
            os.replace(temp_path, input_path)
            print(f"Fixed moov atom and transcoded to H.264: {input_path}")
        else:
            print(f"Failed to transcode video: {result.stderr.decode('utf-8', errors='ignore')}")
            if os.path.exists(temp_path):
                os.remove(temp_path)
    except Exception as e:
        print(f"Error transcoding video: {e}")
        if os.path.exists(temp_path):
            os.remove(temp_path)


class ModelConfig:
    def __init__(self, device=None):
        self.hidden_size = 128
        self.num_layers = 2
        self.dropout = 0.3
        self.learning_rate = 0.001
        self.weight_decay = 0.0001
        self.sequence_length = 16
        self.num_workers = 4
        self.class_names = ["empty", "standing", "sitting", "lying", "bending", "crawling", "empty"]
        self.checkpoint_dir = "checkpoints"
        self.device = device or torch.device("cpu")


class RuleConfig:
    def __init__(self, fps=20.0, cgdd_frame_gap=5, v_cr=0.009, theta_cr_deg=45.0, p_cr=1.0, t_cr_sec=10.0):
        self.fps = fps
        self.cgdd_frame_gap = cgdd_frame_gap
        self.v_cr = v_cr
        self.theta_cr_deg = theta_cr_deg
        self.p_cr = p_cr
        self.t_cr_sec = t_cr_sec


class PoseExtractor:
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.pose = None
        self.last_frame_shape = None
        self.mp_drawing = mp.solutions.drawing_utils
        self._create_pose()

    def _create_pose(self):
        if self.pose is not None:
            self.pose.close()
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            enable_segmentation=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

    def extract(self, frame):
        # 检查帧尺寸是否变化，如果变化则重新创建pose实例
        current_shape = frame.shape[:2]
        if self.last_frame_shape is not None and current_shape != self.last_frame_shape:
            self._create_pose()
        self.last_frame_shape = current_shape
        
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        try:
            results = self.pose.process(frame_rgb)
        except RuntimeError:
            # 如果处理失败，尝试重新创建pose实例
            self._create_pose()
            results = self.pose.process(frame_rgb)

        if not results.pose_landmarks:
            return None

        h, w = frame.shape[:2]
        landmarks = results.pose_landmarks.landmark

        keypoints = []
        for lm in landmarks:
            keypoints.extend([lm.x, lm.y])

        left_hip = landmarks[self.mp_pose.PoseLandmark.LEFT_HIP]
        right_hip = landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP]
        center_y = (left_hip.y + right_hip.y) / 2

        nose = landmarks[self.mp_pose.PoseLandmark.NOSE]
        shoulder_y = (landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER].y +
                      landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER].y) / 2
        leg_center_y = (left_hip.y + right_hip.y) / 2

        dx = nose.x - (left_hip.x + right_hip.x) / 2
        dy = nose.y - leg_center_y
        tilt_deg = abs(np.arctan2(dy, abs(dx) + 0.001)) * 180 / np.pi

        min_x = min_y = 1.0
        max_x = max_y = 0.0
        for lm in landmarks:
            min_x = min(min_x, lm.x)
            max_x = max(max_x, lm.x)
            min_y = min(min_y, lm.y)
            max_y = max(max_y, lm.y)

        bbox_w = (max_x - min_x) * w
        bbox_h = (max_y - min_y) * h
        wh_ratio = bbox_w / (bbox_h + 0.001)

        return type('PoseFrameFeatures', (), {
            'keypoints': np.array(keypoints),
            'center_y': center_y,
            'tilt_deg': tilt_deg,
            'wh_ratio': wh_ratio,
            'bbox': (min_x * w, min_y * h, bbox_w, bbox_h)
        })()


class FallRuleEngine:
    def __init__(self, cfg):
        self.cfg = cfg
        self.history = {"center_y": deque(maxlen=20), "tilt_deg": deque(maxlen=20),
                        "wh_ratio": deque(maxlen=20), "fall_flag": deque(maxlen=20)}
        self.frame_idx = 0
        self.fall_start_frame = None

    def _cgdd(self):
        if len(self.history["center_y"]) < self.cfg.cgdd_frame_gap + 1:
            return False
        y1 = self.history["center_y"][-1]
        y2 = self.history["center_y"][-(self.cfg.cgdd_frame_gap + 1)]
        dt = self.cfg.cgdd_frame_gap / self.cfg.fps
        v = abs(y1 - y2) / dt
        return v >= self.cfg.v_cr

    def _btd(self, tilt_deg):
        return tilt_deg > self.cfg.theta_cr_deg

    def _scdd(self, wh_ratio):
        return wh_ratio >= self.cfg.p_cr

    def _can_stand_up(self):
        if len(self.history["fall_flag"]) < 10:
            return True
        recent_flags = list(self.history["fall_flag"])[-10:]
        if sum(recent_flags) < 5:
            return True
        tilt_history = list(self.history["tilt_deg"])[-10:]
        if any(t < 30 for t in tilt_history):
            return True
        return False

    def update(self, feat):
        self.frame_idx += 1
        self.history["center_y"].append(feat.center_y)
        self.history["tilt_deg"].append(feat.tilt_deg)
        self.history["wh_ratio"].append(feat.wh_ratio)

        M1 = self._cgdd()
        M2 = self._btd(feat.tilt_deg)
        M3 = self._scdd(feat.wh_ratio)
        # 跌倒检测规则：满足任意两个条件即可触发跌倒检测
        conditions_met = sum([M1, M2, M3])
        fall_now = 1 if conditions_met >= 2 else 0
        self.history["fall_flag"].append(fall_now)

        if fall_now and self.fall_start_frame is None:
            self.fall_start_frame = self.frame_idx

        alert = 0
        if self.fall_start_frame is not None and not self._can_stand_up():
            elapsed = (self.frame_idx - self.fall_start_frame) / self.cfg.fps
            if elapsed >= self.cfg.t_cr_sec:
                alert = 1

        return {"M1": float(M1), "M2": float(M2), "M3": float(M3), "fall_rule": float(fall_now), "alert": float(alert)}


system = FallDetectionSystem()
ai_agent = AIAgent()
camera_streams = {}
active_sessions = {}


@app.before_request
def handle_routes():
    import os
    path = request.path
    
    # API路由不处理
    if path.startswith('/api/'):
        return None
    
    # 根路径返回index.html
    if path == '/':
        return send_from_directory(app.static_folder, "index.html")
    
    # 静态文件（有扩展名）
    filename = path.split('/')[-1] if path else ''
    if '.' in filename:
        file_path = os.path.join(app.static_folder, path.lstrip('/'))
        if os.path.exists(file_path):
            return send_from_directory(app.static_folder, path.lstrip('/'))
    
    # 前端路由返回index.html
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"error": "用户名不存在"}), 401
    
    if user.password_hash != password:
        return jsonify({"error": "密码错误"}), 401

    session['user_id'] = user.id
    session['username'] = user.username
    session['role'] = user.role
    user.last_login = datetime.utcnow()
    db.session.commit()

    return jsonify({"status": "ok", "user": user.to_dict()})


@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    email = data.get("email")
    phone = data.get("phone")

    if not username or not password:
        return jsonify({"error": "用户名和密码不能为空"}), 400

    if len(password) < 6:
        return jsonify({"error": "密码长度至少为6位"}), 400

    blocked_usernames = {'admin', 'root', 'administrator', 'superuser', 'system'}
    if username.lower() in blocked_usernames:
        return jsonify({"error": "该用户名不可用"}), 400

    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({"error": "用户名已存在"}), 409

    user = User(
        username=username,
        password_hash=password,
        role='user',
        email=email,
        phone=phone
    )
    db.session.add(user)
    db.session.commit()

    return jsonify({"status": "ok", "user": user.to_dict()}), 201


@app.route("/api/auth/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"status": "ok"})


@app.route("/api/auth/current", methods=["GET"])
def current_user():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            return jsonify({"logged_in": True, "user": user.to_dict()})
    return jsonify({"logged_in": False})


@app.route("/api/users", methods=["GET"])
def list_users():
    users = User.query.all()
    return jsonify({"users": [u.to_dict() for u in users]})


@app.route("/api/users", methods=["POST"])
def create_user():
    if 'user_id' not in session:
        return jsonify({"error": "请先登录"}), 401
    
    current_user = User.query.get(session['user_id'])
    if not current_user or current_user.role != 'admin':
        return jsonify({"error": "需要管理员权限"}), 403

    data = request.json
    username = data.get("username")
    password = data.get("password")
    role = data.get("role", "user")
    email = data.get("email")
    phone = data.get("phone")

    if not username or not password:
        return jsonify({"error": "用户名和密码不能为空"}), 400

    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({"error": "用户名已存在"}), 409

    user = User(
        username=username,
        password_hash=password,
        role=role,
        email=email,
        phone=phone
    )
    db.session.add(user)
    db.session.commit()

    return jsonify({"status": "ok", "user": user.to_dict()}), 201


@app.route("/api/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    if 'user_id' not in session:
        return jsonify({"error": "请先登录"}), 401
    
    current_user = User.query.get(session['user_id'])
    if not current_user or current_user.role != 'admin':
        return jsonify({"error": "需要管理员权限"}), 403
    
    # 不能修改自己
    if session['user_id'] == user_id:
        return jsonify({"error": "不能修改自己的信息"}), 400
    
    data = request.json
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({"error": "用户不存在"}), 404
    
    if 'email' in data:
        user.email = data['email']
    if 'phone' in data:
        user.phone = data['phone']
    
    db.session.commit()
    return jsonify({"status": "ok", "user": user.to_dict()})


@app.route("/api/users/<int:user_id>/password", methods=["PUT"])
def reset_user_password(user_id):
    if 'user_id' not in session:
        return jsonify({"error": "请先登录"}), 401
    
    current_user = User.query.get(session['user_id'])
    if not current_user or current_user.role != 'admin':
        return jsonify({"error": "需要管理员权限"}), 403

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "用户不存在"}), 404

    data = request.json
    new_password = data.get("password")
    if not new_password:
        return jsonify({"error": "新密码不能为空"}), 400

    user.password_hash = new_password
    db.session.commit()

    return jsonify({"status": "ok", "message": "密码已重置"})


@app.route("/api/users/<int:user_id>/role", methods=["PUT"])
def change_user_role(user_id):
    if 'user_id' not in session:
        return jsonify({"error": "请先登录"}), 401
    
    current_user = User.query.get(session['user_id'])
    if not current_user or current_user.role != 'admin':
        return jsonify({"error": "需要管理员权限"}), 403

    if current_user.id == user_id:
        return jsonify({"error": "不能修改自己的角色"}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "用户不存在"}), 404

    data = request.json
    new_role = data.get("role")
    if new_role not in ['admin', 'user']:
        return jsonify({"error": "角色无效"}), 400

    user.role = new_role
    db.session.commit()

    return jsonify({"status": "ok", "user": user.to_dict()})


@app.route("/api/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    if 'user_id' not in session:
        return jsonify({"error": "请先登录"}), 401
    
    current_user = User.query.get(session['user_id'])
    if not current_user or current_user.role != 'admin':
        return jsonify({"error": "需要管理员权限"}), 403

    if current_user.id == user_id:
        return jsonify({"error": "不能删除自己"}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "用户不存在"}), 404

    db.session.delete(user)
    db.session.commit()

    return jsonify({"status": "ok", "message": "用户已删除"})


@app.route("/api/users/me", methods=["DELETE"])
def delete_my_account():
    if 'user_id' not in session:
        return jsonify({"error": "请先登录"}), 401
    
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({"error": "用户不存在"}), 404
    
    db.session.delete(user)
    db.session.commit()
    
    session.clear()
    return jsonify({"status": "ok", "message": "账户已删除"})


@app.route("/api/cameras", methods=["GET", "POST"])
def manage_cameras():
    if request.method == "GET":
        cameras = Camera.query.all()
        return jsonify({"cameras": [c.to_dict() for c in cameras]})
    else:
        data = request.json
        camera = Camera(
            name=data.get("name"),
            location=data.get("location"),
            camera_type=data.get("camera_type", "rtsp"),
            url=data.get("url"),
            user_id=session.get('user_id')
        )
        db.session.add(camera)
        db.session.commit()
        return jsonify({"status": "ok", "camera": camera.to_dict()})


@app.route("/api/cameras/<int:id>", methods=["PUT", "DELETE"])
def camera_ops(id):
    camera = Camera.query.get_or_404(id)
    if request.method == "PUT":
        data = request.json
        camera.name = data.get("name", camera.name)
        camera.location = data.get("location", camera.location)
        camera.url = data.get("url", camera.url)
        camera.is_active = data.get("is_active", camera.is_active)
        db.session.commit()
        return jsonify({"status": "ok", "camera": camera.to_dict()})
    else:
        db.session.delete(camera)
        db.session.commit()
        return jsonify({"status": "ok"})


@app.route("/api/upload", methods=["POST"])
def upload_file():
    file = request.files.get('file')

    if not file:
        return jsonify({"error": "No file provided"}), 400

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    filename = f"{uuid.uuid4().hex}_{file.filename}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    file_type = request.form.get('type', 'video')
    
    file_size = os.path.getsize(filepath)

    return jsonify({
        "status": "ok",
        "filename": filename,
        "filepath": filepath,
        "file_type": file_type,
        "file_size": file_size
    })


@app.route("/api/detect/file", methods=["POST"])
def detect_file():
    data = request.json
    filepath = data.get("filepath")
    file_type = data.get("file_type", "video")

    if not filepath or not os.path.exists(filepath):
        return jsonify({"error": "File not found"}), 404

    results = []
    ai_analysis = {"risk_level": 0, "risk_label": "low", "recommendations": []}
    output_video_path = None
    
    # 获取用户ID（支持session或直接传入）
    user_id = session.get('user_id') or data.get('user_id') or 1  # 默认用户ID为1
    
    # 创建分析记录
    analysis_record = AnalysisRecord(
        user_id=user_id,
        original_filename=os.path.basename(filepath),
        input_path=filepath,
        file_type=file_type,
        status='processing'
    )
    db.session.add(analysis_record)
    db.session.commit()
    
    if file_type == "video":
        cap = cv2.VideoCapture(filepath)
        frame_idx = 0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        duration = total_frames / fps if fps > 0 else 0
        
        # 获取视频尺寸
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # 创建输出视频路径
        output_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'output')
        os.makedirs(output_dir, exist_ok=True)
        output_video_path = os.path.join(output_dir, f"output_{os.path.basename(filepath)}")
        
        # 创建视频写入器
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))
        
        while cap.isOpened():
            ok, frame = cap.read()
            if not ok:
                break
            frame_idx += 1
            
            processed_frame, result = system.process_frame(frame)
            result['frame_idx'] = frame_idx
            result['timestamp'] = frame_idx / fps if fps > 0 else 0
            
            ai_result = ai_agent.analyze_behavior(result)
            if ai_result:
                result['ai_risk'] = ai_result.get('risk_level', 0)
            
            results.append(result)
            
            # 将处理后的帧写入输出视频
            out.write(processed_frame)

            if len(results) >= 200:
                break

        cap.release()
        out.release()
        
        # 修复MP4文件的moov atom位置，使其支持流式播放
        fix_mp4_for_streaming(output_video_path)
        
        ai_analysis = ai_agent.analyze_batch(results)
        
    else:
        frame = cv2.imread(filepath)
        if frame is not None:
            processed_frame, result = system.process_frame(frame)
            result['frame_idx'] = 1
            result['timestamp'] = 0
            
            ai_result = ai_agent.analyze_behavior(result)
            if ai_result:
                result['ai_risk'] = ai_result.get('risk_level', 0)
                ai_analysis = ai_result
            
            results.append(result)

    for r in results:
        record = DetectionRecord(
            event_type=r.get('event_type', '正常'),
            detected_class=r.get('detected_class', 'unknown'),
            confidence=r.get('confidence', 0),
            m1_triggered=r.get('M1', False),
            m2_triggered=r.get('M2', False),
            m3_triggered=r.get('M3', False),
            fall_detected=r.get('fall_detected', False),
            alert_triggered=r.get('alert', False),
            video_path=filepath,
            user_id=session.get('user_id')
        )
        db.session.add(record)
    
    # 更新分析记录
    analysis_record.processed_filename = os.path.basename(output_video_path) if output_video_path else None
    analysis_record.output_path = output_video_path
    analysis_record.status = 'completed'
    analysis_record.total_frames = len(results)
    analysis_record.detected_frames = sum(1 for r in results if r.get('status') != 'no_person')
    analysis_record.fall_detected = any(r.get('fall_detected') for r in results)
    analysis_record.alert_count = sum(1 for r in results if r.get('alert'))
    analysis_record.ai_analysis = json.dumps(ai_analysis)
    analysis_record.completed_at = datetime.utcnow()
    db.session.commit()

    # 返回文件名而不是完整路径
    output_video_filename = os.path.basename(output_video_path) if output_video_path else None
    
    return jsonify({
        "status": "ok", 
        "results": results,
        "ai_analysis": ai_analysis,
        "output_video": output_video_filename,
        "analysis_id": analysis_record.id,
        "summary": {
            "total_frames": len(results),
            "fall_frames": sum(1 for r in results if r.get('fall_detected')),
            "alert_frames": sum(1 for r in results if r.get('alert')),
            "avg_confidence": sum(r.get('confidence', 0) for r in results) / len(results) if results else 0
        }
    })


@app.route("/api/analysis/records", methods=["GET"])
def get_analysis_records():
    """获取分析记录列表"""
    user_id = session.get('user_id') or 1  # 默认用户ID为1
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    records = AnalysisRecord.query.filter_by(user_id=user_id)\
        .order_by(AnalysisRecord.created_at.desc())\
        .paginate(page=page, per_page=per_page)
    
    return jsonify({
        "records": [r.to_dict() for r in records.items],
        "total": records.total,
        "page": records.page,
        "per_page": records.per_page,
        "pages": records.pages
    })


@app.route("/api/analysis/record/<int:record_id>", methods=["GET"])
def get_analysis_record(record_id):
    """获取单个分析记录详情"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    
    record = AnalysisRecord.query.filter_by(id=record_id, user_id=user_id).first()
    if not record:
        return jsonify({"error": "Record not found"}), 404
    
    return jsonify(record.to_dict())


@app.route("/api/analysis/record/<int:record_id>", methods=["DELETE"])
def delete_analysis_record(record_id):
    """删除分析记录"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    
    record = AnalysisRecord.query.filter_by(id=record_id, user_id=user_id).first()
    if not record:
        return jsonify({"error": "Record not found"}), 404
    
    # 删除相关文件
    if record.output_path and os.path.exists(record.output_path):
        os.remove(record.output_path)
    if record.input_path and os.path.exists(record.input_path):
        os.remove(record.input_path)
    
    # 删除数据库记录
    db.session.delete(record)
    db.session.commit()
    
    return jsonify({"status": "ok", "message": "Record deleted"})


@app.route("/api/download/video/<filename>", methods=["GET"])
def download_output_video(filename):
    output_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'output')
    if not os.path.exists(output_dir):
        return jsonify({"error": "Output directory not found"}), 404
    
    # 处理中文文件名（已由URL编码）
    filepath = os.path.join(output_dir, filename)
    if not os.path.exists(filepath):
        return jsonify({"error": "File not found"}), 404
    
    # 使用send_file替代send_from_directory来支持中文文件名
    import mimetypes
    mime_type, _ = mimetypes.guess_type(filepath)
    mime_type = mime_type or 'video/mp4'
    
    # 获取文件大小
    file_size = os.path.getsize(filepath)
    
    # 处理Range请求（支持流媒体播放）
    range_header = request.headers.get('Range', None)
    if range_header:
        # 解析Range头
        range_match = re.match(r'bytes=(\d+)-(\d*)', range_header)
        if range_match:
            start = int(range_match.group(1))
            end = int(range_match.group(2)) if range_match.group(2) else file_size - 1
            length = end - start + 1
            
            # 读取文件的指定范围
            with open(filepath, 'rb') as f:
                f.seek(start)
                content = f.read(length)
            
            response = make_response(content)
            response.headers['Content-Type'] = mime_type
            response.headers['Content-Length'] = str(length)
            response.headers['Content-Range'] = f'bytes {start}-{end}/{file_size}'
            response.headers['Accept-Ranges'] = 'bytes'
            response.headers['Cache-Control'] = 'no-cache'
            response.headers['Access-Control-Expose-Headers'] = 'Content-Range,Content-Length'
            response.status_code = 206
            return response
    
    # 如果没有Range请求，返回完整文件
    response = make_response(send_file(
        filepath,
        mimetype=mime_type,
        as_attachment=False,
        download_name=filename
    ))
    response.headers['Accept-Ranges'] = 'bytes'
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['Access-Control-Expose-Headers'] = 'Content-Range,Content-Length'
    return response


@app.route("/api/detect", methods=["POST"])
def detect_fall():
    global system

    data = request.json
    image_data = data.get("image")

    if not image_data:
        return jsonify({"error": "No image data"}), 400

    try:
        if image_data.startswith('data:image/'):
            image_data = image_data.split(',')[1]
        
        frame_bytes = base64.b64decode(image_data)
        frame = cv2.imdecode(np.frombuffer(frame_bytes, np.uint8), cv2.IMREAD_COLOR)

        if frame is None:
            return jsonify({"error": "Cannot decode image"}), 400

        processed_frame, result = system.process_frame(frame)

        detected_class = result.get("detected_class", "unknown")
        confidence = result.get("confidence", 0)
        fall_detected = result.get("fall_detected", False)
        alert = result.get("alert", False)
        
        behavior_map = {
            "standing": "站立",
            "walking": "行走",
            "sitting": "坐下",
            "lying": "躺卧",
            "bending": "弯腰",
            "falling": "跌倒",
            "unknown": "未知",
            "未检测到人体": "未检测到人体"
        }
        
        label = behavior_map.get(detected_class, detected_class)
        
        if fall_detected or alert:
            label = "⚠️ 跌倒"

        return jsonify({
            "success": True,
            "label": label,
            "confidence": confidence,
            "fall_detected": fall_detected,
            "alert": alert,
            "behavior": detected_class,
            "behavior_cn": behavior_map.get(detected_class, detected_class),
            "M1": result.get("M1", False),
            "M2": result.get("M2", False),
            "M3": result.get("M3", False),
            "status": result.get("status", "detecting")
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/frame", methods=["POST"])
def process_frame():
    global system

    data = request.json
    frame_data = data.get("frame")
    camera_id = data.get("camera_id")

    if not frame_data:
        return jsonify({"error": "No frame data"}), 400

    try:
        frame_bytes = base64.b64decode(frame_data)
        frame = cv2.imdecode(np.frombuffer(frame_bytes, np.uint8), cv2.IMREAD_COLOR)

        if frame is None:
            return jsonify({"error": "Cannot decode image"}), 400

        processed_frame, result = system.process_frame(frame)

        ai_result = ai_agent.analyze_behavior(result)

        _, buffer = cv2.imencode(".jpg", processed_frame)
        processed_base64 = base64.b64encode(buffer).decode("utf-8")

        result["frame"] = processed_base64
        result["ai_analysis"] = ai_result

        if result.get("fall_detected") or result.get("alert"):
            record = DetectionRecord(
                event_type="跌倒告警" if result.get("alert") else "疑似跌倒",
                detected_class=result.get("detected_class", "unknown"),
                confidence=result.get("confidence", 0),
                m1_triggered=result.get("M1", False),
                m2_triggered=result.get("M2", False),
                m3_triggered=result.get("M3", False),
                fall_detected=result.get("fall_detected", False),
                alert_triggered=result.get("alert", False),
                camera_id=camera_id
            )
            db.session.add(record)
            db.session.commit()

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/history", methods=["GET"])
def get_history():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    event_type = request.args.get("event_type", "")
    camera_id = request.args.get("camera_id", type=int)
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")

    query = DetectionRecord.query

    if event_type:
        query = query.filter_by(event_type=event_type)
    if camera_id:
        query = query.filter_by(camera_id=camera_id)
    if start_date:
        query = query.filter(DetectionRecord.timestamp >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.filter(DetectionRecord.timestamp <= datetime.fromisoformat(end_date))

    query = query.order_by(DetectionRecord.timestamp.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "items": [r.to_dict() for r in pagination.items],
        "total": pagination.total,
        "page": page,
        "per_page": per_page,
        "pages": pagination.pages
    })


@app.route("/api/history/clear", methods=["POST"])
def clear_history():
    DetectionRecord.query.delete()
    db.session.commit()
    return jsonify({"status": "ok"})


@app.route("/api/statistics", methods=["GET"])
def get_statistics():
    total = DetectionRecord.query.count()
    alert_count = DetectionRecord.query.filter_by(event_type="跌倒告警").count()
    warning_count = DetectionRecord.query.filter_by(event_type="疑似跌倒").count()
    normal_count = DetectionRecord.query.filter_by(event_type="正常").count()

    today = datetime.utcnow().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_alerts = DetectionRecord.query.filter(
        DetectionRecord.timestamp >= today_start,
        DetectionRecord.event_type.in_(["跌倒告警", "疑似跌倒"])
    ).count()

    return jsonify({
        "total": total,
        "alert_count": alert_count,
        "warning_count": warning_count,
        "normal_count": normal_count,
        "today_alerts": today_alerts
    })


@app.route("/api/alerts", methods=["GET"])
def get_alerts():
    if 'user_id' not in session:
        return jsonify({"error": "请先登录"}), 401
    
    user_id = session['user_id']
    current_user = User.query.get(user_id)
    
    if current_user.role == 'admin':
        alerts = Alert.query.filter_by(acknowledged=False).order_by(Alert.sent_at.desc()).limit(50).all()
    else:
        alerts = Alert.query.filter_by(user_id=user_id).order_by(Alert.sent_at.desc()).limit(50).all()
    
    return jsonify({"alerts": [a.to_dict() for a in alerts]})


@app.route("/api/alerts/<int:id>/acknowledge", methods=["POST"])
def acknowledge_alert(id):
    alert = Alert.query.get_or_404(id)
    alert.acknowledged = True
    alert.acknowledged_by = session.get('user_id')
    alert.acknowledged_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"status": "ok"})


@app.route("/api/alerts/all", methods=["GET"])
def get_all_alerts():
    """管理员获取所有告警"""
    if 'user_id' not in session:
        return jsonify({"error": "请先登录"}), 401
    
    current_user = User.query.get(session['user_id'])
    if not current_user or current_user.role != 'admin':
        return jsonify({"error": "需要管理员权限"}), 403
    
    alerts = Alert.query.order_by(Alert.sent_at.desc()).all()
    return jsonify({"alerts": [a.to_dict() for a in alerts]})


@app.route("/api/auth/change-password", methods=["POST"])
def change_password():
    if 'user_id' not in session:
        return jsonify({"error": "请先登录"}), 401
    
    data = request.json
    old_password = data.get("old_password")
    new_password = data.get("new_password")
    
    if not old_password or not new_password:
        return jsonify({"error": "请提供旧密码和新密码"}), 400
    
    if len(new_password) < 6:
        return jsonify({"error": "密码长度至少为6位"}), 400
    
    user = User.query.get(session['user_id'])
    if user.password_hash != old_password:
        return jsonify({"error": "旧密码不正确"}), 401
    
    user.password_hash = new_password
    db.session.commit()
    return jsonify({"status": "ok"})


@app.route("/api/settings", methods=["GET"])
def get_settings():
    if 'user_id' not in session:
        return jsonify({"error": "请先登录"}), 401
    
    current_user = User.query.get(session['user_id'])
    if not current_user or current_user.role != 'admin':
        return jsonify({"error": "需要管理员权限"}), 403
    
    settings = {
        "security": {
            "min_password_length": 6,
            "session_timeout": 60,
            "allow_registration": True,
            "blocked_usernames": "admin, root, administrator"
        },
        "ai": {
            "ollama_model": "llama3",
            "ollama_endpoint": "http://localhost:11434",
            "max_response_length": 1000,
            "enable_ai_assistant": True
        },
        "video": {
            "max_file_size": 100,
            "analysis_fps": 10,
            "detection_threshold": 0.5,
            "output_quality": "medium"
        },
        "alert": {
            "enable_fall_alert": True,
            "silence_period": 5,
            "default_severity": "high"
        }
    }
    return jsonify(settings)


@app.route("/api/settings", methods=["PUT"])
def save_settings():
    if 'user_id' not in session:
        return jsonify({"error": "请先登录"}), 401
    
    current_user = User.query.get(session['user_id'])
    if not current_user or current_user.role != 'admin':
        return jsonify({"error": "需要管理员权限"}), 403
    
    data = request.json
    return jsonify({"status": "ok"})


@app.route("/api/statistics/daily", methods=["GET"])
def get_daily_statistics():
    if 'user_id' not in session:
        return jsonify({"error": "请先登录"}), 401
    
    current_user = User.query.get(session['user_id'])
    if not current_user or current_user.role != 'admin':
        return jsonify({"error": "需要管理员权限"}), 403
    
    days_range = request.args.get('range', '7d')
    days = 7
    if days_range == '30d':
        days = 30
    elif days_range == '90d':
        days = 90
    
    trend = []
    today = datetime.utcnow().date()
    for i in range(days):
        date = today - timedelta(days=i)
        count = AnalysisRecord.query.filter(
            db.func.date(AnalysisRecord.created_at) == date
        ).count()
        trend.append({
            "day": f"{date.month}/{date.day}",
            "date": date.isoformat(),
            "count": count
        })
    
    trend.reverse()
    return jsonify({"trend": trend})


@app.route("/api/statistics/top-users", methods=["GET"])
def get_top_users():
    if 'user_id' not in session:
        return jsonify({"error": "请先登录"}), 401
    
    current_user = User.query.get(session['user_id'])
    if not current_user or current_user.role != 'admin':
        return jsonify({"error": "需要管理员权限"}), 403
    
    users = User.query.all()
    user_stats = []
    for user in users:
        analysis_count = AnalysisRecord.query.filter_by(user_id=user.id).count()
        user_stats.append({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "analysis_count": analysis_count
        })
    
    user_stats.sort(key=lambda x: x['analysis_count'], reverse=True)
    return jsonify({"users": user_stats[:10]})


@app.route("/api/ai/analyze", methods=["POST"])
def ai_analyze():
    data = request.json
    result = ai_agent.analyze_behavior(data)
    return jsonify(result)


@app.route("/api/ai/report", methods=["GET"])
def ai_report():
    report = ai_agent.generate_report()
    return jsonify(report)


@app.route("/api/ai/chat", methods=["POST"])
def ai_chat():
    data = request.json
    message = data.get("message", "")
    user_id = session.get('user_id')
    response = ai_agent.chat(message, user_id)
    return jsonify({"response": response})


@app.route("/api/ai/ollama/status", methods=["GET"])
def ollama_status():
    """获取Ollama状态"""
    return jsonify({
        "available": ai_agent.ollama_available,
        "host": ai_agent.ollama_host,
        "model": ai_agent.ollama_model,
        "enabled": ai_agent.ollama_enabled
    })


@app.route("/api/ai/ollama/models", methods=["GET"])
def ollama_models():
    """获取Ollama可用模型列表"""
    models = ai_agent.get_ollama_models()
    return jsonify({"models": models})


@app.route("/api/ai/ollama/config", methods=["POST"])
def ollama_config():
    """配置Ollama"""
    data = request.json
    host = data.get("host")
    model = data.get("model")
    enabled = data.get("enabled", True)
    
    ai_agent.ollama_enabled = enabled
    success = False
    if host or model:
        success = ai_agent.set_ollama_config(host, model)
    
    return jsonify({
        "status": "ok",
        "available": ai_agent.ollama_available,
        "host": ai_agent.ollama_host,
        "model": ai_agent.ollama_model,
        "enabled": ai_agent.ollama_enabled
    })


@app.route("/api/config", methods=["POST"])
def save_config():
    data = request.json
    for key, value in data.items():
        cfg = SystemConfig.query.filter_by(key=key).first()
        if cfg:
            cfg.value = json.dumps(value)
        else:
            cfg = SystemConfig(key=key, value=json.dumps(value))
            db.session.add(cfg)
    db.session.commit()
    return jsonify({"status": "ok"})


@app.route("/api/config/get", methods=["GET"])
def get_config():
    configs = SystemConfig.query.all()
    return jsonify({c.key: json.loads(c.value) if c.value else None for c in configs})


@app.route("/api/status", methods=["GET"])
def status():
    return jsonify({
        "status": "running",
        "has_model": system.model is not None,
        "class_names": system.class_names,
        "active_cameras": len(camera_streams),
        "ai_risk_level": ai_agent.risk_score
    })


@app.route("/api/camera/start", methods=["POST"])
def start_camera():
    data = request.json
    camera_id = data.get("camera_id")
    camera_type = data.get("type", "local")

    if camera_type == "local":
        return jsonify({
            "status": "ok",
            "message": "Local camera ready. Use browser getUserMedia API.",
            "stream_url": "/api/camera/local/stream"
        })
    else:
        return jsonify({"status": "ok", "message": "Camera stream initialized"})


@app.route("/api/upload/batch", methods=["POST"])
def upload_batch():
    files = request.files.getlist('files')
    if not files:
        return jsonify({"error": "No files provided"}), 400

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    results = []
    for file in files:
        try:
            filename = f"{uuid.uuid4().hex}_{file.filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            file_type = 'video' if file.mimetype.startswith('video') else 'image'
            file_size = os.path.getsize(filepath)
            
            results.append({
                "filename": filename,
                "filepath": filepath,
                "file_type": file_type,
                "file_size": file_size,
                "status": "uploaded"
            })
        except Exception as e:
            results.append({
                "filename": file.filename,
                "error": str(e),
                "status": "failed"
            })

    return jsonify({
        "status": "ok",
        "results": results,
        "total": len(files),
        "success": sum(1 for r in results if r["status"] == "uploaded"),
        "failed": sum(1 for r in results if r["status"] == "failed")
    })


@app.route("/api/report/generate", methods=["POST"])
def generate_report():
    data = request.json
    report_type = data.get("type", "daily")
    start_date = data.get("start_date")
    end_date = data.get("end_date")
    
    query = DetectionRecord.query
    
    if start_date:
        start = datetime.fromisoformat(start_date)
        query = query.filter(DetectionRecord.timestamp >= start)
    
    if end_date:
        end = datetime.fromisoformat(end_date)
        query = query.filter(DetectionRecord.timestamp <= end)
    
    records = query.all()
    
    total = len(records)
    fall_count = sum(1 for r in records if r.fall_detected)
    alert_count = sum(1 for r in records if r.alert_triggered)
    
    behavior_stats = {}
    for r in records:
        behavior = r.detected_class or 'unknown'
        behavior_stats[behavior] = behavior_stats.get(behavior, 0) + 1
    
    daily_stats = {}
    for r in records:
        date_key = r.timestamp.date().isoformat()
        if date_key not in daily_stats:
            daily_stats[date_key] = {"total": 0, "falls": 0, "alerts": 0}
        daily_stats[date_key]["total"] += 1
        if r.fall_detected:
            daily_stats[date_key]["falls"] += 1
        if r.alert_triggered:
            daily_stats[date_key]["alerts"] += 1
    
    ai_report = ai_agent.generate_report()
    
    report = {
        "report_type": report_type,
        "period": {
            "start": start_date,
            "end": end_date
        },
        "summary": {
            "total_records": total,
            "fall_events": fall_count,
            "alert_events": alert_count,
            "fall_rate": fall_count / total if total > 0 else 0,
            "alert_rate": alert_count / total if total > 0 else 0
        },
        "behavior_distribution": behavior_stats,
        "daily_statistics": daily_stats,
        "ai_analysis": ai_report,
        "generated_at": datetime.utcnow().isoformat()
    }
    
    return jsonify(report)


@app.route("/api/report/export", methods=["POST"])
def export_report():
    data = request.json
    format_type = data.get("format", "json")
    start_date = data.get("start_date")
    end_date = data.get("end_date")
    
    query = DetectionRecord.query
    
    if start_date:
        start = datetime.fromisoformat(start_date)
        query = query.filter(DetectionRecord.timestamp >= start)
    
    if end_date:
        end = datetime.fromisoformat(end_date)
        query = query.filter(DetectionRecord.timestamp <= end)
    
    records = query.all()
    
    if format_type == "csv":
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', 'Timestamp', 'Event Type', 'Detected Class', 'Confidence', 
                      'M1 Triggered', 'M2 Triggered', 'M3 Triggered', 
                      'Fall Detected', 'Alert Triggered', 'Video Path'])
        
        for r in records:
            writer.writerow([
                r.id, r.timestamp.isoformat() if r.timestamp else '',
                r.event_type, r.detected_class, r.confidence,
                r.m1_triggered, r.m2_triggered, r.m3_triggered,
                r.fall_detected, r.alert_triggered, r.video_path
            ])
        
        output.seek(0)
        return output.getvalue(), 200, {
            'Content-Type': 'text/csv',
            'Content-Disposition': 'attachment; filename=detection_report.csv'
        }
    
    else:
        return jsonify({
            "records": [r.to_dict() for r in records],
            "total": len(records)
        })


@app.route("/api/statistics/advanced", methods=["GET"])
def advanced_statistics():
    records = DetectionRecord.query.all()
    
    if not records:
        return jsonify({"error": "No data available"}), 404
    
    behavior_stats = {}
    for r in records:
        behavior = r.detected_class or 'unknown'
        if behavior not in behavior_stats:
            behavior_stats[behavior] = {
                "count": 0,
                "avg_confidence": 0,
                "fall_count": 0,
                "alert_count": 0
            }
        behavior_stats[behavior]["count"] += 1
        behavior_stats[behavior]["avg_confidence"] += r.confidence or 0
        if r.fall_detected:
            behavior_stats[behavior]["fall_count"] += 1
        if r.alert_triggered:
            behavior_stats[behavior]["alert_count"] += 1
    
    for behavior in behavior_stats:
        count = behavior_stats[behavior]["count"]
        behavior_stats[behavior]["avg_confidence"] /= count if count > 0 else 1
    
    hourly_stats = {}
    for r in records:
        if r.timestamp:
            hour = r.timestamp.hour
            if hour not in hourly_stats:
                hourly_stats[hour] = {"total": 0, "falls": 0, "alerts": 0}
            hourly_stats[hour]["total"] += 1
            if r.fall_detected:
                hourly_stats[hour]["falls"] += 1
            if r.alert_triggered:
                hourly_stats[hour]["alerts"] += 1
    
    trend_data = []
    sorted_dates = sorted(set(r.timestamp.date() for r in records if r.timestamp))
    for date in sorted_dates[-30:]:
        day_records = [r for r in records if r.timestamp and r.timestamp.date() == date]
        trend_data.append({
            "date": date.isoformat(),
            "total": len(day_records),
            "falls": sum(1 for r in day_records if r.fall_detected),
            "alerts": sum(1 for r in day_records if r.alert_triggered)
        })
    
    return jsonify({
        "behavior_statistics": behavior_stats,
        "hourly_distribution": hourly_stats,
        "trend_analysis": trend_data,
        "summary": {
            "total_records": len(records),
            "unique_behaviors": len(behavior_stats),
            "most_common_behavior": max(behavior_stats.items(), key=lambda x: x[1]["count"])[0] if behavior_stats else None,
            "peak_hour": max(hourly_stats.items(), key=lambda x: x[1]["total"])[0] if hourly_stats else None
        }
    })


@app.route("/api/ai/predict", methods=["POST"])
def ai_predict():
    data = request.json
    historical_data = data.get("data", [])
    
    if not historical_data:
        return jsonify({"error": "No data provided"}), 400
    
    predictions = []
    for item in historical_data:
        result = ai_agent.analyze_behavior(item)
        predictions.append({
            "input": item,
            "prediction": result
        })
    
    return jsonify({
        "predictions": predictions,
        "summary": {
            "total": len(predictions),
            "high_risk": sum(1 for p in predictions if p["prediction"].get("risk_level", 0) > 0.7),
            "medium_risk": sum(1 for p in predictions if 0.4 < p["prediction"].get("risk_level", 0) <= 0.7),
            "low_risk": sum(1 for p in predictions if p["prediction"].get("risk_level", 0) <= 0.4)
        }
    })


@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "database": "connected",
            "model": "loaded" if system.model else "not_loaded",
            "ai_agent": "active"
        }
    })


def init_db():
    with app.app_context():
        db.create_all()

        admin = User.query.filter_by(username="admin").first()
        if not admin:
            admin = User(username="admin", password_hash="admin123", role="admin", email="admin@example.com")
            db.session.add(admin)
            db.session.commit()
            print("Default admin user created: admin / admin123")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=5000)
    args = parser.parse_args()

    init_db()
    app.run(host=args.host, port=args.port, debug=False, threaded=True)
