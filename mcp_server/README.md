# GitHub Static Analysis MCP Server

This directory contains the Model Context Protocol (MCP) server implementation that enables LLMs to automatically analyze GitHub commits using our static analysis framework.

## 🚀 Overview

The MCP server provides automated code quality checking by:
1. **Receiving GitHub webhooks** for push events and pull requests
2. **Analyzing commits** using the static analysis framework
3. **Generating reports** with MISRA C:2012 and CERT C/C++ compliance
4. **Sending email notifications** to commit authors
5. **Providing LLM tools** for interactive analysis

## 🏗️ Architecture

```
GitHub Repository → Webhook → MCP Server → LLM → Static Analysis → Email Report
```

### Components

- **`github_analyzer.py`**: MCP server with tools for LLM integration
- **`webhook_handler.py`**: Flask server handling GitHub webhooks
- **`llm_integration_example.py`**: Example LLM workflow implementation
- **`config.yaml`**: Configuration for all server components

## 🔧 Setup

### Prerequisites

- Docker and Docker Compose
- GitHub Personal Access Token
- LLM API key (Anthropic Claude or OpenAI GPT)
- Email credentials (Gmail recommended)

### Quick Start

1. **Clone and setup**:
   ```bash
   git clone <your-repo>
   cd Static_code_analsys
   chmod +x setup.sh
   ./setup.sh
   ```

2. **Configure environment**:
   Edit `.env` file with your credentials:
   ```bash
   GITHUB_TOKEN=ghp_your_token_here
   GITHUB_WEBHOOK_SECRET=your_secret_here
   ANTHROPIC_API_KEY=sk-ant-your_key_here
   EMAIL_USER=your_email@gmail.com
   EMAIL_PASSWORD=your_app_password_here
   FROM_EMAIL=your_email@gmail.com
   ```

3. **Start services**:
   ```bash
   docker-compose up -d
   ```

4. **Configure GitHub webhook**:
   - Repository Settings → Webhooks → Add webhook
   - Payload URL: `http://your-server:5000/webhook`
   - Content type: `application/json`
   - Secret: Your `GITHUB_WEBHOOK_SECRET`
   - Events: `Push`, `Pull requests`

## 🛠️ MCP Tools

The server provides 5 tools for LLM interaction:

### `analyze_commit_changes`
Analyzes specific commit changes for MISRA/CERT violations.

**Parameters:**
- `repo_url`: GitHub repository URL
- `commit_sha`: Commit hash to analyze
- `standards`: List of standards (["MISRA", "CERT"])

**Returns:** Analysis results with violations and metadata

### `generate_analysis_report`
Generates HTML/Markdown reports from analysis results.

**Parameters:**
- `analysis_results`: Results from analyze_commit_changes
- `format`: "html" or "markdown"
- `include_ai_explanations`: Include AI-powered explanations

**Returns:** Formatted report content

### `send_analysis_email`
Sends analysis reports via email.

**Parameters:**
- `report_content`: HTML/Markdown report
- `recipient_email`: Email address
- `subject`: Email subject
- `repo_name`: Repository name
- `commit_sha`: Commit hash

**Returns:** Email delivery status

### `clone_and_analyze_repository`
Clones repository and performs full analysis.

**Parameters:**
- `repo_url`: GitHub repository URL
- `branch`: Branch to analyze (default: main)
- `standards`: Standards to check

**Returns:** Complete repository analysis

### `compare_with_baseline`
Compares current analysis with baseline/previous analysis.

**Parameters:**
- `current_results`: Current analysis results
- `baseline_path`: Path to baseline results

**Returns:** Comparison showing new/fixed violations

## 📊 Usage Examples

### LLM Integration

```python
import asyncio
from anthropic import Anthropic

async def analyze_commit_with_llm(repo_url, commit_sha):
    """Example LLM workflow for commit analysis"""
    
    # Initialize Anthropic client
    client = Anthropic(api_key="your-api-key")
    
    # Analyze commit
    response = await client.messages.create(
        model="claude-3-sonnet-20240229",
        tools=[
            {
                "name": "analyze_commit_changes",
                "description": "Analyze commit for code quality issues",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "repo_url": {"type": "string"},
                        "commit_sha": {"type": "string"},
                        "standards": {"type": "array", "items": {"type": "string"}}
                    }
                }
            }
        ],
        messages=[
            {
                "role": "user", 
                "content": f"Analyze this commit for MISRA and CERT violations: {repo_url}/commit/{commit_sha}"
            }
        ]
    )
    
    return response
```

### Webhook Processing

When a GitHub push event is received:

1. **Webhook validates** signature and extracts commit info
2. **LLM is triggered** with commit details
3. **LLM calls MCP tools** to analyze changes
4. **Report is generated** and emailed to author

## ⚙️ Configuration

### config.yaml Structure

```yaml
github:
  token_env: "GITHUB_TOKEN"
  webhook_secret_env: "GITHUB_WEBHOOK_SECRET"

llm:
  provider: "anthropic"  # or "openai"
  model_config:
    anthropic:
      model: "claude-3-sonnet-20240229"
      max_tokens: 4000

email:
  smtp_server: "smtp.gmail.com"
  smtp_port: 587

analysis:
  standards: ["MISRA", "CERT"]
  file_extensions: [".c", ".cpp", ".h", ".hpp"]
  max_files_per_commit: 50
```

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `GITHUB_TOKEN` | Personal access token | `ghp_xxxxxxxxxxxx` |
| `GITHUB_WEBHOOK_SECRET` | Webhook secret | `my-secret-key` |
| `ANTHROPIC_API_KEY` | Claude API key | `sk-ant-xxxxx` |
| `OPENAI_API_KEY` | GPT API key | `sk-xxxxx` |
| `EMAIL_USER` | SMTP username | `user@gmail.com` |
| `EMAIL_PASSWORD` | SMTP password | `app-password` |

## 🔐 Security

- **Webhook signature verification** prevents unauthorized requests
- **API key encryption** in environment variables
- **Repository filtering** limits access to approved repos
- **Rate limiting** prevents abuse
- **Docker isolation** provides container security

## 📈 Monitoring

### Health Check
```bash
curl http://localhost:5000/health
```

### Logs
```bash
# View real-time logs
docker-compose logs -f mcp-server

# Check specific service
docker-compose logs webhook-handler
```

### Metrics
- Request count and timing
- Analysis success/failure rates  
- Email delivery status
- Memory and CPU usage

## 🚨 Troubleshooting

### Common Issues

1. **Webhook not triggering**
   - Check GitHub webhook configuration
   - Verify webhook secret matches
   - Check server accessibility from GitHub

2. **Analysis failing**
   - Verify clang installation in Docker
   - Check repository access permissions
   - Review analysis timeout settings

3. **Email not sending**
   - Verify SMTP credentials
   - Check Gmail app password setup
   - Review firewall settings

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
docker-compose restart mcp-server
```

## 🔄 Deployment

### Production Setup

1. **Use reverse proxy** (nginx/Apache) for SSL termination
2. **Set up monitoring** (Prometheus/Grafana)
3. **Configure backup** for analysis reports
4. **Scale horizontally** with multiple server instances

### Example nginx config:

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    location /webhook {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 📚 API Reference

### Webhook Endpoints

- `POST /webhook` - GitHub webhook receiver
- `GET /health` - Health check endpoint
- `GET /metrics` - Prometheus metrics (optional)

### MCP Protocol

The server implements MCP protocol version 1.0 with:
- Tool listing and schemas
- Tool execution with parameter validation
- Error handling and logging
- Resource management

## 🤝 Contributing

1. Fork repository
2. Create feature branch
3. Add tests for new functionality
4. Submit pull request

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Support

- Create GitHub issue for bugs
- Check documentation wiki
- Review troubleshooting guide
- Contact maintainers

---

**Note**: This MCP server is designed for production use with proper security, monitoring, and error handling. Always review and test in staging before production deployment.
