#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查所有表中的记录
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'back'))
os.environ['FLASK_APP'] = 'app.py'

from app import app, db, User, DetectionRecord, AnalysisRecord, AlertRecord

def check_all_records():
    """检查所有表"""
    with app.app_context():
        print("=== 检查所有表中的记录 ===\n")
        
        # DetectionRecord 表
        print("📊 DetectionRecord 表:")
        all_records = DetectionRecord.query.all()
        print(f"  总记录数：{len(all_records)}")
        for record in all_records:
            user = User.query.get(record.user_id) if record.user_id else None
            username = user.username if user else f"未知 (ID={record.user_id})"
            print(f"  - ID: {record.id}, 用户：{username}, 文件名：{record.filename}, 时间：{record.created_at}")
        
        print("\n📊 AnalysisRecord 表:")
        all_analysis = AnalysisRecord.query.all()
        print(f"  总记录数：{len(all_analysis)}")
        for record in all_analysis:
            user = User.query.get(record.user_id) if record.user_id else None
            username = user.username if user else f"未知 (ID={record.user_id})"
            print(f"  - ID: {record.id}, 用户：{username}, 文件名：{record.original_filename}, 时间：{record.created_at}")
        
        print("\n📊 AlertRecord 表:")
        all_alerts = AlertRecord.query.all()
        print(f"  总记录数：{len(all_alerts)}")
        for record in all_alerts[:10]:  # 只显示前 10 条
            user = User.query.get(record.user_id) if record.user_id else None
            username = user.username if user else f"未知 (ID={record.user_id})"
            print(f"  - ID: {record.id}, 用户：{username}, 行为：{record.behavior}, 时间：{record.created_at}")
        if len(all_alerts) > 10:
            print(f"  ... 还有 {len(all_alerts) - 10} 条记录")

if __name__ == '__main__':
    check_all_records()
