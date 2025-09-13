# Crypto News Bot with Bounty Integration

An intelligent automated bot that generates organic crypto/Web3 content using local LLM (DeepSeek via Ollama), strategically posts bounties for revenue streams, and builds a sustainable following through quality content.

## 🚀 Features

- **📰 News Aggregation**: Scrapes crypto news from multiple sources
- **🤖 AI Content Generation**: Uses DeepSeek via Ollama for intelligent content creation
- **💰 Bounty Integration**: Strategic posting of relevant bounties for revenue
- **📊 Context Awareness**: Maintains posting history and engagement data
- **⏰ Smart Scheduling**: Pre-generates and schedules content throughout the day
- **📈 Analytics**: Tracks engagement, performance, and revenue metrics
- **🔒 Local LLM**: Privacy-focused content generation with DeepSeek

## 🎯 Strategy

- **80% Organic Content**: Quality crypto news and analysis
- **20% Bounty Posts**: Strategic revenue-generating content
- **Context-Aware**: Uses previous posts and trends for better content
- **Scheduled Distribution**: Spreads content throughout the day for maximum engagement

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   News Sources  │    │   Bounty Sites   │    │   DeepSeek LLM  │
│  (CoinDesk,     │    │  (Superteam,     │    │   (via Ollama)  │
│   CoinTelegraph)│    │   Gitcoin, etc)  │    │                 │
└─────────┬───────┘    └─────────┬────────┘    └─────────┬───────┘
          │                      │                       │
          ▼                      ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Content Generator                            │
│  • Context-aware prompt building                               │
│  • Thread generation with engagement data                      │
│  • Content quality filtering                                   │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Content Scheduler                           │
│  • Daily content calendar                                       │
│  • Optimal timing based on engagement                          │
│  • Queue management and approval workflow                      │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Twitter Poster                              │
│  • Rate-limited posting                                        │
│  • Thread management                                           │
│  • Engagement tracking                                         │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

1. **Install Ollama**:
   ```bash
   curl -fsSL https://ollama.ai/install.sh | sh
   ollama pull deepseek-coder
   ```

2. **Clone and Setup**:
   ```bash
   git clone <your-repo-url>
   cd crypto-news-bot
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure Environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

4. **Setup Database**:
   ```bash
   # Option A: Supabase (Recommended)
   # 1. Create Supabase project
   # 2. Run SQL schema from supabase_schema.sql
   # 3. Add SUPABASE_URL and SUPABASE_KEY to .env
   
   # Option B: SQLite (Local Development)
   python -c "from src.storage import init_db; init_db()"
   ```

5. **Run the Bot**:
   ```bash
   # Test once
   python -m src.main --once
   
   # Run scheduler
   python -m src.main
   ```

## ⚙️ Configuration

### Required Environment Variables

```bash
# Twitter API (Basic tier recommended)
TW_API_KEY=your_api_key
TW_API_SECRET=your_api_secret
TW_ACCESS_TOKEN=your_access_token
TW_ACCESS_SECRET=your_access_secret

# News Sources
COINDESK_API_KEY=your_coindesk_key
COINTELEGRAPH_API_KEY=your_cointelegraph_key

# LLM Configuration
OLLAMA_BASE_URL=http://localhost:11434
DEEPSEEK_MODEL=deepseek-coder

# Content Strategy
NEWS_POSTS_PER_DAY=8
BOUNTY_POSTS_PER_DAY=2
CONTENT_MIX_RATIO=0.8
```

### Content Strategy Settings

- **`NEWS_POSTS_PER_DAY`**: Number of news-based posts per day
- **`BOUNTY_POSTS_PER_DAY`**: Number of bounty posts per day
- **`CONTENT_MIX_RATIO`**: Ratio of news to bounty content (0.8 = 80% news)
- **`POST_INTERVAL_MINUTES`**: Time between posts (default: 120 minutes)

## 📊 Database Schema

The bot uses a comprehensive database schema to track:

- **News Articles**: Scraped crypto news with sentiment analysis
- **Bounties**: Available bounty opportunities with reward tracking
- **Content Queue**: Scheduled posts with approval workflow
- **Analytics**: Engagement metrics and revenue tracking
- **Posting History**: Complete record of all posted content

## 🤖 LLM Integration

### DeepSeek via Ollama

The bot uses DeepSeek model running locally via Ollama for:

- **Content Generation**: Creating engaging crypto threads
- **Context Awareness**: Using posting history and trends
- **Quality Control**: Ensuring content meets standards
- **Personalization**: Adapting tone and style over time

### Prompt Engineering

The bot uses sophisticated prompts that include:

- **Previous successful posts** for style consistency
- **Current market trends** for relevance
- **User engagement patterns** for optimization
- **News article context** for accuracy

## 📈 Revenue Integration

### Bounty Revenue Tracking

- **Performance Metrics**: Track bounty post engagement
- **Conversion Rates**: Monitor bounty completion rates
- **Revenue Calculation**: Calculate earnings per post
- **Optimization**: Improve bounty selection criteria

### Content Performance

- **A/B Testing**: Test different content styles
- **Engagement Analysis**: Track likes, retweets, replies
- **Timing Optimization**: Find best posting times
- **Audience Insights**: Build follower understanding

## 🛡️ Safety & Compliance

### Content Guidelines

- ✅ All AI-generated content reviewed for accuracy
- ✅ No financial advice without disclaimers
- ✅ Respect platform automation rules
- ✅ Maintain authentic voice and engagement

### Bounty Integration

- ✅ Only promote relevant, legitimate bounties
- ✅ Disclose promotional content appropriately
- ✅ Maintain quality standards
- ✅ Avoid spammy or repetitive content

## 🚀 Deployment

### Local Development

```bash
# Start Ollama
ollama serve

# Run bot in development mode
python -m src.main --dev
```

### Production with Docker

```bash
# Build and run
docker-compose up --build

# View logs
docker-compose logs -f crypto-news-bot
```

### VPS Deployment

1. **Setup Ollama** on GPU-enabled server
2. **Configure Supabase** for production database
3. **Deploy with Docker** or systemd service
4. **Setup monitoring** and alerts

## 📊 Monitoring

### Key Metrics

- **Content Performance**: Engagement rates, reach, impressions
- **Revenue Tracking**: Bounty earnings, conversion rates
- **Bot Health**: Uptime, error rates, API limits
- **Content Quality**: Approval rates, user feedback

### Alerts

- **High Error Rates**: Bot malfunction detection
- **API Limits**: Rate limit warnings
- **Content Issues**: Quality control alerts
- **Revenue Drops**: Performance monitoring

## 🧪 Testing

```bash
# Run all tests
pytest

# Test specific components
pytest tests/test_llm_service.py
pytest tests/test_content_generator.py

# Test with coverage
pytest --cov=src
```

## 📚 Project Structure

```
crypto-news-bot/
├── src/
│   ├── main.py                 # Main scheduler
│   ├── news_scraper.py         # News aggregation
│   ├── bounty_scraper.py       # Bounty monitoring
│   ├── llm_service.py          # DeepSeek integration
│   ├── content_generator.py    # AI content creation
│   ├── scheduler.py            # Content calendar
│   ├── poster.py               # Twitter posting
│   ├── storage.py              # Database operations
│   ├── analytics.py            # Performance tracking
│   ├── config.py               # Configuration
│   └── utils.py                # Utilities
├── models/                     # LLM prompts and templates
├── data/                       # Local data storage
├── tests/                      # Test suite
├── dockerfile                  # Docker configuration
├── docker-compose.yml          # Docker Compose setup
└── supabase_schema.sql         # Database schema
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

This bot is for educational and research purposes. Users are responsible for ensuring compliance with all applicable terms of service, laws, and regulations. The authors are not responsible for any misuse or violations.

## 🆘 Support

- **Issues**: Report bugs and feature requests on GitHub
- **Discussions**: Join community discussions
- **Documentation**: Check the instructions.md file for detailed setup

---

**Built with ❤️ for the crypto community**