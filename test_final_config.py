"""
最终测试：确认最佳配置
"""
import requests
import json

API_BASE = "https://aixj.vip/v1"
API_KEY = "sk-c07efa399863f1dcee5f7b992c11d7ffa93be7c430dcec24f47ea5f402b09f48"

def test_complete_request():
    """测试完整的实际请求"""
    print("测试完整的 AI 分析请求...")
    print("="*60)
    
    url = f"{API_BASE}/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # 模拟实际的 TikTok 分析请求
    payload = {
        "model": "gpt-5-chat-latest",
        "messages": [
            {
                "role": "system",
                "content": "你是专业的TikTok内容策略分析师，请用中文回答。"
            },
            {
                "role": "user",
                "content": """你是一位专业的TikTok内容策略分析师，擅长分析高流量视频的成功要素。

请对以下TikTok视频的数据进行深度分析，重点识别其"流量钩子"（Hook）元素。

## 视频基本信息
- 博主：@natadventures2
- 视频描述：Him and me ❤️
- 使用标签：
- 背景音乐：
- 发布时间：2026-02-07 23:15:51

## 视频表现数据
- 播放量：3,9000,000
- 点赞数：298,900
- 评论数：574
- 分享数：81,400
- 时长：6秒

## 分析要求

请从以下维度进行结构化分析，并以JSON格式返回结果：

1. **hook_type**（钩子类型）：识别主要的流量钩子类型，如"悬念型"、"痛点型"、"挑战型"、"情感共鸣型"、"信息价值型"、"娱乐型"等
2. **hook_description**（钩子描述）：详细描述该视频的核心吸引力和钩子机制（100字以内）
3. **opening_script**（开场设计）：推断视频前3秒可能的开场方式和吸引观众的策略
4. **content_structure**（内容结构）：分析视频的内容节奏和结构安排（开头-中间-结尾）
5. **bgm_strategy**（BGM策略）：分析背景音乐的选择策略及其对情绪和完播率的影响
6. **visual_style**（视觉风格）：根据标签和描述推断视频的视觉呈现风格
7. **copywriting_style**（文案风格）：分析标题/描述的文案策略（如疑问句、数字、对比等）
8. **replication_suggestions**（可复用建议）：提供3条具体的内容创作建议，帮助复制该视频的成功要素

请严格按照以下JSON格式返回，不要包含任何额外文字：
```json
{
  "hook_type": "...",
  "hook_description": "...",
  "opening_script": "...",
  "content_structure": "...",
  "bgm_strategy": "...",
  "visual_style": "...",
  "copywriting_style": "...",
  "replication_suggestions": "1. ...\n2. ...\n3. ..."
}
```"""
            }
        ],
        "temperature": 0.7,
        "max_tokens": 1500
    }
    
    try:
        print(f"发送请求...")
        print(f"模型: gpt-5-chat-latest")
        print(f"max_tokens: 1500")
        print(f"temperature: 0.7")
        
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        
        print(f"\nStatus: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            print(f"✅ 请求成功！")
            print(f"\n响应内容:")
            print("-"*60)
            print(content)
            print("-"*60)
            
            # 尝试解析 JSON
            try:
                # 提取 JSON
                import re
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    json_match = re.search(r'\{.*\}', content, re.DOTALL)
                    json_str = json_match.group(0) if json_match else content
                
                result = json.loads(json_str)
                print(f"\n✅ JSON 解析成功！")
                print(f"钩子类型: {result.get('hook_type', 'N/A')}")
                print(f"钩子描述: {result.get('hook_description', 'N/A')[:50]}...")
                return True
                
            except Exception as e:
                print(f"\n⚠️ JSON 解析失败: {e}")
                return True
        else:
            print(f"❌ 请求失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 异常: {e}")
        return False

def test_without_max_tokens():
    """测试不带 max_tokens"""
    print("\n\n测试不带 max_tokens 参数...")
    print("="*60)
    
    url = f"{API_BASE}/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "gpt-5-chat-latest",
        "messages": [
            {"role": "system", "content": "你是助手。"},
            {"role": "user", "content": "请回复'测试成功'"}
        ],
        "temperature": 0.7
        # 不包含 max_tokens
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            print(f"✅ 成功！响应: {content}")
            return True
        else:
            print(f"❌ 失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 异常: {e}")
        return False

if __name__ == "__main__":
    print("最终配置测试\n")
    
    # 测试 1: 完整请求（带 max_tokens）
    result1 = test_complete_request()
    
    # 测试 2: 不带 max_tokens
    result2 = test_without_max_tokens()
    
    print("\n" + "="*60)
    print("最终结论")
    print("="*60)
    print(f"带 max_tokens=1500: {'✅ 成功' if result1 else '❌ 失败'}")
    print(f"不带 max_tokens: {'✅ 成功' if result2 else '❌ 失败'}")
    
    if result1:
        print(f"\n💡 推荐配置:")
        print(f"   模型: gpt-5-chat-latest")
        print(f"   max_tokens: 1500")
        print(f"   temperature: 0.7")
        print(f"\n请在设置页面使用此配置！")
