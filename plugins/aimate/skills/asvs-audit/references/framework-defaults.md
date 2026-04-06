# Known Framework Security Defaults

These frameworks provide security controls by default. Mark requirements as **✅ PASS** if the framework is in use AND no explicit disable/bypass is found.

## Usage Guidelines

1. **Verify framework is actually used**: Check package.json, requirements.txt, or imports
2. **Search for bypass patterns**: Use grep/search for the bypass keywords listed below
3. **If bypass found**: Mark as ❌ FAIL with location of bypass code
4. **If no bypass found**: Mark as ✅ PASS with evidence `framework:<name>:<feature>`

## Framework Security Features Table

| Framework | Default Security Feature | Bypass Pattern to Search For | ASVS Chapters |
|-----------|-------------------------|------------------------------|---------------|
| **React** | XSS protection (auto-escaping JSX) | `dangerouslySetInnerHTML` | V5 |
| **Angular** | XSS protection (auto-sanitization) | `bypassSecurityTrust*`, `[innerHTML]` | V5 |
| **Vue** | XSS protection (auto-escaping templates) | `v-html` directive | V5 |
| **Django** | CSRF protection (middleware) | `@csrf_exempt`, `CSRF_COOKIE_SECURE=False` | V3 |
| **Django** | SQL injection protection (ORM) | `raw()`, `extra()`, `RawSQL()` | V5 |
| **Django** | XSS protection (auto-escaping templates) | `|safe`,`mark_safe()`,`{% autoescape off %}` | V5 |
| **Rails** | CSRF protection (ActionController) | `skip_before_action :verify_authenticity_token` | V3 |
| **Rails** | SQL injection protection (ActiveRecord) | `find_by_sql`, string interpolation in `where()` | V5 |
| **Rails** | XSS protection (ERB auto-escaping) | `raw()`, `html_safe`, `<%==` | V5 |
| **Spring Boot** | CSRF protection (Spring Security) | `csrf().disable()`, `.ignoringAntMatchers()` | V3 |
| **Spring Boot** | SQL injection (JPA/Hibernate) | `createNativeQuery()` with concatenation | V5 |
| **ASP.NET Core** | XSS protection (Razor auto-encoding) | `@Html.Raw()`, `HtmlString` | V5 |
| **ASP.NET Core** | CSRF protection (antiforgery tokens) | `[IgnoreAntiforgeryToken]` | V3 |
| **Express** | (No defaults - requires middleware) | N/A (check for helmet, csurf, etc.) | Various |
| **Express + Helmet** | Security headers (via helmet middleware) | Missing `app.use(helmet())` | V1, V8 |
| **Next.js** | XSS protection (React-based) | `dangerouslySetInnerHTML` | V5 |
| **Laravel** | CSRF protection (VerifyCsrfToken middleware) | `@csrf` missing in forms, route excluded from middleware | V3 |
| **Laravel** | SQL injection (Eloquent ORM) | `DB::raw()`, `whereRaw()` with user input | V5 |
| **FastAPI** | (Limited defaults - requires decorators) | Missing `Depends()` for auth/validation | Various |
| **Flask** | (No defaults - requires extensions) | Check for Flask-SeaSurf, Flask-WTF | V3 |

## Evidence Format Examples

### Framework Default (PASS)

```
Evidence: framework:Django:CSRF_MIDDLEWARE
Evidence: framework:Rails:ActionController::CSRF
Evidence: framework:React:JSX-auto-escaping
```

### Bypass Found (FAIL)

```
Evidence: src/views/UserProfile.tsx:45 - dangerouslySetInnerHTML bypasses React XSS protection
Evidence: app/controllers/api_controller.rb:12 - skip_before_action :verify_authenticity_token disables CSRF
Evidence: views.py:89 - @csrf_exempt decorator disables Django CSRF on payment endpoint
```

### Framework Not Used (N/A)

```
Evidence: N/A - Django framework not in use (project uses Express/Node.js)
Evidence: N/A - React XSS protection not applicable (backend-only API, no templates)
```

## Common Pitfalls

1. **Don't assume**: Always verify the framework is actually configured correctly
2. **Check versions**: Old framework versions may have different defaults
3. **Partial bypasses**: Some protections may be bypassed for specific routes/views only
4. **Third-party packages**: May not follow framework defaults (e.g., REST framework in Django)
5. **Development vs Production**: Some teams disable security for dev - check environment configs
