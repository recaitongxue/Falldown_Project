import pymysql
from config import database_config

# 连接数据库
conn = pymysql.connect(
    host=database_config.host,
    user=database_config.user,
    password=database_config.password,
    database=database_config.database,
    port=database_config.port
)

try:
    with conn.cursor() as cursor:
        # 添加 screenshot_path 字段
        cursor.execute("""
            ALTER TABLE detection_record 
            ADD COLUMN IF NOT EXISTS screenshot_path VARCHAR(500) NULL
        """)
        print("已添加 screenshot_path 字段")
        
        # 添加 label 字段
        cursor.execute("""
            ALTER TABLE detection_record 
            ADD COLUMN IF NOT EXISTS label VARCHAR(50) NULL
        """)
        print("已添加 label 字段")
        
        # 添加 confidence 字段
        cursor.execute("""
            ALTER TABLE detection_record 
            ADD COLUMN IF NOT EXISTS confidence FLOAT NULL
        """)
        print("已添加 confidence 字段")
        
        # 添加 behavior 字段
        cursor.execute("""
            ALTER TABLE detection_record 
            ADD COLUMN IF NOT EXISTS behavior VARCHAR(50) NULL
        """)
        print("已添加 behavior 字段")
        
        # 添加 detected_at 字段
        cursor.execute("""
            ALTER TABLE detection_record 
            ADD COLUMN IF NOT EXISTS detected_at DATETIME NULL
        """)
        print("已添加 detected_at 字段")
        
    conn.commit()
    print("数据库表结构更新成功")
    
except Exception as e:
    print(f"更新失败: {e}")
    conn.rollback()
    
finally:
    conn.close()
