#!/usr/bin/env node
/**
 * Test OpenAI Embeddings
 *
 * Verifies that your OpenAI API key works and can generate embeddings
 * for the text-embedding-3-small model used in the bootstrap.
 *
 * Usage:
 *   node scripts/test_openai_embeddings.js
 */

require('dotenv').config();
const https = require('https');

const OPENAI_API_KEY = process.env.OPENAI_API_KEY;
const MODEL = 'text-embedding-3-small';
const TEST_TEXT = 'This is a test of the OpenAI embeddings API';

// Color codes
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  cyan: '\x1b[36m'
};

function log(emoji, message, color = colors.reset) {
  console.log(`${color}${emoji} ${message}${colors.reset}`);
}

if (!OPENAI_API_KEY) {
  console.log('');
  log('❌', 'OPENAI_API_KEY not found in environment', colors.red);
  console.log('');
  console.log('Add to your .env file:');
  console.log('  OPENAI_API_KEY=sk-proj-...');
  console.log('');
  console.log('Get your key from: https://platform.openai.com/api-keys');
  console.log('');
  process.exit(1);
}

async function testEmbeddings() {
  console.log('');
  log('🔍', 'Testing OpenAI Embeddings API...', colors.cyan);
  console.log('');

  // Check API key format
  if (!OPENAI_API_KEY.startsWith('sk-')) {
    log('⚠️', 'API key should start with "sk-"', colors.yellow);
    console.log(`   Current key starts with: ${OPENAI_API_KEY.substring(0, 10)}...`);
    console.log('');
  }

  log('📝', `Model: ${MODEL}`, colors.cyan);
  log('📝', `Test text: "${TEST_TEXT}"`, colors.cyan);
  console.log('');

  const data = JSON.stringify({
    input: TEST_TEXT,
    model: MODEL
  });

  const options = {
    hostname: 'api.openai.com',
    port: 443,
    path: '/v1/embeddings',
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${OPENAI_API_KEY}`,
      'Content-Length': data.length
    }
  };

  return new Promise((resolve, reject) => {
    const startTime = Date.now();

    const req = https.request(options, (res) => {
      let body = '';

      res.on('data', (chunk) => {
        body += chunk;
      });

      res.on('end', () => {
        const elapsed = Date.now() - startTime;

        try {
          const response = JSON.parse(body);

          if (res.statusCode === 200) {
            const embedding = response.data[0].embedding;
            const dimensions = embedding.length;
            const usage = response.usage;

            console.log('');
            log('✅', 'OpenAI API Key is valid!', colors.green);
            console.log('');
            log('📊', 'Response Details:', colors.cyan);
            console.log(`   Model: ${response.model}`);
            console.log(`   Dimensions: ${dimensions}`);
            console.log(`   Tokens used: ${usage.total_tokens}`);
            console.log(`   Response time: ${elapsed}ms`);
            console.log('');
            log('🔢', 'Sample embedding values:', colors.cyan);
            console.log(`   ${embedding.slice(0, 5).map(v => v.toFixed(6)).join(', ')}...`);
            console.log('');

            if (dimensions !== 1536) {
              log('⚠️', `Warning: Expected 1536 dimensions, got ${dimensions}`, colors.yellow);
              console.log('   Your database schema expects vector(1536)');
              console.log('');
            } else {
              log('✅', 'Vector dimensions match database schema (1536)', colors.green);
              console.log('');
            }

            log('✅', 'Everything looks good!', colors.green);
            console.log('');
            console.log('Your OpenAI API key is working correctly and can:');
            console.log('  ✅ Generate embeddings');
            console.log('  ✅ Use text-embedding-3-small model');
            console.log('  ✅ Return vectors compatible with your Supabase schema');
            console.log('');

            resolve();
          } else {
            console.log('');
            log('❌', `OpenAI API Error (${res.statusCode})`, colors.red);
            console.log('');

            if (response.error) {
              console.log(`Error type: ${response.error.type}`);
              console.log(`Message: ${response.error.message}`);
              console.log('');

              if (response.error.type === 'invalid_request_error') {
                if (response.error.message.includes('API key')) {
                  console.log('Solutions:');
                  console.log('  1. Check your API key is correct');
                  console.log('  2. Get a new key from: https://platform.openai.com/api-keys');
                  console.log('  3. Make sure key starts with "sk-"');
                  console.log('');
                } else if (response.error.message.includes('model')) {
                  console.log('Solutions:');
                  console.log('  1. Model might not be available in your account');
                  console.log('  2. Try: text-embedding-ada-002 (older model)');
                  console.log('  3. Check: https://platform.openai.com/docs/models');
                  console.log('');
                }
              } else if (response.error.type === 'insufficient_quota') {
                console.log('Solutions:');
                console.log('  1. Add credits to your OpenAI account');
                console.log('  2. Check billing: https://platform.openai.com/account/billing');
                console.log('');
              }
            }

            reject(new Error(response.error?.message || 'Unknown error'));
          }
        } catch (err) {
          console.log('');
          log('❌', 'Failed to parse response', colors.red);
          console.log('');
          console.log('Raw response:');
          console.log(body.substring(0, 500));
          console.log('');
          reject(err);
        }
      });
    });

    req.on('error', (err) => {
      console.log('');
      log('❌', 'Network error', colors.red);
      console.log('');
      console.log(`Error: ${err.message}`);
      console.log('');
      console.log('Possible issues:');
      console.log('  1. No internet connection');
      console.log('  2. Firewall blocking api.openai.com');
      console.log('  3. Proxy configuration needed');
      console.log('');
      reject(err);
    });

    req.on('timeout', () => {
      console.log('');
      log('❌', 'Request timed out', colors.red);
      console.log('');
      console.log('The request took too long to complete.');
      console.log('Check your internet connection and try again.');
      console.log('');
      req.destroy();
      reject(new Error('Request timeout'));
    });

    req.setTimeout(30000); // 30 second timeout
    req.write(data);
    req.end();
  });
}

// Run test
testEmbeddings()
  .then(() => {
    process.exit(0);
  })
  .catch((err) => {
    console.error('Test failed:', err.message);
    process.exit(1);
  });
