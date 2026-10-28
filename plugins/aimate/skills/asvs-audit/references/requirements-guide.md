# Requirements guide

How to decide each of the 70 items. The requirement text in the CSV is authoritative; this guide makes it decidable from code. For every item:

- **Applies when**: if this is false, the item is N/A. Prove it with the searches listed.
- **PASS** and **FAIL**: what each looks like in code. Examples are not exhaustive; the requirement text decides edge cases.
- **Search**: the minimum set of terms to search. Add terms for the frameworks in use.
- The severity after the title is the default. Adjust it only with [severity-guidance.md](./severity-guidance.md).
- Items marked **docs** or **deploy** often have evidence outside the repository; see the NEEDS_REVIEW reasons in [audit-rules.md](./audit-rules.md#statuses).

Where [framework-defaults.md](./framework-defaults.md) lists the item, a framework default can be PASS evidence under the conditions given there.

## V1 Encoding and Sanitization

### #1 V1.2.1 Context-aware output encoding · High
- Applies when: the app produces HTML or XML, or sets response headers from request or stored data.
- PASS: all output goes through auto-escaping templates or framework encoding, and every bypass takes only constant or sanitized data.
- Also check the contexts auto-escaping does not cover: unquoted attributes, event-handler attributes (`onclick=` and similar), data inside `<script>` or `<style>` blocks or inline JavaScript and CSS, and non-HTML output such as XML, CSV or email bodies. Each needs encoding for its own context.
- FAIL: request or stored data written into raw HTML, XML, any of the contexts above, or a header value without encoding for that context.
- Search: the bypass patterns in framework-defaults.md, `on[a-z]+=` (with `-E`), `<script`, `style=`, `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write`, HTML built in string templates, `setHeader(`, `header(`, XML built by string concatenation.

### #2 V1.2.2 URL encoding and safe URL protocols · High
- Applies when: the app builds URLs, links or redirects from untrusted data.
- PASS: values are encoded (`encodeURIComponent`, `URLSearchParams`, framework URL helpers), and user-supplied URLs used in `href`, `src` or redirects are limited to `http`/`https` or an allowlist.
- FAIL: untrusted data concatenated into a URL unencoded, or a user-supplied URL rendered or redirected to without a protocol check.
- Search: `href=`, `src=`, `window.location`, `location.href`, `redirect(`, `encodeURIComponent`, `new URL(`, `url_for`, URLs built in string templates.

### #3 V1.2.3 JavaScript and JSON encoding · High
- Applies when: the app builds JavaScript or JSON as text, embeds data in inline `<script>`, or offers JSONP.
- PASS: JSON produced by a serializer; data in inline scripts serialized with `<` escaped (for example Django `json_script`, `serialize-javascript`).
- FAIL: JSON or JavaScript assembled by string concatenation with untrusted data; raw `JSON.stringify` output placed inside `<script>`; JSONP callback names not validated.
- Search: `<script`, `JSON.stringify` in templates, `json_script`, `callback=`, `jsonp`, `'{"'`.

### #4 V1.2.4 Database injection · Critical
- Applies when: the app queries any database (SQL, NoSQL, graph).
- PASS: every query uses bound parameters or query-builder methods; NoSQL filters never take raw request objects.
- FAIL: untrusted data concatenated, interpolated or formatted into query text; request bodies passed directly as MongoDB filters (operator injection).
- Search: `query(`, `execute(`, `raw(`, `Raw(`, `$queryRawUnsafe`, `$executeRawUnsafe`, `sequelize.query`, `literal(`, `whereRaw`, `orderByRaw`, `DB::raw`, `DB::select`, `createNativeQuery`, `createQuery(`, `JdbcTemplate`, `cursor.execute`, `text(`, `FromSqlRaw`, `ExecuteSqlRaw`, `$where`, `find(req.`, `find(request.`.

### #5 V1.2.5 OS command injection · Critical
- Applies when: the app runs operating system commands.
- PASS: commands run with an argument array and no shell (`execFile`, `spawn` without `shell: true`, `subprocess.run([...])`), and untrusted values are either absent or checked against an allowlist.
- FAIL: untrusted data inside a shell command string.
- Search: `child_process`, `exec(`, `execSync`, `spawn(`, `shell: true`, `subprocess`, `os.system`, `popen`, `Runtime.getRuntime().exec`, `ProcessBuilder`, `Process.Start`, `shell_exec`, `system(`, `passthru`, backticks in Ruby and PHP.

### #6 V1.3.1 HTML sanitization of rich text · High
- Applies when: users can submit HTML (rich-text or WYSIWYG editors, markdown rendered with HTML enabled).
- PASS: the HTML is sanitized with a maintained library (DOMPurify, sanitize-html, bleach, nh3, HtmlSanitizer, OWASP Java HTML Sanitizer, Rails `sanitize`) before it is stored or rendered.
- FAIL: user HTML rendered without such a library, or sanitized only in the browser before being sent to the server.
- Search: `tiptap`, `quill`, `ckeditor`, `tinymce`, `draft-js`, `slate`, `lexical`, `marked`, `markdown-it` with `html: true`, `DOMPurify`, `sanitize`.

### #7 V1.3.2 Dynamic code execution · High
- Applies when: always. When nothing is found, the item is PASS with the searches as evidence.
- PASS: no dynamic code execution in first-party code, or only with constant input.
- FAIL: untrusted data reaches dynamic execution, including server-side template injection.
- Search: `eval(`, `new Function(`, `setTimeout(` or `setInterval(` with a string, `vm.run`, Python `exec(` and `compile(`, `parseExpression` (SpEL), OGNL, `ScriptEngine`, PHP `eval` and `create_function`, Ruby `instance_eval`, `class_eval`, `send(` with user input, `render_template_string`, template compile calls on user input.

### #8 V1.5.1 XML external entities (XXE) · High
- Applies when: the app parses XML, including SOAP, SAML, SVG, RSS and office files.
- PASS: the parser is configured to refuse DTDs and external entities, or the parser and version in use are documented as safe by default (cite which).
- FAIL: external entity resolution enabled (`resolve_entities=True`, `noent: true`), or Java `DocumentBuilderFactory`, `SAXParserFactory` or `XMLInputFactory` used without disabling DTDs and external entities.
- Search: `DocumentBuilderFactory`, `SAXParser`, `XMLInputFactory`, `XmlReader`, `XmlDocument`, `lxml`, `etree`, `xml.dom`, `xml.sax`, `libxmljs`, `fast-xml-parser`, `xml2js`, `simplexml_load`, `DOMDocument`, `Nokogiri::XML`.

## V2 Validation and Business Logic

### #9 V2.1.1 Input validation rules documented · Low · docs
- Applies when: always.
- PASS: an API specification (OpenAPI, JSON Schema, GraphQL schema) or a design document defines formats, ranges or patterns for input fields.
- Otherwise: NEEDS_REVIEW `external-docs`, asking where the validation rules are documented.
- Search: `openapi`, `swagger`, `*.schema.json`, `schema.graphql`, `docs/`.

### #10 V2.2.1 Input validated against business expectations · Medium
- Applies when: the app accepts input. For Level 1, focus on input that drives business or security decisions: amounts, quantities, prices, roles, status values, identifiers, redirect targets, file names.
- PASS: such input is validated server-side against an allowlist, schema or range (zod, joi, yup, class-validator, pydantic, marshmallow, FluentValidation, Bean Validation, Laravel and Rails validations).
- FAIL: such input used without validation, for example a negative quantity, a client-supplied price, or a role taken from the request body.
- Search: validation library names, handlers in the inventory that read request bodies and parameters.

### #11 V2.2.2 Validation enforced server-side · High
- Applies when: always.
- PASS: every validation that protects a business or security decision also runs on the server.
- FAIL: a check exists only in front-end code (form schemas, `required`, `pattern`, `maxlength`) and the server accepts the field unchecked.
- Search: front-end form validation, compared with the matching server handlers.

### #12 V2.3.1 Business flows run in order · Medium
- Applies when: the app has multi-step flows such as checkout, sign-up with verification, password reset, onboarding, MFA enrolment or approvals.
- PASS: the server records progress per user and each step checks that the earlier steps were completed.
- FAIL: a later step can be called directly without the server checking the earlier ones.
- Search: `step`, `stage`, `status`, `wizard`, `checkout`, `confirm`, `verify`, flow-related routes in the inventory.

## V3 Web Frontend Security

### #13 V3.2.1 Content not rendered in the wrong context · Medium
- Applies when: the app serves responses a browser may render that are not its own pages: API responses, files uploaded or generated from user input, or other resources.
- PASS: no user-controlled content can be rendered as active content (HTML, SVG, XML) on the application's origin. Controls that achieve this: `Content-Disposition: attachment`, a separate origin, a `sandbox` Content-Security-Policy, `Sec-Fetch-*` checks, or `X-Content-Type-Options: nosniff` together with a correct, non-active `Content-Type`.
- FAIL: user-controlled content that a browser can render as HTML, SVG or XML on the application's origin, for example uploads served inline with their uploaded content type, or API responses echoing input with a `text/html` type.
- Search: `sendFile`, `res.download`, `Content-Disposition`, `FileResponse`, `send_file`, `File(`, static upload folders, signed storage URLs.

### #14 V3.2.2 Text rendered as text · High
- Applies when: client-side code inserts content into the page.
- PASS: text is inserted with `textContent`, `innerText`, `createTextNode` or normal framework text binding.
- FAIL: content meant as text inserted with `innerHTML`, `outerHTML`, `insertAdjacentHTML`, jQuery `.html()` or `.append()` with a string, or a framework bypass.
- Search: the terms above and the bypass patterns in framework-defaults.md.

### #15 V3.3.1 Cookie Secure flag and name prefix · Medium
- Applies when: the app or its framework sets cookies.
- PASS: every cookie has the `Secure` attribute in production and a `__Host-` or `__Secure-` name prefix. Secure set only when the environment is production counts as set.
- FAIL: any cookie without `Secure`, or without one of the two prefixes. Framework session cookies such as `connect.sid`, `sessionid`, `laravel_session` and `JSESSIONID` have no prefix unless configured.
- Search: `cookie(`, `Set-Cookie`, `setcookie`, `cookies.set`, `SESSION_COOKIE_`, `cookie:` options, session middleware configuration.

### #16 V3.4.1 Strict-Transport-Security · Medium · deploy
- Applies when: the app serves responses to browsers.
- PASS: HSTS set on all responses with `max-age` of at least 31536000, in app code or in configuration in the repository.
- FAIL: HSTS configured below 31536000 or disabled; or the repository contains the TLS-terminating server configuration and it does not set HSTS. Known defaults below a year: ASP.NET Core `UseHsts` (30 days), Django `SECURE_HSTS_SECONDS` (0).
- Otherwise: NEEDS_REVIEW `deployment`.
- Search: `Strict-Transport-Security`, `hsts`, `helmet`, `SECURE_HSTS_SECONDS`, `UseHsts`, `add_header`, header blocks in platform configs.

### #17 V3.4.2 CORS origin allowlist · High
- Applies when: the app sets CORS headers.
- PASS: `Access-Control-Allow-Origin` is a fixed value or checked against an exact allowlist; `*` only on responses without sensitive data.
- FAIL: the request `Origin` reflected without an allowlist (`origin: true`, a callback that always allows), an unanchored regex, `null` allowed, or `*` on responses with sensitive data.
- Search: `cors(`, `Access-Control-Allow-Origin`, `allowedOrigins`, `CORS_ALLOWED`, `AddCors`, `@CrossOrigin`.

### #18 V3.5.1 Cross-site request forgery protection · High
- Applies when: browsers send credentials automatically (cookies or basic auth) to state-changing endpoints, and those endpoints accept requests that skip the CORS preflight (form-encoded, multipart or `text/plain` bodies). N/A when authentication uses only an `Authorization` header set by JavaScript. Usually exactly one of #18 and #19 applies.
- PASS: anti-forgery tokens validated on every state-changing endpoint, or a required custom header the browser cannot add cross-origin.
- FAIL: a state-changing endpoint that accepts such requests without either control. SameSite cookies alone do not pass this item; they lower the severity to Medium.
- Search: `csrf`, `xsrf`, `antiforgery`, `verify_authenticity_token`, `SameSite`, form handlers in the inventory.

### #19 V3.5.2 CORS preflight not bypassable · High
- Applies when: the app relies on the CORS preflight instead of anti-forgery tokens and browsers send cookies.
- PASS: state-changing endpoints reject requests that would not trigger a preflight, by checking `Content-Type: application/json` or requiring a custom header.
- FAIL: a body parser that accepts any content type as JSON (for example `express.json({ type: '*/*' })`), or the same action also reachable through a simple request.
- Search: body parser configuration, `Content-Type` checks.

### #20 V3.5.3 Safe methods do not change state · Medium
- Applies when: the app has state-changing operations.
- PASS: no `GET`, `HEAD` or `OPTIONS` handler changes state, or strict `Sec-Fetch-*` validation is in place.
- FAIL: a `GET` or `HEAD` handler that writes data, sends messages or changes account state.
- Search: `GET` route definitions in the inventory whose handlers create, update, delete or send.

## V4 API and Web Service

### #21 V4.1.1 Content-Type with charset · Low
- Applies when: the app returns HTTP responses with a body.
- PASS: responses carry a `Content-Type` matching the body, with a `charset` for `text/*` and XML types. Framework helpers such as `res.json` and template rendering set it.
- FAIL: raw responses without `Content-Type`, or `text/*` or XML responses without `charset`. JSON does not need a charset.
- Search: `res.end(`, `res.write(`, `res.send(` with strings, `HttpResponse(`, `Content-Type`, `content_type=`.

### #22 V4.4.1 WebSockets over TLS · Medium
- Applies when: the app uses WebSockets.
- PASS: clients connect with `wss://`, or derive the scheme from an `https` page.
- FAIL: a hard-coded `ws://` URL for a non-local host.
- Otherwise: NEEDS_REVIEW `deployment` when the server listens without TLS and the TLS proxy is not in the repository.
- Search: `ws://`, `wss://`, `new WebSocket(`, `socket.io`, `SignalR`, `ActionCable`, `channels`.

## V5 File Handling

### #23 V5.2.1 Upload size limit · Medium
- Applies when: the app accepts file uploads, including base64 file fields and presigned upload URLs.
- PASS: every upload path enforces a maximum size on the server, in the upload library, body size limit, presigned policy (`content-length-range`) or repository web server config.
- FAIL: an upload path without a server-side size limit.
- Search: `multer`, `formidable`, `busboy`, `multipart`, `UploadFile`, `request.FILES`, `IFormFile`, `MultipartFile`, `->file(`, `createPresignedPost`, `getSignedUrl`, `type="file"`, `client_max_body_size`.

### #24 V5.2.2 File type validated by extension and content · Medium
- Applies when: the app accepts uploads that it parses, processes, or serves to other users.
- PASS: an extension allowlist plus a content check (magic bytes, a file-type library, or image re-encoding).
- FAIL: no extension allowlist, or a check based only on the client-supplied MIME type or in the browser.
- Search: the upload terms above, `mimetype`, `file-type`, `magic`, `extension`, `accept=`.

### #25 V5.3.1 Uploaded files never executed · Critical
- Applies when: uploaded or generated files are stored in a folder the web server serves.
- PASS: files stored outside the web root or in object storage, or served by a static handler that never executes code (Node or Python static servers, nginx locations without a script handler).
- FAIL: files stored where the server executes scripts (PHP, JSP or ASP document roots) without execution disabled for that folder.
- Search: upload destination paths, `public/`, `static/`, `wwwroot/`, `uploads/`, web server configuration.

### #26 V5.3.2 Safe file paths and outbound URLs · High
- Applies when: file paths or outbound request URLs are built from user input.
- PASS: paths use generated names or IDs, or the user value is reduced to a base name, checked against an allowlist and the resolved path is confirmed inside the base directory; outbound URLs from users are checked against an allowlist of hosts.
- FAIL: user input in a file path or include, or in an outbound request URL, without those checks.
- Search: `readFile`, `createReadStream`, `sendFile`, `res.download`, `open(`, `os.path.join`, `Path(`, `File(`, `include`, `require(` with variables, `fetch(`, `axios`, `got(`, `requests.`, `HttpClient`, `urlopen`, `file_get_contents`, `curl_exec`.

## V6 Authentication

Decide applicability per item. The password-policy items #28–#35 apply when the app handles passwords itself; with only social or enterprise single sign-on and no local passwords, they are N/A. #36 applies to any login, including one-time codes and magic links. #37, #38 and #39 apply under their own conditions below, which do not depend on local passwords. With a hosted identity provider that keeps passwords for the app (Auth0, Cognito, Keycloak, Entra External ID), judge its configuration when it is in the repository; otherwise use NEEDS_REVIEW `external-system`.

### #27 V6.1.1 Anti-automation documented · Low · docs
- Applies when: the app has any login.
- PASS: documentation describes rate limiting, anti-automation and lockout, and how lockout abuse is prevented.
- Otherwise: NEEDS_REVIEW `external-docs`.
- Search: `SECURITY.md`, `docs/`, ADRs, `rate limit`, `lockout`, `brute force`.

### #28 V6.2.1 Minimum password length 8 · Medium
- PASS: the server enforces at least 8 characters on registration, password change, reset and admin-set passwords.
- FAIL: a lower minimum, or no server-side check on one of those paths.
- Search: `minLength`, `min(`, `MinimumLength`, `RequiredLength`, `AUTH_PASSWORD_VALIDATORS`, `Password::min`, password schemas.

### #29 V6.2.2 Users can change their password · Medium
- PASS: a logged-in user can change their own password.
- FAIL: no such function. A reset-by-email flow alone does not count.
- Search: `changePassword`, `change_password`, `password/change`, `updatePassword`, account settings routes.

### #30 V6.2.3 Change requires the current password · Medium
- Applies when: a password change function exists (#29). Otherwise N/A, pointing to #29.
- PASS: the server verifies the current password before setting the new one.
- FAIL: the current password is not required or only checked in the browser.
- Search: the change handler from #29.

### #31 V6.2.4 Common passwords rejected · Medium
- PASS: registration and password change check against at least the 3,000 most common passwords (a bundled list, the Have I Been Pwned range API, Django `CommonPasswordValidator`, Laravel `Password::uncompromised()`, zxcvbn).
- FAIL: either path lacks such a check.
- Search: `pwned`, `haveibeenpwned`, `CommonPasswordValidator`, `uncompromised`, `zxcvbn`, `common-passwords`.

### #32 V6.2.5 No composition rules · Low
- PASS: no rules require character types and no characters are forbidden.
- FAIL: rules requiring upper case, lower case, digits or symbols, or restricting allowed characters. ASP.NET Core Identity (`RequireDigit`, `RequireUppercase`, `RequireNonAlphanumeric`) and Cognito require these by default.
- Search: password regexes, `RequireDigit`, `RequireUppercase`, `mixedCase`, `numbers()`, `symbols()`, `[A-Z]`, `[0-9]`.

### #33 V6.2.6 Password fields masked · Low
- Applies when: the app renders password inputs.
- PASS: every password input is `type="password"` by default; a show-password toggle is fine.
- FAIL: a password input rendered as plain text by default.
- Search: `type="password"`, password inputs in forms and components.

### #34 V6.2.7 Paste and password managers allowed · Low
- Applies when: the app renders password inputs.
- PASS: nothing blocks paste, drop or autofill.
- FAIL: `onpaste`, `paste` or `drop` handlers that cancel the event on password fields, or code that clears autofilled values.
- Search: `onPaste`, `onpaste`, `paste`, `preventDefault` near password fields.

### #35 V6.2.8 Password used exactly as entered · Medium
- PASS: the password is hashed and checked exactly as received.
- FAIL: trimming, case changes or truncation before hashing or comparing, including bcrypt's 72-byte truncation when longer passwords are accepted without pre-hashing.
- Search: `trim(`, `toLowerCase(`, `lower(`, `substring(` near password handling, `bcrypt`.

### #36 V6.3.1 Brute-force protection · Medium
- Applies when: the app has a login.
- PASS: server-side rate limiting, lockout or CAPTCHA on login, password reset and MFA verification (express-rate-limit, django-axes, Laravel `throttle`, ASP.NET Identity `lockoutOnFailure: true`, Devise `lockable`, rack-attack, or rules in repository gateway config). When #27 found documentation, the controls must also match it. When it did not, judge against this baseline; #27 already reports the missing documentation.
- FAIL: one of those endpoints has none, or the controls contradict the documentation.
- Search: `rateLimit`, `rate-limit`, `throttle`, `lockout`, `axes`, `rack-attack`, `captcha`, `recaptcha`, `turnstile`.

### #37 V6.3.2 No default accounts · High
- PASS: no account with a well-known name and fixed password is created in production, and no hard-coded credential check exists.
- FAIL: seeds, migrations or startup code that run in production and create users such as `admin`, `root`, `sa`, `test` or `demo` with a fixed password, or code comparing credentials with constants.
- Search: `seed`, `migrations`, `admin`, `root`, `password:`, `createUser`, `INSERT INTO users`, `== "admin"`.

### #38 V6.4.1 Initial passwords and activation codes · Medium
- Applies when: the app generates initial passwords, activation codes or invite links.
- PASS: generated with a secure random source (`crypto.randomBytes`, `secrets`, `SecureRandom`, `RandomNumberGenerator`), they follow the existing password policy and expire after a short period or after first use; initial passwords must be changed.
- FAIL: `Math.random`, `random`, timestamps or sequential values; the existing password policy is not followed; neither short expiry nor first-use invalidation; or an initial password kept as the long-term password.
- Search: `invite`, `activation`, `verification code`, `temporaryPassword`, `generatePassword`, `Math.random`, `random.`.

### #39 V6.4.2 No password hints or secret questions · Medium
- PASS: none present.
- FAIL: a password hint field or security questions used for recovery.
- Search: `hint`, `security_question`, `securityQuestion`, `secret_question`.

## V7 Session Management

Items #40–#45 apply when the app keeps logged-in sessions. Without authentication they are N/A.

### #40 V7.2.1 Session tokens verified on the backend · High
- PASS: every request's session or token is checked by server code.
- FAIL: access decided from a token decoded in the browser, or front-end route guards protecting APIs that do not check the token themselves.
- Search: session and JWT middleware, API handlers without it.

### #41 V7.2.2 Session tokens generated per login · High
- PASS: tokens are created per login.
- FAIL: a static key or shared secret used as a user's session, for example a hard-coded token in front-end code.
- Search: hard-coded `Authorization` or `Bearer` values, `API_KEY` used for user requests.

### #42 V7.2.3 Reference tokens are random and 128 bits · High
- Applies when: the app uses opaque session tokens. Self-contained tokens only (JWT) make this N/A; they are covered in V9.
- PASS: a framework session store whose generator you confirmed is not replaced by configuration (for example a custom `genid`), or custom tokens with at least 128 bits of entropy from a cryptographically secure random source, counted before encoding (16 random bytes or more).
- FAIL: tokens from `Math.random`, UUID v1, timestamps or counters, or with less than 128 bits of entropy. A UUID v4 has 122 random bits and fails.
- Search: session token generation, `randomBytes`, `token_urlsafe`, `uuid`, `Math.random`, `genid`, `session_id_generator`, `SessionIdGenerator`.

### #43 V7.2.4 New session token at login · High
- PASS: at login and at every re-authentication the user gets a new session token and the previous one stops working (`req.session.regenerate`, Django `login()`, Rails `reset_session`, `session_regenerate_id(true)`, Spring session fixation protection enabled).
- FAIL: custom login or re-authentication code that stores the user on the existing session without regenerating it, or that issues a new token while the old one stays valid.
- Search: login handlers, `regenerate`, `reset_session`, `session_regenerate_id`, `sessionFixation`.

### #44 V7.4.1 Logout and expiry end the session on the server · Medium
- PASS: logout and expiry invalidate the server-side session; for self-contained tokens, a deny list, per-user token version or key rotation.
- FAIL: logout only clears the cookie or browser storage while the token stays valid on the server.
- Search: logout handlers, `destroy`, `invalidate`, `flush`, `revoke`, token version fields.

### #45 V7.4.2 Sessions end when an account is disabled or deleted · Medium
- Applies when: accounts can be disabled or deleted.
- PASS: disabling or deleting removes or revokes that user's sessions, or every request checks that the account is still active.
- FAIL: an existing session of a disabled or deleted user keeps working.
- Search: `disable`, `deactivate`, `ban`, `suspend`, `deleteUser`, `is_active`, `isActive`.

## V8 Authorization

### #46 V8.1.1 Authorization rules documented · Low · docs
- Applies when: the app has more than one role or data owned per user or tenant.
- PASS: documentation describes function-level and data-level access rules.
- Otherwise: NEEDS_REVIEW `external-docs`.
- Search: `SECURITY.md`, `docs/`, ADRs, `roles`, `permissions`.

### #47 V8.2.1 Function-level access control · High
- Applies when: the app has functions that not everyone may use.
- PASS: every inventory entry point is either deliberately public or checked on the server for login and the required role or permission.
- FAIL: a privileged route without a role check, or a route that should require login and does not. List every such route.
- Search: the authorization entries in the inventory compared with every entry point.

### #48 V8.2.2 Data-level access control (IDOR) · High
- Applies when: entry points take an identifier for an object owned by a user or tenant.
- PASS: queries are scoped to the current user or tenant, or ownership is checked before use.
- FAIL: an object loaded by an identifier from the request without an ownership or permission check. List every such entry point.
- Search: entry points with `:id`, `{id}`, `params.id`, `findById`, `findUnique`, `get_object_or_404`, `find(`.

### #49 V8.3.1 Authorization enforced on the server · High
- PASS: authorization decisions are made on the server from server-side data.
- FAIL: protection only in the front end (hidden buttons, route guards), or a role or permission taken from something the client controls (request body, header, cookie, unverified token claims).
- Search: front-end guards, `role` read from requests, `isAdmin` in client state.

## V9 Self-contained Tokens

Items #50–#53 apply when the app creates or validates self-contained tokens (JWT, JWS, PASETO). Otherwise N/A. When a library validates tokens for the app, judge its configuration.

### #50 V9.1.1 Signature checked before use · Critical
- PASS: every token is verified with a signature or MAC check before its claims are used.
- FAIL: claims used after a call that does not verify, or with verification disabled (`verify_signature: False`, `ignoreSignature`, `verify=False`).
- What a call does depends on the library, so determine which library the import comes from before judging. Node `jsonwebtoken` `jwt.decode` and `jose` `decodeJwt` never verify. Python PyJWT `jwt.decode` verifies unless its options disable it. A decode-only call is a FAIL only when its claims are used for a decision without a verified token elsewhere on the same path.
- Search: `jwt.decode`, `decodeJwt`, `jwt_decode`, `verify_signature`, `jwtVerify`, `jwt.verify`.

### #51 V9.1.2 Algorithm allowlist · Critical
- PASS: the verify call or configuration pins the allowed algorithms, or the library enforces the algorithm from the key type for the version in use (cite it); `none` is never accepted.
- FAIL: no allowlist where the library takes the algorithm from the token header, or `none` allowed.
- Search: `algorithms`, `ValidAlgorithms`, `alg`, `none`, verify calls.

### #52 V9.1.3 Keys from trusted sources only · Critical
- PASS: keys come from configuration or a configured JWKS URL.
- FAIL: keys fetched from a URL in the token (`jku`, `x5u`), an embedded `jwk` trusted, or a JWKS URL derived from the token's issuer without an allowlist.
- Search: `jku`, `x5u`, `jwk`, `jwks`, `getSigningKey`, `iss`.

### #53 V9.2.1 Validity period checked · High
- PASS: `exp` and `nbf` are checked (the default in common libraries).
- FAIL: `ignoreExpiration: true`, `verify_exp: False`, `ValidateLifetime = false`, or custom decoding without the checks.
- Search: `ignoreExpiration`, `verify_exp`, `ValidateLifetime`, `clockTolerance`, `exp`.

## V10 OAuth and OIDC

Items #54–#58 apply only when the app is itself an OAuth authorization server or OpenID provider, issuing codes and tokens to other clients (for example node-oidc-provider, Spring Authorization Server, Duende IdentityServer, OpenIddict, django-oauth-toolkit, Doorkeeper, Laravel Passport). An app that only signs users in through another provider is N/A: "app is an OAuth client only (uses `<library>`)". Library defaults count as evidence when you cite the library version.

Applicability search, shared by all five: `oidc-provider`, `spring-security-oauth2-authorization-server`, `Duende.IdentityServer`, `IdentityServer4`, `OpenIddict`, `oauth2_provider`, `doorkeeper`, `laravel/passport`, `/authorize` and `/token` route handlers, `grant_type`, `authorization_code`. Then search the configuration terms listed per item.

### #54 V10.4.1 Redirect URIs matched exactly · High
- PASS: redirect URIs compared by exact string with a per-client registered list.
- FAIL: prefix, wildcard or pattern matching, or unregistered redirect URIs accepted.
- Search: `redirect_uri`, `redirectUris`, `RedirectUris`, `startsWith`, `allowed_redirect`.

### #55 V10.4.2 Authorization codes used once · High
- PASS: a code works once, and reuse revokes the tokens issued from it.
- FAIL: codes reusable, or reuse does not revoke tokens.
- Search: authorization code storage and consumption, `consume`, `revoke`, `used`.

### #56 V10.4.3 Authorization codes short-lived · Medium
- PASS: code lifetime at most 10 minutes.
- FAIL: longer lifetime.
- Search: `AuthorizationCodeLifetime`, `AUTHORIZATION_CODE_EXPIRE_SECONDS`, `authorizationCodeTimeToLive`, `ttl`, `expires`.

### #57 V10.4.4 Grants restricted per client · Medium
- PASS: each client may use only the grants it needs; implicit (`token`) and password grants are disabled.
- FAIL: all grants allowed for every client, or implicit or password grant enabled.
- Search: `AllowedGrantTypes`, `grant_types`, `authorizationGrantType`, `implicit`, `password` grant, `AllowPasswordFlow`, `AllowImplicitFlow`.

### #58 V10.4.5 Refresh token replay prevented · High
- PASS: for public clients, sender-constrained refresh tokens (DPoP, mTLS) or rotation that invalidates used tokens and revokes the family on reuse.
- FAIL: reusable refresh tokens for public clients.
- Search: `RefreshTokenUsage`, `OneTimeOnly`, `rotateRefreshToken`, `REFRESH_TOKEN_REUSE`, `dpop`, `refresh_token`.

## V11 Cryptography

Items #59–#61 apply when first-party code calls encryption or hashing primitives directly. Library internals (TLS, password hashing libraries, JWT libraries) are out of scope here.

### #59 V11.3.1 No insecure modes or padding · High
- PASS: no ECB mode and no PKCS#1 v1.5 encryption padding.
- FAIL: `aes-*-ecb`, `AES/ECB`, `MODE_ECB`, `CipherMode.ECB`, Java `Cipher.getInstance("AES")` (defaults to ECB), `RSA_PKCS1_PADDING`, `PKCS1v15()` for encryption, `RSA/ECB/PKCS1Padding`.
- Search: the terms above, `createCipheriv`, `Cipher.getInstance`, `Cipher(`, `openssl_encrypt`.

### #60 V11.3.2 Approved ciphers and modes · High
- PASS: authenticated encryption such as AES-GCM or ChaCha20-Poly1305.
- FAIL: DES, 3DES, RC4 or Blowfish, or AES-CBC or AES-CTR without a separate MAC.
- Search: `createCipheriv`, `Cipher`, `AES`, `DES`, `RC4`, `Blowfish`, `openssl_encrypt`, `Fernet` (passes: AES-CBC with HMAC).

### #61 V11.4.1 Approved hash functions · High
- PASS: SHA-256 or stronger wherever hashing serves a security purpose.
- FAIL: MD5 or SHA-1 used for signatures, HMAC, key derivation, token generation, password handling or security-relevant integrity checks. MD5 or SHA-1 for cache keys, ETags or deduplication is not a failure; confirm the purpose in verification. Lower the severity to Low only when MD5 or SHA-1 verifies a third-party file downloaded over TLS against a constant digest pinned in the repository. Keep High for everything else, including digests fetched over the network, downloads over plain HTTP, signatures, HMACs, key derivation, passwords, tokens, or integrity checks over data an attacker can influence.
- Search: `md5`, `sha1`, `SHA1`, `MessageDigest`, `createHash`, `hashlib`, `createHmac`.

## V12 Secure Communication

### #62 V12.1.1 Only TLS 1.2 and 1.3 · Medium · deploy
- Applies when: always for an app reached over the network.
- PASS: TLS configuration in the repository enables only TLS 1.2 and 1.3, or a managed platform enforces it (cite the configuration).
- FAIL: TLS 1.0 or 1.1 enabled (`ssl_protocols TLSv1`, `minVersion: 'TLSv1'`, `PROTOCOL_TLSv1`, `SslProtocols.Tls`, older load balancer security policies).
- Otherwise: NEEDS_REVIEW `deployment`.
- Search: `ssl_protocols`, `minVersion`, `TLSv1`, `SslProtocols`, `ssl_policy`, `SecurityPolicy`.

### #63 V12.2.1 TLS for all external connections · High
- Applies when: always.
- PASS: all external URLs in production code and configuration use `https`, certificate checks are on, and HTTP to HTTPS redirection is visible in the repository.
- FAIL: `http://` URLs to non-local services in production code or configuration, or certificate checks disabled (`rejectUnauthorized: false`, `verify=False`, `NODE_TLS_REJECT_UNAUTHORIZED=0`, `InsecureSkipVerify: true`, certificate callbacks returning true, `CURLOPT_SSL_VERIFYPEER` false).
- Otherwise: NEEDS_REVIEW `deployment` when no failure is found but the HTTPS redirect is not in the repository.
- Search: `http://`, the certificate settings above, `SECURE_SSL_REDIRECT`, `UseHttpsRedirection`, `force_ssl`, `return 301 https`.

### #64 V12.2.2 Publicly trusted certificates · Medium · deploy
- Applies when: always.
- PASS: repository configuration shows managed public certificates (cert-manager with a public issuer, AWS ACM, a platform-managed domain).
- FAIL: self-signed or private CA certificates configured for a public endpoint.
- Otherwise: NEEDS_REVIEW `deployment`.
- Search: `ssl_certificate`, `cert-manager`, `ClusterIssuer`, `acm`, `certificate`, `openssl req`.

## V13 Configuration

### #65 V13.4.1 No source control metadata deployed · Medium · deploy
- Applies when: always.
- PASS: the build ships only build output, or `.dockerignore` excludes `.git`, or the platform deploys from build artifacts.
- FAIL: `COPY . .` without a `.dockerignore` that excludes `.git`, or a web server serving the project root.
- Otherwise: NEEDS_REVIEW `deployment` when no deployment configuration is in the repository.
- Search: `Dockerfile*`, `.dockerignore`, `COPY`, `rsync`, web server `root` directives.

## V14 Data Protection

### #66 V14.2.1 No sensitive data in URLs · Medium
- Applies when: always.
- PASS: tokens, keys, passwords and personal data travel in headers or bodies.
- FAIL: session tokens, API keys, passwords or long-lived tokens in query strings or paths built by the app, or a login form using `GET`. One-time tokens in emailed links (password reset, email verification, invitations) are not a failure.
- Search: `?token=`, `api_key=`, `apikey=`, `access_token=`, `password=`, `method="get"` on forms with passwords, `searchParams.set` with secrets.

### #67 V14.3.1 Client storage cleared at logout · Medium
- Applies when: client-side code stores authenticated data (tokens, user profile, cached responses) in browser storage or app state that survives navigation.
- PASS: logout and session expiry clear that storage, or the server sends `Clear-Site-Data` on logout and the client also clears its own state.
- FAIL: logout leaves tokens or user data in `localStorage`, `sessionStorage`, IndexedDB or persisted state.
- Search: `localStorage`, `sessionStorage`, `indexedDB`, `persist`, `Clear-Site-Data`, logout handlers in the front end.

## V15 Secure Coding and Architecture

### #68 V15.1.1 Dependency remediation time frames documented · Low · docs
- Applies when: always.
- PASS: documentation defines time frames for fixing vulnerable dependencies and for updating libraries in general. A Dependabot or Renovate configuration alone is not documentation.
- Otherwise: NEEDS_REVIEW `external-docs`.
- Search: `SECURITY.md`, `docs/`, `remediation`, `patch policy`, `SLA`.

### #69 V15.2.1 Dependencies within remediation time frames · severity of the worst advisory
- Applies when: always.
- Use the dependency audit from Phase 1 and the time frames #68 found. Decide by the first rule that matches:
  - FAIL: an advisory in a production dependency is older than the documented time frame for its severity. One evidence entry per such advisory: `audit:<command> (<lock file>)` as location, the package, installed version, advisory ID, publication date and fixed version in the reason. Severity is the highest advisory severity.
  - NEEDS_REVIEW `tool-failure`: the audit could not run for at least one production lock file.
  - NEEDS_REVIEW `external-docs`: no documented time frames.
  - NEEDS_REVIEW `external-system`: advisories exist but the audit gives no publication dates; or the advisories pass but compliance with the general update time frame cannot be checked from the repository.
  - PASS: documented time frames exist, every production lock file was audited, no advisory is outside its time frame, and the documentation sets no general update deadline that needs checking.
- Every advisory that is not a FAIL here is still reported under "Known vulnerable dependencies" in Other findings.

### #70 V15.3.1 Only required fields returned · Medium
- Applies when: the app returns data objects through an API or server-rendered data.
- PASS: every field returned is needed by the consumer and the requester may see it. Explicit field lists, DTOs, serializers or model-level hidden fields (Laravel `$hidden`, `toJSON` overrides, Prisma `select` or `omit`) are how this is usually achieved; check the fields they include.
- FAIL: a response contains sensitive or internal fields the consumer does not need (password hashes, tokens, internal flags, other users' personal data), whether a whole record is returned (`res.json(user)`, `fields = '__all__'`, `SELECT *` returned directly) or an explicit list includes them. Severity becomes High when password hashes or secrets are exposed.
- Search: `res.json(`, `return user`, `fields = '__all__'`, `SELECT *`, serializers, response DTOs.
