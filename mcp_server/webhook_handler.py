"""
GitHub Webhook Integration for Automatic Commit Analysis
Receives webhook events and triggers static analysis via MCP
"""

import json
import os
import asyncio
import logging
import hmac
import hashlib
from typing import Dict, Any, Optional
from datetime import datetime

# Web framework imports
from flask import Flask, request, jsonify
import requests

# GitHub API
from github import Github

# MCP Client (for calling our MCP server)
import subprocess
import tempfile

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Configuration
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
WEBHOOK_SECRET = os.environ.get("GITHUB_WEBHOOK_SECRET")
MCP_SERVER_PATH = os.path.join(os.path.dirname(__file__), "github_analyzer.py")

# LLM Configuration (for Claude/GPT integration)
LLM_CONFIG = {
    "provider": os.environ.get("LLM_PROVIDER", "anthropic"),  # anthropic, openai
    "api_key": os.environ.get("LLM_API_KEY"),
    "model": os.environ.get("LLM_MODEL", "claude-3-sonnet-20240229"),
}

def verify_webhook_signature(payload_body, signature_header):
    """Verify GitHub webhook signature."""
    if not WEBHOOK_SECRET:
        return True  # Skip verification if no secret set
    
    if not signature_header:
        return False
    
    hash_object = hmac.new(
        WEBHOOK_SECRET.encode('utf-8'),
        payload_body,
        hashlib.sha256
    )
    expected_signature = "sha256=" + hash_object.hexdigest()
    
    return hmac.compare_digest(expected_signature, signature_header)

@app.route('/webhook', methods=['POST'])
def github_webhook():
    """Handle GitHub webhook events."""
    
    # Verify signature
    signature = request.headers.get('X-Hub-Signature-256')
    if not verify_webhook_signature(request.get_data(), signature):
        return jsonify({"error": "Invalid signature"}), 401
    
    # Parse event
    event_type = request.headers.get('X-GitHub-Event')
    payload = request.get_json()
    
    if event_type == 'push':
        return handle_push_event(payload)
    elif event_type == 'pull_request':
        return handle_pull_request_event(payload)
    else:
        return jsonify({"message": f"Event {event_type} not handled"}), 200

def handle_push_event(payload: Dict[str, Any]) -> tuple:
    """Handle push events (commits to main branch)."""
    
    try:
        # Extract commit information
        commits = payload.get('commits', [])
        repository = payload.get('repository', {})
        repo_url = repository.get('clone_url', '')
        repo_name = repository.get('full_name', 'unknown/repo')
        
        # Filter for commits to main/master branch
        ref = payload.get('ref', '')
        if not (ref.endswith('/main') or ref.endswith('/master')):
            return jsonify({"message": "Not a main/master branch push"}), 200
        
        # Process each commit
        analysis_results = []
        for commit in commits:
            commit_sha = commit.get('id')
            commit_author = commit.get('author', {})
            commit_message = commit.get('message', '')
            
            # Get changed files
            added = commit.get('added', [])
            modified = commit.get('modified', []) 
            changed_files = added + modified
            
            # Filter for C/C++ files
            c_cpp_extensions = {'.c', '.cpp', '.cc', '.cxx', '.h', '.hpp', '.hh', '.hxx'}
            cpp_files = [f for f in changed_files if any(f.endswith(ext) for ext in c_cpp_extensions)]
            
            if not cpp_files:
                continue
            
            # Trigger analysis via LLM + MCP
            analysis_result = asyncio.run(trigger_llm_analysis(
                repo_url=repo_url,
                repo_name=repo_name,
                commit_sha=commit_sha,
                commit_author=commit_author.get('name', 'Unknown'),
                commit_author_email=commit_author.get('email', ''),
                commit_message=commit_message,
                changed_files=cpp_files,
                event_type='push'
            ))
            
            analysis_results.append(analysis_result)
        
        return jsonify({
            "message": f"Processed {len(analysis_results)} commits",
            "results": analysis_results
        }), 200
        
    except Exception as e:
        logging.error(f"Push event handling failed: {str(e)}")
        return jsonify({"error": str(e)}), 500

def handle_pull_request_event(payload: Dict[str, Any]) -> tuple:
    """Handle pull request events."""
    
    try:
        action = payload.get('action')
        if action not in ['opened', 'synchronize', 'reopened']:
            return jsonify({"message": f"PR action {action} not handled"}), 200
        
        pull_request = payload.get('pull_request', {})
        repository = payload.get('repository', {})
        
        # Extract PR information
        pr_number = pull_request.get('number')
        pr_title = pull_request.get('title', '')
        pr_author = pull_request.get('user', {}).get('login', 'unknown')
        repo_url = repository.get('clone_url', '')
        repo_name = repository.get('full_name', 'unknown/repo')
        
        # Get PR commits using GitHub API
        if GITHUB_TOKEN:
            g = Github(GITHUB_TOKEN)
            repo = g.get_repo(repo_name)
            pr = repo.get_pull(pr_number)
            
            # Get changed files
            changed_files = [f.filename for f in pr.get_files()]
            c_cpp_extensions = {'.c', '.cpp', '.cc', '.cxx', '.h', '.hpp', '.hh', '.hxx'}
            cpp_files = [f for f in changed_files if any(f.endswith(ext) for ext in c_cpp_extensions)]
            
            if not cpp_files:
                return jsonify({"message": "No C/C++ files changed in PR"}), 200
            
            # Get latest commit
            commits = list(pr.get_commits())
            if commits:
                latest_commit = commits[-1]
                commit_sha = latest_commit.sha
                
                # Trigger analysis
                analysis_result = asyncio.run(trigger_llm_analysis(
                    repo_url=repo_url,
                    repo_name=repo_name,
                    commit_sha=commit_sha,
                    commit_author=pr_author,
                    commit_author_email=pull_request.get('user', {}).get('email', ''),
                    commit_message=pr_title,
                    changed_files=cpp_files,
                    event_type='pull_request',
                    pr_number=pr_number
                ))
                
                return jsonify({
                    "message": f"Analyzed PR #{pr_number}",
                    "result": analysis_result
                }), 200
        
        return jsonify({"message": "GitHub token not configured"}), 200
        
    except Exception as e:
        logging.error(f"PR event handling failed: {str(e)}")
        return jsonify({"error": str(e)}), 500

async def trigger_llm_analysis(
    repo_url: str,
    repo_name: str, 
    commit_sha: str,
    commit_author: str,
    commit_author_email: str,
    commit_message: str,
    changed_files: list,
    event_type: str,
    pr_number: Optional[int] = None
) -> Dict[str, Any]:
    """Trigger LLM analysis using our static analysis MCP server."""
    
    try:
        # Create LLM prompt for analysis
        prompt = f"""
You are a senior software engineer responsible for code quality in embedded C/C++ projects.

A new {'commit' if event_type == 'push' else 'pull request'} has been made to the repository with C/C++ code changes:

**Repository:** {repo_name}
**Commit SHA:** {commit_sha}
**Author:** {commit_author} ({commit_author_email})
**Message:** {commit_message}
**Changed C/C++ Files:** {', '.join(changed_files)}

Your task is to:
1. Analyze the code changes for MISRA C:2012 and CERT C/C++ violations
2. Generate a comprehensive report with explanations
3. Send the report to the commit author via email

Use the static analysis MCP tools available to you:
- analyze_commit_changes: To analyze the specific commit
- generate_analysis_report: To create a detailed report  
- send_analysis_email: To email the report to the author

Please proceed with the analysis and report generation.
"""

        # Call LLM with MCP tools available
        if LLM_CONFIG["provider"] == "anthropic":
            result = await call_claude_with_mcp(prompt)
        elif LLM_CONFIG["provider"] == "openai":  
            result = await call_openai_with_mcp(prompt)
        else:
            raise ValueError(f"Unsupported LLM provider: {LLM_CONFIG['provider']}")
        
        return {
            "status": "success",
            "commit_sha": commit_sha,
            "analysis_triggered": True,
            "llm_result": result
        }
        
    except Exception as e:
        logging.error(f"LLM analysis failed: {str(e)}")
        return {
            "status": "error", 
            "commit_sha": commit_sha,
            "error": str(e)
        }

async def call_claude_with_mcp(prompt: str) -> str:
    """Call Claude with MCP tools for static analysis."""
    
    # This would integrate with Claude's MCP capabilities
    # For now, we'll simulate the MCP call directly
    
    try:
        # Start MCP server process
        mcp_process = subprocess.Popen(
            ['python', MCP_SERVER_PATH],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Create MCP request for analysis (simplified)
        mcp_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "analyze_commit_changes",
                "arguments": {
                    "repo_url": "https://github.com/example/repo.git", 
                    "commit_sha": "abc123",
                    "changed_files": ["src/main.c"],
                    "commit_author_email": "dev@example.com"
                }
            }
        }
        
        # Send request and get response
        stdout, stderr = mcp_process.communicate(json.dumps(mcp_request))
        
        if mcp_process.returncode != 0:
            raise Exception(f"MCP server error: {stderr}")
        
        return stdout
        
    except Exception as e:
        logging.error(f"Claude MCP call failed: {str(e)}")
        return f"Analysis failed: {str(e)}"

async def call_openai_with_mcp(prompt: str) -> str:
    """Call OpenAI with MCP tools for static analysis."""
    
    # Similar implementation for OpenAI
    # Would use OpenAI's function calling capabilities
    
    try:
        import openai
        
        client = openai.OpenAI(api_key=LLM_CONFIG["api_key"])
        
        # Define available functions (MCP tools)
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "analyze_commit_changes",
                    "description": "Analyze C/C++ code changes in a GitHub commit",
                    "parameters": {
                        "type": "object", 
                        "properties": {
                            "repo_url": {"type": "string"},
                            "commit_sha": {"type": "string"},
                            "changed_files": {"type": "array", "items": {"type": "string"}},
                            "commit_author_email": {"type": "string"}
                        }
                    }
                }
            }
        ]
        
        response = client.chat.completions.create(
            model=LLM_CONFIG["model"],
            messages=[{"role": "user", "content": prompt}],
            tools=tools,
            tool_choice="auto"
        )
        
        return response.choices[0].message.content or "Analysis completed"
        
    except Exception as e:
        logging.error(f"OpenAI MCP call failed: {str(e)}")
        return f"Analysis failed: {str(e)}"

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "mcp_server_available": os.path.exists(MCP_SERVER_PATH)
    })

@app.route('/trigger-analysis', methods=['POST'])
def manual_trigger():
    """Manual trigger endpoint for testing."""
    
    try:
        data = request.get_json()
        required_fields = ['repo_url', 'commit_sha', 'changed_files', 'author_email']
        
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400
        
        result = asyncio.run(trigger_llm_analysis(
            repo_url=data['repo_url'],
            repo_name=data.get('repo_name', 'manual/test'),
            commit_sha=data['commit_sha'],
            commit_author=data.get('author', 'Manual Trigger'),
            commit_author_email=data['author_email'],
            commit_message=data.get('message', 'Manual analysis trigger'),
            changed_files=data['changed_files'],
            event_type='manual'
        ))
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
