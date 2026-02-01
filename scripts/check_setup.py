"""
Quick setup verification script.

Checks:
- Python version
- Required packages
- API keys in .env
- Arc documentation files
- Configuration files
"""

import sys
from pathlib import Path


def check_python_version():
    """Check Python version >= 3.11"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print("❌ Python 3.11+ required")
        print(f"   Current: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True


def check_packages():
    """Check required packages are installed"""
    required = [
        "discord",
        "langchain",
        "openai",
        "transformers",
        "torch",
        "qdrant_client",
        "structlog",
        "pydantic",
        "yaml",
    ]
    
    missing = []
    for package in required:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        print("   Run: pip install -r requirements.txt")
        return False
    
    return True


def check_env_file():
    """Check .env file exists and has required keys"""
    env_file = Path(".env")
    
    if not env_file.exists():
        print("❌ .env file not found")
        print("   Run: cp .env.example .env")
        print("   Then add your API keys")
        return False
    
    print("✅ .env file exists")
    
    # Check for required keys
    required_keys = [
        "DISCORD_TOKEN",
        "OPENROUTER_API_KEY",
        "OPENAI_API_KEY",
    ]
    
    content = env_file.read_text()
    missing = []
    
    for key in required_keys:
        if key not in content or f"{key}=your_" in content:
            missing.append(key)
            print(f"⚠️  {key} not set")
        else:
            print(f"✅ {key} configured")
    
    if missing:
        print(f"\n⚠️  Configure these keys in .env: {', '.join(missing)}")
        return False
    
    return True


def check_arc_docs():
    """Check Arc documentation files exist"""
    arc_docs = Path("arc_docs")
    arc_blogs = Path("arc_blogs")
    arc_pdf = Path("Arc Litepaper - 2025.pdf")
    
    all_good = True
    
    if arc_docs.exists():
        count = len(list(arc_docs.glob("*.md")))
        print(f"✅ arc_docs/ ({count} files)")
    else:
        print("⚠️  arc_docs/ directory not found")
        all_good = False
    
    if arc_blogs.exists():
        count = len(list(arc_blogs.glob("*.md")))
        print(f"✅ arc_blogs/ ({count} files)")
    else:
        print("⚠️  arc_blogs/ directory not found")
        all_good = False
    
    if arc_pdf.exists():
        print("✅ Arc Litepaper PDF")
    else:
        print("⚠️  Arc Litepaper PDF not found")
        all_good = False
    
    return all_good


def check_config_files():
    """Check configuration files exist"""
    config_yaml = Path("config/config.yaml")
    agents_yaml = Path("config/agents.yaml")
    
    all_good = True
    
    if config_yaml.exists():
        print("✅ config/config.yaml")
    else:
        print("❌ config/config.yaml not found")
        all_good = False
    
    if agents_yaml.exists():
        print("✅ config/agents.yaml")
    else:
        print("❌ config/agents.yaml not found")
        all_good = False
    
    return all_good


def main():
    """Run all checks"""
    print("=" * 60)
    print("Arc Discord Bot - Setup Verification")
    print("=" * 60)
    print()
    
    checks = [
        ("Python Version", check_python_version),
        ("Required Packages", check_packages),
        ("Environment Variables", check_env_file),
        ("Arc Documentation", check_arc_docs),
        ("Configuration Files", check_config_files),
    ]
    
    results = []
    
    for name, check_func in checks:
        print(f"\n--- {name} ---")
        result = check_func()
        results.append((name, result))
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    all_passed = all(result for _, result in results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print()
    
    if all_passed:
        print("🎉 All checks passed! You're ready to run the bot.")
        print()
        print("Next steps:")
        print("1. Start Qdrant: docker-compose up -d qdrant")
        print("2. Run bot: python -m src.main")
    else:
        print("⚠️  Some checks failed. Please fix the issues above.")
        print()
        print("See docs/SETUP_GUIDE.md for detailed instructions.")
        sys.exit(1)


if __name__ == "__main__":
    main()
