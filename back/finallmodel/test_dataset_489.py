#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试数据集 489 - 将图片序列合成为视频并检测
"""

import os
import cv2
import sys

# 添加模型目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
model_dir = os.path.join(current_dir, 'model')
sys.path.insert(0, model_dir)

from fall_detector import FallDetector


def create_video_from_images(image_dir, output_video_path, fps=30):
    """将图片序列合成为视频"""
    # 获取所有图片文件
    image_files = sorted([f for f in os.listdir(image_dir) if f.endswith('.png')])
    
    if not image_files:
        print(f"错误: 目录 {image_dir} 中没有找到图片文件")
        return False
    
    print(f"找到 {len(image_files)} 张图片")
    
    # 读取第一张图片获取尺寸
    first_img = cv2.imread(os.path.join(image_dir, image_files[0]))
    height, width = first_img.shape[:2]
    print(f"图片尺寸: {width}x{height}")
    
    # 创建视频写入器
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))
    
    if not out.isOpened():
        print("错误: 无法创建视频写入器")
        return False
    
    # 写入所有图片
    for i, img_file in enumerate(image_files):
        img_path = os.path.join(image_dir, img_file)
        img = cv2.imread(img_path)
        
        if img is not None:
            out.write(img)
        
        if (i + 1) % 100 == 0:
            print(f"处理图片 {i+1}/{len(image_files)}")
    
    out.release()
    print(f"视频已保存: {output_video_path}")
    
    return True


def test_video(input_video_path, output_dir=None):
    """测试视频检测"""
    if not os.path.exists(input_video_path):
        print(f"错误: 视频文件不存在 - {input_video_path}")
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
    print("\n" + "=" * 60)
    print("检测结果统计")
    print("=" * 60)
    print(f"总帧数: {summary['total_frames']}")
    print(f"检测到跌倒的帧数: {summary['detected_frames']}")
    print(f"是否检测到跌倒: {'是' if summary['fall_detected'] else '否'}")
    print(f"报警次数: {summary['alert_count']}")
    print(f"视频帧率: {summary['fps']:.2f} FPS")
    print(f"视频时长: {summary['duration']:.2f} 秒")
    
    # 输出结果视频路径
    output_video = result['output_video']
    print(f"\n结果视频已保存: {output_video}")
    
    return output_video


def main():
    # 设置路径
    dataset_dir = os.path.join(current_dir, 'dataset/train/489')
    rgb_dir = os.path.join(dataset_dir, 'rgb')
    temp_video = os.path.join(current_dir, 'outputs', 'dataset_489_temp.mp4')
    
    print("=" * 60)
    print("测试数据集 489")
    print("=" * 60)
    
    # 先将图片合成为视频
    print("\n步骤 1: 合成视频...")
    if not create_video_from_images(rgb_dir, temp_video, fps=30):
        print("合成视频失败")
        return
    
    # 测试视频检测
    print("\n步骤 2: 运行检测...")
    output_video = test_video(temp_video)
    
    if output_video:
        print(f"\n✅ 完成! 结果视频: {output_video}")
    else:
        print("\n❌ 失败!")


if __name__ == "__main__":
    main()
