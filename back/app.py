#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
跌倒检测系统后端服务
基于论文《基于深度学习的人体姿势跌倒检测算法》
"""

import os
import sys
import json
import uuid
import datetime
import time
import re
import subprocess
from flask import Flask, request, jsonify, send_from_directory, make_response, send_file, Response
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv

# 加载配置
from config import app_config, database_config, ollama_config, load_config_from_env

# 加载环境变量
load_dotenv()
load_config_from_env()

# 添加模型路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'finallmodel', 'model'))

from fall_detector import FallDetector
from ai_agent import AIAgent

app = Flask(__name__)

# 配置
app.config['SECRET_KEY'] = app_config.secret_key
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{database_config.user}:{database_config.password}@{database_config.host}:{database_config.port}/{database_config.database}?charset=utf8mb4&connect_timeout=10&read_timeout=30&write_timeout=30"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), app_config.upload_folder)
app.config['OUTPUT_FOLDER'] = os.path.join(os.path.dirname(__file__), app_config.output_folder)
app.config['MAX_CONTENT_LENGTH'] = app_config.max_content_length
app.config['JSON_AS_ASCII'] = False  # 确保JSON响应支持中文
app.config['JSONIFY_MIMETYPE'] = 'application/json; charset=utf-8'

# 初始化数据库
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# 初始化检测器（线程安全）
_detector_instance = None

def get_detector():
    """获取检测器实例（线程安全）"""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = FallDetector()
    return _detector_instance

# 延迟初始化AI智能体，避免Flask启动时检测失败
ai_agent = None

def get_ai_agent():
    """延迟获取AI智能体实例"""
    global ai_agent
    if ai_agent is None:
        ai_agent = AIAgent()
    return ai_agent

# 启用CORS
CORS(app, supports_credentials=True)

# 创建必要目录
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)


def fix_mp4_for_streaming(input_path):
    """修复MP4文件使其支持流式播放（重新编码为H.264并移动moov atom到文件开头）"""
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


# 数据库模型
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
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'phone': self.phone,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'is_active': self.is_active
        }


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
    
    user = db.relationship('User', backref=db.backref('cameras', lazy=True))
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'location': self.location,
            'camera_type': self.camera_type,
            'url': self.url,
            'is_active': self.is_active,
            'user_id': self.user_id,
            'status': self.status,
            'resolution': self.resolution,
            'fps': self.fps,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class DetectionRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    camera_id = db.Column(db.Integer, db.ForeignKey('camera.id'))
    filename = db.Column(db.String(255))
    file_path = db.Column(db.String(500))
    output_path = db.Column(db.String(500))
    total_frames = db.Column(db.Integer)
    detected_frames = db.Column(db.Integer)
    fall_detected = db.Column(db.Boolean)
    alert_count = db.Column(db.Integer)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)
    completed_at = db.Column(db.DateTime)
    
    user = db.relationship('User', backref=db.backref('detections', lazy=True))
    camera = db.relationship('Camera', backref=db.backref('detections', lazy=True))
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'camera_id': self.camera_id,
            'filename': self.filename,
            'file_path': self.file_path,
            'output_path': self.output_path,
            'total_frames': self.total_frames,
            'detected_frames': self.detected_frames,
            'fall_detected': self.fall_detected,
            'alert_count': self.alert_count,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }


class AlertRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    detection_id = db.Column(db.Integer, db.ForeignKey('detection_record.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    frame_number = db.Column(db.Integer)
    timestamp = db.Column(db.Float)
    behavior = db.Column(db.String(50))
    confidence = db.Column(db.Float)
    M1 = db.Column(db.Boolean)
    M2 = db.Column(db.Boolean)
    M3 = db.Column(db.Boolean)
    center_gravity_speed = db.Column(db.Float)
    body_tilt_angle = db.Column(db.Float)
    contour_ratio = db.Column(db.Float)
    acknowledged = db.Column(db.Boolean, default=False)
    acknowledged_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)
    
    detection = db.relationship('DetectionRecord', backref=db.backref('alerts', lazy=True))
    user = db.relationship('User', backref=db.backref('alert_records', lazy=True))
    
    def to_dict(self):
        return {
            'id': self.id,
            'detection_id': self.detection_id,
            'user_id': self.user_id,
            'frame_number': self.frame_number,
            'timestamp': self.timestamp,
            'behavior': self.behavior,
            'confidence': self.confidence,
            'M1': self.M1,
            'M2': self.M2,
            'M3': self.M3,
            'center_gravity_speed': self.center_gravity_speed,
            'body_tilt_angle': self.body_tilt_angle,
            'contour_ratio': self.contour_ratio,
            'acknowledged': self.acknowledged,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'created_at': self.created_at.isoformat()
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
    sent_at = db.Column(db.DateTime, default=datetime.datetime.now)
    acknowledged = db.Column(db.Boolean, default=False)
    acknowledged_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    acknowledged_at = db.Column(db.DateTime)
    response_action = db.Column(db.Text)
    
    record = db.relationship('DetectionRecord', backref=db.backref('alert_notifications', lazy=True))
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('alerts', lazy=True))
    ack_user = db.relationship('User', foreign_keys=[acknowledged_by])
    
    def to_dict(self):
        user = User.query.get(self.user_id) if self.user_id else None
        return {
            'id': self.id,
            'record_id': self.record_id,
            'user_id': self.user_id,
            'username': user.username if user else None,
            'alert_type': self.alert_type,
            'severity': self.severity,
            'message': self.message,
            'title': self.title or '跌倒检测告警',
            'detection_type': self.detection_type or 'fall',
            'confidence': self.confidence or 0.0,
            'sent_to': self.sent_to,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'acknowledged': self.acknowledged,
            'acknowledged_by': self.acknowledged_by,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'timestamp': self.sent_at.isoformat() if self.sent_at else None
        }


class SystemConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True)
    value = db.Column(db.Text)
    
    def to_dict(self):
        return {'key': self.key, 'value': self.value}


class ConversationSession(db.Model):
    """对话会话模型"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), nullable=False)  # 用户ID或'admin'
    title = db.Column(db.String(200), nullable=False, default='新对话')
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class ConversationHistory(db.Model):
    """对话历史记录模型"""
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('conversation_session.id'), nullable=False)
    user_id = db.Column(db.String(100), nullable=False)  # 用户ID或'admin'
    role = db.Column(db.String(20), nullable=False)  # 'user' or 'assistant'
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.now)
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'user_id': self.user_id,
            'role': self.role,
            'content': self.content,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }


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
    
    user = db.relationship('User', backref=db.backref('analysis_records', lazy=True))
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'original_filename': self.original_filename,
            'processed_filename': self.processed_filename,
            'input_path': self.input_path,
            'output_path': self.output_path,
            'file_type': self.file_type,
            'status': self.status,
            'total_frames': self.total_frames,
            'detected_frames': self.detected_frames,
            'fall_detected': self.fall_detected,
            'alert_count': self.alert_count,
            'ai_analysis': self.ai_analysis,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }


# API路由
@app.route('/api/upload', methods=['POST'])
def upload_file():
    """上传视频文件（支持中文文件名）"""
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'error': '未找到文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'error', 'error': '文件名不能为空'}), 400
    
    # 使用原始文件名保存
    original_filename = file.filename
    
    # 处理中文文件名：使用UUID重命名，保留原文件名记录
    name, ext = os.path.splitext(original_filename)
    # 生成唯一文件名（使用UUID避免冲突）
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    
    # 如果文件已存在，添加时间戳
    if os.path.exists(filepath):
        timestamp = int(time.time())
        unique_filename = f"{uuid.uuid4().hex}_{timestamp}{ext}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    
    file.save(filepath)
    
    # 获取文件信息
    file_size = os.path.getsize(filepath)
    
    return jsonify({
        'status': 'ok',
        'filename': unique_filename,
        'original_name': original_filename,
        'filepath': filepath,
        'file_size': file_size
    }), 200


@app.route('/api/detect/file', methods=['POST'])
def detect_video():
    """检测视频文件 - 优化版本（支持中文文件名）"""
    data = request.get_json()
    filepath = data.get('filepath')
    mode = data.get('mode', 'fast')
    show_labels = data.get('show_labels', True)
    show_bboxes = data.get('show_bboxes', True)
    
    if not filepath:
        return jsonify({'status': 'error', 'error': '文件路径为空'}), 400
    
    # 检查文件是否存在
    if not os.path.exists(filepath):
        # 尝试不同编码
        try:
            filepath_gbk = filepath.encode('utf-8').decode('gbk')
            if os.path.exists(filepath_gbk):
                filepath = filepath_gbk
            else:
                return jsonify({'status': 'error', 'error': f'文件路径无效: {filepath}'}), 400
        except:
            return jsonify({'status': 'error', 'error': f'文件路径无效: {filepath}'}), 400
    
    # 获取原始文件名（用于输出命名）
    original_filename = os.path.basename(filepath)
    name, ext = os.path.splitext(original_filename)
    
    # 使用UUID生成输出文件名，避免中文问题
    output_name = f"{uuid.uuid4().hex}_detected{ext}"
    output_video = os.path.join(app.config['OUTPUT_FOLDER'], output_name)
    
    try:
        # 获取检测器实例
        detector = get_detector()
        detector.reset()  # 重置检测器状态
        
        # 执行检测 - 将输出路径传递给检测器
        result = detector.detect_video(
            filepath,
            mode=mode,
            show_labels=show_labels,
            show_bboxes=show_bboxes,
            output_path=output_video
        )
        
        # 修复输出视频以支持流式播放
        if result.get('success', False) and os.path.exists(output_video):
            fix_mp4_for_streaming(output_video)
        
        # 保存到数据库
        record = DetectionRecord(
            filename=original_filename,
            file_path=filepath,
            output_path=output_video,
            total_frames=result['summary']['total_frames'],
            detected_frames=result['summary']['detected_frames'],
            fall_detected=result['summary']['fall_detected'],
            alert_count=result['summary']['alert_count'],
            status='completed',
            completed_at=datetime.datetime.now()
        )
        db.session.add(record)
        db.session.commit()
        
        # 保存告警记录
        for alert in result.get('alerts', []):
            alert_record = AlertRecord(
                detection_id=record.id,
                user_id=1,  # 默认用户
                frame_number=alert['frame_number'],
                timestamp=alert['timestamp'],
                behavior=alert['behavior'],
                confidence=alert['confidence'],
                M1=alert['M1'],
                M2=alert['M2'],
                M3=alert['M3'],
                center_gravity_speed=alert.get('center_gravity_speed'),
                body_tilt_angle=alert.get('body_tilt_angle'),
                contour_ratio=alert.get('contour_ratio')
            )
            db.session.add(alert_record)
        db.session.commit()
        
        # 使用AI智能体分析结果
        ai_analysis = get_ai_agent().analyze_batch(result.get('alerts', []))
        
        # 转换numpy类型为Python原生类型
        def convert_numpy_types(obj):
            import numpy as np
            if isinstance(obj, np.generic):
                return obj.item()
            elif isinstance(obj, dict):
                return {key: convert_numpy_types(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy_types(item) for item in obj]
            else:
                return obj
        
        result = convert_numpy_types(result)
        ai_analysis = convert_numpy_types(ai_analysis)
        
        # 返回结果（包含输出视频的文件名，用于前端播放）
        return jsonify({
            'status': 'ok',
            'summary': result['summary'],
            'output_video': output_name,  # 返回UUID生成的文件名
            'output_path': output_video,
            'results': result.get('frames', []),
            'alerts': result.get('alerts', []),
            'record_id': record.id,
            'ai_analysis': ai_analysis
        }), 200
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        app.logger.error(f"Video detection error: {error_trace}")
        print(f"Video detection error: {error_trace}")
        return jsonify({'status': 'error', 'error': str(e), 'trace': error_trace}), 500


@app.route('/api/detect', methods=['POST'])
def detect_image():
    """实时图像检测 - 优化版本"""
    data = request.get_json()
    image_data = data.get('image')
    
    if not image_data:
        return jsonify({'success': False, 'error': '未提供图像数据'}), 400
    
    try:
        # 获取检测器实例
        detector = get_detector()
        
        # 执行检测
        result = detector.detect_image(image_data)
        
        # 构建响应（确保返回格式与fallmodel一致）
        response = {
            'success': True,
            'label': result['label'],
            'confidence': result['confidence'],
            'behavior': result['behavior'],
            'behavior_cn': result['behavior_cn'],
            'behavior_confidence': result.get('behavior_confidence', 0.0),
            'is_fall': result.get('is_fall', False),
            'M1': result.get('M1', False),
            'M2': result.get('M2', False),
            'M3': result.get('M3', False),
            'center_gravity_speed': result.get('center_gravity_speed', 0.0),
            'body_tilt_angle': result.get('body_tilt_angle', 0.0),
            'contour_ratio': result.get('contour_ratio', 0.0),
            'alert': result.get('alert', False),
            'frame_number': result.get('frame_number', 0),
            'timestamp': result.get('timestamp', 0.0),
            'joints': result.get('joints', {}),
            'status': result.get('status', 'detecting')
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        import traceback
        print(f"图像检测失败: {e}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e),
            'label': '检测失败',
            'is_fall': False,
            'behavior': 'empty',
            'behavior_cn': '空帧'
        }), 500


@app.route('/api/download/video/<filename>', methods=['GET'])
def download_video(filename):
    """下载检测结果视频"""
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename, as_attachment=True)


@app.route('/api/video/stream/<path:filename>', methods=['GET'])
def stream_video(filename):
    """流式播放检测结果视频（支持HTTP范围请求和中文文件名）"""
    import urllib.parse
    import glob
    
    # 解码文件名（处理URL编码）
    decoded_filename = filename
    try:
        decoded_filename = urllib.parse.unquote(filename, encoding='utf-8')
    except:
        pass
    
    # 直接使用请求的文件名（前端已经处理好了命名）
    video_path = os.path.join(app.config['OUTPUT_FOLDER'], decoded_filename)
    
    # 检查文件是否存在
    if os.path.exists(video_path):
        pass  # 文件找到
    else:
        # 尝试匹配包含关键词的文件
        name_without_ext = os.path.splitext(decoded_filename)[0]
        pattern = os.path.join(app.config['OUTPUT_FOLDER'], f"*{name_without_ext}*")
        matches = glob.glob(pattern)
        
        if matches:
            video_path = matches[0]
        else:
            # 尝试反向匹配：列出所有detected文件
            detected_pattern = os.path.join(app.config['OUTPUT_FOLDER'], "*_detected.mp4")
            detected_files = glob.glob(detected_pattern)
            
            if detected_files:
                # 返回第一个检测到的文件（作为备选）
                video_path = detected_files[0]
            else:
                return jsonify({'status': 'error', 'error': '视频文件不存在'}), 404
    
    # 获取文件大小
    file_size = os.path.getsize(video_path)
    
    # 设置视频MIME类型
    ext = os.path.splitext(filename)[1].lower()
    mime_type = {
        '.mp4': 'video/mp4',
        '.webm': 'video/webm',
        '.ogg': 'video/ogg',
        '.avi': 'video/x-msvideo'
    }.get(ext, 'video/mp4')
    
    # 处理范围请求
    range_header = request.headers.get('Range', None)
    
    if range_header:
        # 解析范围请求
        range_match = re.search(r'bytes=(\d+)-(\d*)', range_header)
        if range_match:
            start = int(range_match.group(1))
            end_str = range_match.group(2)
            if end_str:
                end = int(end_str)
            else:
                end = file_size - 1
        else:
            start = 0
            end = file_size - 1
        
        # 限制结束位置不超过文件大小
        end = min(end, file_size - 1)
        
        # 计算读取的字节数
        chunk_size = end - start + 1
        
        # 读取文件片段
        with open(video_path, 'rb') as f:
            f.seek(start)
            content = f.read(chunk_size)
        
        # 构建响应
        response = make_response(content)
        response.headers['Content-Type'] = mime_type
        response.headers['Content-Range'] = f'bytes {start}-{end}/{file_size}'
        response.headers['Content-Length'] = chunk_size
        response.headers['Accept-Ranges'] = 'bytes'
        response.headers['Access-Control-Expose-Headers'] = 'Content-Range, Content-Length'
        response.status_code = 206  # Partial Content
        
        return response
    else:
        # 返回完整文件（使用流式响应）
        def generate():
            with open(video_path, 'rb') as f:
                while chunk := f.read(1024 * 1024):  # 1MB chunks
                    yield chunk
        
        response = Response(generate(), mimetype=mime_type)
        response.headers['Content-Length'] = file_size
        response.headers['Accept-Ranges'] = 'bytes'
        return response


@app.route('/api/history', methods=['GET'])
def get_history():
    """获取检测历史"""
    records = DetectionRecord.query.order_by(DetectionRecord.created_at.desc()).limit(20).all()
    return jsonify([record.to_dict() for record in records]), 200


@app.route('/api/history/<int:record_id>', methods=['GET'])
def get_history_detail(record_id):
    """获取检测记录详情"""
    record = DetectionRecord.query.get(record_id)
    if not record:
        return jsonify({'success': False, 'error': '记录不存在'}), 404
    
    alerts = AlertRecord.query.filter_by(detection_id=record_id).all()
    
    return jsonify({
        'success': True,
        'record': record.to_dict(),
        'alerts': [alert.to_dict() for alert in alerts]
    }), 200


@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """获取统计数据"""
    total_records = DetectionRecord.query.count()
    fall_records = DetectionRecord.query.filter_by(fall_detected=True).count()
    normal_records = DetectionRecord.query.filter_by(fall_detected=False).count()
    total_alerts = AlertRecord.query.count()
    
    return jsonify({
        'success': True,
        'total_analyses': total_records,
        'alert_count': total_alerts,
        'fall_count': fall_records,
        'normal_count': normal_records,
        'fall_rate': fall_records / max(total_records, 1) * 100
    }), 200


@app.route('/api/analysis/records', methods=['GET'])
def get_analysis_records():
    """获取分析记录（分页）"""
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    
    query = DetectionRecord.query.order_by(DetectionRecord.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    records = []
    for record in pagination.items:
        records.append({
            'id': record.id,
            'original_filename': record.filename,
            'processed_filename': os.path.basename(record.output_path) if record.output_path else None,
            'status': record.status,
            'fall_detected': record.fall_detected,
            'alert_count': record.alert_count,
            'total_frames': record.total_frames,
            'detected_frames': record.detected_frames,
            'created_at': record.created_at.strftime('%Y-%m-%d %H:%M:%S') if record.created_at else None
        })
    
    return jsonify({
        'success': True,
        'records': records,
        'total': pagination.total,
        'page': page,
        'per_page': per_page
    }), 200


@app.route('/api/analysis/record/<int:record_id>', methods=['DELETE'])
def delete_analysis_record(record_id):
    """删除分析记录"""
    record = DetectionRecord.query.get(record_id)
    if not record:
        return jsonify({'success': False, 'error': '记录不存在'}), 404
    
    # 删除相关文件
    if record.file_path and os.path.exists(record.file_path):
        os.remove(record.file_path)
    if record.output_path and os.path.exists(record.output_path):
        os.remove(record.output_path)
    
    # 删除告警记录
    AlertRecord.query.filter_by(detection_id=record_id).delete()
    
    # 删除记录
    db.session.delete(record)
    db.session.commit()
    
    return jsonify({'success': True, 'message': '删除成功'}), 200


@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.datetime.now().isoformat()}), 200


# AI智能体相关API
@app.route('/api/ai/chat', methods=['POST'])
def ai_chat():
    """与AI智能体对话（带数据库持久化和会话管理）"""
    data = request.get_json()
    message = data.get('message')
    user_id = data.get('user_id', 'default')
    session_id = data.get('session_id')

    if not message:
        return jsonify({'success': False, 'error': '消息不能为空'}), 400

    response = get_ai_agent().chat(message, user_id)

    try:
        if session_id is None:
            # 如果没有session_id，创建新会话
            title = message[:20] + '...' if len(message) > 20 else message
            session = ConversationSession(user_id=user_id, title=title)
            db.session.add(session)
            db.session.flush()
            session_id = session.id
        else:
            # 更新现有会话的时间
            session = ConversationSession.query.get(session_id)
            if session:
                session.updated_at = datetime.datetime.now()

        # 保存对话到数据库
        user_msg = ConversationHistory(session_id=session_id, user_id=user_id, role='user', content=message)
        assistant_msg = ConversationHistory(session_id=session_id, user_id=user_id, role='assistant', content=response)
        db.session.add(user_msg)
        db.session.add(assistant_msg)
        db.session.commit()

        return jsonify({
            'success': True,
            'response': response,
            'session_id': session_id
        }), 200
    except Exception as e:
        print(f"Failed to save chat to DB: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/ai/history', methods=['GET'])
def ai_history():
    """获取用户AI对话历史（从数据库）"""
    user_id = request.args.get('user_id', 'default')

    try:
        # 直接从数据库查询，确保刷新后也能获取历史
        records = ConversationHistory.query.filter_by(user_id=user_id).order_by(ConversationHistory.timestamp).all()
        history = [record.to_dict() for record in records]

        return jsonify({
            'success': True,
            'data': history
        }), 200
    except Exception as e:
        print(f"AI history error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/ai/clear', methods=['POST'])
def ai_clear():
    """清除用户AI对话历史（从数据库）"""
    data = request.get_json()
    user_id = data.get('user_id', 'default')

    try:
        # 从数据库删除
        ConversationHistory.query.filter_by(user_id=user_id).delete()
        ConversationSession.query.filter_by(user_id=user_id).delete()
        db.session.commit()
        
        # 同时清除内存中的缓存
        agent = get_ai_agent()
        if user_id in agent.conversation_context:
            agent.conversation_context[user_id] = []

        return jsonify({
            'success': True,
            'message': '对话历史已清除'
        }), 200
    except Exception as e:
        print(f"AI clear error: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# 会话管理API
@app.route('/api/ai/sessions', methods=['GET'])
def get_ai_sessions():
    """获取用户的对话会话列表"""
    user_id = request.args.get('user_id', 'default')
    
    try:
        sessions = ConversationSession.query.filter_by(user_id=user_id).order_by(ConversationSession.updated_at.desc()).all()
        return jsonify({
            'success': True,
            'data': [session.to_dict() for session in sessions]
        }), 200
    except Exception as e:
        print(f"Get sessions error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/ai/sessions', methods=['POST'])
def create_ai_session():
    """创建新的对话会话"""
    data = request.get_json()
    user_id = data.get('user_id', 'default')
    title = data.get('title', '新对话')
    
    try:
        session = ConversationSession(user_id=user_id, title=title)
        db.session.add(session)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': session.to_dict()
        }), 201
    except Exception as e:
        print(f"Create session error: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/ai/sessions/<int:session_id>', methods=['DELETE'])
def delete_ai_session(session_id):
    """删除指定对话会话"""
    user_id = request.args.get('user_id', 'default')
    
    try:
        # 删除会话及其历史记录
        ConversationHistory.query.filter_by(session_id=session_id).delete()
        ConversationSession.query.filter_by(id=session_id, user_id=user_id).delete()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '会话已删除'
        }), 200
    except Exception as e:
        print(f"Delete session error: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/ai/sessions/<int:session_id>/history', methods=['GET'])
def get_session_history(session_id):
    """获取指定会话的对话历史"""
    try:
        history = ConversationHistory.query.filter_by(session_id=session_id).order_by(ConversationHistory.timestamp).all()
        return jsonify({
            'success': True,
            'data': [msg.to_dict() for msg in history]
        }), 200
    except Exception as e:
        print(f"Get session history error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/ai/report', methods=['GET'])
def ai_report():
    """获取AI分析报告"""
    report = get_ai_agent().generate_report()
    
    return jsonify({
        'success': True,
        'report': report
    }), 200


def _get_ollama_host():
    """获取正确的Ollama连接地址（内部辅助函数）"""
    host = ollama_config.host
    if not host.startswith('http://') and not host.startswith('https://'):
        host = 'http://' + host
    # 如果绑定地址是0.0.0.0，替换为localhost用于客户端连接
    host = host.replace('0.0.0.0', 'localhost')
    return host

@app.route('/api/ai/status', methods=['GET'])
def ai_status():
    """获取AI智能体状态"""
    agent = get_ai_agent()
    # 使用直接检查来确保正确检测Ollama状态
    import requests
    ollama_available = False
    try:
        host = _get_ollama_host()
        resp = requests.get(f"{host}/api/tags", timeout=5)
        ollama_available = resp.status_code == 200
    except Exception as e:
        print(f"Ollama check failed in ai_status: {e}")
    
    return jsonify({
        'success': True,
        'ollama_available': ollama_available,
        'risk_score': agent.risk_score,
        'behavior_history_count': len(agent.behavior_history),
        'debug': {
            'host': ollama_config.host,
            'agent_instance_id': id(agent)
        }
    }), 200


# 用户相关API
@app.route('/api/user/register', methods=['POST'])
def register_user():
    """注册用户"""
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    if not username or not email or not password:
        return jsonify({'status': 'error', 'error': '缺少必要参数'}), 400
    
    if User.query.filter_by(username=username).first():
        return jsonify({'status': 'error', 'error': '用户名已存在'}), 400
    
    if User.query.filter_by(email=email).first():
        return jsonify({'status': 'error', 'error': '邮箱已注册'}), 400
    
    from werkzeug.security import generate_password_hash
    new_user = User(
        username=username,
        email=email,
        password_hash=generate_password_hash(password)
    )
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'status': 'ok', 'user': new_user.to_dict()}), 201


@app.route('/api/auth/register', methods=['POST'])
def auth_register():
    """注册用户（兼容/auth路径）"""
    return register_user()


@app.route('/api/user/login', methods=['POST'])
def login_user():
    """用户登录"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    user = User.query.filter_by(username=username).first()
    
    if not user:
        return jsonify({'status': 'error', 'error': '用户不存在'}), 401
    
    from werkzeug.security import check_password_hash
    if not check_password_hash(user.password_hash, password):
        return jsonify({'status': 'error', 'error': '密码错误'}), 401
    
    return jsonify({'status': 'ok', 'user': user.to_dict()}), 200


@app.route('/api/auth/login', methods=['POST'])
def auth_login():
    """用户登录（兼容/auth路径）"""
    return login_user()


# 告警相关API
@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """获取告警列表"""
    alerts = AlertRecord.query.order_by(AlertRecord.created_at.desc()).all()
    return jsonify({
        'success': True,
        'data': [alert.to_dict() for alert in alerts]
    }), 200


@app.route('/api/alerts/<int:alert_id>/acknowledge', methods=['POST'])
def acknowledge_alert(alert_id):
    """确认告警"""
    alert = AlertRecord.query.get(alert_id)
    if not alert:
        return jsonify({'success': False, 'error': '告警不存在'}), 404
    
    alert.acknowledged = True
    alert.acknowledged_at = datetime.datetime.now()
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': '告警已确认'
    }), 200


@app.route('/api/alerts/clear', methods=['POST'])
def clear_alerts():
    """清空所有告警"""
    try:
        AlertRecord.query.delete()
        db.session.commit()
        return jsonify({
            'success': True,
            'message': '所有告警已清空'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# 用户认证API
@app.route('/api/auth/current', methods=['GET'])
def get_current_user():
    """获取当前用户信息（模拟登录状态）"""
    # 这里应该从session或token获取用户信息
    # 目前返回模拟数据
    return jsonify({
        'success': True,
        'user': {
            'id': 1,
            'username': 'admin',
            'email': 'admin@example.com'
        }
    }), 200


# 摄像头管理API
@app.route('/api/cameras', methods=['GET'])
def get_cameras():
    """获取摄像头列表"""
    # 从数据库读取摄像头列表
    cameras = Camera.query.all()
    return jsonify({
        'success': True,
        'cameras': [camera.to_dict() for camera in cameras]
    }), 200


@app.route('/api/cameras', methods=['POST'])
def add_camera():
    """添加摄像头"""
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({'success': False, 'error': '摄像头名称不能为空'}), 400
    
    # 创建摄像头记录并保存到数据库
    new_camera = Camera(
        name=data['name'],
        location=data.get('location'),
        camera_type=data.get('camera_type', 'rtsp'),
        url=data.get('url'),
        resolution=data.get('resolution', '1280x720'),
        fps=data.get('fps', 25),
        status='offline',
        is_active=True,
        user_id=1  # 默认用户ID
    )
    
    db.session.add(new_camera)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': '摄像头添加成功',
        'data': new_camera.to_dict()
    }), 201


# 管理员端API

@app.route('/api/status', methods=['GET'])
def get_system_status():
    """获取系统状态"""
    import requests
    ollama_available = False
    try:
        resp = requests.get(f"{ollama_config.host}/api/tags", timeout=5)
        ollama_available = resp.status_code == 200
    except Exception as e:
        pass
    
    return jsonify({
        'success': True,
        'status': 'running',
        'services': {
            'backend': 'online',
            'database': 'online',
            'ollama': 'online' if ollama_available else 'offline'
        },
        'version': '1.0.0'
    }), 200


@app.route('/api/ai/ollama/status', methods=['GET'])
def ollama_status():
    """获取Ollama服务状态"""
    import requests
    try:
        host = _get_ollama_host()
        resp = requests.get(f"{host}/api/tags", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            models = [m['name'] for m in data.get('models', [])]
            return jsonify({
                'success': True,
                'available': True,
                'models': models,
                'host': ollama_config.host
            }), 200
        else:
            return jsonify({
                'success': False,
                'available': False,
                'error': f"API returned status {resp.status_code}"
            }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'available': False,
            'error': str(e)
        }), 200


@app.route('/api/users', methods=['GET'])
def get_users():
    """获取用户列表"""
    users = User.query.all()
    user_list = [user.to_dict() for user in users]
    
    return jsonify({
        'success': True,
        'data': user_list,
        'total': len(user_list)
    }), 200


@app.route('/api/users', methods=['POST'])
def create_user():
    """创建新用户"""
    from werkzeug.security import generate_password_hash
    data = request.get_json()
    
    if not data or 'username' not in data or 'email' not in data or 'password' not in data:
        return jsonify({'success': False, 'error': '用户名、邮箱和密码不能为空'}), 400
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'success': False, 'error': '用户名已存在'}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'success': False, 'error': '邮箱已被注册'}), 400
    
    new_user = User(
        username=data['username'],
        email=data['email'],
        password_hash=generate_password_hash(data['password']),
        role=data.get('role', 'user'),
        is_active=True,
        created_at=datetime.datetime.now()
    )
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': '用户创建成功',
        'data': new_user.to_dict()
    }), 201


@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """更新用户信息"""
    from werkzeug.security import generate_password_hash
    data = request.get_json()

    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'error': '用户不存在'}), 404

    if 'username' in data:
        existing = User.query.filter_by(username=data['username']).first()
        if existing and existing.id != user_id:
            return jsonify({'success': False, 'error': '用户名已存在'}), 400
        user.username = data['username']

    if 'email' in data:
        existing = User.query.filter_by(email=data['email']).first()
        if existing and existing.id != user_id:
            return jsonify({'success': False, 'error': '邮箱已被注册'}), 400
        user.email = data['email']

    if 'password' in data and data['password']:
        user.password_hash = generate_password_hash(data['password'])

    if 'role' in data:
        user.role = data['role']

    if 'is_active' in data:
        user.is_active = data['is_active']

    if 'phone' in data:
        user.phone = data['phone']

    db.session.commit()

    return jsonify({
        'success': True,
        'message': '用户更新成功',
        'data': user.to_dict()
    }), 200


@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """删除用户"""
    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'error': '用户不存在'}), 404

    db.session.delete(user)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': '用户删除成功'
    }), 200


@app.route('/api/users/<int:user_id>/password', methods=['PUT'])
def reset_user_password(user_id):
    """重置用户密码"""
    from werkzeug.security import generate_password_hash
    data = request.get_json()

    if not data or 'password' not in data or not data['password']:
        return jsonify({'success': False, 'error': '密码不能为空'}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'error': '用户不存在'}), 404

    user.password_hash = generate_password_hash(data['password'])
    db.session.commit()

    return jsonify({
        'success': True,
        'message': '密码重置成功'
    }), 200



@app.route('/api/statistics/daily', methods=['GET'])
def get_daily_statistics():
    """获取每日统计数据"""
    import random
    range_days = request.args.get('range', '7d')
    days = int(range_days.replace('d', ''))
    
    statistics = []
    today = datetime.date.today()
    for i in range(days):
        date = today - datetime.timedelta(days=i)
        statistics.append({
            'date': date.isoformat(),
            'detections': random.randint(50, 200),
            'falls': random.randint(0, 15),
            'users': random.randint(10, 50)
        })
    
    statistics.reverse()
    
    return jsonify({
        'success': True,
        'data': statistics,
        'range': range_days
    }), 200


@app.route('/api/statistics/top-users', methods=['GET'])
def get_top_users():
    """获取活跃用户排名"""
    import random
    users = User.query.all()[:10]
    top_users = []
    
    for user in users:
        top_users.append({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'detections': random.randint(100, 1000),
            'fall_events': random.randint(0, 50),
            'risk_level': 'low' if random.random() > 0.3 else 'medium'
        })
    
    top_users.sort(key=lambda x: x['detections'], reverse=True)
    
    return jsonify({
        'success': True,
        'data': top_users
    }), 200


@app.route('/api/alerts/all', methods=['GET'])
def get_all_alerts():
    """获取所有告警记录"""
    alerts = Alert.query.order_by(Alert.sent_at.desc()).all()
    alert_list = [alert.to_dict() for alert in alerts]
    
    return jsonify({
        'success': True,
        'data': alert_list,
        'total': len(alert_list)
    }), 200


@app.route('/api/settings', methods=['GET'])
def get_settings():
    """获取系统设置"""
    settings = {
        'system_name': '跌倒检测系统',
        'detection_interval': 300,
        'alert_threshold': 0.7,
        'max_history_days': 30,
        'auto_cleanup': True,
        'email_notifications': False,
        'sms_notifications': False,
        'ollama_model': ollama_config.model,
        'ollama_host': ollama_config.host
    }
    
    return jsonify({
        'success': True,
        'data': settings
    }), 200


@app.route('/api/settings', methods=['POST'])
def update_settings():
    """更新系统设置"""
    data = request.get_json()
    
    if 'ollama_model' in data:
        ollama_config.model = data['ollama_model']
    if 'ollama_host' in data:
        ollama_config.host = data['ollama_host']
    
    return jsonify({
        'success': True,
        'message': '设置更新成功'
    }), 200


@app.route('/api/admin/ai/chat', methods=['POST'])
def admin_ai_chat():
    """管理员端AI智能助手（带数据库持久化和会话管理）"""
    from ai_agent import get_ai_agent

    data = request.get_json()
    message = data.get('message', '')
    session_id = data.get('session_id')

    if not message:
        return jsonify({'success': False, 'error': '消息不能为空'}), 400

    try:
        agent = get_ai_agent()
        response = agent.chat(message, user_id='admin')

        if session_id is None:
            # 如果没有session_id，创建新会话
            title = message[:20] + '...' if len(message) > 20 else message
            session = ConversationSession(user_id='admin', title=title)
            db.session.add(session)
            db.session.flush()
            session_id = session.id
        else:
            # 更新现有会话的时间
            session = ConversationSession.query.get(session_id)
            if session:
                session.updated_at = datetime.datetime.now()

        # 保存对话到数据库
        user_msg = ConversationHistory(session_id=session_id, user_id='admin', role='user', content=message)
        assistant_msg = ConversationHistory(session_id=session_id, user_id='admin', role='assistant', content=response)
        db.session.add(user_msg)
        db.session.add(assistant_msg)
        db.session.commit()

        return jsonify({
            'success': True,
            'response': response,
            'session_id': session_id
        }), 200
    except Exception as e:
        print(f"Admin AI chat error: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/admin/ai/history', methods=['GET'])
def admin_ai_history():
    """获取管理员AI对话历史（从数据库）"""
    try:
        # 直接从数据库查询，确保刷新后也能获取历史
        records = ConversationHistory.query.filter_by(user_id='admin').order_by(ConversationHistory.timestamp).all()
        history = [record.to_dict() for record in records]

        return jsonify({
            'success': True,
            'data': history
        }), 200
    except Exception as e:
        print(f"Admin AI history error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/admin/ai/clear', methods=['POST'])
def admin_ai_clear():
    """清除管理员AI对话历史（从数据库）"""
    try:
        # 从数据库删除
        ConversationHistory.query.filter_by(user_id='admin').delete()
        ConversationSession.query.filter_by(user_id='admin').delete()
        db.session.commit()
        
        # 同时清除内存中的缓存
        from ai_agent import get_ai_agent
        agent = get_ai_agent()
        if 'admin' in agent.conversation_context:
            agent.conversation_context['admin'] = []

        return jsonify({
            'success': True,
            'message': '对话历史已清除'
        }), 200
    except Exception as e:
        print(f"Admin AI clear error: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# 管理员端会话管理API
@app.route('/api/admin/ai/sessions', methods=['GET'])
def get_admin_ai_sessions():
    """获取管理员的对话会话列表"""
    try:
        sessions = ConversationSession.query.filter_by(user_id='admin').order_by(ConversationSession.updated_at.desc()).all()
        return jsonify({
            'success': True,
            'data': [session.to_dict() for session in sessions]
        }), 200
    except Exception as e:
        print(f"Get admin sessions error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/admin/ai/sessions', methods=['POST'])
def create_admin_ai_session():
    """创建管理员的新对话会话"""
    data = request.get_json()
    title = data.get('title', '新对话')
    
    try:
        session = ConversationSession(user_id='admin', title=title)
        db.session.add(session)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': session.to_dict()
        }), 201
    except Exception as e:
        print(f"Create admin session error: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/admin/ai/sessions/<int:session_id>', methods=['DELETE'])
def delete_admin_ai_session(session_id):
    """删除管理员的指定对话会话"""
    try:
        # 删除会话及其历史记录
        ConversationHistory.query.filter_by(session_id=session_id).delete()
        ConversationSession.query.filter_by(id=session_id, user_id='admin').delete()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '会话已删除'
        }), 200
    except Exception as e:
        print(f"Delete admin session error: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/admin/ai/sessions/<int:session_id>/history', methods=['GET'])
def get_admin_session_history(session_id):
    """获取管理员指定会话的对话历史"""
    try:
        history = ConversationHistory.query.filter_by(session_id=session_id).order_by(ConversationHistory.timestamp).all()
        return jsonify({
            'success': True,
            'data': [msg.to_dict() for msg in history]
        }), 200
    except Exception as e:
        print(f"Get admin session history error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/admin/ai/analyze', methods=['POST'])
def admin_ai_analyze():
    """管理员端AI数据分析"""
    from ai_agent import get_ai_agent
    
    data = request.get_json()
    analysis_type = data.get('type', '')
    
    if not analysis_type:
        return jsonify({'success': False, 'error': '分析类型不能为空'}), 400
    
    try:
        agent = get_ai_agent()
        
        if analysis_type == 'system_summary':
            total_users = User.query.count()
            total_alerts = Alert.query.count()
            total_detections = DetectionRecord.query.count()
            fall_detections = DetectionRecord.query.filter_by(fall_detected=True).count()
            
            summary = "系统数据分析报告:\n"
            summary += f"- 总用户数: {total_users}\n"
            summary += f"- 总告警数: {total_alerts}\n"
            summary += f"- 总检测次数: {total_detections}\n"
            summary += f"- 跌倒检测次数: {fall_detections}\n"
            summary += f"- 跌倒检测率: {fall_detections / max(total_detections, 1) * 100:.1f}%\n"
            summary += "\n请基于以上数据提供分析建议。"
            
            response = agent.chat(summary)
            
        elif analysis_type == 'user_risk':
            user_id = data.get('user_id')
            if user_id:
                user = User.query.get(user_id)
                if user:
                    detections = DetectionRecord.query.filter_by(user_id=user_id).count()
                    falls = DetectionRecord.query.filter_by(user_id=user_id, fall_detected=True).count()
                    
                    user_summary = "用户风险分析报告:\n"
                    user_summary += f"用户名: {user.username}\n"
                    user_summary += f"邮箱: {user.email}\n"
                    user_summary += f"注册时间: {user.created_at}\n"
                    user_summary += f"检测次数: {detections}\n"
                    user_summary += f"跌倒事件: {falls}\n"
                    risk_level = '高' if falls > 10 else '中' if falls > 3 else '低'
                    user_summary += f"风险等级: {risk_level}\n"
                    user_summary += "\n请分析该用户的健康风险并提供建议。"
                    
                    response = agent.chat(user_summary)
                else:
                    return jsonify({'success': False, 'error': '用户不存在'}), 404
            else:
                return jsonify({'success': False, 'error': '用户ID不能为空'}), 400
        
        elif analysis_type == 'alert_trend':
            alerts = Alert.query.order_by(Alert.sent_at.desc()).limit(30).all()
            recent_alerts = [{'time': a.sent_at.strftime('%Y-%m-%d %H:%M'), 'severity': a.severity} for a in alerts]
            
            trend_summary = "最近30条告警记录趋势分析:\n"
            trend_summary += str(recent_alerts) + "\n"
            trend_summary += "\n请分析告警趋势并提供优化建议。"
            
            response = agent.chat(trend_summary)
        
        else:
            return jsonify({'success': False, 'error': '未知的分析类型'}), 400
        
        return jsonify({
            'success': True,
            'response': response
        }), 200
    except Exception as e:
        print(f"Admin AI analyze error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    # 创建数据库表
    with app.app_context():
        db.create_all()
    
    app.run(host='0.0.0.0', port=5000, debug=False)
