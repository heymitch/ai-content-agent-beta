#!/usr/bin/env node
/**
 * Test Supabase connection from Replit
 * Tests both Transaction pooler (6543) and Direct (5432) connections
 */

const { Client } = require('pg');
require('dotenv').config();

const colors = {
  reset: '\x1b[0m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  cyan: '\x1b[36m'
};

async function testConnection(url, name) {
  console.log(`\n${colors.cyan}🔌 Testing ${name}...${colors.reset}`);

  const client = new Client({
    connectionString: url,
    ssl: { rejectUnauthorized: false },
    connectionTimeoutMillis: 15000
  });

  try {
    await client.connect();
    console.log(`${colors.green}✅ Connected successfully!${colors.reset}`);

    // Try a simple query
    const result = await client.query('SELECT NOW() as current_time');
    console.log(`${colors.green}✅ Query successful: ${result.rows[0].current_time}${colors.reset}`);

    await client.end();
    return true;
  } catch (err) {
    console.log(`${colors.red}❌ Failed: ${err.message}${colors.reset}`);
    return false;
  }
}

async function main() {
  console.log('\n' + '='.repeat(60));
  console.log('🧪 SUPABASE CONNECTION TEST');
  console.log('='.repeat(60));

  const dbUrl = process.env.SUPABASE_DB_URL;

  if (!dbUrl) {
    console.log(`\n${colors.red}❌ SUPABASE_DB_URL not found in environment${colors.reset}`);
    console.log(`${colors.yellow}Please add it to your .env file${colors.reset}`);
    process.exit(1);
  }

  // Parse the URL to check which port is being used
  const urlMatch = dbUrl.match(/:(\d+)\//);
  const port = urlMatch ? urlMatch[1] : 'unknown';

  console.log(`\n📋 Connection Details:`);
  console.log(`   Port: ${port}`);
  console.log(`   Type: ${port === '5432' ? 'Direct connection' : port === '6543' ? 'Transaction pooler ✅' : 'Unknown'}`);

  if (port === '5432') {
    console.log(`\n${colors.yellow}⚠️  WARNING: Using Direct connection (port 5432)${colors.reset}`);
    console.log(`${colors.yellow}   For Replit, use Transaction pooler (port 6543) instead${colors.reset}`);
  }

  // Test the configured connection
  const success = await testConnection(dbUrl, 'Your SUPABASE_DB_URL');

  console.log('\n' + '='.repeat(60));
  if (success) {
    console.log(`${colors.green}🎉 Connection test PASSED!${colors.reset}`);
    console.log(`${colors.green}   Bootstrap should work on Replit${colors.reset}`);
  } else {
    console.log(`${colors.red}❌ Connection test FAILED${colors.reset}`);
    console.log(`\n${colors.yellow}Troubleshooting steps:${colors.reset}`);
    console.log('   1. Use Transaction pooler URL (port 6543, not 5432)');
    console.log('   2. Get it from: Supabase Dashboard → Settings → Database → Connection String');
    console.log('   3. Select "Transaction pooler" mode');
    console.log('   4. Check for special characters in password (encode $ as %24)');
    console.log('   5. Verify your Supabase project is not paused');
  }
  console.log('='.repeat(60) + '\n');
}

main().catch(console.error);
