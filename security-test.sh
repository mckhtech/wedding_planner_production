#!/bin/bash

# ============================================
# API Security Testing Suite
# ============================================
# Tests for data leakage, authentication, rate limiting, and more
# Run this script to verify production readiness

API_URL="https://api.preweddingai.mckhtech.com"
# For local testing: API_URL="http://localhost:8000"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_WARNING=0

# Function to print test results
print_test() {
    local test_name=$1
    local result=$2
    local message=$3
    
    if [ "$result" = "PASS" ]; then
        echo -e "${GREEN}✓ PASS${NC} - $test_name"
        [ -n "$message" ] && echo -e "  ${BLUE}→${NC} $message"
        ((TESTS_PASSED++))
    elif [ "$result" = "FAIL" ]; then
        echo -e "${RED}✗ FAIL${NC} - $test_name"
        [ -n "$message" ] && echo -e "  ${RED}→${NC} $message"
        ((TESTS_FAILED++))
    elif [ "$result" = "WARN" ]; then
        echo -e "${YELLOW}⚠ WARN${NC} - $test_name"
        [ -n "$message" ] && echo -e "  ${YELLOW}→${NC} $message"
        ((TESTS_WARNING++))
    fi
}

echo "============================================"
echo "🔒 API Security Testing Suite"
echo "============================================"
echo "Testing: $API_URL"
echo ""

# ============================================
# 1. BASIC CONNECTIVITY & HEALTH
# ============================================

echo -e "${BLUE}[1] Basic Connectivity Tests${NC}"
echo "─────────────────────────────────────────"

# Test 1.1: Health endpoint
HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" "$API_URL/health")
HTTP_CODE=$(echo "$HEALTH_RESPONSE" | tail -n1)
BODY=$(echo "$HEALTH_RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
    print_test "Health endpoint accessible" "PASS" "Status: $HTTP_CODE"
else
    print_test "Health endpoint accessible" "FAIL" "Status: $HTTP_CODE"
fi

# Test 1.2: Check for sensitive data in health response
if echo "$BODY" | grep -qi "password\|secret\|key"; then
    print_test "Health endpoint data leakage" "FAIL" "Sensitive data found in response"
else
    print_test "Health endpoint data leakage" "PASS" "No sensitive data exposed"
fi

# Test 1.3: Root endpoint
ROOT_RESPONSE=$(curl -s -w "\n%{http_code}" "$API_URL/")
HTTP_CODE=$(echo "$ROOT_RESPONSE" | tail -n1)

if [ "$HTTP_CODE" = "200" ]; then
    print_test "Root endpoint accessible" "PASS"
else
    print_test "Root endpoint accessible" "FAIL" "Status: $HTTP_CODE"
fi

echo ""

# ============================================
# 2. SECURITY HEADERS
# ============================================

echo -e "${BLUE}[2] Security Headers Tests${NC}"
echo "─────────────────────────────────────────"

HEADERS=$(curl -s -I "$API_URL/health")

# Test 2.1: X-Frame-Options
if echo "$HEADERS" | grep -qi "X-Frame-Options: DENY"; then
    print_test "X-Frame-Options header" "PASS" "Clickjacking protection enabled"
else
    print_test "X-Frame-Options header" "FAIL" "Missing clickjacking protection"
fi

# Test 2.2: X-Content-Type-Options
if echo "$HEADERS" | grep -qi "X-Content-Type-Options: nosniff"; then
    print_test "X-Content-Type-Options header" "PASS" "MIME sniffing prevention enabled"
else
    print_test "X-Content-Type-Options header" "FAIL" "Missing MIME sniffing protection"
fi

# Test 2.3: X-XSS-Protection
if echo "$HEADERS" | grep -qi "X-XSS-Protection"; then
    print_test "X-XSS-Protection header" "PASS" "XSS protection enabled"
else
    print_test "X-XSS-Protection header" "WARN" "XSS protection header missing"
fi

# Test 2.4: Strict-Transport-Security (HSTS)
if echo "$HEADERS" | grep -qi "Strict-Transport-Security"; then
    print_test "HSTS header" "PASS" "HTTPS enforcement enabled"
else
    print_test "HSTS header" "WARN" "HSTS not configured (OK if testing locally)"
fi

# Test 2.5: Content-Security-Policy
if echo "$HEADERS" | grep -qi "Content-Security-Policy"; then
    print_test "Content-Security-Policy header" "PASS" "CSP configured"
else
    print_test "Content-Security-Policy header" "WARN" "CSP not configured"
fi

# Test 2.6: Server header leakage
if echo "$HEADERS" | grep -qi "Server: uvicorn"; then
    print_test "Server header leakage" "WARN" "Server type exposed"
else
    print_test "Server header leakage" "PASS" "Server type hidden"
fi

echo ""

# ============================================
# 3. AUTHENTICATION TESTS
# ============================================

echo -e "${BLUE}[3] Authentication & Authorization Tests${NC}"
echo "─────────────────────────────────────────"

# Test 3.1: Protected endpoint without token
AUTH_RESPONSE=$(curl -s -w "\n%{http_code}" "$API_URL/api/auth/me")
HTTP_CODE=$(echo "$AUTH_RESPONSE" | tail -n1)
BODY=$(echo "$AUTH_RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "401" ]; then
    print_test "Protected endpoint requires auth" "PASS" "Correctly returns 401"
else
    print_test "Protected endpoint requires auth" "FAIL" "Expected 401, got $HTTP_CODE"
fi

# Test 3.2: Check error message doesn't leak info
if echo "$BODY" | grep -qi "database\|sql\|traceback\|stack"; then
    print_test "Error message data leakage" "FAIL" "Internal details exposed in error"
else
    print_test "Error message data leakage" "PASS" "Error messages sanitized"
fi

# Test 3.3: Invalid token
INVALID_TOKEN_RESPONSE=$(curl -s -w "\n%{http_code}" \
    -H "Authorization: Bearer invalid_token_12345" \
    "$API_URL/api/auth/me")
HTTP_CODE=$(echo "$INVALID_TOKEN_RESPONSE" | tail -n1)

if [ "$HTTP_CODE" = "401" ]; then
    print_test "Invalid token rejected" "PASS" "Invalid tokens properly rejected"
else
    print_test "Invalid token rejected" "FAIL" "Invalid token not properly rejected"
fi

# Test 3.4: Malformed authorization header
MALFORMED_AUTH=$(curl -s -w "\n%{http_code}" \
    -H "Authorization: InvalidFormat" \
    "$API_URL/api/auth/me")
HTTP_CODE=$(echo "$MALFORMED_AUTH" | tail -n1)

if [ "$HTTP_CODE" = "401" ] || [ "$HTTP_CODE" = "403" ]; then
    print_test "Malformed auth header handled" "PASS"
else
    print_test "Malformed auth header handled" "FAIL" "Got $HTTP_CODE"
fi

echo ""

# ============================================
# 4. RATE LIMITING TESTS
# ============================================

echo -e "${BLUE}[4] Rate Limiting Tests${NC}"
echo "─────────────────────────────────────────"

# Test 4.1: Check for rate limit headers
RATE_HEADERS=$(curl -s -I "$API_URL/api/templates")

if echo "$RATE_HEADERS" | grep -qi "X-RateLimit"; then
    print_test "Rate limit headers present" "PASS" "Rate limiting active"
else
    print_test "Rate limit headers present" "WARN" "Rate limit headers not found"
fi

# Test 4.2: Rapid requests to test rate limiting
echo -e "  ${BLUE}Testing rate limiting (sending 10 rapid requests)...${NC}"
RATE_LIMITED=false

for i in {1..10}; do
    RESPONSE=$(curl -s -w "\n%{http_code}" "$API_URL/api/templates")
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    
    if [ "$HTTP_CODE" = "429" ]; then
        RATE_LIMITED=true
        break
    fi
    sleep 0.1
done

if [ "$RATE_LIMITED" = true ]; then
    print_test "Rate limiting enforcement" "PASS" "Rate limit triggered after repeated requests"
else
    print_test "Rate limiting enforcement" "WARN" "Rate limit not triggered (may need more requests)"
fi

echo ""

# ============================================
# 5. INPUT VALIDATION TESTS
# ============================================

echo -e "${BLUE}[5] Input Validation Tests${NC}"
echo "─────────────────────────────────────────"

# Test 5.1: SQL Injection attempt in login
SQL_INJECTION=$(curl -s -w "\n%{http_code}" \
    -X POST "$API_URL/api/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"email":"admin'\''--","password":"anything"}')
HTTP_CODE=$(echo "$SQL_INJECTION" | tail -n1)
BODY=$(echo "$SQL_INJECTION" | head -n-1)

if echo "$BODY" | grep -qi "sql\|syntax\|error"; then
    print_test "SQL injection protection" "FAIL" "SQL error exposed"
else
    print_test "SQL injection protection" "PASS" "SQL injection attempt handled safely"
fi

# Test 5.2: XSS attempt
XSS_ATTEMPT=$(curl -s -w "\n%{http_code}" \
    -X POST "$API_URL/api/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"email":"<script>alert(1)</script>","password":"test"}')
HTTP_CODE=$(echo "$XSS_ATTEMPT" | tail -n1)
BODY=$(echo "$XSS_ATTEMPT" | head -n-1)

if echo "$BODY" | grep -q "<script>"; then
    print_test "XSS input sanitization" "FAIL" "Script tags not sanitized"
else
    print_test "XSS input sanitization" "PASS" "XSS attempt sanitized"
fi

# Test 5.3: Oversized request
LARGE_PAYLOAD=$(printf 'A%.0s' {1..100000})
OVERSIZED_RESPONSE=$(curl -s -w "\n%{http_code}" \
    -X POST "$API_URL/api/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$LARGE_PAYLOAD\",\"password\":\"test\"}" \
    2>/dev/null)
HTTP_CODE=$(echo "$OVERSIZED_RESPONSE" | tail -n1)

if [ "$HTTP_CODE" = "413" ] || [ "$HTTP_CODE" = "400" ]; then
    print_test "Large payload rejection" "PASS" "Oversized requests rejected"
else
    print_test "Large payload rejection" "WARN" "Large payloads may not be limited"
fi

echo ""

# ============================================
# 6. PATH TRAVERSAL TESTS
# ============================================

echo -e "${BLUE}[6] Path Traversal & File Access Tests${NC}"
echo "─────────────────────────────────────────"

# Test 6.1: Directory traversal attempt
TRAVERSAL_RESPONSE=$(curl -s -w "\n%{http_code}" "$API_URL/uploads/../.env")
HTTP_CODE=$(echo "$TRAVERSAL_RESPONSE" | tail -n1)

if [ "$HTTP_CODE" = "404" ] || [ "$HTTP_CODE" = "403" ]; then
    print_test "Path traversal protection" "PASS" "Directory traversal blocked"
else
    print_test "Path traversal protection" "FAIL" "Path traversal may be possible (Status: $HTTP_CODE)"
fi

# Test 6.2: Encoded path traversal
ENCODED_TRAVERSAL=$(curl -s -w "\n%{http_code}" "$API_URL/uploads/%2e%2e%2f.env")
HTTP_CODE=$(echo "$ENCODED_TRAVERSAL" | tail -n1)

if [ "$HTTP_CODE" = "404" ] || [ "$HTTP_CODE" = "403" ]; then
    print_test "Encoded path traversal protection" "PASS"
else
    print_test "Encoded path traversal protection" "FAIL" "Encoded traversal may work (Status: $HTTP_CODE)"
fi

# Test 6.3: Access to .env file
ENV_ACCESS=$(curl -s -w "\n%{http_code}" "$API_URL/.env")
HTTP_CODE=$(echo "$ENV_ACCESS" | tail -n1)

if [ "$HTTP_CODE" = "404" ] || [ "$HTTP_CODE" = "403" ]; then
    print_test ".env file access blocked" "PASS"
else
    print_test ".env file access blocked" "FAIL" "CRITICAL: .env may be accessible!"
fi

echo ""

# ============================================
# 7. CORS TESTS
# ============================================

echo -e "${BLUE}[7] CORS Configuration Tests${NC}"
echo "─────────────────────────────────────────"

# Test 7.1: CORS headers present
CORS_RESPONSE=$(curl -s -I -H "Origin: https://pre-wedding-ai.vercel.app" "$API_URL/api/templates")

if echo "$CORS_RESPONSE" | grep -qi "Access-Control-Allow-Origin"; then
    print_test "CORS headers configured" "PASS" "CORS enabled"
else
    print_test "CORS headers configured" "FAIL" "CORS not configured"
fi

# Test 7.2: Unauthorized origin
UNAUTHORIZED_ORIGIN=$(curl -s -I -H "Origin: https://malicious-site.com" "$API_URL/api/templates")

if echo "$UNAUTHORIZED_ORIGIN" | grep -q "Access-Control-Allow-Origin: https://malicious-site.com"; then
    print_test "CORS origin restriction" "FAIL" "Accepts requests from any origin"
else
    print_test "CORS origin restriction" "PASS" "Only authorized origins allowed"
fi

echo ""

# ============================================
# 8. SENSITIVE DATA EXPOSURE TESTS
# ============================================

echo -e "${BLUE}[8] Sensitive Data Exposure Tests${NC}"
echo "─────────────────────────────────────────"

# Test 8.1: Check various endpoints for sensitive data
ENDPOINTS=("/" "/health" "/api/templates")
SENSITIVE_PATTERNS="(password|secret|api[_-]?key|token|database|sql|redis|aws)"

for endpoint in "${ENDPOINTS[@]}"; do
    RESPONSE=$(curl -s "$API_URL$endpoint")
    
    if echo "$RESPONSE" | grep -qiE "$SENSITIVE_PATTERNS"; then
        print_test "Data exposure: $endpoint" "FAIL" "Sensitive data may be exposed"
    else
        print_test "Data exposure: $endpoint" "PASS" "No sensitive data found"
    fi
done

# Test 8.2: Error endpoint response
ERROR_RESPONSE=$(curl -s "$API_URL/api/nonexistent/endpoint")

if echo "$ERROR_RESPONSE" | grep -qi "traceback\|stack\|file.*line"; then
    print_test "Error message sanitization" "FAIL" "Stack traces exposed"
else
    print_test "Error message sanitization" "PASS" "Errors properly sanitized"
fi

echo ""

# ============================================
# 9. API DOCUMENTATION EXPOSURE
# ============================================

echo -e "${BLUE}[9] API Documentation Exposure Tests${NC}"
echo "─────────────────────────────────────────"

# Test 9.1: Swagger/OpenAPI docs
DOCS_RESPONSE=$(curl -s -w "\n%{http_code}" "$API_URL/docs")
HTTP_CODE=$(echo "$DOCS_RESPONSE" | tail -n1)

if [ "$HTTP_CODE" = "404" ]; then
    print_test "API docs disabled in production" "PASS" "Docs not accessible"
else
    print_test "API docs disabled in production" "WARN" "API docs are accessible (Status: $HTTP_CODE)"
fi

# Test 9.2: ReDoc
REDOC_RESPONSE=$(curl -s -w "\n%{http_code}" "$API_URL/redoc")
HTTP_CODE=$(echo "$REDOC_RESPONSE" | tail -n1)

if [ "$HTTP_CODE" = "404" ]; then
    print_test "ReDoc disabled in production" "PASS"
else
    print_test "ReDoc disabled in production" "WARN" "ReDoc accessible"
fi

# Test 9.3: OpenAPI JSON
OPENAPI_RESPONSE=$(curl -s -w "\n%{http_code}" "$API_URL/openapi.json")
HTTP_CODE=$(echo "$OPENAPI_RESPONSE" | tail -n1)

if [ "$HTTP_CODE" = "404" ]; then
    print_test "OpenAPI schema disabled" "PASS"
else
    print_test "OpenAPI schema disabled" "WARN" "OpenAPI schema accessible"
fi

echo ""

# ============================================
# 10. HTTPS & SSL TESTS
# ============================================

echo -e "${BLUE}[10] HTTPS & SSL Tests${NC}"
echo "─────────────────────────────────────────"

# Only test if using HTTPS
if [[ "$API_URL" == https://* ]]; then
    # Test 10.1: SSL certificate validity
    SSL_CHECK=$(curl -s -o /dev/null -w "%{ssl_verify_result}" "$API_URL/health")
    
    if [ "$SSL_CHECK" = "0" ]; then
        print_test "SSL certificate valid" "PASS" "Certificate is valid"
    else
        print_test "SSL certificate valid" "FAIL" "Certificate validation failed"
    fi
    
    # Test 10.2: TLS version
    TLS_VERSION=$(curl -s -I "$API_URL/health" --tlsv1.2 -o /dev/null -w "%{http_code}")
    
    if [ "$TLS_VERSION" = "200" ]; then
        print_test "TLS 1.2+ supported" "PASS"
    else
        print_test "TLS 1.2+ supported" "FAIL"
    fi
else
    print_test "HTTPS configuration" "WARN" "Testing local HTTP endpoint"
fi

echo ""

# ============================================
# SUMMARY
# ============================================

echo "============================================"
echo "📊 Test Summary"
echo "============================================"
echo -e "${GREEN}Passed:  $TESTS_PASSED${NC}"
echo -e "${YELLOW}Warnings: $TESTS_WARNING${NC}"
echo -e "${RED}Failed:  $TESTS_FAILED${NC}"
echo "============================================"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All critical tests passed!${NC}"
    echo -e "${GREEN}Your API is production-ready! 🚀${NC}"
    exit 0
elif [ $TESTS_FAILED -le 2 ]; then
    echo -e "${YELLOW}⚠ Some tests failed. Review and fix critical issues.${NC}"
    exit 1
else
    echo -e "${RED}✗ Multiple security issues detected!${NC}"
    echo -e "${RED}DO NOT deploy to production until fixed!${NC}"
    exit 1
fi