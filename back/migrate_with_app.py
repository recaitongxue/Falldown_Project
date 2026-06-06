import sys
sys.path.insert(0, '.')

from app import app, db
from sqlalchemy import text

with app.app_context():
    try:
        # 获取当前表结构
        result = db.session.execute(text("DESCRIBE detection_record"))
        columns = [row[0] for row in result.fetchall()]
        print(f"当前字段: {columns}")
        
        # 需要添加的字段
        fields_to_add = [
            ('screenshot_path', 'VARCHAR(500)'),
            ('label', 'VARCHAR(50)'),
            ('confidence', 'FLOAT'),
            ('behavior', 'VARCHAR(50)'),
            ('detected_at', 'DATETIME')
        ]
        
        for field_name, field_type in fields_to_add:
            if field_name not in columns:
                try:
                    db.session.execute(text(f"ALTER TABLE detection_record ADD COLUMN {field_name} {field_type} NULL"))
                    db.session.commit()
                    print(f"成功添加字段: {field_name}")
                except Exception as e:
                    print(f"添加字段 {field_name} 失败: {e}")
                    db.session.rollback()
            else:
                print(f"字段 {field_name} 已存在")
        
        print("数据库迁移完成")
        
    except Exception as e:
        print(f"迁移失败: {e}")
