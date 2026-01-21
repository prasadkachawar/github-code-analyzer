"""
MCP Server for GitHub Integration with Static Analysis Framework
Provides tools for LLMs to analyze commits and generate reports
"""

import asyncio
import json
import os
import tempfile
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

# MCP imports
from mcp.server import Server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
import mcp.server.stdio
import mcp.types as types

# Static analyzer imports
import sys
sys.path.append(str(Path(__file__).parent.parent))
from static_analyzer import StaticAnalyzer, AnalyzerConfig
from static_analyzer.cli import main as cli_main

app = Server("static-analysis-github-mcp")

# Configuration
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
EMAIL_CONFIG = {
    "smtp_server": os.environ.get("SMTP_SERVER", "smtp.gmail.com"),
    "smtp_port": int(os.environ.get("SMTP_PORT", "587")),
    "email_user": os.environ.get("EMAIL_USER"),
    "email_password": os.environ.get("EMAIL_PASSWORD"),
    "from_email": os.environ.get("FROM_EMAIL")
}

@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available tools for GitHub commit analysis."""
    return [
        Tool(
            name="analyze_commit_changes",
            description="Analyze C/C++ code changes in a GitHub commit for MISRA/CERT violations",
            inputSchema={
                "type": "object",
                "properties": {
                    "repo_url": {
                        "type": "string",
                        "description": "GitHub repository URL (e.g., https://github.com/owner/repo)"
                    },
                    "commit_sha": {
                        "type": "string", 
                        "description": "Git commit SHA to analyze"
                    },
                    "changed_files": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of changed C/C++ files to analyze"
                    },
                    "commit_author": {
                        "type": "string",
                        "description": "Commit author name"
                    },
                    "commit_author_email": {
                        "type": "string", 
                        "description": "Commit author email"
                    },
                    "commit_message": {
                        "type": "string",
                        "description": "Commit message"
                    },
                    "standards": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Standards to check (MISRA, CERT)",
                        "default": ["MISRA", "CERT"]
                    },
                    "config_file": {
                        "type": "string",
                        "description": "Path to analyzer config file (optional)"
                    }
                },
                "required": ["repo_url", "commit_sha", "changed_files", "commit_author_email"]
            }
        ),
        
        Tool(
            name="generate_analysis_report",
            description="Generate comprehensive analysis report with AI explanations",
            inputSchema={
                "type": "object",
                "properties": {
                    "analysis_results": {
                        "type": "object",
                        "description": "Raw analysis results from static analyzer"
                    },
                    "commit_info": {
                        "type": "object", 
                        "description": "Commit metadata (author, message, sha, etc.)"
                    },
                    "include_ai_explanations": {
                        "type": "boolean",
                        "description": "Include AI-generated explanations",
                        "default": True
                    },
                    "report_format": {
                        "type": "string",
                        "enum": ["html", "markdown", "json"],
                        "description": "Report output format",
                        "default": "html"
                    }
                },
                "required": ["analysis_results", "commit_info"]
            }
        ),
        
        Tool(
            name="send_analysis_email",
            description="Send analysis report via email to commit author",
            inputSchema={
                "type": "object", 
                "properties": {
                    "recipient_email": {
                        "type": "string",
                        "description": "Email address to send report to"
                    },
                    "recipient_name": {
                        "type": "string",
                        "description": "Recipient name"
                    },
                    "report_content": {
                        "type": "string",
                        "description": "HTML or markdown report content"
                    },
                    "commit_sha": {
                        "type": "string",
                        "description": "Git commit SHA"
                    },
                    "repo_name": {
                        "type": "string", 
                        "description": "Repository name"
                    },
                    "violation_count": {
                        "type": "integer",
                        "description": "Total number of violations found"
                    },
                    "severity_summary": {
                        "type": "object",
                        "description": "Summary of violations by severity"
                    }
                },
                "required": ["recipient_email", "report_content", "commit_sha", "repo_name"]
            }
        ),
        
        Tool(
            name="clone_and_analyze_repository", 
            description="Clone GitHub repository and analyze specific files",
            inputSchema={
                "type": "object",
                "properties": {
                    "repo_url": {
                        "type": "string",
                        "description": "GitHub repository URL"
                    },
                    "branch_or_commit": {
                        "type": "string", 
                        "description": "Branch name or commit SHA to checkout",
                        "default": "main"
                    },
                    "files_to_analyze": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Specific files to analyze (relative paths)"
                    },
                    "analysis_config": {
                        "type": "object",
                        "description": "Analysis configuration overrides"
                    }
                },
                "required": ["repo_url"]
            }
        ),
        
        Tool(
            name="compare_with_baseline",
            description="Compare current analysis with baseline to find new violations",
            inputSchema={
                "type": "object",
                "properties": {
                    "current_results": {
                        "type": "object", 
                        "description": "Current analysis results"
                    },
                    "baseline_results": {
                        "type": "object",
                        "description": "Baseline analysis results (e.g., from main branch)"
                    },
                    "commit_sha": {
                        "type": "string",
                        "description": "Current commit SHA"
                    },
                    "baseline_sha": {
                        "type": "string", 
                        "description": "Baseline commit SHA"
                    }
                },
                "required": ["current_results", "baseline_results"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[types.Content]:
    """Handle tool calls from LLM."""
    
    if name == "analyze_commit_changes":
        return await analyze_commit_changes(**arguments)
    elif name == "generate_analysis_report":
        return await generate_analysis_report(**arguments)
    elif name == "send_analysis_email":
        return await send_analysis_email(**arguments)
    elif name == "clone_and_analyze_repository":
        return await clone_and_analyze_repository(**arguments)
    elif name == "compare_with_baseline":
        return await compare_with_baseline(**arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")

async def analyze_commit_changes(
    repo_url: str,
    commit_sha: str, 
    changed_files: List[str],
    commit_author_email: str,
    commit_author: str = "Unknown",
    commit_message: str = "",
    standards: List[str] = ["MISRA", "CERT"],
    config_file: Optional[str] = None
) -> List[types.Content]:
    """Analyze C/C++ code changes in a GitHub commit."""
    
    try:
        # Filter for C/C++ files only
        c_cpp_extensions = {'.c', '.cpp', '.cc', '.cxx', '.h', '.hpp', '.hh', '.hxx'}
        cpp_files = [f for f in changed_files if any(f.endswith(ext) for ext in c_cpp_extensions)]
        
        if not cpp_files:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "status": "skipped",
                    "message": "No C/C++ files found in commit changes",
                    "commit_sha": commit_sha,
                    "changed_files": changed_files
                }, indent=2)
            )]
        
        # Create temporary directory for analysis
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_dir = os.path.join(temp_dir, "repo")
            
            # Clone repository
            clone_cmd = [
                "git", "clone", "--depth", "1", 
                "--branch", "main",  # We'll checkout specific commit after
                repo_url, repo_dir
            ]
            
            # Handle GitHub token authentication
            if GITHUB_TOKEN:
                # Modify URL to include token
                if "github.com" in repo_url:
                    auth_url = repo_url.replace("https://", f"https://{GITHUB_TOKEN}@")
                    clone_cmd[5] = auth_url
            
            subprocess.run(clone_cmd, check=True, capture_output=True, text=True)
            
            # Checkout specific commit
            subprocess.run(
                ["git", "checkout", commit_sha], 
                cwd=repo_dir, 
                check=True, 
                capture_output=True, 
                text=True
            )
            
            # Prepare file paths for analysis
            files_to_analyze = []
            for file_path in cpp_files:
                full_path = os.path.join(repo_dir, file_path)
                if os.path.exists(full_path):
                    files_to_analyze.append(full_path)
            
            if not files_to_analyze:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "status": "error",
                        "message": "None of the changed C/C++ files exist in the repository",
                        "commit_sha": commit_sha,
                        "searched_files": cpp_files
                    }, indent=2)
                )]
            
            # Create analyzer configuration
            if config_file and os.path.exists(os.path.join(repo_dir, config_file)):
                config = AnalyzerConfig.from_file(os.path.join(repo_dir, config_file))
            else:
                config = AnalyzerConfig.create_default()
                # Override with specified standards
                config.config["standards"] = standards
            
            # Create analyzer and run analysis
            analyzer = StaticAnalyzer(config)
            report = analyzer.analyze_files(files_to_analyze)
            
            # Prepare results
            results = {
                "status": "success",
                "commit_info": {
                    "sha": commit_sha,
                    "author": commit_author,
                    "author_email": commit_author_email,
                    "message": commit_message,
                    "repository": repo_url
                },
                "analysis_metadata": {
                    "analyzed_files": [os.path.relpath(f, repo_dir) for f in files_to_analyze],
                    "total_files": len(files_to_analyze),
                    "standards_checked": standards,
                    "analysis_timestamp": datetime.now().isoformat()
                },
                "violations": [v.to_dict() for v in report.violations],
                "summary": report.summary if hasattr(report, 'summary') else {
                    "total_violations": len(report.violations),
                    "by_severity": _count_by_severity(report.violations),
                    "by_standard": _count_by_standard(report.violations),
                    "files_analyzed": len(files_to_analyze)
                }
            }
            
            return [TextContent(
                type="text", 
                text=json.dumps(results, indent=2)
            )]
            
    except subprocess.CalledProcessError as e:
        return [TextContent(
            type="text",
            text=json.dumps({
                "status": "error",
                "message": f"Git operation failed: {e.stderr if e.stderr else str(e)}",
                "commit_sha": commit_sha
            }, indent=2)
        )]
    
    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({
                "status": "error", 
                "message": f"Analysis failed: {str(e)}",
                "commit_sha": commit_sha
            }, indent=2)
        )]

async def generate_analysis_report(
    analysis_results: Dict[str, Any],
    commit_info: Dict[str, Any],
    include_ai_explanations: bool = True,
    report_format: str = "html"
) -> List[types.Content]:
    """Generate comprehensive analysis report."""
    
    try:
        if analysis_results.get("status") != "success":
            error_msg = analysis_results.get("message", "Unknown analysis error")
            return [TextContent(
                type="text",
                text=f"Cannot generate report: {error_msg}"
            )]
        
        violations = analysis_results.get("violations", [])
        summary = analysis_results.get("summary", {})
        
        if report_format == "html":
            report_content = _generate_html_report(
                violations, summary, commit_info, include_ai_explanations
            )
        elif report_format == "markdown":
            report_content = _generate_markdown_report(
                violations, summary, commit_info, include_ai_explanations
            )
        else:  # json
            report_content = json.dumps({
                "report_metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "commit_info": commit_info,
                    "include_ai_explanations": include_ai_explanations
                },
                "summary": summary,
                "violations": violations
            }, indent=2)
        
        return [TextContent(
            type="text",
            text=report_content
        )]
        
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Report generation failed: {str(e)}"
        )]

async def send_analysis_email(
    recipient_email: str,
    report_content: str,
    commit_sha: str,
    repo_name: str,
    recipient_name: str = "Developer",
    violation_count: int = 0,
    severity_summary: Optional[Dict] = None
) -> List[types.Content]:
    """Send analysis report via email."""
    
    try:
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from email.mime.base import MIMEBase
        from email import encoders
        
        if not all([EMAIL_CONFIG["email_user"], EMAIL_CONFIG["email_password"], EMAIL_CONFIG["from_email"]]):
            return [TextContent(
                type="text",
                text=json.dumps({
                    "status": "error",
                    "message": "Email configuration incomplete. Please set EMAIL_USER, EMAIL_PASSWORD, and FROM_EMAIL environment variables."
                })
            )]
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = EMAIL_CONFIG["from_email"]
        msg['To'] = recipient_email
        
        # Determine subject based on violations
        if violation_count == 0:
            subject = f"✅ Static Analysis: No violations - {repo_name} ({commit_sha[:8]})"
        elif violation_count <= 5:
            subject = f"⚠️ Static Analysis: {violation_count} violations - {repo_name} ({commit_sha[:8]})"
        else:
            subject = f"🚨 Static Analysis: {violation_count} violations - {repo_name} ({commit_sha[:8]})"
            
        msg['Subject'] = subject
        
        # Create email body
        email_body = f"""
        <html>
        <body>
        <h2>Static Analysis Report</h2>
        <p>Hello {recipient_name},</p>
        
        <p>This is an automated static analysis report for your recent commit:</p>
        
        <ul>
        <li><strong>Repository:</strong> {repo_name}</li>
        <li><strong>Commit:</strong> {commit_sha}</li>
        <li><strong>Total Violations:</strong> {violation_count}</li>
        </ul>
        
        {_format_severity_summary_html(severity_summary) if severity_summary else ""}
        
        <hr>
        
        {report_content}
        
        <hr>
        <p><em>This report was generated automatically by the Static Analysis Framework.</em></p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(email_body, 'html'))
        
        # Send email
        server = smtplib.SMTP(EMAIL_CONFIG["smtp_server"], EMAIL_CONFIG["smtp_port"])
        server.starttls()
        server.login(EMAIL_CONFIG["email_user"], EMAIL_CONFIG["email_password"])
        
        text = msg.as_string()
        server.sendmail(EMAIL_CONFIG["from_email"], recipient_email, text)
        server.quit()
        
        return [TextContent(
            type="text",
            text=json.dumps({
                "status": "success",
                "message": f"Analysis report sent to {recipient_email}",
                "subject": subject,
                "violation_count": violation_count
            }, indent=2)
        )]
        
    except Exception as e:
        return [TextContent(
            type="text", 
            text=json.dumps({
                "status": "error",
                "message": f"Failed to send email: {str(e)}"
            }, indent=2)
        )]

async def clone_and_analyze_repository(
    repo_url: str,
    branch_or_commit: str = "main",
    files_to_analyze: Optional[List[str]] = None,
    analysis_config: Optional[Dict] = None
) -> List[types.Content]:
    """Clone repository and analyze specified files."""
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_dir = os.path.join(temp_dir, "repo")
            
            # Clone repository
            clone_cmd = ["git", "clone", "--depth", "10", repo_url, repo_dir]
            if GITHUB_TOKEN and "github.com" in repo_url:
                auth_url = repo_url.replace("https://", f"https://{GITHUB_TOKEN}@")
                clone_cmd[3] = auth_url
            
            subprocess.run(clone_cmd, check=True, capture_output=True, text=True)
            
            # Checkout specific branch/commit
            subprocess.run(
                ["git", "checkout", branch_or_commit],
                cwd=repo_dir,
                check=True,
                capture_output=True,
                text=True
            )
            
            # Determine files to analyze
            if files_to_analyze:
                full_paths = [os.path.join(repo_dir, f) for f in files_to_analyze]
                existing_files = [f for f in full_paths if os.path.exists(f)]
            else:
                # Find all C/C++ files
                c_cpp_extensions = {'.c', '.cpp', '.cc', '.cxx', '.h', '.hpp', '.hh', '.hxx'}
                existing_files = []
                for root, dirs, files in os.walk(repo_dir):
                    # Skip .git directory
                    if '.git' in dirs:
                        dirs.remove('.git')
                    for file in files:
                        if any(file.endswith(ext) for ext in c_cpp_extensions):
                            existing_files.append(os.path.join(root, file))
            
            if not existing_files:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "status": "skipped",
                        "message": "No C/C++ files found for analysis"
                    })
                )]
            
            # Create analyzer configuration
            if analysis_config:
                config = AnalyzerConfig(analysis_config)
            else:
                config = AnalyzerConfig.create_default()
            
            # Run analysis
            analyzer = StaticAnalyzer(config)
            report = analyzer.analyze_files(existing_files)
            
            # Prepare results
            results = {
                "status": "success",
                "repository": repo_url,
                "branch_or_commit": branch_or_commit,
                "analyzed_files": [os.path.relpath(f, repo_dir) for f in existing_files],
                "violations": [v.to_dict() for v in report.violations],
                "summary": {
                    "total_violations": len(report.violations),
                    "by_severity": _count_by_severity(report.violations),
                    "by_standard": _count_by_standard(report.violations),
                    "files_analyzed": len(existing_files)
                },
                "analysis_timestamp": datetime.now().isoformat()
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(results, indent=2)
            )]
            
    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({
                "status": "error",
                "message": f"Repository analysis failed: {str(e)}"
            })
        )]

async def compare_with_baseline(
    current_results: Dict[str, Any],
    baseline_results: Dict[str, Any], 
    commit_sha: str = "unknown",
    baseline_sha: str = "unknown"
) -> List[types.Content]:
    """Compare current analysis with baseline to find new violations."""
    
    try:
        current_violations = current_results.get("violations", [])
        baseline_violations = baseline_results.get("violations", [])
        
        # Create signature sets for comparison
        def create_signature(violation):
            return (
                violation["rule_id"],
                violation["location"]["file_path"],
                violation["location"]["line"],
                violation["location"]["column"]
            )
        
        baseline_signatures = {create_signature(v) for v in baseline_violations}
        
        # Find new violations
        new_violations = []
        for violation in current_violations:
            if create_signature(violation) not in baseline_signatures:
                new_violations.append(violation)
        
        # Find fixed violations
        current_signatures = {create_signature(v) for v in current_violations}
        fixed_violations = []
        for violation in baseline_violations:
            if create_signature(violation) not in current_signatures:
                fixed_violations.append(violation)
        
        comparison_results = {
            "status": "success",
            "commit_comparison": {
                "current_sha": commit_sha,
                "baseline_sha": baseline_sha
            },
            "summary": {
                "total_current": len(current_violations),
                "total_baseline": len(baseline_violations),
                "new_violations": len(new_violations),
                "fixed_violations": len(fixed_violations),
                "net_change": len(new_violations) - len(fixed_violations)
            },
            "new_violations": new_violations,
            "fixed_violations": fixed_violations,
            "comparison_timestamp": datetime.now().isoformat()
        }
        
        return [TextContent(
            type="text",
            text=json.dumps(comparison_results, indent=2)
        )]
        
    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({
                "status": "error",
                "message": f"Baseline comparison failed: {str(e)}"
            })
        )]

# Helper functions
def _count_by_severity(violations):
    """Count violations by severity."""
    counts = {"critical": 0, "major": 0, "minor": 0, "info": 0}
    for violation in violations:
        severity = violation.get("severity", "unknown")
        if severity in counts:
            counts[severity] += 1
    return counts

def _count_by_standard(violations):
    """Count violations by standard."""
    counts = {"MISRA": 0, "CERT": 0}
    for violation in violations:
        standard = violation.get("standard", "unknown")
        if standard in counts:
            counts[standard] += 1
    return counts

def _generate_html_report(violations, summary, commit_info, include_ai_explanations):
    """Generate HTML report."""
    html = f"""
    <h3>Static Analysis Results</h3>
    <p><strong>Total Violations:</strong> {summary.get('total_violations', 0)}</p>
    
    <h4>Summary by Severity:</h4>
    <ul>
    """
    
    for severity, count in summary.get('by_severity', {}).items():
        if count > 0:
            emoji = {"critical": "🔴", "major": "🟠", "minor": "🟡", "info": "🔵"}.get(severity, "⚪")
            html += f"<li>{emoji} {severity.upper()}: {count}</li>"
    
    html += "</ul>"
    
    if violations:
        html += "<h4>Violations:</h4>"
        for i, violation in enumerate(violations[:10], 1):  # Show first 10
            html += f"""
            <div style="border: 1px solid #ddd; margin: 10px 0; padding: 10px;">
                <h5>#{i}: {violation['rule_id']}</h5>
                <p><strong>File:</strong> {violation['location']['file_path']}:{violation['location']['line']}</p>
                <p><strong>Message:</strong> {violation['message']}</p>
                {f"<p><strong>AI Explanation:</strong> {violation.get('ai_explanation', '')}</p>" if include_ai_explanations and violation.get('ai_explanation') else ""}
            </div>
            """
        
        if len(violations) > 10:
            html += f"<p><em>... and {len(violations) - 10} more violations</em></p>"
    
    return html

def _generate_markdown_report(violations, summary, commit_info, include_ai_explanations):
    """Generate Markdown report."""
    md = f"""
# Static Analysis Report

**Total Violations:** {summary.get('total_violations', 0)}

## Summary by Severity:
"""
    
    for severity, count in summary.get('by_severity', {}).items():
        if count > 0:
            emoji = {"critical": "🔴", "major": "🟠", "minor": "🟡", "info": "🔵"}.get(severity, "⚪")
            md += f"- {emoji} {severity.upper()}: {count}\n"
    
    if violations:
        md += "\n## Violations:\n"
        for i, violation in enumerate(violations[:10], 1):
            md += f"""
### #{i}: {violation['rule_id']}

- **File:** {violation['location']['file_path']}:{violation['location']['line']}
- **Message:** {violation['message']}
"""
            if include_ai_explanations and violation.get('ai_explanation'):
                md += f"- **AI Explanation:** {violation['ai_explanation']}\n"
        
        if len(violations) > 10:
            md += f"\n*... and {len(violations) - 10} more violations*\n"
    
    return md

def _format_severity_summary_html(severity_summary):
    """Format severity summary for email."""
    if not severity_summary:
        return ""
    
    html = "<h4>Violation Summary:</h4><ul>"
    for severity, count in severity_summary.items():
        if count > 0:
            emoji = {"critical": "🔴", "major": "🟠", "minor": "🟡", "info": "🔵"}.get(severity, "⚪")
            html += f"<li>{emoji} {severity.upper()}: {count}</li>"
    html += "</ul>"
    return html

async def main():
    """Run the MCP server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
