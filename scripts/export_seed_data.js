#!/usr/bin/env node
/**
 * Export Seed Data from Supabase
 *
 * Exports content_examples and research data to sql/002_seed_data.sql
 * so clients get proven content examples when they bootstrap.
 */

require('dotenv').config();
const { Client } = require('pg');
const fs = require('fs');
const path = require('path');

const DB_URL = process.env.SUPABASE_DB_URL;

if (!DB_URL) {
  console.error('❌ SUPABASE_DB_URL not set in .env');
  process.exit(1);
}

async function exportData() {
  const client = new Client({
    connectionString: DB_URL,
    ssl: { rejectUnauthorized: false }
  });

  try {
    await client.connect();
    console.log('✅ Connected to Supabase');

    // Export content_examples
    const { rows: examples } = await client.query(`
      SELECT * FROM content_examples
      WHERE status = 'approved'
      ORDER BY created_at DESC
    `);

    // Export research
    const { rows: research } = await client.query(`
      SELECT * FROM research
      WHERE status = 'active'
      ORDER BY created_at DESC
    `);

    console.log(`📊 Found ${examples.length} content examples`);
    console.log(`📊 Found ${research.length} research entries`);

    // Generate SQL INSERT statements
    let sql = `-- ============================================================================
-- Seed Data: Content Examples & Research
-- ============================================================================
-- This file contains proven content examples and research data
-- Safe to run multiple times (uses ON CONFLICT DO NOTHING)
--
-- Exported: ${new Date().toISOString()}
-- ============================================================================

`;

    // Content examples
    if (examples.length > 0) {
      sql += `\n-- Content Examples (${examples.length} rows)\n`;

      for (const row of examples) {
        const values = [
          `'${row.id}'`,
          row.platform ? `'${row.platform.replace(/'/g, "''")}'` : 'NULL',
          row.content ? `'${row.content.replace(/'/g, "''")}'` : 'NULL',
          row.human_score || 'NULL',
          row.engagement_rate || 'NULL',
          row.impressions || 'NULL',
          row.clicks || 'NULL',
          row.content_type ? `'${row.content_type.replace(/'/g, "''")}'` : 'NULL',
          row.creator ? `'${row.creator.replace(/'/g, "''")}'` : 'NULL',
          row.hook_line ? `'${row.hook_line.replace(/'/g, "''")}'` : 'NULL',
          row.main_points ? `'${JSON.stringify(row.main_points).replace(/'/g, "''")}'::text[]` : 'NULL',
          row.cta_line ? `'${row.cta_line.replace(/'/g, "''")}'` : 'NULL',
          row.tags ? `'${JSON.stringify(row.tags).replace(/'/g, "''")}'::text[]` : 'NULL',
          row.topics ? `'${JSON.stringify(row.topics).replace(/'/g, "''")}'::text[]` : 'NULL',
          'NULL', // embedding (too large, clients will regenerate)
          row.created_at ? `'${row.created_at.toISOString()}'` : 'NOW()',
          row.updated_at ? `'${row.updated_at.toISOString()}'` : 'NOW()',
          row.status ? `'${row.status}'` : "'approved'"
        ];

        sql += `INSERT INTO content_examples (id, platform, content, human_score, engagement_rate, impressions, clicks, content_type, creator, hook_line, main_points, cta_line, tags, topics, embedding, created_at, updated_at, status)
VALUES (${values.join(', ')})
ON CONFLICT (id) DO NOTHING;\n\n`;
      }
    }

    // Research
    if (research.length > 0) {
      sql += `\n-- Research Entries (${research.length} rows)\n`;

      for (const row of research) {
        const values = [
          `'${row.id}'`,
          row.topic ? `'${row.topic.replace(/'/g, "''")}'` : 'NULL',
          row.summary ? `'${row.summary.replace(/'/g, "''")}'` : 'NULL',
          row.full_report ? `'${row.full_report.replace(/'/g, "''")}'` : 'NULL',
          row.key_stats ? `'${JSON.stringify(row.key_stats).replace(/'/g, "''")}'::text[]` : 'NULL',
          row.source_urls ? `'${JSON.stringify(row.source_urls).replace(/'/g, "''")}'::text[]` : 'NULL',
          row.source_names ? `'${JSON.stringify(row.source_names).replace(/'/g, "''")}'::text[]` : 'NULL',
          row.primary_source ? `'${row.primary_source.replace(/'/g, "''")}'` : 'NULL',
          row.credibility_score || 5,
          row.research_date ? `'${row.research_date.toISOString().split('T')[0]}'` : 'CURRENT_DATE',
          row.last_verified ? `'${row.last_verified.toISOString().split('T')[0]}'` : 'NULL',
          row.used_in_content_ids ? `'${JSON.stringify(row.used_in_content_ids).replace(/'/g, "''")}'::uuid[]` : 'NULL',
          row.usage_count || 0,
          row.topics ? `'${JSON.stringify(row.topics).replace(/'/g, "''")}'::text[]` : 'NULL',
          'NULL', // embedding
          row.created_at ? `'${row.created_at.toISOString()}'` : 'NOW()',
          row.updated_at ? `'${row.updated_at.toISOString()}'` : 'NOW()',
          row.status ? `'${row.status}'` : "'active'"
        ];

        sql += `INSERT INTO research (id, topic, summary, full_report, key_stats, source_urls, source_names, primary_source, credibility_score, research_date, last_verified, used_in_content_ids, usage_count, topics, embedding, created_at, updated_at, status)
VALUES (${values.join(', ')})
ON CONFLICT (id) DO NOTHING;\n\n`;
      }
    }

    sql += `\n-- ============================================================================
-- Success Message
-- ============================================================================

DO $$
BEGIN
  RAISE NOTICE '✅ Seed data loaded!';
  RAISE NOTICE '   ${examples.length} content examples';
  RAISE NOTICE '   ${research.length} research entries';
  RAISE NOTICE '';
  RAISE NOTICE '💡 Note: Vector embeddings are NULL and will be generated when used.';
END $$;
`;

    // Write to file
    const outputPath = path.join(__dirname, '..', 'sql', '002_seed_data.sql');
    fs.writeFileSync(outputPath, sql, 'utf8');

    console.log('');
    console.log(`✅ Exported to: ${outputPath}`);
    console.log('');
    console.log('📝 Summary:');
    console.log(`   ${examples.length} content examples`);
    console.log(`   ${research.length} research entries`);
    console.log('');
    console.log('💡 This will be automatically applied when clients run npm start');
    console.log('');

  } catch (err) {
    console.error('❌ Error:', err.message);
    process.exit(1);
  } finally {
    await client.end();
  }
}

exportData();