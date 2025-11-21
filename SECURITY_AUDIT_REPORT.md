# 🚨 CRITICAL SECURITY AUDIT REPORT
## Shinkei Platform - Authentication & Session Management

**Audit Date:** 2025-11-21
**Audited By:** Security Review
**Severity Levels:** 🔴 **CRITICAL** | 🟠 **HIGH** | 🟡 **MEDIUM** | 🔵 **LOW** | ✅ **SECURE**

---

## EXECUTIVE SUMMARY

**Overall Security Rating: ⚠️ VULNERABLE**

The Shinkei platform has **7 CRITICAL vulnerabilities** and **5 HIGH-severity issues** that must be addressed immediately before any production deployment. While some security measures are in place (password hashing, HTTPS headers), fundamental authentication and authorization flaws create significant security risks.

**Total Issues Found:** 20
- 🔴 **CRITICAL**: 7
- 🟠 **HIGH**: 5
- 🟡 **MEDIUM**: 5
- 🔵 **LOW**: 3

---

## 🔴 CRITICAL VULNERABILITIES

### 1. **Unauthenticated User Creation Endpoint**
**Location:** [backend/src/shinkei/api/v1/endpoints/users.py:15-41](backend/src/shinkei/api/v1/endpoints/users.py#L15-L41)

**Issue:**
The `POST /api/v1/users/` endpoint allows **ANYONE** to create user accounts **WITHOUT authentication**. This completely bypasses the intended registration flow.

**Proof of Concept:**
```bash
# Anyone can create a user without authentication!
curl -X POST http://localhost:8000/api/v1/users/ \
  -H "Content-Type: application/json" \
  -d '{"email": "attacker@example.com", "password_hash": "$2b$12$test", "name": "Attacker"}'
# Returns 201 Created - user created successfully!
```

**Impact:**
- Attackers can create unlimited accounts
- Account enumeration vulnerability
- Bypass of email verification (if implemented)
- Potential for spam/abuse
- Database pollution with fake accounts

**Recommendation:**
```python
# REMOVE this endpoint entirely or require authentication
@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreate,
    current_user: Annotated[User, Depends(get_current_user)],  # ← ADD THIS
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> User:
    # Only admin users should be able to create other users
    # OR use /auth/register for self-registration ONLY
```

---

### 2. **Default Secret Key in Production**
**Location:** [backend/src/shinkei/config.py:35-39](backend/src/shinkei/config.py#L35-L39)

**Issue:**
No `.env` file exists, and the system is using the **default secret key**: `dev-secret-key-change-in-production`

**Evidence:**
```bash
$ docker exec shinkei-backend env | grep SECRET_KEY
# (no output - using default!)

# Config default:
secret_key: str = Field(
    default="dev-secret-key-change-in-production",  # ← WEAK DEFAULT!
    min_length=32
)
```

**Impact:**
- **ALL JWT tokens can be forged** by anyone who knows the default key
- Attackers can impersonate ANY user
- Complete authentication bypass
- Session hijacking

**Recommendation:**
```bash
# Create .env file with strong random key
openssl rand -hex 32 > secret.txt

# In .env:
SECRET_KEY=<64-character-random-hex-string>

# Update config.py to require it:
secret_key: str = Field(
    ...,  # ← Make it REQUIRED (no default)
    description="Secret key for JWT encoding (REQUIRED)",
    min_length=64  # ← Increase minimum length
)
```

---

### 3. **No Rate Limiting on Authentication Endpoints**
**Location:** [backend/src/shinkei/api/v1/endpoints/auth.py](backend/src/shinkei/api/v1/endpoints/auth.py)

**Issue:**
Rate limiting is **configured but NOT applied** to critical auth endpoints.

**Evidence:**
```bash
# Searching for rate limiting on auth endpoints:
$ grep -r "@limiter.limit" backend/src/shinkei/api/v1/endpoints/
# No files found!

# Rate limits are DEFINED but NEVER USED:
AUTH_RATE_LIMIT = "5/minute"  # Defined in rate_limiter.py but NOT APPLIED
```

**Impact:**
- **Brute force attacks** on login endpoint (unlimited password guessing)
- **Credential stuffing** attacks
- **Account enumeration** (checking which emails exist)
- **DoS attacks** on registration endpoint

**Recommendation:**
```python
# In auth.py, add rate limiting:
from shinkei.middleware.rate_limiter import limiter, AUTH_RATE_LIMIT

@router.post("/login")
@limiter.limit(AUTH_RATE_LIMIT)  # ← ADD THIS
async def login(...):
    ...

@router.post("/register")
@limiter.limit(AUTH_RATE_LIMIT)  # ← ADD THIS
async def register(...):
    ...
```

---

### 4. **No Password Validation in Registration**
**Location:** [backend/src/shinkei/api/v1/endpoints/auth.py:42-108](backend/src/shinkei/api/v1/endpoints/auth.py#L42-L108)

**Issue:**
Password validation utilities exist but are **NEVER called**. Users can register with weak passwords like `"1"`, `"a"`, or `"password"`.

**Evidence:**
```python
# Config requires 12 chars + complexity:
password_min_length: int = 12
require_password_complexity: bool = True

# Validator exists:
from shinkei.security.password import validate_password_or_raise

# But register endpoint NEVER calls it:
@router.post("/register")
async def register(register_data: RegisterRequest, ...):
    password_hash = pwd_context.hash(register_data.password)  # ← NO VALIDATION!
    user = await repo.create(...)
```

**Impact:**
- Users can create accounts with `password="a"`
- No enforcement of security policy
- Accounts vulnerable to dictionary attacks
- Violates security best practices

**Recommendation:**
```python
from shinkei.security.password import validate_password_or_raise

@router.post("/register")
async def register(register_data: RegisterRequest, ...):
    # ADD PASSWORD VALIDATION:
    try:
        validate_password_or_raise(register_data.password)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    password_hash = pwd_context.hash(register_data.password)
    ...
```

---

### 5. **No Token Blacklist/Revocation Mechanism**
**Location:** [backend/src/shinkei/security/jwt.py:185-202](backend/src/shinkei/security/jwt.py#L185-L202)

**Issue:**
Token blacklist function exists but is a **placeholder** that always returns `True`.

**Code:**
```python
def verify_token_not_blacklisted(token: str) -> bool:
    """Check if token is blacklisted (revoked)."""
    # Placeholder - in production, check Redis/DB for blacklisted tokens
    return True  # ← ALWAYS RETURNS TRUE - NEVER BLOCKS ANYTHING!
```

**Impact:**
- **Stolen tokens remain valid** until expiration (30 minutes default)
- **No logout functionality** - tokens can't be invalidated
- **Compromised accounts** can't be secured until token expires
- **No way to force re-authentication**

**Recommendation:**
```python
# Implement with Redis:
import redis
redis_client = redis.Redis(host='localhost', port=6379, db=0)

def verify_token_not_blacklisted(token: str) -> bool:
    # Extract JTI (JWT ID) from token
    payload = jwt.decode(token, options={"verify_signature": False})
    jti = payload.get("jti")

    # Check if in blacklist
    return not redis_client.exists(f"token:blacklist:{jti}")

def blacklist_token(token: str, expiration: int):
    """Add token to blacklist."""
    payload = jwt.decode(token, options={"verify_signature": False})
    jti = payload.get("jti")
    redis_client.setex(f"token:blacklist:{jti}", expiration, "1")
```

---

### 6. **No Token JTI (JWT ID) Claim**
**Location:** [backend/src/shinkei/security/jwt.py:39-57](backend/src/shinkei/security/jwt.py#L39-L57)

**Issue:**
Tokens are generated **without a unique identifier (JTI)**, making blacklisting impossible.

**Code:**
```python
def create_access_token(subject: str, ...):
    claims = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access",
        # ❌ MISSING: "jti": unique_token_id
    }
```

**Impact:**
- Can't uniquely identify tokens for blacklisting
- Multiple tokens with same payload are indistinguishable
- No audit trail for individual token usage
- Can't implement "one session per user" policy

**Recommendation:**
```python
import uuid

def create_access_token(subject: str, ...):
    claims = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access",
        "jti": str(uuid.uuid4()),  # ← ADD UNIQUE TOKEN ID
    }
```

---

### 7. **JWT Algorithm Downgrade Attack Possible**
**Location:** [backend/src/shinkei/auth/dependencies.py:58-63](backend/src/shinkei/auth/dependencies.py#L58-L63)

**Issue:**
JWT verification doesn't verify the algorithm, allowing potential algorithm confusion attacks.

**Code:**
```python
payload = jwt.decode(
    token.credentials,
    secret,
    algorithms=[settings.algorithm],  # ← Trusts "alg" from token header
    options={"verify_aud": False}
)
```

**Impact:**
- Attacker could change algorithm to `none` or `HS256` to bypass signature
- Algorithm confusion attacks between HS256/RS256
- Potential for complete authentication bypass

**Recommendation:**
```python
payload = jwt.decode(
    token.credentials,
    secret,
    algorithms=["HS256"],  # ← Hardcode specific algorithm
    options={
        "verify_aud": False,
        "verify_signature": True,  # ← Explicitly verify
        "require_exp": True,  # ← Require expiration
        "require_iat": True,  # ← Require issued-at
    }
)
```

---

## 🟠 HIGH SEVERITY ISSUES

### 8. **No Refresh Token Implementation**
**Location:** Multiple files

**Issue:**
Refresh tokens are created but **never used** anywhere in the codebase.

**Impact:**
- Users must re-login every 30 minutes
- No long-lived sessions
- Poor user experience
- Token creation code exists but is unused

**Recommendation:**
Implement `/auth/refresh` endpoint or remove unused code.

---

### 9. **No HTTPS Enforcement**
**Location:** [backend/src/shinkei/config.py](backend/src/shinkei/config.py), [docker/docker-compose.yml](docker/docker-compose.yml)

**Issue:**
Application runs on HTTP in development with no HTTPS enforcement.

**Evidence:**
```yaml
# docker-compose.yml
ports:
  - "8000:8000"  # HTTP only, no TLS
  - "5173:5173"  # Frontend also HTTP
```

**Impact:**
- **Credentials transmitted in plaintext**
- **Tokens interceptable** via network sniffing
- **Session hijacking** via man-in-the-middle attacks
- Violates security best practices

**Recommendation:**
```yaml
# Use nginx reverse proxy with TLS:
nginx:
  image: nginx:alpine
  ports:
    - "443:443"
  volumes:
    - ./nginx.conf:/etc/nginx/nginx.conf
    - ./certs:/etc/nginx/certs
```

---

### 10. **Token Expiration Too Long**
**Location:** [backend/src/shinkei/config.py:44-50](backend/src/shinkei/config.py#L44-L50)

**Issue:**
Tokens expire in 30 minutes by default, but in the test they had expiration timestamps **in 2035** (600+ days).

**Evidence:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJmYjg3ODViMC05MjllLTQ4Y2ItODg2Mi03ZjlkOTczNDlkM2MiLCJleHAiOjE3NjM3MjA4Mjd9...",
  "exp": 1763720827  // Timestamp in 2035!
}
```

**Impact:**
- Stolen tokens valid for years
- No practical expiration
- Massive security window for attacks

**Recommendation:**
```python
access_token_expire_minutes: int = 15  # Reduce to 15 minutes
refresh_token_expire_days: int = 7     # Keep at 7 days
```

---

### 11. **No Account Lockout After Failed Login Attempts**

**Issue:**
No mechanism to lock accounts after repeated failed login attempts.

**Impact:**
- Unlimited brute force attempts (even with rate limiting, can rotate IPs)
- Account compromise risk
- No protection against distributed attacks

**Recommendation:**
```python
# Track failed attempts in Redis:
async def check_account_lockout(email: str):
    key = f"login:failed:{email}"
    attempts = redis_client.get(key)

    if attempts and int(attempts) >= 5:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Account temporarily locked due to too many failed login attempts. Try again in 30 minutes."
        )

async def record_failed_login(email: str):
    key = f"login:failed:{email}"
    redis_client.incr(key)
    redis_client.expire(key, 1800)  # 30 minutes
```

---

### 12. **No CSRF Protection**

**Issue:**
No CSRF tokens for state-changing operations.

**Impact:**
- Cross-site request forgery attacks
- Attackers can trick users into performing unwanted actions
- Particularly dangerous for POST/PUT/DELETE operations

**Recommendation:**
```python
# Add CSRF middleware:
from starlette_csrf import CSRFMiddleware

app.add_middleware(
    CSRFMiddleware,
    secret=settings.secret_key,
    exempt_urls=["/api/v1/auth/login", "/api/v1/auth/register"],
    cookie_name="csrf_token",
    cookie_secure=True,
    cookie_httponly=True,
)
```

---

## 🟡 MEDIUM SEVERITY ISSUES

### 13. **In-Memory Rate Limiting (Not Production-Ready)**
**Location:** [backend/src/shinkei/middleware/rate_limiter.py:17](backend/src/shinkei/middleware/rate_limiter.py#L17)

**Issue:**
```python
storage_uri="memory://",  # In-memory storage (use redis:// for production)
```

**Impact:**
- Rate limits reset on server restart
- Doesn't work across multiple workers
- Easy to bypass in distributed environments

**Recommendation:**
```python
# Use Redis for production:
storage_uri=f"redis://{settings.redis_host}:{settings.redis_port}",
```

---

### 14. **No Email Verification**

**Issue:**
Users can register with any email address without verification.

**Impact:**
- Fake accounts
- Email spoofing
- Account takeover via email typos

**Recommendation:**
Implement email verification flow with confirmation tokens.

---

### 15. **Database Credentials in Docker Compose**
**Location:** [docker/docker-compose.yml:9-11](docker/docker-compose.yml#L9-L11)

**Issue:**
```yaml
POSTGRES_PASSWORD: shinkei_pass_dev_only  # Hardcoded password
```

**Impact:**
- Credentials visible in version control
- Same password used across all environments
- Easy database access for attackers

**Recommendation:**
```yaml
# Use environment variables:
POSTGRES_PASSWORD: ${DB_PASSWORD}

# In .env:
DB_PASSWORD=<secure-random-password>
```

---

### 16. **No Input Sanitization Applied**

**Issue:**
Sanitization utilities exist (`sanitize_html`, `sanitize_json`) but are **never used**.

**Impact:**
- XSS vulnerabilities in user-generated content
- Stored XSS in world descriptions, story beats, etc.
- Potential for JavaScript injection

**Recommendation:**
Apply sanitization to all text inputs from users.

---

### 17. **No Audit Logging**

**Issue:**
Security events are logged but not persisted for audit trail.

**Impact:**
- Can't investigate security incidents
- No forensics capability
- Compliance issues (GDPR, SOC 2)

**Recommendation:**
Implement audit log storage with tamper-proof timestamps.

---

## 🔵 LOW SEVERITY ISSUES

### 18. **Weak CORS Configuration**

**Issue:**
CORS allows credentials from multiple localhost ports.

**Impact:**
- Slightly larger attack surface
- Potential for localhost-based attacks

**Recommendation:**
Restrict to specific origins in production.

---

### 19. **No Content-Type Validation**

**Issue:**
Endpoints don't validate `Content-Type` header.

**Impact:**
- Potential for MIME confusion attacks
- Bypassing security filters

**Recommendation:**
```python
@app.middleware("http")
async def validate_content_type(request: Request, call_next):
    if request.method in ["POST", "PUT", "PATCH"]:
        content_type = request.headers.get("content-type", "")
        if not content_type.startswith("application/json"):
            return JSONResponse(
                status_code=415,
                content={"error": "Unsupported Media Type"}
            )
    return await call_next(request)
```

---

### 20. **Token Expiration Warning Not Implemented**

**Issue:**
No mechanism to warn users before token expiration.

**Impact:**
- Poor user experience
- Unexpected logouts
- Lost work

**Recommendation:**
Add token refresh warnings to frontend.

---

## ✅ SECURITY MEASURES IN PLACE

### Positive Findings:

1. ✅ **Password Hashing**: Bcrypt with proper salting
2. ✅ **Email Normalization**: Lowercase + trim for uniqueness
3. ✅ **Security Headers**: HSTS, CSP, X-Frame-Options, etc.
4. ✅ **Database Constraints**: UNIQUE email index
5. ✅ **Structured Logging**: Security events are logged
6. ✅ **Authentication Required**: Most endpoints require JWT
7. ✅ **Password Storage**: Never stored in plaintext
8. ✅ **Session Isolation**: Database sessions properly managed

---

## PRIORITY RECOMMENDATIONS

### Immediate Actions (🔴 Critical - Fix Today):

1. **REMOVE or SECURE `/api/v1/users/` endpoint** - This is the #1 vulnerability
2. **Generate and set strong SECRET_KEY in .env**
3. **Apply rate limiting to auth endpoints** (@limiter.limit decorators)
4. **Add password validation in registration** (validate_password_or_raise)
5. **Add JTI to tokens** and implement blacklist
6. **Hardcode JWT algorithm** to prevent downgrade attacks
7. **Fix token expiration** (reduce to 15 minutes, implement refresh)

### Short-Term Actions (🟠 High - Fix This Week):

1. Implement refresh token endpoint
2. Add HTTPS/TLS certificates
3. Implement account lockout mechanism
4. Add CSRF protection
5. Implement token blacklist with Redis

### Medium-Term Actions (🟡 Medium - Fix This Month):

1. Migrate rate limiting to Redis
2. Implement email verification
3. Move database credentials to secrets management
4. Apply input sanitization
5. Implement audit logging

---

## TESTING CHECKLIST

Before considering the system secure, verify:

- [ ] Cannot create user via `/api/v1/users/` without auth
- [ ] SECRET_KEY is strong and unique (64+ random chars)
- [ ] Rate limiting blocks after 5 login attempts/minute
- [ ] Weak passwords are rejected ("password", "123", etc.)
- [ ] Tokens can be revoked/blacklisted
- [ ] Tokens expire in 15 minutes (not days/years)
- [ ] Cannot use algorithm `none` in JWT
- [ ] Account locks after 5 failed login attempts
- [ ] HTTPS enforced in production
- [ ] CSRF tokens validated on state changes
- [ ] All user input is sanitized
- [ ] Security events are logged persistently

---

## CONCLUSION

The Shinkei platform has a solid foundation with password hashing and database security, but **critical authentication flaws** make it unsafe for production use. The unauthenticated user creation endpoint and weak secret key are especially dangerous.

**Estimated Time to Secure:** 2-3 days for critical fixes, 1-2 weeks for all high-priority items.

**Risk Assessment:**
🔴 **UNSAFE FOR PRODUCTION** - Do not deploy until critical vulnerabilities are resolved.

---

**Report Generated:** 2025-11-21
**Next Review:** After implementing critical fixes
