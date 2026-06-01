#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复 user_id 为 NULL 的记录，将其分配给 user 用户
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'back'))
os.environ['FLASK_APP'] = 'app.py'

from app import app, db, User, DetectionRecord, AlertRecord

def fix_null_user_ids():
    """修复 NULL 的 user_id"""
    with app.app_context():
        # 获取 user 用户
        user = User.query.filter_by(username='user').first()
        if not user:
            print("❌ 未找到用户 'user'")
            return
        
        print(f"📌 将把所有 user_id=NULL 的记录分配给用户 '{user.username}' (ID={user.id})\n")
        
        # 修复 DetectionRecord
        null_user_records = DetectionRecord.query.filter(DetectionRecord.user_id.is_(None)).all()
        print(f" DetectionRecord 表中有 {len(null_user_records)} 条记录的 user_id 为 NULL")
        
        if null_user_records:
            confirm = input(f"是否将这些记录分配给用户 '{user.username}'？(y/n): ")
            if confirm.lower() == 'y':
                for record in null_user_records:
                    record.user_id = user.id
                db.session.commit()
                print(f"✅ 成功修复 {len(null_user_records)} 条 DetectionRecord 记录\n")
            else:
                print("❌ 已取消操作")
                return
        
        # 修复 AlertRecord
        null_user_alerts = AlertRecord.query.filter(AlertRecord.user_id.is_(None)).all()
        print(f"📊 AlertRecord 表中有 {len(null_user_alerts)} 条记录的 user_id 为 NULL")
        
        if null_user_alerts:
            # 自动确认修复
            print(f"🔧 自动将这些记录分配给用户 '{user.username}'...")
            for alert in null_user_alerts:
                alert.user_id = user.id
            db.session.commit()
            print(f"✅ 成功修复 {len(null_user_alerts)} 条 AlertRecord 记录\n")
        
        # 统计结果
        print("\n=== 修复后的统计 ===")
        all_records = DetectionRecord.query.all()
        print(f"DetectionRecord 总记录数：{len(all_records)}")
        
        for u in User.query.all():
            count = DetectionRecord.query.filter_by(user_id=u.id).count()
            if count > 0:
                print(f"  - 用户 {u.username} (ID={u.id}): {count} 条记录")

if __name__ == '__main__':
    fix_null_user_ids()
