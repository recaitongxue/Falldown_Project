#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
模型整合测试脚本
测试fallmodel的跌倒检测算法与finallmodel的行为识别模型的整合效果
"""

import os
import sys
import cv2
import numpy as np

# 添加模型路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'back', 'finallmodel', 'model'))

from fall_detector import FallDetector, BEHAVIOR_CN_MAP

def test_video_detection(video_path):
    """测试视频检测"""
    print(f"开始测试视频: {video_path}")
    
    # 创建检测器
    detector = FallDetector()
    print("检测器初始化完成")
    print(f"使用设备: {detector.behavior_recognizer.device}")
    
    # 检测视频
    result = detector.detect_video(video_path, mode='fast')
    
    # 打印结果
    print("\n检测结果摘要:")
    print(f"成功: {result['summary']['success']}")
    print(f"总帧数: {result['summary']['total_frames']}")
    print(f"检测到跌倒的帧数: {result['summary']['detected_frames']}")
    print(f"是否检测到跌倒: {result['summary']['fall_detected']}")
    print(f"告警次数: {result['summary']['alert_count']}")
    print(f"帧率: {result['summary']['fps']:.2f}")
    print(f"时长: {result['summary']['duration']:.2f}秒")
    print(f"输出视频: {result['output_video']}")
    
    # 统计各行为类别的检测次数
    behavior_counts = {}
    for frame_result in result['frames']:
        behavior = frame_result.get('behavior', 'unknown')
        behavior_counts[behavior] = behavior_counts.get(behavior, 0) + 1
    
    print("\n行为识别统计:")
    for behavior, count in behavior_counts.items():
        print(f"  {BEHAVIOR_CN_MAP.get(behavior, behavior)}: {count}次")
    
    # 打印告警详情
    if result['alerts']:
        print(f"\n告警详情 ({len(result['alerts'])}条):")
        for i, alert in enumerate(result['alerts'][:5]):  # 只显示前5条
            print(f"  告警{i+1}: 帧={alert['frame_number']}, 时间={alert['timestamp']:.2f}秒")
            print(f"       行为: {alert['behavior_cn']}, 置信度: {alert['confidence']:.2f}")
            print(f"       M1={alert['M1']}, M2={alert['M2']}, M3={alert['M3']}")
    
    return result

def test_single_frame(frame_path):
    """测试单帧检测"""
    print(f"\n测试单帧图像: {frame_path}")
    
    # 创建检测器
    detector = FallDetector()
    
    # 读取图像
    frame = cv2.imread(frame_path)
    if frame is None:
        print("无法读取图像")
        return None
    
    # 检测帧
    result = detector.detect_frame(frame)
    
    # 打印结果
    print("单帧检测结果:")
    print(f"状态: {result['status']}")
    print(f"标签: {result['label']}")
    print(f"是否跌倒: {result['is_fall']}")
    print(f"行为: {result['behavior_cn']} (置信度: {result['behavior_confidence']:.2f})")
    print(f"M1(重心下降): {result['M1']} (速度: {result['center_gravity_speed']:.4f} m/s)")
    print(f"M2(身体倾斜): {result['M2']} (角度: {result['body_tilt_angle']:.1f}度)")
    print(f"M3(轮廓变形): {result['M3']} (比例: {result['contour_ratio']:.2f})")
    print(f"综合置信度: {result['confidence']:.2f}")
    print(f"是否告警: {result['alert']}")
    
    return result

def main():
    # 测试视频路径
    test_video = r"d:\falldown\back\finallmodel\99ae60137b9243d6187c2e6895195ddf.mp4"
    
    if os.path.exists(test_video):
        # 测试视频检测
        result = test_video_detection(test_video)
        
        # 验证输出格式是否与fallmodel一致
        print("\n" + "="*60)
        print("验证输出格式:")
        print("="*60)
        
        # 检查输出字段
        frame_result = result['frames'][0] if result['frames'] else {}
        required_fields = ['status', 'label', 'is_fall', 'M1', 'M2', 'M3', 
                          'center_gravity_speed', 'body_tilt_angle', 'contour_ratio',
                          'confidence', 'behavior', 'behavior_confidence', 'behavior_cn',
                          'frame_number', 'timestamp', 'alert']
        
        print("输出字段检查:")
        for field in required_fields:
            exists = field in frame_result
            status = "✓" if exists else "✗"
            print(f"  {status} {field}: {'存在' if exists else '缺失'}")
        
        # 检查行为识别是否正常工作
        behaviors_detected = set(f['behavior'] for f in result['frames'] if 'behavior' in f)
        print(f"\n检测到的行为类别: {', '.join(BEHAVIOR_CN_MAP.get(b, b) for b in behaviors_detected)}")
        
        # 检查跌倒检测是否使用了fallmodel的三重条件
        fall_frames = [f for f in result['frames'] if f.get('is_fall')]
        if fall_frames:
            print(f"\n跌倒检测验证（使用fallmodel的三重条件）:")
            sample_fall = fall_frames[0]
            print(f"  M1(重心下降): {sample_fall['M1']}")
            print(f"  M2(身体倾斜): {sample_fall['M2']}")
            print(f"  M3(轮廓变形): {sample_fall['M3']}")
            print(f"  只有当三个条件都满足时才判定为跌倒: {sample_fall['M1'] and sample_fall['M2'] and sample_fall['M3']}")
    else:
        print(f"测试视频不存在: {test_video}")
    
    print("\n" + "="*60)
    print("测试完成！")
    print("="*60)

if __name__ == "__main__":
    main()