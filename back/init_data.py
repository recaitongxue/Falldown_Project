#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""初始化数据库示例数据"""

import os
import sys
import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from exsampy_app import app, db, DetectionRecord, AlertRecord, User
from werkzeug.security import generate_password_hash

def init_sample_data():
    """初始化示例数据"""
    with app.app_context():
        # 创建表（如果不存在）
        db.create_all()
        
        # 添加示例用户
        if not User.query.filter_by(username='admin').first():
            admin_user = User(
                username='admin',
                email='admin@example.com',
                password_hash=generate_password_hash('admin123'),
                role='admin'
            )
            db.session.add(admin_user)
            print('创建管理员用户: admin/admin123')
        
        if not User.query.filter_by(username='user').first():
            normal_user = User(
                username='user',
                email='user@example.com',
                password_hash=generate_password_hash('user123'),
                role='user'
            )
            db.session.add(normal_user)
            print('创建普通用户: user/user123')
        
        # 添加示例检测记录
        sample_records = [
            {
                'filename': '老人日常活动.mp4',
                'file_path': '/uploads/sample1.mp4',
                'output_path': '/outputs/sample1_detected.mp4',
                'total_frames': 1200,
                'detected_frames': 1200,
                'fall_detected': False,
                'alert_count': 0,
                'status': 'completed'
            },
            {
                'filename': '老人跌倒场景1.mp4',
                'file_path': '/uploads/sample2.mp4',
                'output_path': '/outputs/sample2_detected.mp4',
                'total_frames': 1500,
                'detected_frames': 1500,
                'fall_detected': True,
                'alert_count': 12,
                'status': 'completed'
            },
            {
                'filename': '老人散步视频.mp4',
                'file_path': '/uploads/sample3.mp4',
                'output_path': '/outputs/sample3_detected.mp4',
                'total_frames': 800,
                'detected_frames': 800,
                'fall_detected': False,
                'alert_count': 0,
                'status': 'completed'
            },
            {
                'filename': '老人跌倒场景2.mp4',
                'file_path': '/uploads/sample4.mp4',
                'output_path': '/outputs/sample4_detected.mp4',
                'total_frames': 1800,
                'detected_frames': 1800,
                'fall_detected': True,
                'alert_count': 25,
                'status': 'completed'
            },
            {
                'filename': '日常监控视频.mp4',
                'file_path': '/uploads/sample5.mp4',
                'output_path': '/outputs/sample5_detected.mp4',
                'total_frames': 2000,
                'detected_frames': 2000,
                'fall_detected': False,
                'alert_count': 0,
                'status': 'completed'
            }
        ]
        
        for record_data in sample_records:
            if not DetectionRecord.query.filter_by(filename=record_data['filename']).first():
                record = DetectionRecord(
                    filename=record_data['filename'],
                    file_path=record_data['file_path'],
                    output_path=record_data['output_path'],
                    total_frames=record_data['total_frames'],
                    detected_frames=record_data['detected_frames'],
                    fall_detected=record_data['fall_detected'],
                    alert_count=record_data['alert_count'],
                    status=record_data['status'],
                    created_at=datetime.datetime.now()
                )
                db.session.add(record)
                print(f'添加示例记录: {record_data["filename"]}')
        
        # 添加示例告警记录
        fall_records = DetectionRecord.query.filter_by(fall_detected=True).all()
        for record in fall_records:
            if AlertRecord.query.filter_by(detection_id=record.id).count() == 0:
                # 添加一些告警记录
                for i in range(min(record.alert_count, 5)):
                    alert = AlertRecord(
                        detection_id=record.id,
                        frame_number=100 + i * 50,
                        timestamp=5.0 + i * 2.5,
                        behavior='falling',
                        confidence=0.85 + i * 0.03,
                        M1=True,
                        M2=True,
                        M3=True,
                        center_gravity_speed=0.08 + i * 0.02,
                        body_tilt_angle=30.0 + i * 5.0,
                        contour_ratio=0.6 + i * 0.05
                    )
                    db.session.add(alert)
                print(f'添加告警记录到: {record.filename}')
        
        db.session.commit()
        print('示例数据初始化完成！')

if __name__ == '__main__':
    init_sample_data()
