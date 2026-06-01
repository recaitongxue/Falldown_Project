#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复用户分析记录的 user_id 关联问题
将所有 user_id=1 但实际属于普通用户的记录转移到正确的用户
"""

import sys
import os

# 添加后端目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'back'))

# 设置环境变量（如果需要）
os.environ['FLASK_APP'] = 'app.py'

from app import app, db, User, DetectionRecord, AlertRecord

def fix_user_records():
    """修复用户记录关联"""
    with app.app_context():
        # 获取所有用户
        users = User.query.all()
        print(f"找到 {len(users)} 个用户:")
        for user in users:
            print(f"  - ID: {user.id}, 用户名：{user.username}, 邮箱：{user.email}")
        
        # 统计每个用户的记录数
        print("\n修复前各用户的记录数:")
        for user in users:
            count = DetectionRecord.query.filter_by(user_id=user.id).count()
            print(f"  - 用户 {user.username} (ID={user.id}): {count} 条记录")
        
        # 检查 user_id=1 的所有记录
        admin = User.query.get(1)
        if admin:
            admin_records = DetectionRecord.query.filter_by(user_id=1).all()
            print(f"\nAdmin (ID=1) 当前有 {len(admin_records)} 条记录")
            
            # 询问是否需要迁移
            if len(admin_records) > 0:
                print("\n⚠️  警告：以下记录将从 admin 迁移到目标用户")
                for record in admin_records[:10]:  # 只显示前 10 条
                    print(f"  - ID: {record.id}, 文件名：{record.filename}, 创建时间：{record.created_at}")
                if len(admin_records) > 10:
                    print(f"  ... 还有 {len(admin_records) - 10} 条记录")
                
                # 自动迁移到 user 用户（ID=2）
                user = User.query.filter_by(username='user').first()
                if user:
                    print(f"\n开始迁移记录到用户 '{user.username}' (ID={user.id})...")
                    migrated_count = 0
                    for record in admin_records:
                        record.user_id = user.id
                        migrated_count += 1
                    
                    db.session.commit()
                    print(f"✅ 成功迁移 {migrated_count} 条记录")
                    
                    # 同时迁移关联的告警记录
                    admin_alerts = AlertRecord.query.filter_by(user_id=1).all()
                    if admin_alerts:
                        print(f"\n同时迁移 {len(admin_alerts)} 条告警记录...")
                        for alert in admin_alerts:
                            alert.user_id = user.id
                        db.session.commit()
                        print(f"✅ 成功迁移 {len(admin_alerts)} 条告警记录")
                else:
                    print("\n❌ 未找到用户 'user'，无法迁移")
        
        # 再次统计
        print("\n修复后各用户的记录数:")
        for user in users:
            count = DetectionRecord.query.filter_by(user_id=user.id).count()
            print(f"  - 用户 {user.username} (ID={user.id}): {count} 条记录")

if __name__ == '__main__':
    fix_user_records()
