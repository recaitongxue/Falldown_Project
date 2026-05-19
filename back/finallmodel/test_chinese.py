#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试中文字体绘制
"""

import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


def test_chinese_drawing():
    """测试中文绘制"""
    # 创建测试图像
    img = np.zeros((200, 400, 3), dtype=np.uint8)
    img.fill(50)  # 灰色背景
    
    # 获取字体
    def get_font(font_size=20):
        font_paths = [
            "C:/Windows/Fonts/simhei.ttf",
            "C:\\Windows\\Fonts\\simhei.ttf",
            "C:/Windows/Fonts/msyh.ttc",
            "C:\\Windows\\Fonts\\msyh.ttc",
            "C:/Windows/Fonts/simsun.ttc",
            "C:\\Windows\\Fonts\\simsun.ttc",
        ]
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    return ImageFont.truetype(font_path, font_size)
                except Exception as e:
                    print(f"加载失败 {font_path}: {e}")
                    continue
        return ImageFont.load_default()
    
    font = get_font(24)
    
    # 使用PIL绘制中文
    img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    
    draw.text((10, 20), "测试中文显示", font=font, fill=(255, 255, 255))
    draw.text((10, 60), "跌倒检测系统", font=font, fill=(0, 255, 0))
    draw.text((10, 100), "行为: 站立", font=font, fill=(0, 255, 255))
    draw.text((10, 140), "置信度: 0.95", font=font, fill=(255, 255, 0))
    
    # 转换回OpenCV格式
    result = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
    
    # 保存测试图像
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_chinese_output.png')
    cv2.imwrite(output_path, result)
    print(f"测试图像已保存: {output_path}")
    
    return True


if __name__ == "__main__":
    print("测试中文字体绘制...")
    test_chinese_drawing()
    print("完成!")
