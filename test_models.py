"""
测试不同的模型名称和请求格式
"""
import os
import httpx
from openai import OpenAI

# 配置
API_BASE = "https://aixj.vip/v1"
API_KEY = "sk-c07efa399863f1dcee5f7b992c11d7ffa93be7c430dcec24f47ea5f402b09f48"

# 要测试的模型列表
MODELS_TO_TEST = [
    "gpt-4.1-mini",
    "gpt-4o-mini",
    "gpt-3.5-turbo",
    "gpt-4",
    "gpt-4o",
    "gpt-4-turbo",
    "chatgpt-4o-latest",
]

# 测试消息
TEST_MESSAGES = [
    {"role": "system", "content": "你是一个助手，请用中文回复。"},
    {"role": "user", "content": "请回复'测试成功'这4个字，不要多说。"}
]

def test_model(model_name: str):
    """测试单个模型"""
    print(f"\n{'='*60}")
    print(f"测试模型: {model_name}")
    print(f"{'='*60}")
    
    try:
        client = OpenAI(
            api_key=API_KEY,
            base_url=API_BASE,
            http_client=httpx.Client(timeout=30.0)
        )
        
        response = client.chat.completions.create(
            model=model_name,
            messages=TEST_MESSAGES,
            max_tokens=50,
            temperature=0.7,
        )
        
        content = response.choices[0].message.content
        print(f"✅ 成功！")
        print(f"响应: {content}")
        print(f"Usage: {response.usage}")
        return True
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ 失败: {error_msg}")
        
        # 提取关键错误信息
        if "400" in error_msg:
            print(f"   → 400错误: 模型可能不支持或请求格式错误")
        elif "401" in error_msg or "403" in error_msg:
            print(f"   → 认证错误: API Key 可能无效")
        elif "404" in error_msg:
            print(f"   → 404错误: 模型不存在")
        elif "429" in error_msg:
            print(f"   → 429错误: 请求频率限制")
        elif "500" in error_msg:
            print(f"   → 500错误: 服务器内部错误")
        
        return False

def test_list_models():
    """尝试获取可用模型列表"""
    print(f"\n{'='*60}")
    print(f"尝试获取可用模型列表")
    print(f"{'='*60}")
    
    try:
        client = OpenAI(
            api_key=API_KEY,
            base_url=API_BASE,
            http_client=httpx.Client(timeout=30.0)
        )
        
        models = client.models.list()
        print(f"✅ 成功获取模型列表！")
        print(f"可用模型:")
        for model in models.data:
            print(f"  - {model.id}")
        return True
        
    except Exception as e:
        print(f"❌ 获取模型列表失败: {e}")
        print(f"   → 该API可能不支持 models.list 接口")
        return False

if __name__ == "__main__":
    print("开始测试 API 配置...")
    print(f"API Base: {API_BASE}")
    print(f"API Key: {API_KEY[:10]}...{API_KEY[-4:]}")
    
    # 首先尝试获取模型列表
    test_list_models()
    
    # 测试各个模型
    results = {}
    for model in MODELS_TO_TEST:
        results[model] = test_model(model)
    
    # 汇总结果
    print(f"\n{'='*60}")
    print(f"测试汇总")
    print(f"{'='*60}")
    success_models = [m for m, r in results.items() if r]
    failed_models = [m for m, r in results.items() if not r]
    
    print(f"✅ 可用模型 ({len(success_models)}):")
    for m in success_models:
        print(f"  - {m}")
    
    print(f"\n❌ 不可用模型 ({len(failed_models)}):")
    for m in failed_models:
        print(f"  - {m}")
    
    if success_models:
        print(f"\n💡 建议: 在设置中使用以下模型之一:")
        print(f"   {success_models[0]}")
    else:
        print(f"\n💡 建议:")
        print(f"   1. 联系 API 服务商确认支持的模型列表")
        print(f"   2. 检查 API Key 是否有效")
        print(f"   3. 尝试其他 API 服务商")
