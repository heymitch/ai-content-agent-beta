# Content Agent - Client-Scalable Setup

A sophisticated content strategy agent with RAG-powered knowledge base, designed for easy client onboarding and deployment.

## 🚀 Quick Start

### For Your Business (Current Setup)
```bash
# Your current working setup is in clients/your-business/
cd clients/your-business/
python ../../main.py
```

### For New Clients
```bash
# Onboard a new client
python setup/client_onboarding.py --client client-name

# Health check
python utils/health_check.py

# Setup database functions (if needed)
python setup/setup_database.py --client client-name
```

## 📁 Project Structure

```
content-agent/
├── main.py                     # Core agent application
├── requirements.txt            # Python dependencies
├── supabase_schema.sql         # Database schema reference
├── setup/                      # Setup and onboarding scripts
│   ├── client_onboarding.py    # Full client onboarding
│   └── setup_database.py       # Database setup utilities
├── utils/                      # Reusable utilities
│   ├── embedding_utils.py      # Embedding generation tools
│   └── health_check.py         # System health monitoring
├── clients/                    # Client-specific configurations
│   └── your-business/          # Your current working setup
│       ├── .env                # Environment variables
│       └── docs/               # Brand documentation
└── archive/                    # Archived setup/debug files
```

## 🛠️ Features

### Core Agent Capabilities
- **Strategic Content Planning**: AI-powered content strategy with brand voice integration
- **RAG-Powered Knowledge Base**: Semantic search across training content and frameworks
- **Conversation Memory**: Maintains context across chat sessions
- **Enhanced Webhook Delivery**: Comprehensive strategic context for downstream automation
- **Multi-Platform Support**: Slack integration with extensible platform support

### Training Data Sources
- **Social Content**: 1900+ training examples with embeddings
- **Proven Content**: High-performing posts from industry leaders
- **Strategic Frameworks**: Content strategy and brand voice guidelines
- **Custom Brand Docs**: Client-specific brand guidelines and voice

### RAG Search Functions
- `match_social_content`: Search training social media content
- `match_high_performing_content`: Search proven high-performing content
- `match_documents`: Search general documents and resources
- `match_knowledge`: Search strategic frameworks and guidelines

## 🔧 Client Onboarding

### 1. Prepare Client Assets
Create folder structure for new client:
```
clients/client-name/
├── docs/                       # Brand guidelines
│   ├── brand_voice.md
│   ├── content_strategy.md
│   └── company_context.md
└── training-data/              # Training content
    ├── social-content/         # Social media posts (.md files)
    ├── high-performing/        # Proven content (.md files)
    └── documents/              # General resources (.md files)
```

### 2. Run Onboarding Script
```bash
python setup/client_onboarding.py \
  --client client-name \
  --supabase-url "your-supabase-url" \
  --supabase-key "your-supabase-key" \
  --openai-key "your-openai-key"
```

### 3. Validate Setup
```bash
python utils/health_check.py
```

## 📊 Database Setup

### Required Supabase Tables
- `knowledge_base`: Strategic frameworks and guidelines
- `documents`: General documents and resources
- `social_content`: Social media training content
- `high_performing_content`: Proven high-performing content
- `conversation_history`: Chat conversation logs
- `strategic_plans`: Generated strategic plans

### Required RAG Functions
The onboarding script will provide SQL to add these functions to your Supabase:
- `match_knowledge()`
- `match_documents()`
- `match_social_content()`
- `match_high_performing_content()`

## 🔑 Environment Variables

### Required
```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
OPENAI_API_KEY=your_openai_api_key
```

### Optional (for Slack integration)
```env
SLACK_WEBHOOK_URL=your_slack_webhook_url
SLACK_BOT_TOKEN=your_slack_bot_token
PLAN_DELIVERY_WEBHOOK_URL=your_plan_delivery_webhook
```

## 🚦 Health Monitoring

### Quick Health Check
```bash
python utils/health_check.py --quick
```

### Comprehensive Health Check
```bash
python utils/health_check.py
```

Checks include:
- Environment variables
- Database connectivity
- RAG function availability
- OpenAI API access
- File structure validation

## 🎯 Deployment

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run health check
python utils/health_check.py

# Start agent
python main.py
```

### Production Deployment
1. Set up client using onboarding script
2. Configure environment variables
3. Validate with health check
4. Deploy using your preferred platform (Heroku, Railway, etc.)

## 📚 Usage Examples

### Adding Training Content
```bash
# Add markdown files to training folders
clients/client-name/training-data/social-content/post-1.md
clients/client-name/training-data/high-performing/proven-thread.md

# Regenerate embeddings
python setup/client_onboarding.py --client client-name
```

### Testing RAG Search
```python
from utils.embedding_utils import test_rag_search
from supabase import create_client

supabase = create_client(url, key)
test_rag_search(supabase, 'match_social_content', 'content strategy')
```

## 🔄 Maintenance

### Regular Tasks
- **Monitor embedding counts**: Ensure new content gets embedded
- **Health checks**: Run before deployments
- **Client updates**: Re-run onboarding when adding new training data

### Troubleshooting
- Check `archive/` folder for debugging scripts from initial setup
- Run `python utils/health_check.py` to diagnose issues
- Validate RAG functions in Supabase SQL Editor

## 📝 License

This project is configured for client services delivery. Each client deployment should have its own isolated database and configuration.

---

**Need help?** Check the health monitoring output or review archived setup scripts in the `archive/` folder.# Trigger deployment Wed Oct  1 15:02:55 MST 2025
