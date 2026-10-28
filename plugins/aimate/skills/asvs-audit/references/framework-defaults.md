# Framework defaults

Some frameworks protect against a class of issue unless code switches the protection off. This file lists which ASVS 5.0 items such a default can pass, and what switches it off.

## When a default counts as PASS evidence

All four must hold, otherwise evaluate the item from the code as usual:

1. The framework is used for every relevant location of that item. For example, React escaping covers #1 only when all HTML is rendered by React; a backend that also builds HTML strings needs its own check. Template auto-escaping covers HTML body text and quoted attribute values only; data placed in unquoted attributes, event-handler attributes, `href` or `src` URLs, or `<script>` and `<style>` blocks needs its own check under #1 and #2.
2. The item number is listed for that framework below. A default never covers other items in the same chapter.
3. Every bypass pattern listed was searched in first-party code. Each hit was checked: a hit that handles only constant or sanitized data is fine; any other hit is a FAIL location.
4. The evidence has two entries: `framework:<name>@<version>:<feature>`, and the `path:line` where the framework is installed or configured (for example the dependency in the manifest, or the middleware list).

Frameworks with no security defaults for these items: Express, Fastify, Koa, Flask and FastAPI. Never use framework-default evidence for them; check the middleware and code.

## Defaults by framework

| Framework | Protection | Items | Bypass patterns to search |
|---|---|---|---|
| React, Next.js | JSX escapes text | #1, #14 | `dangerouslySetInnerHTML`, `ref.current.innerHTML`, `innerHTML =`, `insertAdjacentHTML`, `document.write`. JSX does not check URL protocols, so #2 still needs its own check. |
| Angular | Template sanitization of HTML and URLs | #1, #2, #14 | `bypassSecurityTrustHtml`, `bypassSecurityTrustUrl`, `bypassSecurityTrustResourceUrl`, `bypassSecurityTrustScript`, `bypassSecurityTrustStyle`, `nativeElement.innerHTML`. Style and CSS contexts are not covered; check them in code. |
| Vue | Template escaping | #1, #14 | `v-html`, `innerHTML` in render functions, `domProps` |
| Django | Template auto-escaping | #1, #14 | `\|safe`, `mark_safe(`, `{% autoescape off %}`, `format_html` with unescaped input |
| Django | ORM parameterization | #4 | `.raw(`, `.extra(`, `RawSQL(`, `cursor.execute(` with f-strings, `%` or `.format()` |
| Django | CSRF middleware | #18 | `@csrf_exempt`, `CsrfViewMiddleware` missing from `MIDDLEWARE` |
| Rails | ERB escaping | #1, #14 | `raw(`, `.html_safe`, `<%==` |
| Rails | ActiveRecord parameterization | #4 | `find_by_sql`, `connection.execute`, string interpolation in `where`, `order`, `pluck`, `select` |
| Rails | CSRF protection (`ActionController::Base`) | #18 | `skip_before_action :verify_authenticity_token`, `protect_from_forgery with: :null_session` on cookie-authenticated controllers |
| Spring Security | CSRF protection | #18 | `csrf().disable()`, `csrf(c -> c.disable())`, `csrf(AbstractHttpConfigurer::disable)`, `ignoringRequestMatchers`, `ignoringAntMatchers` |
| Spring Security | Session fixation protection | #43 | `sessionFixation().none()` |
| Spring Data JPA | Parameter binding | #4 | `createNativeQuery(` or `createQuery(` with concatenation, `JdbcTemplate` calls with concatenation, `@Query` with SpEL on raw input |
| Thymeleaf | Template escaping | #1, #14 | `th:utext` |
| ASP.NET Core | Razor encoding | #1, #14 | `@Html.Raw(`, `new HtmlString(`, `MarkupString` |
| ASP.NET Core | Antiforgery for Razor Pages and forms | #18 | `[IgnoreAntiforgeryToken]`, MVC controllers without `[ValidateAntiForgeryToken]` or a global `AutoValidateAntiforgeryTokenAttribute` filter |
| Entity Framework Core | Parameterization | #4 | `FromSqlRaw(`, `ExecuteSqlRaw(` with concatenation or interpolation. `FromSqlInterpolated` and `FromSql` with interpolation are safe. |
| Laravel | Blade escaping | #1, #14 | `{!! !!}` |
| Laravel | Eloquent and query builder parameterization | #4 | `DB::raw(`, `whereRaw(`, `selectRaw(`, `orderByRaw(`, `havingRaw(`, `DB::select(` or `DB::statement(` with concatenation |
| Laravel | CSRF middleware for the `web` group | #18 | entries in the CSRF middleware `$except` list or `validateCsrfTokens(except:`, cookie-authenticated routes outside the `web` group |
| Prisma | Parameterized queries | #4 | `$queryRawUnsafe`, `$executeRawUnsafe`, `Prisma.raw(`. Tagged `$queryRaw` templates are safe. |
| SQLAlchemy | Parameterized ORM and `text()` with bound parameters | #4 | `text(` or `execute(` with f-strings, `%` or `.format()` |
| Sequelize, TypeORM, Knex | Parameterized query builders | #4 | `sequelize.query(` or `.query(` with concatenation, `literal(`, `.where(` with template strings, `knex.raw(` with concatenation |
| express-session | Random 24-byte session IDs | #42 | a custom `genid` function |
| helmet 8 or later | HSTS with a one-year `max-age` | #16 | `hsts: false`, `strictTransportSecurity: false`, a `maxAge` below 31536000, `helmet()` not mounted before all routes. Helmet 3–7 default to 180 days, so they pass only with an explicit `maxAge` of at least 31536000. |

Check the installed framework version against the default you rely on; read the lock file when the manifest gives only a range. Older versions can differ, and a default changed in configuration is a bypass.
