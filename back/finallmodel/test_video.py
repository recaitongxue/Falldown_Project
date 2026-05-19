#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试视频文件并保存检测结果
"""

import os
import cv2
import sys

# 添加模型目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
model_dir = os.path.join(current_dir, 'model')
sys.path.insert(0, model_dir)

from fall_detector import FallDetector


def test_video_and_save(input_video_path, output_dir=None):
    """
    测试视频文件并保存检测结果
    """
    if not os.path.exists(input_video_path):
        print(f"错误: 输入视频文件不存在 - {input_video_path}")
        return None
    
    # 创建检测器
    detector = FallDetector()
    
    # 设置输出目录
    if output_dir is None:
        output_dir = os.path.join(current_dir, 'outputs')
    os.makedirs(output_dir, exist_ok=True)
    
    # 执行检测
    print(f"开始处理视频: {input_video_path}")
    result = detector.detect_video(input_video_path, mode='fast')
    
    if not result.get('success', False):
        print(f"检测失败: {result.get('error', '未知错误')}")
        return None
    
    # 输出统计信息
    summary = result['summary']
    print("\n检测完成!")
    print(f"总帧数: {summary['total_frames']}")
    print(f"检测到跌倒的帧数: {summary['detected_frames']}")
    print(f"是否检测到跌倒: {'是' if summary['fall_detected'] else '否'}")
    print(f"报警次数: {summary['alert_count']}")
    print(f"视频帧率: {summary['fps']:.2f} FPS")
    print(f"视频时长: {summary['duration']:.2f} 秒")
    
    # 输出结果视频路径
    output_video = result['output_video']
    print(f"\n结果视频已保存到: {output_video}")
    
    return output_video


def main():
    # 输入视频路径
    input_video = os.path.join(current_dir, '99ae60137b9243d6187c2e6895195ddf.mp4')
    
    # 测试并保存
    output_video = test_video_and_save(input_video)
    
    if output_video:
        print(f"\n✅ 测试完成! 结果视频: {output_video}")
    else:
        print("\n❌ 测试失败!")


if __name__ == "__main__":
    main()
