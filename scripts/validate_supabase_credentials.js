#!/usr/bin/env node
/**
 * Validates Supabase credentials before attempting connection
 * Helps diagnose "Tenant or user not found" errors
 */

require('dotenv').config();

function validateCredentials() {
  console.log('🔍 Validating Supabase credentials...\n');

  const dbUrl = process.env.SUPABASE_DB_URL;
  const apiUrl = process.env.SUPABASE_URL;
  const apiKey = process.env.SUPABASE_KEY;

  let hasErrors = false;

  // Check if credentials exist
  console.log('📋 Checking environment variables:');

  if (!dbUrl) {
    console.log('   ❌ SUPABASE_DB_URL missing');
    hasErrors = true;
  } else {
    console.log('   ✅ SUPABASE_DB_URL found');
  }

  if (!apiUrl) {
    console.log('   ❌ SUPABASE_URL missing');
    hasErrors = true;
  } else {
    console.log('   ✅ SUPABASE_URL found');
  }

  if (!apiKey) {
    console.log('   ❌ SUPABASE_KEY missing');
    hasErrors = true;
  } else {
    console.log('   ✅ SUPABASE_KEY found');
  }

  if (hasErrors) {
    console.log('\n❌ Missing required credentials. Check your .env file.\n');
    process.exit(1);
  }

  console.log('');

  // Parse connection string
  console.log('🔍 Parsing SUPABASE_DB_URL:\n');

  try {
    const url = new URL(dbUrl);

    console.log(`   Protocol: ${url.protocol}`);
    console.log(`   User: ${url.username}`);
    console.log(`   Password: ${'*'.repeat(10)} (${url.password.length} chars)`);
    console.log(`   Host: ${url.hostname}`);
    console.log(`   Port: ${url.port}`);
    console.log(`   Database: ${url.pathname.substring(1)}`);

    // Extract project reference from hostname
    const hostnameParts = url.hostname.split('.');
    let projectRef = null;

    if (hostnameParts[0].startsWith('postgres')) {
      // Pooler format: postgres.PROJECT.supabase.com
      projectRef = hostnameParts[1];
    } else if (hostnameParts[0] === 'db') {
      // Direct format: db.PROJECT.supabase.com
      projectRef = hostnameParts[1];
    }

    console.log(`   Project Reference: ${projectRef || 'Could not extract'}`);
    console.log('');

    // Validate project reference matches API URL
    if (projectRef && apiUrl) {
      const apiProjectRef = apiUrl.replace('https://', '').split('.')[0];

      console.log('🔗 Checking project reference consistency:\n');
      console.log(`   Database: ${projectRef}`);
      console.log(`   API URL:  ${apiProjectRef}`);

      if (projectRef === apiProjectRef) {
        console.log('   ✅ Project references match\n');
      } else {
        console.log('   ⚠️  Project references DO NOT match');
        console.log('   This might cause issues. Verify both are for the same project.\n');
        hasErrors = true;
      }
    }

    // Check for common issues
    console.log('⚠️  Common issues to check:\n');

    // Check password encoding
    const password = url.password;
    const specialChars = ['@', '#', '%', '&', '+', '=', '?'];
    const hasSpecialChars = specialChars.some(char => password.includes(char));

    if (hasSpecialChars) {
      console.log('   ⚠️  Password contains special characters');
      console.log('      These must be URL-encoded:');
      console.log('      @ → %40, # → %23, % → %25, & → %26');
      console.log('      Try resetting your database password to something simpler.\n');
      hasErrors = true;
    } else {
      console.log('   ✅ Password has no special characters\n');
    }

    // Check pooler type
    if (url.hostname.includes('pooler')) {
      console.log('   ✅ Using connection pooler (recommended)\n');
    } else if (url.hostname.includes('db.')) {
      console.log('   ⚠️  Using direct connection (not recommended)');
      console.log('      Consider switching to pooler for better performance:\n');
      console.log(`      postgresql://${url.username}:${url.password}@aws-1-us-east-1.pooler.supabase.com:5432/postgres\n`);
    }

    // Check SSL settings
    const sslParam = url.searchParams.get('sslmode');
    if (!sslParam) {
      console.log('   💡 No SSL mode specified');
      console.log('      If connection fails, try adding: ?sslmode=require\n');
    }

    // Check database name
    const dbName = url.pathname.substring(1);
    if (dbName !== 'postgres') {
      console.log('   ⚠️  Database name is not "postgres"');
      console.log(`      Found: "${dbName}"`);
      console.log('      Supabase typically uses "postgres" as the database name.\n');
      hasErrors = true;
    } else {
      console.log('   ✅ Database name is correct (postgres)\n');
    }

  } catch (err) {
    console.log('   ❌ Invalid connection string format');
    console.log(`   Error: ${err.message}\n`);
    hasErrors = true;
  }

  // Check API URL format
  console.log('🔍 Checking SUPABASE_URL format:\n');

  if (apiUrl.startsWith('https://') && apiUrl.includes('.supabase.co')) {
    console.log('   ✅ API URL format looks correct');
    console.log(`   ${apiUrl}\n`);
  } else {
    console.log('   ⚠️  API URL format looks incorrect');
    console.log(`   Found: ${apiUrl}`);
    console.log('   Expected: https://PROJECT.supabase.co\n');
    hasErrors = true;
  }

  // Check API key format
  console.log('🔍 Checking SUPABASE_KEY format:\n');

  if (apiKey.startsWith('eyJ')) {
    console.log('   ✅ API key format looks correct (JWT)\n');
  } else if (apiKey.startsWith('sb_secret_')) {
    console.log('   ⚠️  Using service_role key (secret key)');
    console.log('   This works but be careful with security.\n');
  } else {
    console.log('   ⚠️  API key format looks incorrect');
    console.log('   Expected to start with: eyJ (anon key) or sb_secret_ (service key)\n');
    hasErrors = true;
  }

  // Final verdict
  console.log('═'.repeat(60));

  if (hasErrors) {
    console.log('⚠️  Issues found - please review above warnings');
    console.log('');
    console.log('Next steps:');
    console.log('1. Fix the issues listed above');
    console.log('2. Run: npm run diagnose');
    console.log('3. If still failing, check Supabase project status\n');
    process.exit(1);
  } else {
    console.log('✅ Credentials look valid');
    console.log('');
    console.log('Next step: npm run diagnose (to test actual connection)\n');
    process.exit(0);
  }
}

validateCredentials();