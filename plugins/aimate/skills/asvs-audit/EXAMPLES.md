# Examples

Filled-in fragments of a report, for the formats in [REPORT-TEMPLATE.md](./references/REPORT-TEMPLATE.md). The application here is invented.

## A FAIL finding

````markdown
### #4 V1.2.4 Injection Prevention: SQL built from request data

- **Severity**: 🔴 Critical
- **Chapter**: V1 Encoding and Sanitization
- **Requirement**: Verify that data selection or database queries (e.g., SQL, HQL, NoSQL, Cypher) use parameterized queries, ORMs, entity frameworks, or are otherwise protected from SQL Injection and other database injection attacks. This is also relevant when writing stored procedures.
- **Description**: Two queries insert request values straight into SQL text. The order lookup is reachable by any signed-in user, and sign-up is open, so anyone can read every order in the database: raised to Critical. The report export is reachable only by administrators: lowered from Critical to High.
- **Locations**:

  | Location | Code | Why it fails | Severity |
  |---|---|---|---|
  | `src/orders/repository.ts:41` | `` db.query(`SELECT * FROM orders WHERE id = ${id}`) `` | `id` comes from `GET /orders/:id` (src/orders/routes.ts:12) unchanged. | Critical |
  | `src/admin/reports.ts:88` | `` db.query(`... ORDER BY ${req.query.sort}`) `` | Sort column from the query string; route requires the admin role. | High |

- **Remediation**: Pass values as parameters. Column names cannot be parameters, so map the sort value to an allowlist.

  ```typescript
  db.query("SELECT * FROM orders WHERE id = $1", [id]);

  const SORTABLE = new Map([
    ["date", "created_at"],
    ["total", "total"],
  ]);
  const sort = typeof req.query.sort === "string" ? req.query.sort : "";
  const column = SORTABLE.get(sort) ?? "created_at";
  db.query(`SELECT * FROM report ORDER BY ${column}`);
  ```
````

## Verification summary rows

```markdown
| #18 V3.5.1 | V3 Web Frontend Security<br>V3.5 Browser Origin Separation | Verify that, if the application does not rely on the CORS preflight mechanism ... | ✅ PASS | `framework:Django@5.0:CsrfViewMiddleware` + `config/settings.py:44` middleware enabled; no `csrf_exempt` |
| #23 V5.2.1 | V5 File Handling<br>V5.2 File Upload and Content | Verify that the application will only accept files of a size ... | ⚪ N/A | N/A - no file uploads; searched `multer`, `multipart`, `type="file"`, `createPresignedPost` in all tracked files |
| #16 V3.4.1 | V3 Web Frontend Security<br>V3.4 Browser Security Mechanism Headers | Verify that a Strict-Transport-Security header field is included ... | ⚠️ NEEDS_REVIEW | `deployment` |
| #4 V1.2.4 | V1 Encoding and Sanitization<br>V1.2 Injection Prevention | Verify that data selection or database queries ... | ❌ FAIL | See finding #4, 2 locations |
```

## A needs-review row

```markdown
| #16 V3.4.1 | `deployment` | Does the load balancer or CDN in front of the app send `Strict-Transport-Security` with `max-age` of at least 31536000 on every response? | `Strict-Transport-Security`, `hsts`, `helmet`, `SECURE_HSTS_SECONDS` in all tracked files: 0 hits |
```

## A rejected candidate

```markdown
- #61 `src/cache/keys.ts:9`: MD5 builds cache keys only; no security purpose.
```
