"""
Test OpenRouter API directly.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from src.utils import get_config, setup_logging

setup_logging(log_level="INFO", json_format=False)


async def test_openrouter():
    """Test OpenRouter API."""
    print("\n🧪 Testing OpenRouter API...")
    print("=" * 60)
    
    config = get_config()
    
    api_key = config.llm.api_key
    model = config.llm.model
    
    print(f"✓ API Key: {api_key[:15]}...")
    print(f"✓ Model: {model}")
    
    # Prepare request
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/arc-discord-bot",
        "X-Title": "Arc Discord Multimodal Bot Test",
    }
    
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": "Say 'test successful' in 3 words"}
        ],
        "max_tokens": 50,
        "temperature": 0.7,
    }
    
    print(f"\n⏳ Sending request to OpenRouter...")
    print(f"   URL: {url}")
    print(f"   Model: {model}")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=payload,
                headers=headers,
                timeout=30.0,
            )
            
            print(f"\n📊 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                print(f"✅ SUCCESS!")
                print(f"✅ Response: {content}")
                print(f"✅ Model used: {data.get('model', 'unknown')}")
                
                usage = data.get("usage", {})
                print(f"\n📈 Usage:")
                print(f"   Prompt tokens: {usage.get('prompt_tokens', 0)}")
                print(f"   Completion tokens: {usage.get('completion_tokens', 0)}")
                print(f"   Total tokens: {usage.get('total_tokens', 0)}")
                
                return True
            else:
                print(f"❌ FAILED!")
                print(f"❌ Status: {response.status_code}")
                print(f"❌ Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        print("=" * 60)


if __name__ == "__main__":
    result = asyncio.run(test_openrouter())
    sys.exit(0 if result else 1)
