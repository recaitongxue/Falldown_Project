#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
跌倒检测系统配置文件
"""

import os
from dataclasses import dataclass


@dataclass
class OllamaConfig:
    """Ollama AI智能体配置"""
    host: str = "http://localhost:11434"
    model: str = "qwen3:1.7b"
    enabled: bool = True


@dataclass
class ModelConfig:
    """行为识别模型配置"""
    hidden_size: int = 128
    num_layers: int = 2
    dropout: float = 0.3
    sequence_length: int = 16
    class_names: list = None
    
    def __post_init__(self):
        if self.class_names is None:
            self.class_names = ["empty", "standing", "sitting", "lying", "bending", "crawling", "empty"]


@dataclass
class RuleConfig:
    """跌倒检测规则配置（基于论文）"""
    fps: float = 20.0
    cgdd_frame_gap: int = 10        # 重心下降检测帧间隔
    v_cr: float = 0.015              # 重心下降速度阈值
    theta_cr_deg: float = 60.0       # 身体倾斜角度阈值（度）
    p_cr: float = 0.7                # 轮廓变形比例阈值
    t_cr_sec: float = 15.0           # 跌倒后报警延迟时间（秒）
    elbow_angle_cr: float = 160.0    # 肘部角度阈值（伸直状态）
    knee_angle_cr: float = 160.0     # 膝盖角度阈值（伸直状态）
    hip_angle_cr: float = 150.0      # 臀部角度阈值（伸直状态）


@dataclass
class AppConfig:
    """应用程序配置"""
    secret_key: str = "fall_detection_secret_key_2025"
    upload_folder: str = "uploads"
    output_folder: str = "outputs"
    max_content_length: int = 500 * 1024 * 1024  # 500MB


@dataclass
class DatabaseConfig:
    """数据库配置"""
    host: str = "localhost"
    port: int = 3306
    user: str = "root"
    password: str = ""
    database: str = "falldown_db"


# 全局配置实例
ollama_config = OllamaConfig()
model_config = ModelConfig()
rule_config = RuleConfig()
app_config = AppConfig()
database_config = DatabaseConfig()


def load_config_from_env():
    """从环境变量加载配置"""
    # Ollama配置
    if os.getenv('OLLAMA_HOST'):
        ollama_config.host = os.getenv('OLLAMA_HOST')
    if os.getenv('OLLAMA_MODEL'):
        ollama_config.model = os.getenv('OLLAMA_MODEL')
    if os.getenv('OLLAMA_ENABLED') is not None:
        ollama_config.enabled = os.getenv('OLLAMA_ENABLED').lower() == 'true'
    
    # 规则配置
    if os.getenv('RULE_FPS'):
        rule_config.fps = float(os.getenv('RULE_FPS'))
    if os.getenv('RULE_CGDD_FRAME_GAP'):
        rule_config.cgdd_frame_gap = int(os.getenv('RULE_CGDD_FRAME_GAP'))
    if os.getenv('RULE_V_CR'):
        rule_config.v_cr = float(os.getenv('RULE_V_CR'))
    if os.getenv('RULE_THETA_CR_DEG'):
        rule_config.theta_cr_deg = float(os.getenv('RULE_THETA_CR_DEG'))
    if os.getenv('RULE_P_CR'):
        rule_config.p_cr = float(os.getenv('RULE_P_CR'))
    if os.getenv('RULE_T_CR_SEC'):
        rule_config.t_cr_sec = float(os.getenv('RULE_T_CR_SEC'))
    
    # 模型配置
    if os.getenv('MODEL_HIDDEN_SIZE'):
        model_config.hidden_size = int(os.getenv('MODEL_HIDDEN_SIZE'))
    if os.getenv('MODEL_NUM_LAYERS'):
        model_config.num_layers = int(os.getenv('MODEL_NUM_LAYERS'))
    if os.getenv('MODEL_DROPOUT'):
        model_config.dropout = float(os.getenv('MODEL_DROPOUT'))
    if os.getenv('MODEL_SEQUENCE_LENGTH'):
        model_config.sequence_length = int(os.getenv('MODEL_SEQUENCE_LENGTH'))
    
    # 应用配置
    if os.getenv('SECRET_KEY'):
        app_config.secret_key = os.getenv('SECRET_KEY')
    
    # 数据库配置
    if os.getenv('MYSQL_HOST'):
        database_config.host = os.getenv('MYSQL_HOST')
    if os.getenv('MYSQL_PORT'):
        database_config.port = int(os.getenv('MYSQL_PORT'))
    if os.getenv('MYSQL_USER'):
        database_config.user = os.getenv('MYSQL_USER')
    if os.getenv('MYSQL_PASSWORD'):
        database_config.password = os.getenv('MYSQL_PASSWORD')
    if os.getenv('MYSQL_DATABASE'):
        database_config.database = os.getenv('MYSQL_DATABASE')
