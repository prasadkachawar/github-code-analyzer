"""
Example LLM Integration Script
Shows how to use the static analysis framework as MCP tools with Claude or other LLMs
"""

import json
import os
import asyncio
import tempfile
from datetime import datetime
from pathlib import Path

# Add parent directory to path for static analyzer imports
import sys
sys.path.append(str(Path(__file__).parent.parent))

from static_analyzer import StaticAnalyzer, AnalyzerConfig
from static_analyzer.models import Standard

class StaticAnalysisMCPTools:
    """MCP-style tools for LLM integration with static analysis."""
    
    def __init__(self):
        """Initialize the tools."""
        self.analyzer = None
        self.temp_dirs = []
    
    async def analyze_github_commit(self, 
                                  repo_url: str, 
                                  commit_sha: str,
                                  changed_files: list,
                                  author_email: str,
                                  author_name: str = "Developer") -> dict:
        """
        Analyze C/C++ files from a GitHub commit.
        
        This tool clones the repository, checks out the specific commit,
        and runs static analysis on the changed C/C++ files.
        """
        
        try:
            # Create temporary directory
            temp_dir = tempfile.mkdtemp()
            self.temp_dirs.append(temp_dir)
            
            # Clone repository (simplified - in real implementation would use git library)
            import subprocess
            repo_dir = os.path.join(temp_dir, "repo")
            
            # Clone with authentication if needed
            clone_cmd = ["git", "clone", "--depth", "1", repo_url, repo_dir]
            subprocess.run(clone_cmd, check=True, capture_output=True)
            
            # Checkout specific commit
            subprocess.run(["git", "checkout", commit_sha], cwd=repo_dir, check=True)
            
            # Filter for C/C++ files
            c_cpp_extensions = {'.c', '.cpp', '.cc', '.cxx', '.h', '.hpp', '.hh', '.hxx'}
            cpp_files = [f for f in changed_files if any(f.endswith(ext) for ext in c_cpp_extensions)]
            
            if not cpp_files:
                return {
                    "status": "skipped",
                    "message": "No C/C++ files found in commit",
                    "commit_sha": commit_sha
                }
            
            # Prepare full file paths
            files_to_analyze = []
            for file_path in cpp_files:
                full_path = os.path.join(repo_dir, file_path)
                if os.path.exists(full_path):
                    files_to_analyze.append(full_path)
            
            # Create analyzer and run analysis
            config = AnalyzerConfig.create_default()
            analyzer = StaticAnalyzer(config)
            report = analyzer.analyze_files(files_to_analyze)
            
            # Prepare results in MCP-friendly format
            results = {
                "status": "success",
                "commit_info": {
                    "sha": commit_sha,
                    "author_name": author_name,
                    "author_email": author_email,
                    "repository": repo_url
                },
                "analysis_summary": {
                    "total_violations": len(report.violations),
                    "analyzed_files": [os.path.basename(f) for f in files_to_analyze],
                    "standards_checked": ["MISRA", "CERT"],
                    "timestamp": datetime.now().isoformat()
                },
                "violations": [
                    {
                        "rule_id": v.rule_id,
                        "standard": v.standard.value,
                        "severity": v.severity.value,
                        "location": {
                            "file": os.path.basename(v.location.file_path),
                            "line": v.location.line,
                            "column": v.location.column
                        },
                        "message": v.message,
                        "source_context": v.source_context
                    }
                    for v in report.violations
                ],
                "severity_counts": {
                    "critical": len([v for v in report.violations if v.severity.value == "critical"]),
                    "major": len([v for v in report.violations if v.severity.value == "major"]),
                    "minor": len([v for v in report.violations if v.severity.value == "minor"]),
                    "info": len([v for v in report.violations if v.severity.value == "info"])
                }
            }
            
            return results
            
        except subprocess.CalledProcessError as e:
            return {
                "status": "error",
                "message": f"Git operation failed: {e}",
                "commit_sha": commit_sha
            }
        except Exception as e:
            return {
                "status": "error", 
                "message": f"Analysis failed: {e}",
                "commit_sha": commit_sha
            }
    
    async def generate_report_email(self, 
                                  analysis_results: dict,
                                  recipient_email: str,
                                  recipient_name: str = "Developer") -> dict:
        """
        Generate and send an email report based on static analysis results.
        
        This tool creates a comprehensive HTML email report with:
        - Executive summary
        - Detailed violation listings
        - Severity breakdown
        - Recommendations
        """
        
        try:
            if analysis_results.get("status") != "success":
                return {
                    "status": "error",
                    "message": f"Cannot generate report: {analysis_results.get('message', 'Unknown error')}"
                }
            
            violations = analysis_results.get("violations", [])
            severity_counts = analysis_results.get("severity_counts", {})
            commit_info = analysis_results.get("commit_info", {})
            
            # Generate HTML email content
            html_content = self._generate_html_email_report(
                violations, severity_counts, commit_info, recipient_name
            )
            
            # In a real implementation, this would send via SMTP
            # For now, we'll save to file and return the content
            
            email_report = {
                "status": "success",
                "recipient": recipient_email,
                "subject": self._generate_email_subject(severity_counts, commit_info),
                "html_content": html_content,
                "summary": {
                    "total_violations": len(violations),
                    "severity_breakdown": severity_counts
                },
                "timestamp": datetime.now().isoformat()
            }
            
            # Save report to file for review
            report_file = f"analysis_report_{commit_info.get('sha', 'unknown')[:8]}.html"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            email_report["report_file_saved"] = report_file
            
            return email_report
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Report generation failed: {e}"
            }
    
    async def compare_with_baseline(self, 
                                  current_analysis: dict,
                                  baseline_commit_sha: str,
                                  repo_url: str) -> dict:
        """
        Compare current analysis results with a baseline (e.g., main branch).
        
        This helps identify new violations introduced in the current commit.
        """
        
        try:
            # In a real implementation, this would:
            # 1. Fetch baseline analysis from storage or run fresh analysis
            # 2. Compare violation signatures
            # 3. Identify new, fixed, and persistent violations
            
            # For demonstration, we'll simulate a baseline comparison
            current_violations = current_analysis.get("violations", [])
            
            # Simulate baseline with some violations
            baseline_violations = [
                {
                    "rule_id": "MISRA-C-2012-8.7",
                    "location": {"file": "main.c", "line": 10},
                    "message": "Existing violation"
                }
            ]
            
            # Find new violations (simplified comparison)
            def violation_signature(v):
                return (v["rule_id"], v["location"]["file"], v["location"]["line"])
            
            baseline_sigs = {violation_signature(v) for v in baseline_violations}
            new_violations = [v for v in current_violations 
                            if violation_signature(v) not in baseline_sigs]
            
            comparison_result = {
                "status": "success", 
                "baseline_commit": baseline_commit_sha,
                "current_commit": current_analysis.get("commit_info", {}).get("sha"),
                "comparison_summary": {
                    "baseline_violations": len(baseline_violations),
                    "current_violations": len(current_violations),
                    "new_violations": len(new_violations),
                    "net_change": len(current_violations) - len(baseline_violations)
                },
                "new_violations": new_violations,
                "regression_detected": len(new_violations) > 0
            }
            
            return comparison_result
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Baseline comparison failed: {e}"
            }
    
    def _generate_html_email_report(self, violations, severity_counts, commit_info, recipient_name):
        """Generate HTML email report content."""
        
        total_violations = len(violations)
        commit_sha = commit_info.get("sha", "unknown")[:8]
        repo_name = commit_info.get("repository", "").split("/")[-1] if commit_info.get("repository") else "unknown"
        
        # Determine overall status
        if total_violations == 0:
            status_emoji = "✅"
            status_text = "Clean Code - No Violations"
            status_color = "#28a745"
        elif severity_counts.get("critical", 0) > 0:
            status_emoji = "🚨"  
            status_text = "Critical Issues Found"
            status_color = "#dc3545"
        elif severity_counts.get("major", 0) > 0:
            status_emoji = "⚠️"
            status_text = "Major Issues Found"
            status_color = "#fd7e14"
        else:
            status_emoji = "🟡"
            status_text = "Minor Issues Found"
            status_color = "#ffc107"
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Static Analysis Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f6f8fa; }}
        .container {{ max-width: 800px; margin: 0 auto; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .header {{ background: {status_color}; color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
        .content {{ padding: 20px; }}
        .summary {{ background: #f8f9fa; padding: 15px; border-radius: 6px; margin: 15px 0; }}
        .violation {{ border-left: 4px solid #dc3545; margin: 10px 0; padding: 10px; background: #f8f9fa; }}
        .violation.major {{ border-left-color: #fd7e14; }}
        .violation.minor {{ border-left-color: #ffc107; }}
        .violation.info {{ border-left-color: #17a2b8; }}
        .severity-badge {{ display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 12px; font-weight: bold; }}
        .severity-critical {{ background: #dc3545; color: white; }}
        .severity-major {{ background: #fd7e14; color: white; }}
        .severity-minor {{ background: #ffc107; color: black; }}
        .severity-info {{ background: #17a2b8; color: white; }}
        .footer {{ border-top: 1px solid #e1e4e8; padding: 15px; color: #6a737d; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{status_emoji} {status_text}</h1>
            <p>Static Analysis Report for {repo_name} (commit {commit_sha})</p>
        </div>
        
        <div class="content">
            <p>Hello {recipient_name},</p>
            <p>Your recent commit has been automatically analyzed for MISRA C:2012 and CERT C/C++ compliance.</p>
            
            <div class="summary">
                <h3>📊 Summary</h3>
                <ul>
                    <li><strong>Total Violations:</strong> {total_violations}</li>
                    <li><strong>Critical:</strong> {severity_counts.get('critical', 0)}</li>
                    <li><strong>Major:</strong> {severity_counts.get('major', 0)}</li>
                    <li><strong>Minor:</strong> {severity_counts.get('minor', 0)}</li>
                    <li><strong>Info:</strong> {severity_counts.get('info', 0)}</li>
                </ul>
            </div>
        """
        
        if violations:
            html += "<h3>🔍 Detailed Violations</h3>"
            
            # Group violations by severity
            for severity in ["critical", "major", "minor", "info"]:
                sev_violations = [v for v in violations if v["severity"] == severity]
                if not sev_violations:
                    continue
                
                html += f"<h4>{severity.upper()} ({len(sev_violations)})</h4>"
                
                for violation in sev_violations[:5]:  # Show first 5 of each severity
                    html += f"""
                    <div class="violation {severity}">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <strong>{violation['rule_id']}</strong>
                            <span class="severity-badge severity-{severity}">{severity.upper()}</span>
                        </div>
                        <p><strong>File:</strong> {violation['location']['file']}:{violation['location']['line']}</p>
                        <p><strong>Message:</strong> {violation['message']}</p>
                        {f"<p><strong>Code:</strong> <code>{violation['source_context']}</code></p>" if violation.get('source_context') else ""}
                    </div>
                    """
                
                if len(sev_violations) > 5:
                    html += f"<p><em>... and {len(sev_violations) - 5} more {severity} violations</em></p>"
        
        else:
            html += """
            <div style="text-align: center; padding: 40px;">
                <h2>🎉 Congratulations!</h2>
                <p>No static analysis violations found in your code.</p>
                <p>Your code meets MISRA C:2012 and CERT C/C++ standards.</p>
            </div>
            """
        
        html += """
        </div>
        
        <div class="footer">
            <p>This report was generated automatically by the Static Analysis Framework.</p>
            <p>For questions about violations, consult the MISRA C:2012 or CERT C/C++ documentation.</p>
        </div>
    </div>
</body>
</html>
        """
        
        return html
    
    def _generate_email_subject(self, severity_counts, commit_info):
        """Generate appropriate email subject line."""
        
        total = sum(severity_counts.values())
        repo_name = commit_info.get("repository", "").split("/")[-1] if commit_info.get("repository") else "repo"
        commit_sha = commit_info.get("sha", "unknown")[:8]
        
        if total == 0:
            return f"✅ Clean Code - {repo_name} ({commit_sha})"
        elif severity_counts.get("critical", 0) > 0:
            return f"🚨 Critical Issues - {repo_name} ({commit_sha}) - {total} violations"
        elif severity_counts.get("major", 0) > 0:
            return f"⚠️ Code Issues - {repo_name} ({commit_sha}) - {total} violations"  
        else:
            return f"🟡 Minor Issues - {repo_name} ({commit_sha}) - {total} violations"

# Example usage as MCP-style tool calls
async def example_llm_workflow():
    """Example of how an LLM would use these tools."""
    
    tools = StaticAnalysisMCPTools()
    
    # Simulate LLM receiving a commit notification and using tools
    print("🤖 LLM: I've received a GitHub commit notification. Let me analyze it...")
    
    # Step 1: Analyze the commit
    analysis_result = await tools.analyze_github_commit(
        repo_url="https://github.com/example/embedded-project.git",
        commit_sha="abc123def456",
        changed_files=["src/main.c", "src/utils.c", "include/config.h"],
        author_email="developer@company.com",
        author_name="John Developer"
    )
    
    print(f"📊 Analysis complete: {analysis_result['analysis_summary']['total_violations']} violations found")
    
    # Step 2: Generate and send report
    if analysis_result["status"] == "success":
        report_result = await tools.generate_report_email(
            analysis_results=analysis_result,
            recipient_email="developer@company.com",
            recipient_name="John Developer"
        )
        
        print(f"📧 Report generated and saved: {report_result.get('report_file_saved')}")
        
        # Step 3: Compare with baseline (optional)
        baseline_comparison = await tools.compare_with_baseline(
            current_analysis=analysis_result,
            baseline_commit_sha="main",
            repo_url="https://github.com/example/embedded-project.git"
        )
        
        if baseline_comparison["regression_detected"]:
            print(f"🔴 Regression detected: {baseline_comparison['comparison_summary']['new_violations']} new violations")
        else:
            print("✅ No regression detected")
    
    print("🎉 Automated analysis workflow complete!")

if __name__ == "__main__":
    # Run example workflow
    asyncio.run(example_llm_workflow())
