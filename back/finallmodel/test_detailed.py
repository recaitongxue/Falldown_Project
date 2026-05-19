#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
详细测试视频检测 - 记录跌倒检测结果
"""

import os
import cv2
import sys

# 添加模型目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
model_dir = os.path.join(current_dir, 'model')
sys.path.insert(0, model_dir)

from fall_detector import FallDetector


def test_detailed():
    input_video = os.path.join(current_dir, '99ae60137b9243d6187c2e6895195ddf.mp4')
    
    if not os.path.exists(input_video):
        print(f"错误: 视频文件不存在 - {input_video}")
        return
    
    # 创建检测器
    detector = FallDetector()
    
    cap = cv2.VideoCapture(input_video)
    if not cap.isOpened():
        print("无法打开视频")
        return
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    print(f"视频信息: {width}x{height}, {fps:.2f} FPS, {total_frames}帧")
    
    detector.set_fps(fps)
    
    # 统计数据
    total_detected = 0
    fall_count = 0
    alert_count = 0
    behavior_counts = {}
    
    frame_idx = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        result = detector.detect_frame(frame)
        
        # 统计
        if result['status'] == 'detecting':
            total_detected += 1
            
            behavior = result['behavior']
            behavior_counts[behavior] = behavior_counts.get(behavior, 0) + 1
            
            if result['is_fall']:
                fall_count += 1
                
            if result.get('alert'):
                alert_count += 1
        
        frame_idx += 1
        if frame_idx % 500 == 0:
            print(f"处理帧 {frame_idx}/{total_frames}")
    
    cap.release()
    
    # 输出统计结果
    print("\n" + "=" * 60)
    print("检测结果统计")
    print("=" * 60)
    print(f"总帧数: {total_frames}")
    print(f"检测到人体的帧数: {total_detected} ({total_detected/total_frames*100:.1f}%)")
    print(f"检测到跌倒的帧数: {fall_count} ({fall_count/total_frames*100:.1f}%)")
    print(f"报警次数: {alert_count}")
    
    print("\n行为分布:")
    for behavior, count in behavior_counts.items():
        percentage = count / total_detected * 100 if total_detected > 0 else 0
        print(f"  {behavior}: {count}帧 ({percentage:.1f}%)")


if __name__ == "__main__":
    test_detailed()
