# Severity Assignment Guidance

Use this table to assign severity levels to FAIL findings. The default severity is based on the ASVS chapter, but can be overridden with direct code evidence showing different impact.

## Severity Table

| ASVS Chapter | Default Severity | Can Override To | Override Conditions |
|---|---|---|---|
| V1 Architecture | Medium | **Critical** | If authentication bypass or fundamental security flaw |
| V2 Authentication | **Critical** | Medium | If non-critical authentication method (e.g., remember-me token) |
| V3 Session Mgmt | High | **Critical** | If session hijacking is trivial (e.g., no httpOnly) |
| V4 Access Control | **Critical** | High | For non-sensitive resources only |
| V5 Validation | High | Medium | For non-critical UX fields only |
| V6 Cryptography | High | Medium | For non-sensitive data encryption |
| V7 Error & Logging | Medium | High | If exposes secrets or enables attacks |
| V8 Data Protection | High | **Critical** | If PII stored in plaintext or logged |
| V9 Communication | High | **Critical** | If sensitive data over unencrypted channel |
| V10 Malicious Code | Medium | High | If third-party dependency vulnerability |
| V11 Business Logic | Medium | High | If financial/critical business impact |
| V12 Files & Resources | High | **Critical** | If remote code execution via upload |
| V13 API & Web Services | High | **Critical** | If mass data exposure or injection |
| V14 Configuration | Medium | High | If production secrets exposed |

## Severity Level Definitions

| Severity | Icon | Impact | Example |
|----------|------|--------|---------|
| **Critical** | 🔴 | Immediate exploitation leading to full compromise | SQL injection in authentication, RCE via file upload, plaintext passwords |
| **High** | 🟠 | Directly exploitable with significant impact | Missing CSRF protection, weak crypto, session fixation |
| **Medium** | 🟡 | Requires preconditions or has limited impact | Password policy weakness, missing rate limiting, verbose errors |
| **Low** | 🟢 | Informational or requires complex attack chain | Documentation gaps, deprecated but still secure methods |

## Assignment Rules

1. **Start with the table default** for the ASVS chapter
2. **Evaluate actual impact** based on:
   - Data sensitivity (PII, financial, auth credentials)
   - Ease of exploitation (requires auth? network access? user interaction?)
   - Business criticality (user-facing? admin? internal tool?)
3. **Override only with evidence**: If impact differs from default, document why in the finding
4. **When in doubt, escalate**: Prefer higher severity if uncertain

## Examples

### Using Default Severity

```
Finding: Missing CSRF protection in user profile update
Chapter: V3 Session Management
Default: High
Assessment: Standard web form, requires authenticated user → Keep High
```

### Overriding to Higher Severity

```
Finding: Session cookies without httpOnly flag
Chapter: V3 Session Management
Default: High
Assessment: Trivial XSS → session hijacking, user accounts fully compromised → Override to Critical
Evidence: Tested with XSS payload, successfully extracted admin session token
```

### Overriding to Lower Severity

```
Finding: Weak password policy (min 6 chars)
Chapter: V2 Authentication
Default: Critical
Assessment: Non-critical "remember this device" token, not primary auth → Override to Medium
Evidence: Only affects optional convenience feature, primary login requires strong policy
```
