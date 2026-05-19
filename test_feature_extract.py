#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试特征提取是否正确
"""

import os
import sys
import numpy as np
import cv2

sys.path.append(os.path.join(os.path.dirname(__file__), 'back', 'finallmodel', 'model'))

from pose_features import PoseExtractor

def test_pose_extractor():
    """测试姿态特征提取"""
    print("测试PoseExtractor...")

    # 加载测试图像
    test_video = os.path.join(os.path.dirname(__file__), 'back', 'finallmodel', '99ae60137b9243d6187c2e6895195ddf.mp4')
    cap = cv2.VideoCapture(test_video)

    if not cap.isOpened():
        print(f"无法打开视频: {test_video}")
        return False

    # 创建姿态估计器
    extractor = PoseExtractor()

    # 读取有人的帧（跳过前100帧）
    frame_idx = 0
    ret, frame = cap.read()
    while ret and frame_idx < 200:
        # 检查是否有人
        features = extractor.extract(frame)
        if features is not None:
            print(f"在第{frame_idx}帧找到人体")
            break
        ret, frame = cap.read()
        frame_idx += 1

    cap.release()

    if not ret:
        print("未能找到有人的帧")
        return False

    print(f"帧形状: {frame.shape}")

    print(f"特征形状: {features.keypoints.shape}")
    print(f"关键点数量: {len(features.keypoints)}")
    print(f"关键点示例（前5个）: {features.keypoints[:5]}")
    print(f"center_y: {features.center_y}")
    print(f"tilt_deg: {features.tilt_deg}")
    print(f"wh_ratio: {features.wh_ratio}")

    # 计算完整特征向量
    kp = features.keypoints.astype(np.float32).reshape(-1)
    extra = np.array([
        float(features.center_y),
        float(features.tilt_deg) / 180.0,
        float(features.wh_ratio),
    ], dtype=np.float32)
    full_features = np.concatenate([kp, extra], axis=0)

    print(f"完整特征向量形状: {full_features.shape}")
    print(f"完整特征向量: {full_features[:10]}... (前10个)")
    print(f"特征向量总和: {full_features.sum():.4f}")
    print(f"特征向量范围: [{full_features.min():.4f}, {full_features.max():.4f}]")

    return True

if __name__ == "__main__":
    print("="*60)
    print("特征提取测试")
    print("="*60)

    success = test_pose_extractor()

    print("\n" + "="*60)
    print(f"测试结果: {'成功' if success else '失败'}")
    print("="*60)