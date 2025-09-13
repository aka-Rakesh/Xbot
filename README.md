# Twitter Bounty Bot

An automated bot that scrapes bounty sites for crypto posting bounties and posts engaging threads to Twitter/X to claim bounties and grow an organic following.

## Features

- 🔍 **Automated Scraping**: Monitors bounty sites for new opportunities
- 🧵 **Thread Generation**: Creates engaging Twitter threads from bounty data
- 🤖 **Smart Posting**: Posts threads via Twitter API with rate limiting
- 🔄 **Deduplication**: Prevents duplicate posts and tracks seen bounties
- 📊 **Monitoring**: Comprehensive logging and error handling
- 🐳 **Docker Ready**: Easy deployment with Docker and docker-compose

## Quick Start

### Prerequisites

- Python 3.11+
- Twitter Developer Account with API access
- Docker (optional, for containerized deployment)

### Local Development

1. **Clone and setup**:
   ```bash
   git clone <your-repo-url>
   cd twitter-bounty-bot
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your Twitter API credentials and bounty site URL
   ```

3. **Initialize database**:
   ```bash
   python -c "from src.storage import init_db; init_db()"
   ```

4. **Run the bot**:
   ```bash
   # Run once for testing
   python -m src.main --once
   
   # Run scheduler
   python -m src.main
   ```

### Docker Deployment

1. **Build and run**:
   ```bash
   docker-compose up --build
   ```

2. **View logs**:
   ```bash
   docker-compose logs -f bounty-bot
   ```

## Configuration

### Required Environment Variables

```bash
# Twitter API Credentials
TW_API_KEY=your_api_key
TW_API_SECRET=your_api_secret
TW_ACCESS_TOKEN=your_access_token
TW_ACCESS_SECRET=your_access_secret

# Bounty Site
BOUNTY_SITE_URL=https://your-bounty-site.com

# Bot Behavior
POST_INTERVAL_MINUTES=10
MAX_POSTS_PER_DAY=10
USER_DISPLAY_NAME=MyBountyBot
```

### Optional Variables

```bash
# Database (defaults to SQLite)
DATABASE_URL=sqlite:///./data.db

# OpenAI for LLM thread generation
OPENAI_API_KEY=your_openai_key

# Monitoring
SENTRY_DSN=your_sentry_dsn
```

## Project Structure

```
twitter-bounty-bot/
├── src/
│   ├── main.py          # Scheduler and main entry point
│   ├── scraper.py       # Bounty site scraping
│   ├── poster.py        # Twitter posting functionality
│   ├── generator.py     # Thread generation (templates + LLM)
│   ├── storage.py       # Database operations
│   ├── config.py        # Configuration management
│   └── utils.py         # Utility functions
├── tests/               # Test files
├── migrations/          # Database migrations
├── dockerfile          # Docker configuration
├── docker-compose.yml  # Docker Compose setup
├── requirements.txt    # Python dependencies
└── .env.example       # Environment variables template
```

## Customization

### Adding New Bounty Sites

1. **Update scraper.py**:
   - Modify CSS selectors in `fetch_bounties_requests()`
   - Add site-specific parsing logic
   - Test with `python -c "from src.scraper import fetch_bounties; print(fetch_bounties())"`

2. **Update thread templates**:
   - Modify templates in `generator.py`
   - Customize thread structure and hashtags
   - Add site-specific formatting

### Thread Generation

The bot supports two thread generation modes:

1. **Template-based** (default): Uses predefined templates
2. **LLM-powered**: Uses OpenAI GPT for dynamic content

Enable LLM mode by setting `OPENAI_API_KEY` in your environment.

## Safety & Compliance

⚠️ **Important**: Before going live, ensure compliance with:

- Twitter's automation and spam policies
- Bounty site terms of service
- Applicable laws and regulations
- Platform-specific labeling requirements

## Monitoring

### Logs

- Application logs: `bounty_bot.log`
- Docker logs: `docker-compose logs bounty-bot`

### Health Checks

- Database connectivity
- Twitter API status
- Rate limit monitoring

## Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_scraper.py

# Run with coverage
pytest --cov=src
```

## Troubleshooting

### Common Issues

1. **Twitter API 401/403**: Check credentials and permissions
2. **Rate limit exceeded**: Reduce `POST_INTERVAL_MINUTES`
3. **Scraping fails**: Update CSS selectors for target site
4. **Database errors**: Check `DATABASE_URL` and permissions

### Debug Mode

```bash
# Run with debug logging
PYTHONPATH=. python -m src.main --once
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This bot is for educational and research purposes. Users are responsible for ensuring compliance with all applicable terms of service, laws, and regulations. The authors are not responsible for any misuse or violations.
