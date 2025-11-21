# Twitter Thread Splitter for n8n

Intelligently splits long content into tweet-sized chunks at natural breaking points (sentences, paragraphs) rather than cutting mid-word.

## Features

✅ **Smart Breaking**: Breaks at sentences, paragraphs, or word boundaries
✅ **Thread Numbering**: Adds "1/5 🧵", "(1/5)", or "1/5" format
✅ **Character Aware**: Respects Twitter's 280 character limit
✅ **Preserves Formatting**: Keeps line breaks, emojis, and special characters
✅ **Configurable**: Multiple numbering styles and options

---

## Quick Setup (n8n Workflow)

### 1. Create Code Node

1. Add a **Code** node to your n8n workflow
2. Set **Language** to `JavaScript`
3. Set **Mode** to `Run Once for All Items`
4. Copy the entire contents of `twitter_thread_splitter.js` into the code editor

### 2. Input Format

Your input data should look like:

```json
{
  "content": "Your long post text here. This will be split into multiple tweets at smart breaking points...",
  "post_id": "optional-123"
}
```

**Supported input field names:**
- `content` (recommended)
- `text`
- `post`

### 3. Output Format

The node returns an **array of tweet objects**:

```json
[
  {
    "tweet": "1/3 🧵\n\nYour long post text here. This will be split into multiple tweets at smart breaking points.",
    "thread_position": 1,
    "thread_total": 3,
    "char_count": 112,
    "is_thread": true,
    "post_id": "optional-123",
    "delay_seconds": 0
  },
  {
    "tweet": "2/3 🧵\n\nSentences are kept together, and the splitter finds natural breaking points.",
    "thread_position": 2,
    "thread_total": 3,
    "char_count": 98,
    "is_thread": true,
    "post_id": "optional-123",
    "delay_seconds": 2
  },
  {
    "tweet": "3/3 🧵\n\nThis makes your threads much more readable!",
    "thread_position": 3,
    "thread_total": 3,
    "char_count": 56,
    "is_thread": true,
    "post_id": "optional-123",
    "delay_seconds": 4
  }
]
```

### 4. Connect to Twitter Node

After the Code node, add a **Loop Over Items** node, then connect to **Twitter** node:

```
[Code Node] → [Loop Over Items] → [Twitter Node (Post Tweet)]
```

In the Twitter node:
- **Text**: `{{ $json.tweet }}`
- **Reply to Tweet ID**: Use previous tweet ID for threading (optional)

---

## Configuration Options

Edit these constants at the top of the code:

```javascript
// Character limits
const TWITTER_LIMIT = 280;  // Don't change unless Twitter changes their limit
const THREAD_NUMBERING_SPACE = 10;  // Space reserved for numbering
const MIN_TWEET_LENGTH = 50;  // Avoid creating very short tweets

// Numbering style
const NUMBERING_STYLE = "emoji";  // Options: "emoji", "parentheses", "slash", "none"
```

### Numbering Styles

| Style | Example Output | Description |
|-------|---------------|-------------|
| `"emoji"` | `1/5 🧵\n\nYour tweet text...` | Thread emoji at start (recommended) |
| `"parentheses"` | `Your tweet text... (1/5)` | Numbering at end in parentheses |
| `"slash"` | `1/5\n\nYour tweet text...` | Simple numbering at start |
| `"none"` | `Your tweet text...` | No numbering (not recommended for threads) |

---

## Example Workflow Structure

### Basic Thread Publishing

```
[Trigger]
  → [Get Content from Database/API]
  → [Twitter Thread Splitter (Code Node)]
  → [Loop Over Items]
  → [Wait Node (2 seconds)]  ← Recommended to avoid rate limits
  → [Twitter - Post Tweet]
```

### Advanced with Thread Tracking

```
[Trigger]
  → [Get Content]
  → [Twitter Thread Splitter]
  → [Loop Over Items]
  → [If Node: Is First Tweet?]
     ├─ TRUE → [Twitter - Post Tweet] → [Save Tweet ID]
     └─ FALSE → [Twitter - Reply to Previous Tweet]
  → [Update Database with Thread IDs]
```

---

## Breaking Logic Priority

The splitter tries to break at the best point in this order:

1. **Paragraph break** (`\n\n`) - Best for readability
2. **Sentence ending** (`. ! ?`) - Keeps sentences together
3. **Single newline** (`\n`) - Preserves formatting
4. **Word boundary** (space) - Avoids cutting words
5. **Hard break** (last resort) - Only if no other option

---

## Edge Cases Handled

✅ **Very long sentences**: Breaks at word boundaries if sentence > 280 chars
✅ **URLs**: Won't break in middle of URLs (treats as single word)
✅ **Emojis**: Preserves emoji sequences
✅ **Hashtags/Mentions**: Keeps @mentions and #hashtags together
✅ **Single short post**: Returns as-is without numbering
✅ **Empty input**: Returns empty array

---

## Testing

### Test Input 1: Short Post (No Split)

```json
{
  "content": "This is a short post that fits in one tweet easily."
}
```

**Expected Output**: Single tweet, no numbering

---

### Test Input 2: Long Post (Multi-Tweet)

```json
{
  "content": "This is a longer post that demonstrates how the thread splitter works.\n\nIt intelligently breaks at paragraph boundaries first. If a paragraph is too long, it will break at sentence endings.\n\nThis ensures your threads are readable and flow naturally. No more awkward mid-sentence cuts!\n\nThe splitter also adds thread numbering so readers know there's more to come."
}
```

**Expected Output**: 3-4 tweets with numbering

---

### Test Input 3: Very Long Sentence

```json
{
  "content": "This is an extremely long sentence without any periods or paragraph breaks that goes on and on and will force the splitter to break at word boundaries because there are no natural sentence endings to use as breaking points which is not ideal but the splitter handles it gracefully by finding the last space before the character limit."
}
```

**Expected Output**: 2 tweets, broken at word boundaries

---

## Troubleshooting

### Issue: Tweets are still too long

**Solution**: The code reserves 10 characters for numbering. If you're using a longer format, increase `THREAD_NUMBERING_SPACE`:

```javascript
const THREAD_NUMBERING_SPACE = 15;  // For longer numbering like "(12/25)"
```

---

### Issue: Getting very short tweets

**Solution**: Increase `MIN_TWEET_LENGTH` to avoid breaking too early:

```javascript
const MIN_TWEET_LENGTH = 100;  // Require at least 100 chars per tweet
```

---

### Issue: Want to break at specific markers

**Solution**: Add custom breaking logic in the `findSmartBreak()` function:

```javascript
// Example: Break at "---" separator
const customBreak = searchText.lastIndexOf('---');
if (customBreak > MIN_TWEET_LENGTH) {
  return text.slice(0, customBreak);
}
```

---

## Advanced: Thread Reply Chaining

To create proper Twitter threads (each tweet replies to the previous), use this workflow:

```javascript
// In a separate Function node after the Twitter post
const allTweets = $('Twitter Thread Splitter').all();
const currentIndex = $itemIndex;

// If not the first tweet, get previous tweet's ID
if (currentIndex > 0) {
  const previousTweetId = $items(currentIndex - 1)[0].json.tweet_id;
  return {
    in_reply_to_status_id: previousTweetId
  };
}

return {};
```

---

## License

MIT - Feel free to modify for your needs!

---

## Support

For issues or questions:
- Check n8n community forum for n8n-specific questions
- Twitter's API docs: https://developer.twitter.com/en/docs

---

## Changelog

**v1.0.0** - Initial release
- Smart sentence/paragraph breaking
- Multiple numbering styles
- Character count tracking
- Thread position metadata
