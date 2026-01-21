#!/usr/bin/env python3
"""
GitHub Static Analysis Web Interface
A web application for developers to analyze their GitHub repositories
"""

import os
import sys
import json
import re
import tempfile
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify, redirect, url_for
import requests
from urllib.parse import urlparse

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)

# Configuration
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')
MAX_FILES_TO_ANALYZE = 20
SUPPORTED_EXTENSIONS = ['.c', '.cpp', '.cc', '.cxx', '.h', '.hpp', '.hh', '.hxx']

def is_valid_github_url(url):
    """Validate GitHub repository URL"""
    pattern = r'^https://github\.com/[\w\-\.]+/[\w\-\.]+/?$'
    return re.match(pattern, url) is not None

def extract_repo_info(github_url):
    """Extract owner and repo name from GitHub URL"""
    # Remove .git suffix if present
    url = github_url.rstrip('/')
    if url.endswith('.git'):
        url = url[:-4]
    
    # Parse URL
    parsed = urlparse(url)
    path_parts = parsed.path.strip('/').split('/')
    
    if len(path_parts) >= 2:
        return path_parts[0], path_parts[1]
    return None, None

def clone_repository(repo_url, temp_dir, branch='main'):
    """Clone GitHub repository"""
    try:
        # Try main branch first, then master
        for default_branch in ['main', 'master']:
            try:
                cmd = ['git', 'clone', '--depth', '1', '--branch', default_branch, repo_url, temp_dir]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                if result.returncode == 0:
                    return True, default_branch
            except subprocess.TimeoutExpired:
                return False, "Timeout during clone"
            except Exception as e:
                continue
        
        # If both fail, try without specifying branch
        try:
            cmd = ['git', 'clone', '--depth', '1', repo_url, temp_dir]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                return True, "default"
        except Exception as e:
            return False, f"Clone failed: {str(e)}"
            
        return False, "Unable to clone repository"
        
    except Exception as e:
        return False, f"Clone error: {str(e)}"

def find_source_files(directory):
    """Find C/C++ source files in directory"""
    source_files = []
    
    for root, dirs, files in os.walk(directory):
        # Skip common non-source directories
        dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', '.vscode', '.idea']]
        
        for file in files:
            if any(file.endswith(ext) for ext in SUPPORTED_EXTENSIONS):
                file_path = os.path.join(root, file)
                # Calculate relative path from repo root
                rel_path = os.path.relpath(file_path, directory)
                source_files.append({
                    'full_path': file_path,
                    'relative_path': rel_path,
                    'size': os.path.getsize(file_path)
                })
    
    # Sort by size (analyze smaller files first) and limit count
    source_files.sort(key=lambda x: x['size'])
    return source_files[:MAX_FILES_TO_ANALYZE]

def analyze_repository_web(repo_path):
    """Run static analysis optimized for web interface"""
    try:
        # Import static analyzer
        from static_analyzer import StaticAnalyzer
        
        # Find source files
        source_files = find_source_files(repo_path)
        
        if not source_files:
            return {
                "success": True,
                "violations": [],
                "summary": {
                    "total_violations": 0,
                    "error_count": 0,
                    "warning_count": 0,
                    "info_count": 0,
                    "files_analyzed": 0,
                    "files_found": 0
                },
                "files_analyzed": []
            }
        
        # Get file paths for analysis
        file_paths = [f['full_path'] for f in source_files]
        
        # Run static analyzer
        analyzer = StaticAnalyzer()
        report = analyzer.analyze_files(file_paths)
        
        # Process violations
        violations = []
        error_count = warning_count = info_count = 0
        
        for violation in report.violations:
            severity = violation.severity.value if hasattr(violation.severity, 'value') else str(violation.severity)
            
            # Convert absolute path to relative path
            abs_path = violation.location.file_path
            rel_path = os.path.relpath(abs_path, repo_path) if abs_path.startswith(repo_path) else abs_path
            
            violation_dict = {
                "rule_id": violation.rule_id,
                "severity": severity.upper(),
                "message": violation.message,
                "file": rel_path,
                "line": violation.location.line,
                "column": violation.location.column,
                "standard": "MISRA" if "MISRA" in violation.rule_id else "CERT" if "CERT" in violation.rule_id else "OTHER"
            }
            violations.append(violation_dict)
            
            # Count by severity
            if severity.upper() == "ERROR":
                error_count += 1
            elif severity.upper() == "WARNING":
                warning_count += 1
            else:
                info_count += 1
        
        return {
            "success": True,
            "violations": violations,
            "summary": {
                "total_violations": len(violations),
                "error_count": error_count,
                "warning_count": warning_count,
                "info_count": info_count,
                "files_analyzed": len(file_paths),
                "files_found": len(source_files)
            },
            "files_analyzed": [f['relative_path'] for f in source_files]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "violations": [],
            "summary": {
                "total_violations": 0,
                "error_count": 0,
                "warning_count": 0,
                "info_count": 0,
                "files_analyzed": 0,
                "files_found": 0
            }
        }

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    """Analyze GitHub repository"""
    data = request.get_json()
    
    if not data or 'github_url' not in data:
        return jsonify({'error': 'GitHub URL is required'}), 400
    
    github_url = data['github_url'].strip()
    
    # Validate GitHub URL
    if not is_valid_github_url(github_url):
        return jsonify({'error': 'Invalid GitHub URL. Please provide a valid GitHub repository URL.'}), 400
    
    # Extract repository info
    owner, repo = extract_repo_info(github_url)
    if not owner or not repo:
        return jsonify({'error': 'Could not parse repository information from URL'}), 400
    
    # Create temporary directory for cloning
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Clone repository
            clone_success, branch_or_error = clone_repository(github_url, temp_dir)
            
            if not clone_success:
                return jsonify({'error': f'Failed to clone repository: {branch_or_error}'}), 400
            
            # Analyze repository
            analysis_result = analyze_repository_web(temp_dir)
            
            # Add metadata
            analysis_result.update({
                'repository': {
                    'owner': owner,
                    'name': repo,
                    'url': github_url,
                    'branch': branch_or_error
                },
                'timestamp': datetime.now().isoformat(),
                'analyzer_version': '1.0.0'
            })
            
            return jsonify(analysis_result)
            
        except Exception as e:
            return jsonify({'error': f'Analysis failed: {str(e)}'}), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'GitHub Static Analysis Web Interface',
        'version': '1.0.0'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
