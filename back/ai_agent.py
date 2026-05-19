#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI智能体模块
提供风险分析、报告生成和对话功能
"""

import json
import time
from datetime import datetime
from collections import deque

from config import ollama_config


class AIAgent:
    def __init__(self):
        self.is_running = False
        self.alert_callbacks = []
        self.behavior_history = deque(maxlen=100)
        self.risk_score = 0.0
        self.fall_patterns = []
        self.normal_patterns = []
        self.conversation_context = {}
        # 延迟检测Ollama，避免启动时检测失败
        self._ollama_available = None
    
    def _get_ollama_host(self):
        """获取正确的Ollama连接地址"""
        host = ollama_config.host
        # 确保host有http://前缀
        if not host.startswith('http://') and not host.startswith('https://'):
            host = 'http://' + host
        # 如果绑定地址是0.0.0.0，替换为localhost用于客户端连接
        host = host.replace('0.0.0.0', 'localhost')
        return host

    def _check_ollama(self):
        """检查Ollama服务是否可用"""
        try:
            import requests
            host = self._get_ollama_host()
            resp = requests.get(f"{host}/api/tags", timeout=5)
            success = resp.status_code == 200
            if success:
                print(f"✓ Ollama service available at {host}")
            return success
        except Exception as e:
            print(f"✗ Ollama check failed: {e}")
            return False
    
    @property
    def ollama_available(self):
        """动态检测Ollama可用性"""
        result = self._check_ollama()
        print(f"ollama_available property returning: {result}")
        return result
    
    def set_ollama_config(self, host=None, model=None):
        """设置Ollama配置"""
        if host:
            ollama_config.host = host
        if model:
            ollama_config.model = model
        # 重置缓存，下次检测时重新检查
        self._ollama_available = None
        return self._check_ollama()
    
    def get_ollama_models(self):
        """获取Ollama可用模型列表"""
        try:
            import requests
            host = self._get_ollama_host()
            resp = requests.get(f"{host}/api/tags", timeout=5)
            if resp.status_code == 200:
                return resp.json().get('models', [])
        except Exception as e:
            print(f"Error fetching Ollama models: {e}")
        return []

    def _call_ollama(self, messages):
        """调用Ollama API"""
        try:
            import requests
            host = self._get_ollama_host()
            data = {
                "model": ollama_config.model,
                "messages": messages,
                "stream": False
            }
            resp = requests.post(f"{host}/api/chat", json=data, timeout=60)
            if resp.status_code == 200:
                return resp.json().get('message', {}).get('content', '')
            else:
                print(f"Ollama API error: {resp.status_code}")
                return ""
        except Exception as e:
            print(f"Error calling Ollama: {e}")
            return ""

    def register_alert_callback(self, callback):
        self.alert_callbacks.append(callback)

    def analyze_behavior(self, result, context=None):
        """分析行为并计算风险"""
        self.behavior_history.append({
            'timestamp': datetime.utcnow(),
            'result': result,
            'context': context
        })

        risk = 0.0
        if result.get('fall_detected'):
            risk += 0.6
        if result.get('alert'):
            risk += 0.3
        if result.get('M1') and result.get('M2'):
            risk += 0.1

        recent = list(self.behavior_history)[-10:]
        if len(recent) >= 5:
            fall_count = sum(1 for r in recent if r['result'].get('fall_detected'))
            if fall_count >= 3:
                risk += 0.2

        self.risk_score = min(1.0, risk)
        return {
            'risk_level': self.risk_score,
            'risk_label': 'high' if risk > 0.7 else 'medium' if risk > 0.4 else 'low',
            'recommendation': self._get_recommendation(risk, result),
            'pattern_detected': self._detect_pattern(recent)
        }

    def _get_recommendation(self, risk, result):
        """根据风险等级生成建议"""
        if risk > 0.7:
            return "高风险！立即检查人员状态，建议启动紧急救援流程"
        elif risk > 0.4:
            return "中度风险，增加监控频率，观察人员状态变化"
        else:
            return "风险较低，保持正常监控"

    def _detect_pattern(self, recent):
        """检测行为模式"""
        if len(recent) < 5:
            return None

        statuses = [r['result'].get('detected_class', 'unknown') for r in recent]
        if statuses.count('lying') >= 3:
            return "长时间躺卧"
        if statuses.count('bending') >= 4:
            return "频繁弯腰"
        return None

    def generate_report(self):
        """生成综合报告"""
        history = list(self.behavior_history)
        if not history:
            return {"summary": "暂无数据", "patterns": [], "risk_trend": "stable"}

        fall_events = [h for h in history if h['result'].get('fall_detected')]
        return {
            "total_events": len(history),
            "fall_events": len(fall_events),
            "avg_risk": sum(self.risk_score for _ in history) / len(history),
            "risk_trend": "increasing" if self.risk_score > 0.5 else "stable",
            "patterns": [self._detect_pattern(history[i:i+5]) for i in range(0, len(history)-5, 5)],
            "recommendations": self._generate_recommendations(history)
        }

    def _generate_recommendations(self, history):
        """生成建议列表"""
        recommendations = []
        fall_count = sum(1 for h in history if h['result'].get('fall_detected'))
        if fall_count > 10:
            recommendations.append("近期跌倒事件较多，建议检查环境安全性")
        if self.risk_score > 0.6:
            recommendations.append("当前风险等级较高，需要重点关注")
        return recommendations

    def analyze_batch(self, results):
        """批量分析检测结果"""
        if not results:
            return {"risk_level": 0, "risk_label": "low", "recommendations": []}
        
        fall_count = sum(1 for r in results if r.get('fall_detected'))
        alert_count = sum(1 for r in results if r.get('alert'))
        total = len(results)
        
        risk = 0.0
        if fall_count > total * 0.3:
            risk += 0.5
        if alert_count > total * 0.2:
            risk += 0.3
        
        avg_confidence = sum(r.get('confidence', 0) for r in results) / total if total > 0 else 0
        if avg_confidence > 0.8:
            risk += 0.2
        
        risk = min(1.0, risk)
        
        recommendations = []
        if risk > 0.7:
            recommendations.append("检测到大量跌倒事件，建议立即检查")
            recommendations.append("可能存在安全隐患，需要人工干预")
        elif risk > 0.4:
            recommendations.append("检测到部分异常行为，建议加强监控")
            recommendations.append("关注后续行为变化")
        
        return {
            "risk_level": risk,
            "risk_label": "high" if risk > 0.7 else "medium" if risk > 0.4 else "low",
            "recommendations": recommendations,
            "statistics": {
                "total_frames": total,
                "fall_frames": fall_count,
                "alert_frames": alert_count,
                "avg_confidence": avg_confidence
            }
        }

    def chat(self, message, user_id=None):
        """与用户对话"""
        context_key = user_id or 'default'
        if context_key not in self.conversation_context:
            self.conversation_context[context_key] = []

        self.conversation_context[context_key].append({
            'role': 'user',
            'content': message,
            'timestamp': datetime.utcnow()
        })

        history = list(self.behavior_history)[-5:]
        
        # 优先使用Ollama - 使用直接检查确保正确性
        ollama_available = False
        if ollama_config.enabled:
            try:
                import requests
                host = self._get_ollama_host()
                resp = requests.get(f"{host}/api/tags", timeout=5)
                ollama_available = resp.status_code == 200
            except Exception as e:
                print(f"Ollama check in chat failed: {e}")
        
        if ollama_available:
            print("Using Ollama for response")
            response = self._generate_ollama_response(message, history, context_key)
        else:
            print("Using fallback response")
            response = self._generate_response(message, history)

        self.conversation_context[context_key].append({
            'role': 'assistant',
            'content': response,
            'timestamp': datetime.utcnow()
        })

        return response
    
    def _generate_ollama_response(self, message, history, context_key='default'):
        """使用Ollama生成响应"""
        report = self.generate_report()
        risk_level = report.get('risk_label', 'low')
        fall_events = report.get('fall_events', 0)
        recommendations = report.get('recommendations', [])

        system_prompt = f"""你是一个智能AI助手，可以回答各种问题。

当前系统上下文（跌倒检测系统）：
- 当前风险等级：{risk_level}
- 近期跌倒事件：{fall_events}次
- 系统建议：{' '.join(recommendations)}

你的能力：
1. 分析跌倒风险并提供专业建议
2. 回答用户关于系统功能的问题
3. 帮助用户理解检测结果
4. 提供友好的技术支持
5. 回答各种通用问题，包括日常对话、知识问答等

请用中文回答，保持专业且友好，灵活应对各种问题。
"""

        ollama_messages = [
            {"role": "system", "content": system_prompt}
        ]

        # 添加对话历史
        conversation_history = self.conversation_context.get(context_key, [])
        for msg in conversation_history[-10:]:
            ollama_messages.append({
                "role": msg.get('role', 'user'),
                "content": msg.get('content', '')
            })

        # 添加当前消息
        ollama_messages.append({"role": "user", "content": message})

        response = self._call_ollama(ollama_messages)

        if not response:
            return self._generate_response(message, history)

        return response

    def _generate_response(self, message, history):
        """备用响应生成器（当Ollama不可用时）"""
        message_lower = message.lower()

        if any(kw in message_lower for kw in ['风险', 'risk', '分析']):
            report = self.generate_report()
            return f"当前系统风险评估：{report.get('risk_trend', '稳定')}\n近期跌倒事件：{report.get('fall_events', 0)}次\n建议：{' '.join(report.get('recommendations', ['保持监控']))}"

        if any(kw in message_lower for kw in ['帮助', 'help', '功能']):
            return "我可以帮助您：\n1. 分析跌倒风险\n2. 查看检测历史\n3. 管理摄像头\n4. 生成报告\n5. 回答系统相关问题"

        if any(kw in message_lower for kw in ['状态', 'status', '情况']):
            return f"当前监控状态：\n- 风险等级：{'高' if self.risk_score > 0.6 else '中' if self.risk_score > 0.3 else '低'}\n- 待处理告警：{sum(1 for h in history if h['result'].get('alert') and not h['result'].get('acknowledged'))}条"

        return f"我已收到您的问题：{message}\n当前系统运行正常，如有需要请随时提问。"


# 全局AI代理实例
_ai_agent_instance = None

def get_ai_agent():
    """获取全局AI代理实例"""
    global _ai_agent_instance
    if _ai_agent_instance is None:
        _ai_agent_instance = AIAgent()
    return _ai_agent_instance
