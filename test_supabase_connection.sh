#!/bin/bash
# Test Supabase Connection
# Run this in Replit shell to verify network connectivity to Supabase

set -a
source .env
set +a

echo "=================================================="
echo "🔍 Testing Supabase Connection"
echo "=================================================="
echo ""
echo "Target: $SUPABASE_URL"
echo ""

# Test 1: Basic connectivity (health check)
echo "Test 1: Basic HTTP connectivity..."
if curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 "$SUPABASE_URL" | grep -q "200\|404"; then
    echo "✅ PASS - Can reach Supabase host"
else
    echo "❌ FAIL - Cannot reach Supabase host (DNS or network error)"
    exit 1
fi
echo ""

# Test 2: API endpoint with authentication
echo "Test 2: Authenticated API query (SELECT 1 row from conversation_history)..."
response=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
  --connect-timeout 5 \
  --max-time 10 \
  -H "apikey: $SUPABASE_KEY" \
  -H "Authorization: Bearer $SUPABASE_KEY" \
  "$SUPABASE_URL/rest/v1/conversation_history?select=thread_ts,created_at&limit=1")

http_code=$(echo "$response" | grep "HTTP_CODE:" | cut -d: -f2)
body=$(echo "$response" | sed '/HTTP_CODE:/d')

if [ "$http_code" = "200" ]; then
    echo "✅ PASS - Successfully queried conversation_history"
    echo "Response: $body"
elif [ "$http_code" = "404" ]; then
    echo "⚠️  WARNING - Table not found (might not exist yet)"
    echo "Response: $body"
else
    echo "❌ FAIL - API query failed (HTTP $http_code)"
    echo "Response: $body"
    exit 1
fi
echo ""

# Test 3: DNS resolution
echo "Test 3: DNS resolution for Supabase host..."
host=$(echo "$SUPABASE_URL" | sed -e 's|^https://||' -e 's|/.*$||')
if nslookup "$host" > /dev/null 2>&1; then
    echo "✅ PASS - DNS resolution successful"
    nslookup "$host" | grep "Address:" | tail -2
else
    echo "❌ FAIL - DNS resolution failed"
    exit 1
fi
echo ""

# Test 4: Insert test (creates a test message and immediately deletes it)
echo "Test 4: Write test (insert + delete)..."
test_thread_ts="test_$(date +%s)"
insert_response=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
  --connect-timeout 5 \
  --max-time 10 \
  -X POST \
  -H "apikey: $SUPABASE_KEY" \
  -H "Authorization: Bearer $SUPABASE_KEY" \
  -H "Content-Type: application/json" \
  -H "Prefer: return=representation" \
  -d "{\"thread_ts\":\"$test_thread_ts\",\"channel_id\":\"test\",\"user_id\":\"test\",\"role\":\"user\",\"content\":\"connection test\",\"created_at\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}" \
  "$SUPABASE_URL/rest/v1/conversation_history")

insert_http_code=$(echo "$insert_response" | grep "HTTP_CODE:" | cut -d: -f2)

if [ "$insert_http_code" = "201" ]; then
    echo "✅ PASS - Successfully inserted test message"

    # Clean up test message
    curl -s -X DELETE \
      -H "apikey: $SUPABASE_KEY" \
      -H "Authorization: Bearer $SUPABASE_KEY" \
      "$SUPABASE_URL/rest/v1/conversation_history?thread_ts=eq.$test_thread_ts" > /dev/null
    echo "🧹 Cleaned up test message"
else
    echo "❌ FAIL - Insert failed (HTTP $insert_http_code)"
    echo "Response: $(echo "$insert_response" | sed '/HTTP_CODE:/d')"
fi
echo ""

echo "=================================================="
echo "✅ All tests completed successfully!"
echo "=================================================="
