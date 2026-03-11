#!/usr/bin/env python3
import sys
import pkg_resources
import os

def print_system_info():
    print("\nSystem Information:")
    print("=" * 50)
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")
    print(f"Current working directory: {os.getcwd()}")

def test_ta_lib():
    try:
        import talib
        print("✅ TA-Lib imported successfully")
        
        # Test a simple TA-Lib function
        import numpy as np
        data = np.random.random(100)
        sma = talib.SMA(data, timeperiod=20)
        print("✅ TA-Lib SMA calculation successful")
        return True
    except Exception as e:
        print(f"❌ TA-Lib test failed: {str(e)}")
        return False

def test_langchain():
    try:
        # Print installed packages for debugging
        print("\nInstalled packages:")
        print("=" * 50)
        installed_packages = {pkg.key: pkg.version for pkg in pkg_resources.working_set}
        for pkg, version in sorted(installed_packages.items()):
            print(f"  {pkg}=={version}")
        
        # Check for required packages
        required_packages = ['langchain', 'langchain-community', 'langchain-openai']
        missing_packages = [pkg for pkg in required_packages if pkg not in installed_packages]
        if missing_packages:
            print(f"\n❌ Missing required packages: {', '.join(missing_packages)}")
            return False
        
        # Try importing LangChain components
        print("\nTesting LangChain imports:")
        print("=" * 50)
        
        from langchain_openai import ChatOpenAI
        print("✅ langchain_openai imported")
        
        from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
        print("✅ langchain_community.utilities imported")
        
        from langchain.agents import Tool, AgentExecutor, LLMSingleActionAgent
        print("✅ langchain.agents imported")
        
        from langchain.prompts import StringPromptTemplate
        print("✅ langchain.prompts imported")
        
        from langchain.memory import ConversationBufferMemory
        print("✅ langchain.memory imported")
        
        print("\n✅ All LangChain imports successful")
        return True
    except ImportError as e:
        print(f"\n❌ LangChain import error: {str(e)}")
        print(f"Python path: {sys.path}")
        return False
    except Exception as e:
        print(f"\n❌ LangChain test failed: {str(e)}")
        return False

def main():
    print("\nTesting Dependencies...")
    print("=" * 50)
    
    print_system_info()
    
    ta_lib_ok = test_ta_lib()
    langchain_ok = test_langchain()
    
    print("\nTest Summary:")
    print("=" * 50)
    print(f"TA-Lib: {'✅ PASS' if ta_lib_ok else '❌ FAIL'}")
    print(f"LangChain: {'✅ PASS' if langchain_ok else '❌ FAIL'}")
    
    if ta_lib_ok and langchain_ok:
        print("\n✅ All dependency tests passed!")
    else:
        print("\n❌ Some dependency tests failed!")

if __name__ == "__main__":
    main() 