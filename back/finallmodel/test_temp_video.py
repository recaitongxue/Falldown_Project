#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试临时视频
"""

import os
import cv2
import sys

# 添加模型目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
model_dir = os.path.join(current_dir, 'model')
sys.path.insert(0, model_dir)

from fall_detector import FallDetector


def test_temp_video():
    temp_video = os.path.join(current_dir, 'outputs', 'dataset_489_temp.mp4')
    
    if not os.path.exists(temp_video):
        print(f"错误: 视频文件不存在 - {temp_video}")
        return None
    
    # 创建检测器
    detector = FallDetector()
    
    # 打开视频
    cap = cv2.VideoCapture(temp_video)
    if not cap.isOpened():
        print("无法打开视频")
        return None
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    print(f"视频信息: {width}x{height}, {fps:.2f} FPS, {total_frames}帧")
    
    detector.set_fps(fps)
    
    # 设置输出
    output_dir = os.path.join(current_dir, 'outputs')
    output_video = os.path.join(output_dir, 'dataset_489_detected.mp4')
    
    # 创建视频写入器
    try:
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out_writer = cv2.VideoWriter(output_video, fourcc, fps, (width, height))
        if not out_writer.isOpened():
            print("无法创建视频写入器")
            cap.release()
            return None
    except Exception as e:
        print(f"创建视频写入器失败: {e}")
        cap.release()
        return None
    
    # 统计
    total_detected = 0
    fall_count = 0
    alert_count = 0
    behavior_counts = {}
    
    frame_idx = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        # 检测
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
        
        # 绘制
        frame = detector.draw_result(frame, result)
        out_writer.write(frame)
        
        frame_idx += 1
        if frame_idx % 100 == 0:
            print(f"处理帧 {frame_idx}/{total_frames}")
    
    cap.release()
    out_writer.release()
    
    # 输出统计
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
    
    print(f"\n结果视频已保存: {output_video}")
    
    return output_video


if __name__ == "__main__":
    print("=" * 60)
    print("测试数据集 489 视频")
    print("=" * 60)
    
    output_video = test_temp_video()
    
    if output_video:
        print("\n✅ 完成!")
    else:
        print("\n❌ 失败!")
