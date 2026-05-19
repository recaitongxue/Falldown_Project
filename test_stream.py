#!/usr/bin/env python
import requests

# 测试范围请求
url = "http://localhost:5000/api/video/stream/69210b916d88415fa6a47f0de8e4ec14_detected.mp4"

# 第一次请求：获取文件大小
response = requests.head(url)
print("HEAD请求结果:")
print(f"状态码: {response.status_code}")
if 'Content-Length' in response.headers:
    print(f"文件大小: {response.headers['Content-Length']} bytes")
print()

# 第二次请求：范围请求
headers = {'Range': 'bytes=0-1023'}
response = requests.get(url, headers=headers)
print("范围请求结果:")
print(f"状态码: {response.status_code}")
print(f"Content-Range: {response.headers.get('Content-Range')}")
print(f"Content-Length: {response.headers.get('Content-Length')}")
print(f"Accept-Ranges: {response.headers.get('Accept-Ranges')}")
print(f"响应内容长度: {len(response.content)} bytes")
