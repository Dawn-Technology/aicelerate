# iOS Security

Read when the change touches secrets, authentication, biometrics, cryptography, networking configuration, logging, deep links, web content, file storage, analytics, entitlements, the privacy manifest, or CI, and for a whole-project security audit.

In a change review, check only what the change touches. Report what an attacker or another app can actually reach; a pattern alone is not a finding. Confirm version-sensitive API facts with `apple-docs.md`.

## Severity

| Label | When |
| --- | --- |
| `security-violation` | A secret or personal data is exposed, or a protection can be bypassed, on a path the change introduces or makes reachable. |
| `request-for-change` | Protection is weakened or incomplete without a demonstrated exposure, such as an app-wide transport exception or a keychain item without an explicit accessibility class. |
| `optional` | Defense in depth with bounded value. |

## Checks

| Area | Check |
| --- | --- |
| Secret storage | Tokens, passwords, API keys, private keys, and session identifiers live in the Keychain, never in `UserDefaults`, `@AppStorage`, plists, `.xcconfig`, source, files, Core Data, SwiftData, or archives. Secrets in the app bundle are readable by anyone with the IPA; treat them as public. |
| Keychain calls | Every `SecItemAdd`, `SecItemCopyMatching`, `SecItemUpdate`, and `SecItemDelete` result is checked, including `errSecDuplicateItem`, `errSecItemNotFound`, and `errSecInteractionNotAllowed` (device locked). Updates use add-or-update, not delete-then-add. |
| Keychain accessibility | New items set `kSecAttrAccessible` or `kSecAttrAccessControl` explicitly. Prefer a `ThisDeviceOnly` class for tokens that must not move to backups or other devices. `kSecAttrAccessibleAlways` and `kSecAttrAccessibleAlwaysThisDeviceOnly` are deprecated. Background work that reads an item needs an `AfterFirstUnlock` class. |
| Biometrics | A biometric check that only returns a Boolean (`LAContext.evaluatePolicy`) does not protect a secret that is readable without it. Protect the secret with `SecAccessControl` (`.biometryCurrentSet` or `.userPresence`) so reading the keychain item triggers authentication. Handle enrollment changes, lockout, and the passcode fallback deliberately. |
| Logout and reinstall | Logout removes tokens and user data from the Keychain and caches. Keychain items survive app deletion; a fresh install must not silently reuse an old session. |
| Logging | Secrets and personal data are never logged unredacted. With `Logger`/`os_log`, the system redacts interpolated strings and objects unless they are marked `privacy: .public`; integers, floating-point values, and Booleans are public by default (Apple, "Generating log messages from your code"). So `privacy: .public` on a token, email, identifier, or request body is an exposure, while an interpolated string without a privacy modifier is not a finding. `print` and `NSLog` output is not redacted. Crash and analytics reports must not carry secrets. |
| Transport | `NSAllowsArbitraryLoads` and related ATS exceptions are scoped to named domains in `NSExceptionDomains`, justified, and limited to the build configurations that need them (for example a staging Info.plist or `.xcconfig`). Custom `URLSessionDelegate` trust handling never accepts every certificate; pinning, when used, pins the SPKI or CA and has a rotation plan. |
| Cryptography | Prefer CryptoKit. No hardcoded keys, no nonce reuse with the same key, no raw key-agreement output used as a key (derive with HKDF), and no `Insecure.MD5`/`Insecure.SHA1` for security purposes. Custom encryption names who owns the key, where it is stored, and how it rotates. |
| Deep links and URL schemes | Parameters from universal links, custom URL schemes, push payloads, widgets, and App Intents are untrusted input. Validate them before navigation, authentication, payments, or loading web content. Custom URL schemes can be claimed by other apps; never pass tokens through them. |
| Web content | `WKWebView` loads only expected origins. `WKScriptMessageHandler` checks `frame.isMainFrame` and the origin before acting, and never exposes tokens or privileged actions to arbitrary pages. Use `ASWebAuthenticationSession`, not a web view, for third-party sign-in. |
| Data at rest | Files with personal data use an explicit `FileProtectionType` (`.complete` unless background access needs a weaker class). Caches, screenshots in the app switcher, and the general pasteboard do not hold secrets; sensitive text fields set `textContentType` and `isSecureTextEntry` where appropriate. |
| Client-only enforcement | A PIN, parental lock, paywall, feature flag, or role check that only the app enforces is bypassable. When the server sends the secret (such as the PIN) to the client or trusts a client-chosen identifier, the check belongs on the server, with attempt limits. |
| App lock | An app-level biometric or passcode lock also applies when the app returns from the background, and hides content in the app-switcher snapshot. |
| Server-supplied links and content | URLs from APIs, CMS content, push payloads, or remote config are opened only after a scheme and host check; downloaded files and databases are checked for status and type before use. Remote config that changes security- or safety-relevant behavior is signed or otherwise authenticated. |
| Analytics and third-party SDKs | Free text (searches, names), health data, precise location, and full URLs with query strings are not sent to analytics or crash reporting without consent where required. Stable identifiers shared across SDKs and the backend are deliberate. |
| Debug and internal features | Server switchers, mock data, hidden menus, verbose network logging, and environment dumps are compiled out of release builds (`#if DEBUG` or a build setting), not hidden behind a runtime gesture or flag. |
| Privacy manifest and entitlements | Each target's `PrivacyInfo.xcprivacy` declares its required-reason APIs, tracking domains, and collected data types, including data collected through SDKs. Entitlements, keychain access groups, and app groups are needed and use the full team prefix. |
| Dependencies and CI | Packages from personal forks or tracking branches are deliberate and pinned in `Package.resolved`. CI does not run untrusted branch code with signing or release secrets, does not interpolate PR titles or other user input into shell scripts, and pins third-party actions; downloads are verified. Report CI findings separately from app findings. |

## Not In Scope

Server-side authorization, backend secret management, App Store submission, and penetration testing. When a client finding depends on server behavior, state the assumption and mark it unverified.
