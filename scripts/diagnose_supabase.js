#!/usr/bin/env node
/**
 * Supabase Connection Diagnostic Script
 * Checks extensions, tables, and RPC functions
 */

const { Pool } = require('pg');
require('dotenv').config();

async function diagnose() {
  const connectionString = process.env.SUPABASE_DB_URL;

  if (!connectionString) {
    console.error('❌ SUPABASE_DB_URL not found in .env');
    process.exit(1);
  }

  console.log('🔍 Diagnosing Supabase connection...\n');
  console.log(`📍 Connecting to: ${connectionString.replace(/:[^:@]+@/, ':****@')}\n`);

  const pool = new Pool({ connectionString });

  try {
    // Test connection
    const client = await pool.connect();
    console.log('✅ Connection successful\n');

    // Check extensions
    console.log('📦 Checking extensions:');
    const extensionsResult = await client.query(`
      SELECT extname, extversion
      FROM pg_extension
      WHERE extname IN ('uuid-ossp', 'vector');
    `);

    if (extensionsResult.rows.length === 0) {
      console.log('❌ No required extensions found');
      console.log('   Run this in Supabase SQL Editor:');
      console.log('   CREATE EXTENSION IF NOT EXISTS "uuid-ossp";');
      console.log('   CREATE EXTENSION IF NOT EXISTS vector;\n');
    } else {
      extensionsResult.rows.forEach(row => {
        console.log(`   ✅ ${row.extname} (v${row.extversion})`);
      });
      console.log('');
    }

    // Check tables
    console.log('📋 Checking tables:');
    const tablesResult = await client.query(`
      SELECT tablename
      FROM pg_tables
      WHERE schemaname = 'public'
      AND tablename IN ('company_documents', 'content_examples', 'conversation_history', 'research')
      ORDER BY tablename;
    `);

    if (tablesResult.rows.length === 0) {
      console.log('❌ No tables found - database appears empty');
      console.log('   Run: npm run bootstrap\n');
    } else {
      tablesResult.rows.forEach(row => {
        console.log(`   ✅ ${row.tablename}`);
      });
      console.log('');
    }

    // Check RPC functions
    console.log('🔧 Checking RPC functions:');
    const functionsResult = await client.query(`
      SELECT
        p.proname as function_name,
        pg_get_function_result(p.oid) as return_type
      FROM pg_proc p
      JOIN pg_namespace n ON p.pronamespace = n.oid
      WHERE n.nspname = 'public'
      AND p.proname IN ('match_company_documents', 'match_content_examples', 'match_research')
      ORDER BY p.proname;
    `);

    if (functionsResult.rows.length === 0) {
      console.log('❌ No RPC functions found');
      console.log('   Run: npm run bootstrap\n');
    } else {
      functionsResult.rows.forEach(row => {
        console.log(`   ✅ ${row.function_name}`);
        console.log(`      Returns: ${row.return_type.substring(0, 80)}...`);
      });
      console.log('');
    }

    // Check for migration tracking table
    console.log('📝 Checking migration history:');
    const migrationTableCheck = await client.query(`
      SELECT EXISTS (
        SELECT FROM pg_tables
        WHERE schemaname = 'public'
        AND tablename = 'schema_migrations'
      ) as exists;
    `);

    if (migrationTableCheck.rows[0].exists) {
      const migrationsResult = await client.query(`
        SELECT migration_name, applied_at
        FROM schema_migrations
        ORDER BY applied_at DESC
        LIMIT 5;
      `);

      console.log(`   ✅ Found ${migrationsResult.rows.length} applied migrations:`);
      migrationsResult.rows.forEach(row => {
        const date = new Date(row.applied_at).toISOString().split('T')[0];
        console.log(`      - ${row.migration_name} (${date})`);
      });
      console.log('');
    } else {
      console.log('   ⚠️  No schema_migrations table found');
      console.log('      Bootstrap may not have completed successfully\n');
    }

    // Check company_documents structure if it exists
    if (tablesResult.rows.find(r => r.tablename === 'company_documents')) {
      console.log('🔍 Checking company_documents structure:');
      const columnsResult = await client.query(`
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'company_documents'
        AND column_name IN ('id', 'title', 'content', 'document_type', 'embedding', 'voice_description', 'signature_phrases')
        ORDER BY ordinal_position;
      `);

      const expectedColumns = ['id', 'title', 'content', 'document_type', 'embedding', 'voice_description', 'signature_phrases'];
      const foundColumns = columnsResult.rows.map(r => r.column_name);

      expectedColumns.forEach(col => {
        const found = foundColumns.includes(col);
        const row = columnsResult.rows.find(r => r.column_name === col);
        if (found) {
          console.log(`   ✅ ${col}: ${row.data_type}`);
        } else {
          console.log(`   ❌ ${col}: MISSING`);
        }
      });
      console.log('');
    }

    client.release();

    console.log('✅ Diagnostic complete');

  } catch (err) {
    console.error('❌ Diagnostic failed:');
    console.error(err.message);

    if (err.message.includes('password authentication failed')) {
      console.log('\n💡 Fix: Check your SUPABASE_DB_URL password');
    } else if (err.message.includes('does not exist')) {
      console.log('\n💡 Fix: Run migration 001_full_database.sql first');
    } else if (err.message.includes('could not connect')) {
      console.log('\n💡 Fix: Check network connection to Supabase');
    }

    process.exit(1);
  } finally {
    await pool.end();
  }
}

diagnose();