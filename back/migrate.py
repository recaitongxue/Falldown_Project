import pymysql

# 数据库连接配置
db_config = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': '',
    'database': 'falldown_db'
}

# 连接数据库
conn = pymysql.connect(**db_config)

try:
    with conn.cursor() as cursor:
        # 查询表结构
        cursor.execute("DESCRIBE detection_record")
        columns = [col[0] for col in cursor.fetchall()]
        print(f"当前字段: {columns}")
        
        # 需要添加的字段
        fields_to_add = [
            ('screenshot_path', 'VARCHAR(500) NULL'),
            ('label', 'VARCHAR(50) NULL'),
            ('confidence', 'FLOAT NULL'),
            ('behavior', 'VARCHAR(50) NULL'),
            ('detected_at', 'DATETIME NULL')
        ]
        
        for field_name, field_type in fields_to_add:
            if field_name not in columns:
                try:
                    cursor.execute(f"ALTER TABLE detection_record ADD COLUMN {field_name} {field_type}")
                    print(f"成功添加字段: {field_name}")
                except Exception as e:
                    print(f"添加字段 {field_name} 失败: {e}")
            else:
                print(f"字段 {field_name} 已存在")
        
    conn.commit()
    print("数据库迁移完成")
    
except Exception as e:
    print(f"迁移失败: {e}")
    conn.rollback()
    
finally:
    conn.close()
