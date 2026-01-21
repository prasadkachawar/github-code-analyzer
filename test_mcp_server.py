#!/usr/bin/env python3
"""
Test script for MCP Server functionality
Validates MCP tools and GitHub integration
"""

import json
import asyncio
import tempfile
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_server.github_analyzer import analyze_commit_changes, generate_analysis_report


async def test_mcp_tools():
    """Test MCP server tools"""
    print("🧪 Testing MCP Server Tools")
    print("=" * 50)
    
    # Test 1: Analyze sample commit
    print("\n1. Testing analyze_commit_changes...")
    try:
        # Using a public repo with known issues for testing
        result = await analyze_commit_changes(
            repo_url="https://github.com/torvalds/linux",
            commit_sha="HEAD",
            standards=["MISRA", "CERT"]
        )
        print(f"✅ Analysis completed. Found {len(result.get('violations', []))} violations")
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
    
    # Test 2: Generate report
    print("\n2. Testing generate_analysis_report...")
    try:
        sample_results = {
            "violations": [
                {
                    "rule_id": "MISRA-C-2012-8.7",
                    "severity": "ERROR",
                    "message": "Test violation",
                    "file": "test.c",
                    "line": 10,
                    "column": 5
                }
            ],
            "summary": {
                "total_violations": 1,
                "error_count": 1,
                "warning_count": 0,
                "info_count": 0
            }
        }
        
        report = await generate_analysis_report(
            analysis_results=sample_results,
            format="html",
            include_ai_explanations=False
        )
        print(f"✅ Report generated. Length: {len(report)} characters")
    except Exception as e:
        print(f"❌ Report generation failed: {e}")
    
    print("\n🎉 MCP tools testing completed!")


def test_webhook_endpoint():
    """Test webhook endpoint availability"""
    print("\n🌐 Testing Webhook Endpoint")
    print("=" * 50)
    
    import requests
    
    try:
        # Test health endpoint
        response = requests.get("http://localhost:5000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health endpoint responding")
        else:
            print(f"❌ Health endpoint returned {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to webhook server")
        print("   Make sure the server is running: docker-compose up -d")
    except Exception as e:
        print(f"❌ Webhook test failed: {e}")


def test_configuration():
    """Test configuration loading"""
    print("\n⚙️ Testing Configuration")
    print("=" * 50)
    
    try:
        import yaml
        config_path = Path(__file__).parent / "config.yaml"
        
        if not config_path.exists():
            print("❌ config.yaml not found")
            return
            
        with open(config_path) as f:
            config = yaml.safe_load(f)
        
        # Check required sections
        required_sections = ["github", "llm", "email", "analysis", "webhook"]
        missing_sections = []
        
        for section in required_sections:
            if section not in config:
                missing_sections.append(section)
        
        if missing_sections:
            print(f"❌ Missing config sections: {missing_sections}")
        else:
            print("✅ Configuration structure valid")
            
        # Check environment variables
        env_vars = ["GITHUB_TOKEN", "GITHUB_WEBHOOK_SECRET"]
        missing_env = []
        
        for var in env_vars:
            if not os.getenv(var):
                missing_env.append(var)
        
        if missing_env:
            print(f"⚠️  Missing environment variables: {missing_env}")
        else:
            print("✅ Required environment variables set")
            
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")


def test_static_analyzer():
    """Test static analyzer integration"""
    print("\n🔍 Testing Static Analyzer Integration")
    print("=" * 50)
    
    try:
        from static_analyzer import StaticAnalyzer
        
        # Create test C file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.c', delete=False) as f:
            f.write("""
            #include <stdio.h>
            
            static int unused_variable = 42;  // MISRA violation
            
            int main() {
                char buffer[10];
                gets(buffer);  // CERT violation 
                return 0;
            }
            """)
            test_file = f.name
        
        try:
            # Analyze test file
            analyzer = StaticAnalyzer.create_default_analyzer()
            result = analyzer.analyze_file(test_file)
            
            print(f"✅ Analyzed test file. Found {len(result.violations)} violations")
            
            for violation in result.violations[:3]:  # Show first 3
                print(f"   - {violation.rule_id}: {violation.message}")
                
        finally:
            os.unlink(test_file)
            
    except ImportError as e:
        print(f"❌ Could not import static analyzer: {e}")
    except Exception as e:
        print(f"❌ Static analyzer test failed: {e}")


def main():
    """Run all tests"""
    print("🚀 MCP Server Validation Test Suite")
    print("=" * 60)
    
    # Test configuration first
    test_configuration()
    
    # Test static analyzer
    test_static_analyzer()
    
    # Test webhook endpoint
    test_webhook_endpoint()
    
    # Test MCP tools
    asyncio.run(test_mcp_tools())
    
    print("\n" + "=" * 60)
    print("🏁 Test suite completed!")
    print("\nNext steps:")
    print("1. If tests passed, the MCP server is ready to use")
    print("2. Configure GitHub webhook in your repository")
    print("3. Test with a real commit to trigger the workflow")
    print("4. Monitor logs: docker-compose logs -f mcp-server")


if __name__ == "__main__":
    main()
