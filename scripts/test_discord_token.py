"""
Test Discord bot token validity.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils import get_config, get_logger, setup_logging

logger = get_logger(__name__)


async def test_token():
    """Test if Discord token is valid."""
    setup_logging(log_level="INFO", json_format=False)
    
    print("\n🔍 Testing Discord Token...")
    print("=" * 60)
    
    try:
        # Load config
        config = get_config()
        token = config.discord.token
        
        print(f"✓ Config loaded")
        print(f"✓ Token found (length: {len(token)} chars)")
        print(f"✓ Token starts with: {token[:10]}...")
        
        # Try to login
        import discord
        
        client = discord.Client(intents=discord.Intents.default())
        
        print(f"\n⏳ Attempting login to Discord...")
        
        try:
            await client.login(token)
            print(f"✅ Token is VALID!")
            print(f"✅ Bot user: {client.user}")
            await client.close()
            return True
            
        except discord.errors.LoginFailure as e:
            print(f"❌ Token is INVALID!")
            print(f"❌ Error: {str(e)}")
            print(f"\n💡 Solution:")
            print(f"   1. Go to Discord Developer Portal")
            print(f"   2. Click 'Reset Token'")
            print(f"   3. Copy the new token")
            print(f"   4. Update .env file")
            await client.close()
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        print("=" * 60)


if __name__ == "__main__":
    result = asyncio.run(test_token())
    sys.exit(0 if result else 1)
