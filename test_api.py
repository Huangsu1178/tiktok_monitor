"""
测试API连接是否正常
"""
import os
from openai import OpenAI
import httpx

# 配置你的API信息
API_KEY = "sk-c07efa399863f1dcee5f7b992c11d7ffa93be7c430dcec24f47ea5f402b09f48"
API_BASE = "https://aixj.vip/v1"

# 尝试不同的模型名称
MODELS_TO_TEST = ["gpt-4.1-mini", "gpt-3.5-turbo", "gpt-4"]

def test_api():
    for model in MODELS_TO_TEST:
        print(f"\n{'='*60}")
        print(f"测试模型: {model}")
        print(f"{'='*60}")
        
        try:
            client = OpenAI(
                api_key=API_KEY,
                base_url=API_BASE,
                http_client=httpx.Client(timeout=30.0)
            )
            
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": "你好,请用一句话回复"}
                ],
                max_tokens=50
            )
            
            print(f"✅ 成功!")
            print(f"回复: {response.choices[0].message.content}")
            print(f"\n🎉 建议使用模型: {model}")
            return True
            
        except Exception as e:
            print(f"❌ 失败: {e}")
    
    print(f"\n{'='*60}")
    print("所有模型都失败了,请检查:")
    print("1. API Key是否正确")
    print("2. API Base URL是否正确")
    print("3. 网络连接是否正常")
    print("4. 联系API服务商确认可用的模型列表")
    print(f"{'='*60}")
    return False

if __name__ == "__main__":
    test_api()
