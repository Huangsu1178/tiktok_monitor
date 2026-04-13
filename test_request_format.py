"""
测试不同的请求格式
"""
import requests
import json

API_BASE = "https://aixj.vip/v1"
API_KEY = "sk-c07efa399863f1dcee5f7b992c11d7ffa93be7c430dcec24f47ea5f402b09f48"

def test_format_1_standard():
    """标准 OpenAI 格式"""
    print("\n" + "="*60)
    print("测试格式 1: 标准 OpenAI 格式")
    print("="*60)
    
    url = f"{API_BASE}/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "user", "content": "你好"}
        ],
        "max_tokens": 50
    }
    
    response = requests.post(url, headers=headers, json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:500]}")
    return response.status_code == 200

def test_format_2_no_system():
    """不带 system role"""
    print("\n" + "="*60)
    print("测试格式 2: 不带 system role")
    print("="*60)
    
    url = f"{API_BASE}/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "user", "content": "你好，请回复测试成功"}
        ],
        "max_tokens": 50
    }
    
    response = requests.post(url, headers=headers, json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:500]}")
    return response.status_code == 200

def test_format_3_string_content():
    """messages content 为字符串（非列表）"""
    print("\n" + "="*60)
    print("测试格式 3: 简化格式（prompt 字段）")
    print("="*60)
    
    url = f"{API_BASE}/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "gpt-4o-mini",
        "prompt": "你好，请回复测试成功",
        "max_tokens": 50
    }
    
    response = requests.post(url, headers=headers, json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:500]}")
    return response.status_code == 200

def test_format_4_completions():
    """使用 /completions 端点"""
    print("\n" + "="*60)
    print("测试格式 4: /completions 端点")
    print("="*60)
    
    url = f"{API_BASE}/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "gpt-4o-mini",
        "prompt": "你好，请回复测试成功",
        "max_tokens": 50
    }
    
    response = requests.post(url, headers=headers, json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:500]}")
    return response.status_code == 200

def test_format_5_different_model():
    """测试 gpt-5 系列"""
    print("\n" + "="*60)
    print("测试格式 5: gpt-5-chat 模型")
    print("="*60)
    
    url = f"{API_BASE}/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "gpt-5-chat",
        "messages": [
            {"role": "user", "content": "你好"}
        ],
        "max_tokens": 50
    }
    
    response = requests.post(url, headers=headers, json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:500]}")
    return response.status_code == 200

def test_format_6_stream_false():
    """显式设置 stream=false"""
    print("\n" + "="*60)
    print("测试格式 6: 显式设置 stream=false")
    print("="*60)
    
    url = f"{API_BASE}/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "user", "content": "你好"}
        ],
        "max_tokens": 50,
        "stream": False
    }
    
    response = requests.post(url, headers=headers, json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:500]}")
    return response.status_code == 200

if __name__ == "__main__":
    print("开始测试不同的请求格式...")
    
    results = {
        "标准 OpenAI 格式": test_format_1_standard(),
        "不带 system role": test_format_2_no_system(),
        "简化格式（prompt 字段）": test_format_3_string_content(),
        "/completions 端点": test_format_4_completions(),
        "gpt-5-chat 模型": test_format_5_different_model(),
        "显式设置 stream=false": test_format_6_stream_false(),
    }
    
    print("\n" + "="*60)
    print("测试汇总")
    print("="*60)
    for name, success in results.items():
        status = "✅ 成功" if success else "❌ 失败"
        print(f"{status} - {name}")
