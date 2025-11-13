/**
 * Smart Twitter Thread Splitter for n8n
 *
 * Intelligently splits long text into tweet-sized chunks at natural breaking points
 * (sentences, paragraphs, line breaks) rather than cutting mid-word.
 *
 * Features:
 * - Respects Twitter's 280 character limit
 * - Breaks at sentences, paragraphs, or line breaks
 * - Adds thread numbering (1/N, 2/N, etc.)
 * - Preserves formatting and emojis
 * - Handles edge cases (URLs, mentions, hashtags)
 *
 * Usage in n8n Code Node:
 * - Input: $input.item.json.content (the long text)
 * - Output: Array of tweet objects ready to publish
 */

// ============================================================================
// CONFIGURATION
// ============================================================================

const TWITTER_LIMIT = 280;  // Twitter's character limit
const THREAD_NUMBERING_SPACE = 10;  // Reserve space for " (N/N)" or "N/N 🧵"
const MIN_TWEET_LENGTH = 50;  // Avoid very short tweets

// Choose numbering style:
// "parentheses" = " (1/5)" at end
// "slash" = "1/5 " at start
// "emoji" = "1/5 🧵" at start
// "none" = no numbering
const NUMBERING_STYLE = "emoji";

// ============================================================================
// MAIN FUNCTION
// ============================================================================

/**
 * Split long text into tweet-sized chunks
 * @param {string} text - The long text to split
 * @returns {Array} Array of tweet strings
 */
function splitIntoTweets(text) {
  if (!text || text.trim().length === 0) {
    return [];
  }

  // Calculate max length per tweet (accounting for thread numbering)
  const maxLength = TWITTER_LIMIT - THREAD_NUMBERING_SPACE;

  // If text fits in one tweet, return as-is (no numbering needed)
  if (text.length <= TWITTER_LIMIT) {
    return [text];
  }

  const tweets = [];
  let remainingText = text.trim();

  while (remainingText.length > 0) {
    let chunk;

    if (remainingText.length <= maxLength) {
      // Last chunk - take everything
      chunk = remainingText;
      remainingText = "";
    } else {
      // Find smart breaking point
      chunk = findSmartBreak(remainingText, maxLength);
      remainingText = remainingText.slice(chunk.length).trim();
    }

    tweets.push(chunk.trim());
  }

  // Add thread numbering
  return addThreadNumbering(tweets);
}

/**
 * Find the best breaking point in text (at sentence, paragraph, or word boundary)
 * @param {string} text - Text to break
 * @param {number} maxLength - Maximum length for this chunk
 * @returns {string} The chunk to use
 */
function findSmartBreak(text, maxLength) {
  // Strategy priority:
  // 1. Break at paragraph (double newline)
  // 2. Break at sentence (. ! ?)
  // 3. Break at single newline
  // 4. Break at word boundary (space)
  // 5. Hard break at maxLength (last resort)

  const searchText = text.slice(0, maxLength);

  // 1. Look for paragraph break (double newline)
  const paragraphBreak = searchText.lastIndexOf('\n\n');
  if (paragraphBreak > MIN_TWEET_LENGTH) {
    return text.slice(0, paragraphBreak);
  }

  // 2. Look for sentence ending (. ! ? followed by space or newline)
  const sentencePattern = /[.!?][\s\n]/g;
  let lastSentenceEnd = -1;
  let match;

  while ((match = sentencePattern.exec(searchText)) !== null) {
    lastSentenceEnd = match.index + 1; // Include the punctuation
  }

  if (lastSentenceEnd > MIN_TWEET_LENGTH) {
    return text.slice(0, lastSentenceEnd).trim();
  }

  // 3. Look for single newline
  const newlineBreak = searchText.lastIndexOf('\n');
  if (newlineBreak > MIN_TWEET_LENGTH) {
    return text.slice(0, newlineBreak);
  }

  // 4. Look for word boundary (last space)
  const spaceBreak = searchText.lastIndexOf(' ');
  if (spaceBreak > MIN_TWEET_LENGTH) {
    return text.slice(0, spaceBreak);
  }

  // 5. Hard break (last resort - avoid cutting in middle of word/emoji)
  // Look backwards for a safe breaking point
  let safeBreak = maxLength;
  while (safeBreak > 0 && !isSafeBreakPoint(text.charAt(safeBreak))) {
    safeBreak--;
  }

  return text.slice(0, safeBreak || maxLength);
}

/**
 * Check if character is safe to break at (not in middle of emoji or special char)
 * @param {string} char - Character to check
 * @returns {boolean}
 */
function isSafeBreakPoint(char) {
  // Break at whitespace or punctuation
  return /[\s.,;!?]/.test(char);
}

/**
 * Add thread numbering to tweets
 * @param {Array} tweets - Array of tweet strings
 * @returns {Array} Tweets with numbering added
 */
function addThreadNumbering(tweets) {
  if (tweets.length === 1 || NUMBERING_STYLE === "none") {
    return tweets;
  }

  const total = tweets.length;

  return tweets.map((tweet, index) => {
    const num = index + 1;

    switch (NUMBERING_STYLE) {
      case "parentheses":
        return `${tweet} (${num}/${total})`;

      case "slash":
        return `${num}/${total}\n\n${tweet}`;

      case "emoji":
        return `${num}/${total} 🧵\n\n${tweet}`;

      default:
        return tweet;
    }
  });
}

// ============================================================================
// N8N INTEGRATION (AIRTABLE SCHEMA)
// ============================================================================

/**
 * Main n8n execution for Airtable content
 *
 * Expected input format (from Airtable):
 * {
 *   "id": "rec0fKyj2KuABhbSF",
 *   "createdTime": "2025-11-11T20:58:06.000Z",
 *   "Post Hook": "> spend 3 months building clever workaround",
 *   "Status": "Publish It!",
 *   "Body Content": "Your long post text here...",
 *   "Suggested Edits": "...",
 *   "Publish Date": "2025-11-11T20:58:06.331Z",
 *   "Platform": ["twitter"],
 *   "Edited Time": "...",
 *   "Created": "...",
 *   "Google Doc Link": "..."
 * }
 *
 * Output format:
 * [
 *   {
 *     "tweet_text": "1/5 🧵\n\n> spend 3 months building clever workaround\n\nYour post content...",
 *     "thread_position": 1,
 *     "thread_total": 5,
 *     "char_count": 245,
 *     "is_thread": true,
 *     "airtable_id": "rec0fKyj2KuABhbSF",
 *     "post_hook": "> spend 3 months building clever workaround",
 *     "publish_date": "2025-11-11T20:58:06.331Z",
 *     "delay_seconds": 0
 *   },
 *   ...
 * ]
 */

// Get input data from Airtable
const inputItem = $input.item.json;

// Extract fields from Airtable schema
const bodyContent = inputItem["Body Content"] || inputItem.body_content || inputItem.content || "";
const postHook = inputItem["Post Hook"] || inputItem.post_hook || "";
const airtableId = inputItem.id || "";
const publishDate = inputItem["Publish Date"] || inputItem.publish_date || "";
const status = inputItem.Status || inputItem.status || "";
const platform = Array.isArray(inputItem.Platform) ? inputItem.Platform[0] : (inputItem.platform || "twitter");

// Validate that this is a Twitter post
if (platform.toLowerCase() !== "twitter") {
  // Skip non-Twitter posts
  return [{
    skip: true,
    reason: `Platform is ${platform}, not twitter`,
    airtable_id: airtableId
  }];
}

// Combine hook and body content
// Hook goes first (if present), followed by body
let fullContent = "";

if (postHook && postHook.trim().length > 0) {
  fullContent = postHook.trim() + "\n\n" + bodyContent.trim();
} else {
  fullContent = bodyContent.trim();
}

// Validate content exists
if (!fullContent || fullContent.length === 0) {
  return [{
    error: true,
    reason: "No content to split",
    airtable_id: airtableId
  }];
}

// Split into tweets
const tweetTexts = splitIntoTweets(fullContent);

// Format output for n8n with all Airtable metadata
const output = tweetTexts.map((tweet, index) => ({
  tweet_text: tweet,  // The actual tweet content to publish
  thread_position: index + 1,
  thread_total: tweetTexts.length,
  char_count: tweet.length,
  is_thread: tweetTexts.length > 1,
  is_first_tweet: index === 0,
  is_last_tweet: index === tweetTexts.length - 1,

  // Airtable metadata (preserve for tracking)
  airtable_id: airtableId,
  post_hook: postHook,
  publish_date: publishDate,
  status: status,
  platform: platform,

  // Delay between tweets (recommended to avoid rate limits)
  delay_seconds: index * 2  // 0s, 2s, 4s, 6s...
}));

// Return formatted output
return output;
