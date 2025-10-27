#!/bin/bash

# Run all mock tests without burning API credits
# Usage: ./tests/run_all_tests.sh

echo "=========================================="
echo "🧪 RUNNING COMPLETE TEST SUITE (NO API)"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track results
TOTAL_TESTS=0
PASSED_TESTS=0

# Function to run a test
run_test() {
    local test_name=$1
    local test_file=$2

    echo -e "${YELLOW}Running: $test_name${NC}"
    echo "----------------------------------------"

    if python3 $test_file; then
        echo -e "${GREEN}✅ $test_name PASSED${NC}"
        ((PASSED_TESTS++))
    else
        echo -e "${RED}❌ $test_name FAILED${NC}"
    fi
    ((TOTAL_TESTS++))
    echo ""
}

# Run all tests
run_test "Full System Mock" "tests/test_full_system_mock.py"
run_test "Tool Validation" "tests/test_tool_validation.py"
run_test "Batch Orchestrator" "tests/test_batch_orchestrator_mock.py"
run_test "Multi-Platform Mock" "test_multi_platform_mock.py"

# Summary
echo "=========================================="
echo "📊 FINAL TEST REPORT"
echo "=========================================="
echo -e "Tests Run: $TOTAL_TESTS"
echo -e "Tests Passed: ${GREEN}$PASSED_TESTS${NC}"
echo -e "Tests Failed: ${RED}$((TOTAL_TESTS - PASSED_TESTS))${NC}"

if [ $PASSED_TESTS -eq $TOTAL_TESTS ]; then
    echo ""
    echo -e "${GREEN}🎉 ALL TESTS PASSED!${NC}"
    echo "Your 3-tier system is working perfectly!"
    echo "No API credits were harmed in this testing 💰"
    exit 0
else
    echo ""
    echo -e "${RED}⚠️ Some tests failed${NC}"
    echo "Please review the output above for details"
    exit 1
fi