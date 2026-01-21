#!/usr/bin/env python3
"""
Demo script for Static Code Analysis Framework
Demonstrates key capabilities for embedded C/C++ analysis
"""

import sys
import os
import json
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from static_analyzer import (
        StaticAnalyzer, 
        AnalyzerConfig, 
        create_default_analyzer,
        Standard, 
        Severity
    )
    from static_analyzer.config import create_default_config_file
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure all dependencies are installed:")
    print("pip install -r requirements.txt")
    sys.exit(1)


def demo_basic_analysis():
    """Demonstrate basic static analysis capabilities."""
    print("=" * 60)
    print("STATIC CODE ANALYSIS FRAMEWORK DEMONSTRATION")
    print("=" * 60)
    print()
    
    print("🔧 Creating analyzer with default configuration...")
    try:
        analyzer = create_default_analyzer()
        print("✅ Analyzer created successfully")
    except Exception as e:
        print(f"❌ Failed to create analyzer: {e}")
        return False
    
    print()
    print("📋 Available rules:")
    try:
        rules = analyzer.get_available_rules()
        for rule in rules:
            severity_emoji = {
                'critical': '🔴',
                'major': '🟠', 
                'minor': '🟡',
                'info': '🔵'
            }.get(rule['severity'], '⚪')
            
            print(f"  {severity_emoji} {rule['id']} - {rule['title']}")
        print()
    except Exception as e:
        print(f"❌ Failed to list rules: {e}")
    
    # Analyze sample files
    sample_files = [
        "samples/test_violations.c",
        "samples/compliant_code.c"
    ]
    
    for sample_file in sample_files:
        if os.path.exists(sample_file):
            print(f"🔍 Analyzing: {sample_file}")
            try:
                report = analyzer.analyze_files([sample_file])
                
                violation_count = len(report.violations)
                if violation_count == 0:
                    print(f"  ✅ No violations found")
                else:
                    print(f"  ⚠️  {violation_count} violations found:")
                    
                    # Show summary by severity
                    severity_counts = {}
                    for violation in report.violations:
                        sev = violation.severity.value
                        severity_counts[sev] = severity_counts.get(sev, 0) + 1
                    
                    for severity, count in severity_counts.items():
                        emoji = {
                            'critical': '🔴',
                            'major': '🟠',
                            'minor': '🟡', 
                            'info': '🔵'
                        }.get(severity, '⚪')
                        print(f"    {emoji} {severity.upper()}: {count}")
                
                print()
                
            except Exception as e:
                print(f"  ❌ Analysis failed: {e}")
                print()
        else:
            print(f"⚠️  Sample file not found: {sample_file}")
    
    return True


def demo_configuration():
    """Demonstrate configuration management."""
    print("⚙️  Configuration Management Demo")
    print("-" * 40)
    
    # Create default config file
    config_file = "demo_config.yaml"
    print(f"Creating default configuration: {config_file}")
    
    try:
        create_default_config_file(config_file)
        print("✅ Configuration file created")
        
        # Load and display config
        config = AnalyzerConfig.from_file(config_file)
        print(f"✅ Configuration loaded successfully")
        print(f"   Standards: {[s.value for s in config.get_enabled_standards()]}")
        print(f"   Rules: {len(config.get_enabled_rules())} enabled")
        print(f"   AI Assistant: {'Enabled' if config.is_ai_enabled() else 'Disabled'}")
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
    
    print()


def demo_detailed_violation_analysis():
    """Show detailed violation information."""
    print("🔬 Detailed Violation Analysis")
    print("-" * 40)
    
    analyzer = create_default_analyzer()
    
    # Analyze the violations sample
    if os.path.exists("samples/test_violations.c"):
        try:
            report = analyzer.analyze_files(["samples/test_violations.c"])
            
            if report.violations:
                print(f"Found {len(report.violations)} violations:")
                print()
                
                for i, violation in enumerate(report.violations[:3], 1):  # Show first 3
                    print(f"Violation #{i}:")
                    print(f"  Rule: {violation.rule_id}")
                    print(f"  Standard: {violation.standard.value}")
                    print(f"  Severity: {violation.severity.value}")
                    print(f"  Location: {violation.location.file_path}:{violation.location.line}:{violation.location.column}")
                    print(f"  Message: {violation.message}")
                    
                    if violation.source_context:
                        print(f"  Code: {violation.source_context.strip()}")
                    
                    # Show AI fields if available (they won't be without OpenAI key)
                    if violation.ai_explanation:
                        print(f"  💡 Explanation: {violation.ai_explanation[:100]}...")
                    
                    print()
                
                if len(report.violations) > 3:
                    print(f"... and {len(report.violations) - 3} more violations")
                
        except Exception as e:
            print(f"❌ Detailed analysis failed: {e}")
    
    print()


def demo_json_output():
    """Demonstrate JSON output format."""
    print("📄 JSON Output Format Demo")
    print("-" * 40)
    
    if os.path.exists("samples/sample_output.json"):
        print("Sample JSON output format:")
        try:
            with open("samples/sample_output.json", 'r') as f:
                data = json.load(f)
            
            print(f"  Total violations: {data['summary']['total_violations']}")
            print(f"  Standards: {list(data['summary']['by_standard'].keys())}")
            print(f"  Severity breakdown:")
            for severity, count in data['summary']['by_severity'].items():
                if count > 0:
                    print(f"    {severity}: {count}")
            
            print(f"  AI enhancements: {'Yes' if data['metadata']['config']['ai_enabled'] else 'No'}")
            
        except Exception as e:
            print(f"❌ Failed to read sample output: {e}")
    else:
        print("⚠️  Sample output file not found")
    
    print()


def main():
    """Run the complete demonstration."""
    print("Static Code Analysis Framework for Embedded C/C++")
    print("Version 1.0.0 - Production Quality")
    print()
    
    success = True
    
    try:
        # Basic analysis demo
        success &= demo_basic_analysis()
        
        # Configuration demo
        demo_configuration()
        
        # Detailed analysis
        demo_detailed_violation_analysis()
        
        # JSON output format
        demo_json_output()
        
        print("=" * 60)
        if success:
            print("✅ DEMONSTRATION COMPLETED SUCCESSFULLY")
            print()
            print("Next steps:")
            print("1. Install libclang: pip install libclang")
            print("2. Run: python -m static_analyzer.cli analyze --path your_code/")
            print("3. Configure CI/CD using .github/workflows/static-analysis.yml")
            print("4. Set up deviations using samples/deviations.yaml")
        else:
            print("⚠️  DEMONSTRATION COMPLETED WITH ISSUES")
            print("Please check error messages above and ensure dependencies are installed")
        
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
