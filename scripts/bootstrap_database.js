#!/usr/bin/env node
/**
 * Bootstrap Database Setup
 *
 * Automatically sets up the user's Supabase database on first run.
 * Loads the exact database schema + data from sql/001_full_database.sql
 *
 * This gives new users:
 * - All tables (content_examples, research, company_documents, generated_posts, etc.)
 * - All your actual data (content examples, research, embeddings)
 * - All functions (match_research, search_generated_posts, etc.)
 * - All RLS policies
 * - All indexes (including IVFFlat for vector search)
 * - Extensions (uuid-ossp, pgvector)
 *
 * Requirements:
 * - SUPABASE_DB_URL in Replit Secrets or .env
 *   Format: postgresql://postgres:PASSWORD@db.PROJECT.supabase.co:5432/postgres
 *   Use "Transaction pooler" connection string from Supabase (works best with Replit)
 *
 * Usage:
 * - Runs automatically via package.json prestart hook on Replit
 * - Can also run manually: node scripts/bootstrap_database.js
 * - Safe to run multiple times (idempotent via _migrations table)
 */

const { Client } = require('pg');
const fs = require('fs');
const path = require('path');

const DB_URL = process.env.SUPABASE_DB_URL;
const MIGRATIONS_TABLE = '_migrations';
const SQL_DIR = path.join(__dirname, '..', 'sql');

// Color codes for terminal output
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m'
};

function log(emoji, message, color = colors.reset) {
  console.log(`${color}${emoji} ${message}${colors.reset}`);
}

// Check if DB URL is set
if (!DB_URL) {
  console.log('');
  log('⚠️', 'SUPABASE_DB_URL not set in environment', colors.yellow);
  console.log('');
  console.log('To set up your database, add SUPABASE_DB_URL to:');
  console.log('  - Replit Secrets (for deployed apps)');
  console.log('  - .env file (for local development)');
  console.log('');
  console.log('Get your DB URL from: https://supabase.com/dashboard');
  console.log('→ Project Settings → Database → Connection String');
  console.log('→ Select "Transaction pooler" (works best with Replit)');
  console.log('');
  console.log('Format: postgresql://postgres:PASSWORD@db.PROJECT.supabase.co:6543/postgres');
  console.log('');
  log('⏭️', 'Skipping database bootstrap...', colors.yellow);
  console.log('');
  process.exit(0);
}

async function bootstrap() {
  console.log('');
  log('🔄', 'Starting database bootstrap...', colors.cyan);
  console.log('');

  const client = new Client({
    connectionString: DB_URL,
    ssl: { rejectUnauthorized: false },
    connectionTimeoutMillis: 15000,
    // Disable prepared statements for Transaction pooler compatibility
    statement_timeout: 60000
  });

  try {
    // Connect to database
    await client.connect();
    log('✅', 'Connected to Supabase database', colors.green);
    console.log('');

    // Create migrations tracking table
    await client.query(`
      CREATE TABLE IF NOT EXISTS ${MIGRATIONS_TABLE} (
        id SERIAL PRIMARY KEY,
        filename TEXT UNIQUE NOT NULL,
        applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
      );
    `);

    // Get list of SQL files in order
    if (!fs.existsSync(SQL_DIR)) {
      log('⚠️', `SQL directory not found: ${SQL_DIR}`, colors.yellow);
      console.log('');
      return;
    }

    const files = fs.readdirSync(SQL_DIR)
      .filter(f => f.endsWith('.sql'))
      .sort(); // Lexical sort: 001_*.sql, 002_*.sql, etc.

    if (files.length === 0) {
      log('⚠️', 'No SQL migration files found in sql/ directory', colors.yellow);
      console.log('');
      return;
    }

    log('📁', `Found ${files.length} SQL file(s) to apply`, colors.blue);
    console.log('');

    // Apply each migration
    for (const file of files) {
      // Check if already applied
      const { rows } = await client.query(
        `SELECT 1 FROM ${MIGRATIONS_TABLE} WHERE filename = $1`,
        [file]
      );

      if (rows.length > 0) {
        log('⏭️', `Already applied: ${file}`, colors.yellow);
        continue;
      }

      // Read SQL file
      const filePath = path.join(SQL_DIR, file);
      const sql = fs.readFileSync(filePath, 'utf8');
      const sizeKB = (Buffer.byteLength(sql, 'utf8') / 1024).toFixed(1);

      log('📝', `Applying: ${file} (${sizeKB} KB)...`, colors.cyan);

      try {
        await client.query('BEGIN');

        // Execute SQL (this may take a while for large files)
        await client.query(sql);

        // Record migration
        await client.query(
          `INSERT INTO ${MIGRATIONS_TABLE} (filename) VALUES ($1)`,
          [file]
        );

        await client.query('COMMIT');
        log('✅', `Applied: ${file}`, colors.green);
        console.log('');
      } catch (err) {
        await client.query('ROLLBACK');
        console.log('');
        log('❌', `ERROR applying ${file}:`, colors.red);
        console.error(err.message);
        console.log('');
        console.log('Possible solutions:');
        console.log('  1. Check if extensions are enabled (uuid-ossp, vector)');
        console.log('  2. Verify your SUPABASE_DB_URL is correct');
        console.log('  3. Check Supabase logs for more details');
        console.log('');
        throw err;
      }
    }

    console.log('');
    log('🎉', 'Database bootstrap complete!', colors.green);
    console.log('');
    console.log('Your database now includes:');
    console.log('  ✅ All tables (content_examples, research, generated_posts, etc.)');
    console.log('  ✅ Vector embeddings and semantic search');
    console.log('  ✅ All RPC functions and RLS policies');
    console.log('  ✅ Starter content and examples');
    console.log('');

  } catch (err) {
    console.log('');
    log('❌', 'Bootstrap failed:', colors.red);
    console.error(err.message);
    console.log('');
    console.log('Troubleshooting:');
    console.log('  1. Verify SUPABASE_DB_URL format:');
    console.log('     postgresql://postgres:PASSWORD@db.PROJECT.supabase.co:5432/postgres');
    console.log('  2. Check that you can connect to Supabase from this machine');
    console.log('  3. Enable required extensions in Supabase SQL Editor:');
    console.log('     CREATE EXTENSION IF NOT EXISTS "uuid-ossp";');
    console.log('     CREATE EXTENSION IF NOT EXISTS vector;');
    console.log('');
    process.exit(1);
  } finally {
    await client.end();
  }
}

// Run bootstrap
bootstrap();
