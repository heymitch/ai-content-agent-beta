/**
 * Test File for Twitter Thread Splitter
 *
 * Run this with Node.js to test the splitter locally before using in n8n:
 * node test_twitter_splitter.js
 */

// Copy the core splitting logic from twitter_thread_splitter.js
const TWITTER_LIMIT = 280;
const THREAD_NUMBERING_SPACE = 10;
const MIN_TWEET_LENGTH = 50;
const NUMBERING_STYLE = "emoji";  // Change to test different styles

function splitIntoTweets(text) {
  if (!text || text.trim().length === 0) {
    return [];
  }

  const maxLength = TWITTER_LIMIT - THREAD_NUMBERING_SPACE;

  if (text.length <= TWITTER_LIMIT) {
    return [text];
  }

  const tweets = [];
  let remainingText = text.trim();

  while (remainingText.length > 0) {
    let chunk;

    if (remainingText.length <= maxLength) {
      chunk = remainingText;
      remainingText = "";
    } else {
      chunk = findSmartBreak(remainingText, maxLength);
      remainingText = remainingText.slice(chunk.length).trim();
    }

    tweets.push(chunk.trim());
  }

  return addThreadNumbering(tweets);
}

function findSmartBreak(text, maxLength) {
  const searchText = text.slice(0, maxLength);

  // 1. Paragraph break
  const paragraphBreak = searchText.lastIndexOf('\n\n');
  if (paragraphBreak > MIN_TWEET_LENGTH) {
    return text.slice(0, paragraphBreak);
  }

  // 2. Sentence ending
  const sentencePattern = /[.!?][\s\n]/g;
  let lastSentenceEnd = -1;
  let match;

  while ((match = sentencePattern.exec(searchText)) !== null) {
    lastSentenceEnd = match.index + 1;
  }

  if (lastSentenceEnd > MIN_TWEET_LENGTH) {
    return text.slice(0, lastSentenceEnd).trim();
  }

  // 3. Single newline
  const newlineBreak = searchText.lastIndexOf('\n');
  if (newlineBreak > MIN_TWEET_LENGTH) {
    return text.slice(0, newlineBreak);
  }

  // 4. Word boundary
  const spaceBreak = searchText.lastIndexOf(' ');
  if (spaceBreak > MIN_TWEET_LENGTH) {
    return text.slice(0, spaceBreak);
  }

  // 5. Hard break
  let safeBreak = maxLength;
  while (safeBreak > 0 && !/[\s.,;!?]/.test(text.charAt(safeBreak))) {
    safeBreak--;
  }

  return text.slice(0, safeBreak || maxLength);
}

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
// TEST CASES
// ============================================================================

console.log("🧪 Testing Twitter Thread Splitter\n");
console.log("=" .repeat(80));

// Test 1: Short post (no split)
console.log("\n📝 Test 1: Short Post (No Split Needed)");
console.log("-".repeat(80));
const shortPost = "This is a short post that fits in one tweet easily.";
const result1 = splitIntoTweets(shortPost);
console.log(`Input length: ${shortPost.length} chars`);
console.log(`Output: ${result1.length} tweet(s)\n`);
result1.forEach((tweet, i) => {
  console.log(`Tweet ${i + 1} (${tweet.length} chars):`);
  console.log(tweet);
  console.log();
});

// Test 2: Long post with paragraphs
console.log("\n📝 Test 2: Long Post with Paragraphs");
console.log("-".repeat(80));
const longPost = `This is a longer post that demonstrates how the thread splitter works.

It intelligently breaks at paragraph boundaries first. If a paragraph is too long, it will break at sentence endings.

This ensures your threads are readable and flow naturally. No more awkward mid-sentence cuts!

The splitter also adds thread numbering so readers know there's more to come.`;
const result2 = splitIntoTweets(longPost);
console.log(`Input length: ${longPost.length} chars`);
console.log(`Output: ${result2.length} tweet(s)\n`);
result2.forEach((tweet, i) => {
  console.log(`Tweet ${i + 1} (${tweet.length} chars):`);
  console.log(tweet);
  console.log();
});

// Test 3: Very long sentence
console.log("\n📝 Test 3: Very Long Sentence (No Natural Breaks)");
console.log("-".repeat(80));
const longSentence = "This is an extremely long sentence without any periods or paragraph breaks that goes on and on and will force the splitter to break at word boundaries because there are no natural sentence endings to use as breaking points which is not ideal but the splitter handles it gracefully by finding the last space before the character limit and making sure we don't cut in the middle of a word which would look unprofessional.";
const result3 = splitIntoTweets(longSentence);
console.log(`Input length: ${longSentence.length} chars`);
console.log(`Output: ${result3.length} tweet(s)\n`);
result3.forEach((tweet, i) => {
  console.log(`Tweet ${i + 1} (${tweet.length} chars):`);
  console.log(tweet);
  console.log();
});

// Test 4: Real-world example (technical content)
console.log("\n📝 Test 4: Real-World Example (Technical Content)");
console.log("-".repeat(80));
const technicalPost = `AI agents are transforming content creation, but there's a critical gap most teams miss:

The handoff between generation and publishing.

We built a system that generates LinkedIn posts, validates quality (GPTZero + Editor-in-Chief), saves to Airtable, and syncs analytics back to Supabase.

The key insight? Batch mode with per-post timeout handling. Single posts use Haiku fast path (~300ms). Complex threads use full validation (~60s).

Result: 50+ post batches without timeouts. Quality scores in Supabase. Real engagement metrics from Ayrshare.

Most teams focus on generation quality. We focused on the entire workflow: create → validate → publish → analyze → improve.

That's the difference between a demo and production.`;
const result4 = splitIntoTweets(technicalPost);
console.log(`Input length: ${technicalPost.length} chars`);
console.log(`Output: ${result4.length} tweet(s)\n`);
result4.forEach((tweet, i) => {
  console.log(`Tweet ${i + 1} (${tweet.length} chars):`);
  console.log(tweet);
  console.log();
});

// Summary
console.log("\n" + "=".repeat(80));
console.log("✅ All tests complete!\n");
console.log("Summary:");
console.log(`  Test 1: ${result1.length} tweet(s) - Short post`);
console.log(`  Test 2: ${result2.length} tweet(s) - Long post with paragraphs`);
console.log(`  Test 3: ${result3.length} tweet(s) - Very long sentence`);
console.log(`  Test 4: ${result4.length} tweet(s) - Real-world example`);
console.log("\nReady to use in n8n! 🚀");
