"""
测试 gpt-5 系列模型的不同参数
"""
import requests
import json

API_BASE = "https://aixj.vip/v1"
API_KEY = "sk-c07efa399863f1dcee5f7b992c11d7ffa93be7c430dcec24f47ea5f402b09f48"

def test_model_params(model_name: str, use_system_role: bool = True, use_max_tokens: bool = True):
    """测试模型的不同参数组合"""
    print(f"\n{'='*60}")
    print(f"测试: {model_name}")
    print(f"  - system role: {use_system_role}")
    print(f"  - max_tokens: {use_max_tokens}")
    print(f"{'='*60}")
    
    url = f"{API_BASE}/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # 构建 messages
    if use_system_role:
        messages = [
            {"role": "system", "content": "你是一个助手。"},
            {"role": "user", "content": "你好，请回复'成功'"}
        ]
    else:
        messages = [
            {"role": "user", "content": "你好，请回复'成功'"}
        ]
    
    payload = {
        "model": model_name,
        "messages": messages,
    }
    
    if use_max_tokens:
        payload["max_tokens"] = 50
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            print(f"✅ 成功！响应: {content[:100]}")
            return True
        else:
            print(f"❌ 失败: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ 异常: {e}")
        return False

# 测试 gpt-5 系列模型
models_to_test = [
    "gpt-5-chat",
    "gpt-5-chat-latest",
    "gpt-5",
    "gpt-5-mini",
    "gpt-5-nano",
]

print("测试 gpt-5 系列模型...")
results = {}

for model in models_to_test:
    # 测试默认参数
    key = f"{model} (默认)"
    results[key] = test_model_params(model, use_system_role=True, use_max_tokens=True)

# 测试不带 max_tokens
print(f"\n{'='*60}")
print("测试不带 max_tokens 参数")
print(f"{'='*60}")
key = "gpt-5-chat (无 max_tokens)"
results[key] = test_model_params("gpt-5-chat", use_system_role=True, use_max_tokens=False)

# 测试不带 system role
key = "gpt-5-chat (无 system role)"
results[key] = test_model_params("gpt-5-chat", use_system_role=False, use_max_tokens=True)

# 汇总
print(f"\n{'='*60}")
print("测试汇总")
print(f"{'='*60}")
for name, success in results.items():
    status = "✅" if success else "❌"
    print(f"{status} {name}")

# 找到可用的模型
available = [name for name, success in results.items() if success]
if available:
    print(f"\n💡 推荐在设置中使用: gpt-5-chat")
