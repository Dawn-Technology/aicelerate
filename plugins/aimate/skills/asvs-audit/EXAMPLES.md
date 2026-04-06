# ASVS Audit Examples

Minimal examples showing how each status type should appear in a final report. For evidence formats, see `references/evidence-patterns.md`. For severity rules, see `references/severity-guidance.md`.

---

## Example: ❌ FAIL Finding

````markdown
### #12 - V2.1.2 - Password Security

- **Chapter**: V2 Authentication
- **Section**: V2.1 Password Security
- **ASVS ID**: V2.1.2
- **Internal Item #**: 12
- **Requirement**: Verify that passwords of at least 64 characters are permitted, and that passwords of more than 128 characters are denied.
- **Severity**: 🟡 Medium
- **Location**: `src/lib/auth/validation.ts:23`
- **Evidence**: `src/lib/auth/validation.ts:23` - `maxLength: 50` restricts passwords to 50 characters
- **Description**: The password validation schema enforces a maximum length of 50 characters, which is below the ASVS requirement of permitting at least 64 characters. This unnecessarily limits password strength and may prevent users from using passphrases.
- **Remediation**:
  Update the password validation to allow 64-128 characters:

  ```typescript
  // src/lib/auth/validation.ts
  export const passwordSchema = z.string()
    .min(12, "Password must be at least 12 characters")
    .max(128, "Password must not exceed 128 characters"); // Changed from 50
  ```
````

---

## Example: ✅ PASS Row (Verification Summary Table)

```markdown
| #15 V2.2.1 | V2 Authentication<br>V2.2 General Authenticator Security | Verify that anti-automation controls are effective at mitigating breached credential testing, brute force, and account lockout attacks. | ✅ PASS | `library:next-auth@5.0:built-in-rate-limiting` + `src/app/api/auth/[...nextauth]/route.ts:12` custom lockout after 5 attempts |
```

---

## Example: ⚪ N/A Row (Verification Summary Table)

```markdown
| #45 V12.1.1 | V12 Files and Resources<br>V12.1 File Upload | Verify that the application will not accept large files that could fill up storage or cause a denial of service. | ⚪ N/A | N/A - no file upload endpoints found (searched: `upload`, `multer`, `formidable`, `multipart` in src/) |
```
