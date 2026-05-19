#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
行为识别模型测试脚本
检查GRU模型是否正确加载和工作
"""

import os
import sys
import torch

# 添加模型路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'back', 'finallmodel', 'model'))

from network import FallActionGRU

def test_model_load():
    """测试模型加载"""
    print("测试GRU模型加载...")
    
    # 模型路径
    model_path = os.path.join(os.path.dirname(__file__), 'back', 'finallmodel', 'checkpoints', 'best_gru.pt')
    print(f"模型路径: {model_path}")
    print(f"路径存在: {os.path.exists(model_path)}")
    
    # 检查文件大小
    if os.path.exists(model_path):
        file_size = os.path.getsize(model_path) / (1024 * 1024)
        print(f"模型文件大小: {file_size:.2f} MB")
    
    # 尝试加载模型
    try:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"使用设备: {device}")
        
        model = FallActionGRU(
            input_size=69,
            hidden_size=128,
            num_layers=2,
            num_classes=7,
            dropout=0.2,
        ).to(device)
        
        state = torch.load(model_path, map_location=device, weights_only=True)
        print(f"state_dict keys: {list(state.keys())}")
        
        if "state_dict" in state:
            model.load_state_dict(state["state_dict"], strict=False)
            model.eval()
            print("模型加载成功！")
            
            # 测试前向传播
            dummy_input = torch.randn(1, 24, 69).to(device)
            with torch.no_grad():
                output = model(dummy_input)
            print(f"模型输出形状: {output.shape}")
            print(f"模型输出: {output}")
            print(f"预测类别: {output.argmax(dim=1).item()}")
            
            return True
        else:
            print("state_dict中没有找到'model'键")
            return False
            
    except Exception as e:
        print(f"模型加载失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_joint_points():
    """测试关节点数据结构"""
    print("\n测试关节点数据结构...")
    
    from fall_detector import JointPoints, BEHAVIOR_CLASSES
    
    # 创建测试关节点
    joints = JointPoints(
        head=(100, 50),
        shoulder_center=(100, 100),
        right_shoulder=(120, 100),
        right_elbow=(130, 150),
        right_hand=(135, 200),
        left_shoulder=(80, 100),
        left_elbow=(70, 150),
        left_hand=(65, 200),
        right_hip=(110, 200),
        right_knee=(115, 300),
        right_ankle=(115, 350),
        left_hip=(90, 200),
        left_knee=(85, 300),
        left_ankle=(85, 350)
    )
    
    print(f"关节点列表长度: {len(joints.to_list())}")
    print(f"行为类别: {BEHAVIOR_CLASSES}")
    
    return True

def test_pose_estimator():
    """测试姿态估计器"""
    print("\n测试姿态估计器...")
    
    from fall_detector import PoseEstimator
    import cv2
    
    # 创建测试图像
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    # 绘制一个简单的人形轮廓
    cv2.circle(frame, (320, 50), 20, (255, 255, 255), -1)  # 头
    cv2.line(frame, (320, 70), (320, 150), (255, 255, 255), 3)  # 身体
    cv2.line(frame, (320, 100), (280, 180), (255, 255, 255), 3)  # 左臂
    cv2.line(frame, (320, 100), (360, 180), (255, 255, 255), 3)  # 右臂
    cv2.line(frame, (320, 150), (280, 250), (255, 255, 255), 3)  # 左腿
    cv2.line(frame, (320, 150), (360, 250), (255, 255, 255), 3)  # 右腿
    
    try:
        estimator = PoseEstimator()
        print("姿态估计器初始化成功")
        
        # 测试估计
        joints = estimator.estimate(frame)
        print(f"关节点估计结果: {joints}")
        
        if joints is not None:
            print(f"头部位置: {joints.head}")
            print(f"肩膀中心位置: {joints.shoulder_center}")
            return True
        else:
            print("未检测到人体")
            return False
            
    except Exception as e:
        print(f"姿态估计器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import numpy as np
    
    print("="*60)
    print("行为识别模型测试")
    print("="*60)
    
    # 测试模型加载
    model_ok = test_model_load()
    
    # 测试关节点数据结构
    joints_ok = test_joint_points()
    
    # 测试姿态估计器
    pose_ok = test_pose_estimator()
    
    print("\n" + "="*60)
    print("测试总结:")
    print(f"  模型加载: {'✓' if model_ok else '✗'}")
    print(f"  关节点结构: {'✓' if joints_ok else '✗'}")
    print(f"  姿态估计器: {'✓' if pose_ok else '✗'}")
    print("="*60)