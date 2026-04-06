# Evidence Format Patterns

Use these exact patterns for consistency in audit reports. Every finding must include evidence using one of these formats.

## Evidence Type Reference Table

| Evidence Type | Format | Example |
|---------------|--------|---------|
| **Needs Review** | `NEEDS_REVIEW - <reason>` | `NEEDS_REVIEW - could not read binary file` |
| **Code location** | `<filepath>:<line>` | `src/auth/login.ts:45` |
| **Code range** | `<filepath>:<start>-<end>` | `src/auth/login.ts:45-52` |
| **Config value** | `<filepath>#<key>=<value>` | `config/app.json#session.secure=true` |
| **Env variable** | `env:<VAR_NAME>=<value or 'set'>` | `env:SESSION_SECRET=set` |
| **Framework default** | `framework:<name>:<feature>` | `framework:Django:CSRF_MIDDLEWARE` |
| **Library** | `library:<name>@<version>:<feature>` | `library:helmet@7.0:CSP` |
| **Missing control** | `missing:<what_was_searched>` | `missing:rate-limit middleware in routes/` |
| **Monorepo component** | `[<component>] <any above>` | `[api] src/routes/auth.py:23` |
| **N/A reason** | `N/A - <reason>` | `N/A - no file upload endpoints found` |

## Guidelines by Status

### ✅ PASS Evidence

Include a concrete pointer such as:

- `path/to/file.ext:line` for explicit code
- Specific config key/value (`config.json#key=value`)
- Route name, middleware, or library feature (`library:express-rate-limit@6.0:configured`)

### ⚪ N/A Evidence

Write `N/A - feature not present` with a brief reason:

- `N/A - no WebSocket server/routes found`
- `N/A - no file upload endpoints (searched: multer, formidable, multipart)`
- `N/A - OAuth not used (app uses session-based auth)`

### ⚠️ NEEDS_REVIEW Evidence

Write `NEEDS_REVIEW - <reason>` explaining the limitation:

- `NEEDS_REVIEW - could not verify due to large file size`
- `NEEDS_REVIEW - binary executable, cannot inspect`
- `NEEDS_REVIEW - requires runtime analysis`

### ❌ FAIL Evidence

Include `path/to/file.ext:line` where the insecure behavior exists, or `missing:<what_was_searched>` if the gap is purely absence of a control:

- `src/auth/password.js:23` (shows insecure pattern)
- `missing:rate-limit middleware in routes/` (searched package.json, no rate-limiting library)
- `config/database.yml#ssl=false` (insecure config value)

## Multiple Evidence Pattern

When multiple locations demonstrate the same issue:

```
src/api/v1/auth.ts:45, src/api/v2/auth.ts:78, src/admin/login.ts:34
```

When combining library + custom code:

```
library:next-auth@5.0:built-in-rate-limiting + src/app/api/auth/[...nextauth]/route.ts:12 custom lockout after 5 attempts
```
