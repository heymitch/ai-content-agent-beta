# Analytics & Intelligence System

## Overview

The Analytics & Intelligence System provides automated content performance analysis and strategic insights. It's designed to be **completely optional** and won't interfere with core agent functionality when disabled.

## Features

- 📊 **Performance Analysis**: Analyze post metrics to identify top/worst performers
- 📈 **Pattern Detection**: Discover what hook styles, platforms, and timing work best
- 📝 **Weekly Briefings**: Automated strategic content intelligence reports
- 🔄 **n8n Integration**: Webhook endpoint for automation workflows
- 🎯 **Ayrshare Integration**: Real engagement metrics from social platforms
- ⚙️ **Fully Configurable**: Enable/disable features via environment variables

## Quick Start

### 1. Enable Analytics (Optional)

Add to your `.env` file:
```env
# Basic analytics
ANALYTICS_ENABLED=true
ANALYTICS_USE_MOCK_DATA=true  # Use mock data for testing
```

### 2. Test the System

```bash
# Test analytics endpoints
python test_analytics.py

# Test full workflow
python test_analytics_full.py
```

### 3. Set Up Automated Briefings (Optional)

For weekly automated briefings via n8n:

1. Add to `.env`:
```env
ANALYTICS_AUTO_BRIEFING=true
ANALYTICS_BRIEFING_DAY=monday
ANALYTICS_BRIEFING_TIME=09:00
ANALYTICS_BRIEFING_CHANNEL=content-strategy
```

2. Configure n8n workflow:
   - Add Schedule Trigger: Every Monday at 9am
   - Add HTTP Request node:
     - URL: `https://your-domain.com/api/n8n/weekly-briefing`
     - Method: POST
     - Body (optional):
       ```json
       {
         "days_back": 7,
         "slack_channel": "content-strategy",
         "include_ayrshare": true
       }
       ```

## API Endpoints

### `/api/analyze-performance`
Analyzes post performance data.

**Request:**
```json
{
  "posts": [
    {
      "hook": "I replaced 3 workflows...",
      "platform": "linkedin",
      "quality_score": 24,
      "impressions": 15000,
      "engagements": 1230,
      "engagement_rate": 8.2,
      "published_at": "2025-01-20"
    }
  ],
  "date_range": {
    "start": "2025-01-20",
    "end": "2025-01-27"
  }
}
```

**Response:**
```json
{
  "summary": "Engagement up 15% this week",
  "top_performers": [...],
  "worst_performers": [...],
  "patterns": {
    "best_hook_style": "Specific Number Hook",
    "best_platform": "linkedin",
    "avg_engagement_rate": 7.5
  },
  "recommendations": [
    "Focus on LinkedIn for B2B content",
    "Use specific numbers in hooks"
  ]
}
```

### `/api/generate-briefing`
Generates strategic content briefing.

**Request:**
```json
{
  "analytics": {/* output from analyze-performance */},
  "research": {/* optional trending topics */},
  "user_context": {/* optional goals/audience */}
}
```

### `/api/n8n/weekly-briefing`
Webhook for automated briefings.

**Authentication (optional):**
If `N8N_WEBHOOK_SECRET` is set in your environment, the webhook requires Bearer token authentication:
```
Authorization: Bearer your-secret-token-here
```

**Request (all fields optional):**
```json
{
  "days_back": 7,
  "slack_channel": "content-strategy",
  "include_ayrshare": true
}
```

## Configuration

All settings are optional. Copy `.env.analytics.example` to see all options.

### Core Settings
| Variable | Default | Description |
|----------|---------|-------------|
| `ANALYTICS_ENABLED` | `false` | Master switch for analytics |
| `ANALYTICS_AUTO_BRIEFING` | `false` | Enable scheduled briefings |
| `ANALYTICS_BRIEFING_DAY` | `monday` | Day for briefings |
| `ANALYTICS_BRIEFING_TIME` | `09:00` | Time for briefings |

### Data Sources
| Variable | Default | Description |
|----------|---------|-------------|
| `ANALYTICS_USE_AIRTABLE` | `true` | Use Airtable for post data |
| `ANALYTICS_USE_AYRSHARE` | `false` | Use real engagement metrics |
| `ANALYTICS_USE_MOCK_DATA` | `true` | Use mock data when real unavailable |

### Analysis Parameters
| Variable | Default | Description |
|----------|---------|-------------|
| `ANALYTICS_MIN_POSTS` | `5` | Minimum posts for analysis |
| `ANALYTICS_DAYS_LOOKBACK` | `7` | Days to analyze |
| `ANALYTICS_HIGH_ENGAGEMENT` | `8.0` | High engagement threshold (%) |
| `ANALYTICS_LOW_ENGAGEMENT` | `3.0` | Low engagement threshold (%) |

### Security Settings
| Variable | Default | Description |
|----------|---------|-------------|
| `N8N_WEBHOOK_SECRET` | (empty) | Optional Bearer token for webhook auth |

## Integration Guide

### With Airtable

Analytics automatically fetches posts from your Airtable Content Calendar when `ANALYTICS_USE_AIRTABLE=true`.

Required Airtable fields:
- Hook (text)
- Platform (single select)
- Quality Score (number)
- Publish Date (date)
- Ayrshare ID (text, optional)

### With Ayrshare

For real engagement metrics:

1. Set up Ayrshare account
2. Add API key to `.env`:
   ```env
   AYRSHARE_API_KEY=your_key_here
   ANALYTICS_USE_AYRSHARE=true
   ```
3. Store Ayrshare post IDs in Airtable

### With n8n

**Setting up webhook authentication (optional):**

1. Generate a secret token (any random string)
2. Add to your `.env` file:
   ```env
   N8N_WEBHOOK_SECRET=your-secret-token-here
   ```
3. In n8n HTTP Request node, add header:
   - Header Name: `Authorization`
   - Header Value: `Bearer your-secret-token-here`

**Example n8n workflow:**

1. **Schedule Trigger**: Every Monday 9am
2. **HTTP Request**:
   - URL: `{{$env.API_URL}}/api/n8n/weekly-briefing`
   - Method: POST
   - Headers (if auth enabled):
     - Authorization: `Bearer {{$env.N8N_WEBHOOK_SECRET}}`
   - Body: `{"days_back": 7}`
3. **Slack** (optional): Forward briefing to additional channels

**Note:** Authentication is completely optional. If `N8N_WEBHOOK_SECRET` is not set, the webhook works without authentication (backwards compatible).

## Troubleshooting

### Analytics not working?
1. Check `ANALYTICS_ENABLED=true` in `.env`
2. Run `python test_analytics_full.py` to diagnose
3. Check logs for errors

### No data in briefings?
1. Verify Airtable has posts with dates
2. Check date range matches your posts
3. Try with `ANALYTICS_USE_MOCK_DATA=true` first

### n8n webhook failing?
1. Verify endpoint URL is accessible
2. Check authentication if required
3. Test manually with `curl` or Postman
4. Review server logs

## Architecture

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────┐
│   Data Sources  │────▶│   Analysis   │────▶│  Briefing   │
├─────────────────┤     ├──────────────┤     ├─────────────┤
│ • Airtable      │     │ • Patterns   │     │ • Markdown  │
│ • Ayrshare      │     │ • Top/Worst  │     │ • Topics    │
│ • Mock Data     │     │ • Insights   │     │ • Actions   │
└─────────────────┘     └──────────────┘     └─────────────┘
                              │                     │
                              ▼                     ▼
                        ┌──────────┐         ┌──────────┐
                        │   n8n    │         │  Slack   │
                        └──────────┘         └──────────┘
```

## Security Notes

- **Webhook Authentication**: Optional Bearer token auth via `N8N_WEBHOOK_SECRET`
- **Backwards Compatible**: Works without auth if secret not configured
- **Other Endpoints**: Analytics endpoints don't require auth by default
- **Ayrshare API**: Keep API key secret in environment variables
- **Production**: Consider rate limiting for publicly exposed endpoints

## Support

- Check logs for detailed error messages
- Test with mock data first
- Ensure all environment variables are set correctly
- Analytics won't affect core agent functionality when disabled