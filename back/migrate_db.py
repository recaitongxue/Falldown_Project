#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库迁移脚本 - 添加session_id列和conversation_session表
"""

import pymysql
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 数据库连接配置
db_config = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'database': os.getenv('MYSQL_DATABASE', 'falldown'),
    'charset': 'utf8mb4'
}

def migrate_database():
    try:
        # 连接数据库
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor()
        
        print("开始数据库迁移...")
        
        # 1. 创建 conversation_session 表（如果不存在）
        create_session_table_sql = """
        CREATE TABLE IF NOT EXISTS conversation_session (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id VARCHAR(100) NOT NULL,
            title VARCHAR(200) NOT NULL DEFAULT '新对话',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_user_id (user_id),
            INDEX idx_updated_at (updated_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
        cursor.execute(create_session_table_sql)
        print("✅ conversation_session 表已创建或已存在")
        
        # 2. 检查并添加 session_id 列到 conversation_history 表
        check_column_sql = """
        SELECT COUNT(*) FROM information_schema.columns 
        WHERE table_schema = %s 
        AND table_name = 'conversation_history' 
        AND column_name = 'session_id';
        """
        cursor.execute(check_column_sql, (db_config['database'],))
        column_exists = cursor.fetchone()[0]
        
        if not column_exists:
            add_column_sql = """
            ALTER TABLE conversation_history 
            ADD COLUMN session_id INT NULL,
            ADD INDEX idx_session_id (session_id),
            ADD CONSTRAINT fk_history_session 
                FOREIGN KEY (session_id) 
                REFERENCES conversation_session(id) 
                ON DELETE SET NULL;
            """
            cursor.execute(add_column_sql)
            print("✅ session_id 列已添加到 conversation_history 表")
        else:
            print("ℹ️ session_id 列已存在，跳过")
        
        # 提交更改
        conn.commit()
        print("\n✅ 数据库迁移完成！")
        
    except Exception as e:
        print(f"\n❌ 迁移失败: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    migrate_database()

