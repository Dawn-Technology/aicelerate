# OWASP MASVS and MASTG for iOS

Read for a whole-project security audit. It maps the OWASP Mobile Application Security Verification Standard (MASVS) 2.1.0 to the MASTG iOS tests and to the areas in [`security.md`](security.md). `security.md` stays the company policy: it decides severity, and this file decides coverage.

Source: [OWASP MASVS](https://mas.owasp.org/MASVS/) 2.1.0 and the [MASTG iOS tests](https://mas.owasp.org/MASTG/tests/), retrieved 2026-11-12. Only current MASTG v2 tests are listed (88 of 129); deprecated v1 tests are covered by them. Test titles and control statements are from the OWASP MAS project, licensed [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). When a project names a newer MASVS or MASTG version, say that this list may be out of date.

## Profiles

Each MASTG test belongs to one or more MAS profiles. Decide which apply in the audit baseline and state them in the report:

| Profile | Applies | Means |
| --- | --- | --- |
| L1 | always | Baseline security for every app. |
| P | always | Privacy: data minimization, purpose strings, tracking domains. App Store privacy rules make this relevant for every app. |
| L2 | when the app has accounts or tokens, payments, health, financial, children's, or precise location data, or the project's instructions ask for it | Defense in depth for apps that handle sensitive data. |
| R | only when the project's instructions ask for it | Resilience against reverse engineering and tampering. |

Record why L2 applies or not, with the evidence (for example "Keychain token for login in `AuthStore.swift:12`"). A test that belongs only to profiles that do not apply is out of scope; leave it out of the report.

## How Each Test Is Checked

The audit reads the repository and never builds or runs the app. The `Checked from` column says how:

- `source`: search tracked sources, Info.plists, entitlements, privacy manifests, and project settings.
- `build settings`: read the Release build settings in the `.pbxproj` and `.xcconfig` files.
- `source + advisories`: list the pinned versions in `Package.resolved` (and `Podfile.lock`, `Cartfile.resolved`) and check them against known advisories, such as the GitHub Advisory Database. This sends package names and versions, not code, to that service; when the project's instructions or the user do not allow it, mark the test not checked and list the pinned versions.
- `SBOM`: check an SBOM only when the project has one; otherwise mark the test not checked.
- `runtime` and `binary`: need a running app or the built IPA. Never mark them passed; list them under `Not checked` with their test ID so a tester can run them.

## Statuses

Give every MASVS control one status for the profiles in scope:

| Status | When |
| --- | --- |
| `fail` | At least one in-scope test or `security.md` check for the control has a reachable finding. |
| `pass` | Every in-scope test checked from the repository passed. Runtime and binary tests for the control are still listed under `Not checked`. |
| `not checked` | Every in-scope test for the control needs a running app, the IPA, or an advisory lookup that was not allowed. |
| `not applicable` | The app has no such feature (for example no web views for PLATFORM-2), with the evidence, or no in-scope profile has tests for it. |

A test's own result uses the same words. The `security.md` areas of a control count toward it too, including controls without an iOS test (AUTH-1, AUTH-3, CODE-1, PRIVACY-2, PRIVACY-4).

## Controls

| Control | Statement | MASTG iOS tests | `security.md` areas |
| --- | --- | --- | --- |
| MASVS-STORAGE-1 | The app securely stores sensitive data. | 0299, 0300, 0301, 0302, 0303, 0388 | Secret storage, Keychain calls, Keychain accessibility, Data at rest |
| MASVS-STORAGE-2 | The app prevents leakage of sensitive data. | 0215, 0296, 0297, 0298, 0299, 0300, 0301, 0302, 0303, 0313, 0314, 0388 | Logging, Data at rest, Keychain accessibility, Logout and reinstall, Pasteboard and keyboards |
| MASVS-CRYPTO-1 | The app employs current strong cryptography and uses it according to industry best practices. | 0210, 0211, 0311, 0317, 0349 | Cryptography |
| MASVS-CRYPTO-2 | The app performs key management according to industry best practices. | 0209, 0210, 0213, 0214, 0246, 0248, 0317 | Cryptography, Secret storage, App lock |
| MASVS-AUTH-1 | The app uses secure authentication and authorization protocols and follows the relevant best practices. | none | Logout and reinstall, Client-only enforcement, Secret storage |
| MASVS-AUTH-2 | The app performs local authentication securely according to the platform best practices. | 0266, 0267, 0268, 0269, 0270, 0271 | Biometrics, App lock |
| MASVS-AUTH-3 | The app secures sensitive operations with additional authentication. | none | Biometrics, Client-only enforcement |
| MASVS-NETWORK-1 | The app secures all network traffic according to the current best practices. | 0321, 0322, 0323, 0342, 0343, 0344, 0345, 0348, 0396, 0397 | Transport |
| MASVS-NETWORK-2 | The app performs identity pinning for all remote endpoints under the developer's control. | 0385 | Transport |
| MASVS-PLATFORM-1 | The app uses IPC mechanisms securely. | 0370, 0371, 0389, 0395 | Deep links and URL schemes, Pasteboard and keyboards |
| MASVS-PLATFORM-2 | The app uses WebViews securely. | 0331, 0332, 0333, 0335, 0336, 0376, 0377, 0378, 0379, 0380 | Web content |
| MASVS-PLATFORM-3 | The app uses the user interface securely. | 0276, 0277, 0278, 0279, 0280, 0290, 0346, 0347 | Pasteboard and keyboards, App lock |
| MASVS-CODE-1 | The app requires an up-to-date platform version. | none | App updates and platform version |
| MASVS-CODE-2 | The app has a mechanism for enforcing app updates. | 0383, 0384 | App updates and platform version |
| MASVS-CODE-3 | The app only uses software components without known vulnerabilities. | 0228, 0229, 0230, 0273, 0275 | Dependencies and CI, Build hardening |
| MASVS-CODE-4 | The app validates and sanitizes all untrusted inputs. | 0228, 0229, 0230, 0386 | Deep links and URL schemes, Server-supplied links and content, Untrusted data parsing, Debug and internal features, Build hardening |
| MASVS-RESILIENCE-1 | The app validates the integrity of the platform. | 0240, 0241, 0367 | Anti-tampering |
| MASVS-RESILIENCE-2 | The app implements anti-tampering mechanisms. | 0220, 0354, 0387 | Anti-tampering |
| MASVS-RESILIENCE-3 | The app implements anti-static analysis mechanisms. | 0219, 0358, 0359, 0391 | Anti-tampering, Build hardening, Debug and internal features |
| MASVS-RESILIENCE-4 | The app implements anti-dynamic analysis techniques. | 0240, 0241, 0261, 0367, 0401, 0402 | Anti-tampering |
| MASVS-PRIVACY-1 | The app minimizes access to sensitive data and resources. | 0360, 0361, 0362, 0363, 0390 | Privacy manifest and entitlements |
| MASVS-PRIVACY-2 | The app prevents identification of the user. | none | Analytics and third-party SDKs |
| MASVS-PRIVACY-3 | The app is transparent about data collection and usage. | 0281 | Privacy manifest and entitlements, Analytics and third-party SDKs |
| MASVS-PRIVACY-4 | The app offers user control over their data. | none | Analytics and third-party SDKs |

Test numbers are `MASTG-TEST-<number>`; each one has a page at `https://mas.owasp.org/MASTG/tests/ios/<category>/MASTG-TEST-<number>/` with the steps to run it. Read a test's page when its row below is not enough to decide.

## MASTG iOS Tests

Tests are grouped by their MASTG category; the Controls column gives the MASVS controls each one verifies.

### MASVS-STORAGE

| Test | Title | Controls | Profiles | Checked from | Area in `security.md` |
| --- | --- | --- | --- | --- | --- |
| 0215 | Sensitive Data Not Marked For Backup Exclusion | STORAGE-2 | L1,L2 | source | Data at rest |
| 0296 | Sensitive Data Exposure in Logs | STORAGE-2 | L1,L2 | runtime | Logging |
| 0297 | Sensitive Data Exposure Through Logging APIs | STORAGE-2 | L1,L2 | source | Logging |
| 0298 | Runtime Monitoring of Files Eligible for Backup | STORAGE-2 | L1,L2 | runtime | Data at rest |
| 0299 | Data Protection Classes for Files in Private Storage | STORAGE-1, STORAGE-2 | L2 | runtime | Data at rest |
| 0300 | References to APIs for Storing Unencrypted Data in Private Storage | STORAGE-1, STORAGE-2 | L2 | source | Secret storage, Data at rest |
| 0301 | Runtime Use of APIs for Storing Unencrypted Data in Private Storage | STORAGE-1, STORAGE-2 | L2 | runtime | Data at rest |
| 0302 | Sensitive Data Unencrypted in Private Storage Files | STORAGE-1, STORAGE-2 | L2 | runtime | Data at rest |
| 0303 | References to APIs for Storing Unencrypted Data in Shared Storage | STORAGE-1, STORAGE-2 | L1,L2 | source | Data at rest |
| 0313 | References to APIs for Preventing Keyboard Caching of Text Fields | STORAGE-2 | L2 | source | Pasteboard and keyboards |
| 0314 | Runtime Monitoring of Text Fields Eligible for Keyboard Caching | STORAGE-2 | L2 | runtime | Pasteboard and keyboards |
| 0388 | References to Sensitive Data Stored Unprotected in Shared App Group Containers | STORAGE-1, STORAGE-2 | L2 | source | Data at rest |

### MASVS-CRYPTO

| Test | Title | Controls | Profiles | Checked from | Area in `security.md` |
| --- | --- | --- | --- | --- | --- |
| 0209 | Insufficient Key Sizes | CRYPTO-2 | L1,L2 | source | Cryptography |
| 0210 | Broken Symmetric Encryption Algorithms | CRYPTO-1, CRYPTO-2 | L1,L2 | source | Cryptography |
| 0211 | Broken Hashing Algorithms | CRYPTO-1 | L1,L2 | source | Cryptography |
| 0213 | Use of Hardcoded Cryptographic Keys in Code | CRYPTO-2 | L1,L2 | source | Cryptography |
| 0214 | Hardcoded Cryptographic Keys in Files | CRYPTO-2 | L1,L2 | source | Cryptography |
| 0311 | Insecure Random API Usage | CRYPTO-1 | L1,L2 | source | Cryptography |
| 0317 | Broken Symmetric Encryption Modes | CRYPTO-1, CRYPTO-2 | L1,L2 | source | Cryptography |
| 0349 | Runtime Use of Insecure Random APIs | CRYPTO-1 | L1,L2 | runtime | Cryptography |

### MASVS-AUTH

| Test | Title | Controls | Profiles | Checked from | Area in `security.md` |
| --- | --- | --- | --- | --- | --- |
| 0266 | References to APIs for Event-Bound Biometric Authentication | AUTH-2 | L2 | source | Biometrics |
| 0267 | Runtime Use Of Event-Bound Biometric Authentication | AUTH-2 | L2 | runtime | Biometrics |
| 0268 | References to APIs Allowing Fallback to Non-Biometric Authentication | AUTH-2 | L2 | source | Biometrics |
| 0269 | Runtime Use Of APIs Allowing Fallback to Non-Biometric Authentication | AUTH-2 | L2 | runtime | Biometrics |
| 0270 | References to APIs Detecting Biometric Enrollment Changes | AUTH-2 | L2 | source | Biometrics |
| 0271 | Runtime Use Of APIs Detecting Biometric Enrollment Changes | AUTH-2 | L2 | runtime | Biometrics |

### MASVS-NETWORK

| Test | Title | Controls | Profiles | Checked from | Area in `security.md` |
| --- | --- | --- | --- | --- | --- |
| 0321 | Hardcoded HTTP URLs | NETWORK-1 | L1,L2 | source | Transport |
| 0322 | App Transport Security Configurations Allowing Cleartext Traffic | NETWORK-1 | L1,L2 | source | Transport |
| 0323 | Uses of Low-Level Networking APIs for Cleartext Traffic | NETWORK-1 | L1,L2 | source | Transport |
| 0342 | References to Weak ATS TLS Policy Exceptions in Info.plist | NETWORK-1 | L1,L2 | source | Transport |
| 0343 | URLSession TLS Protocol Configuration | NETWORK-1 | L1,L2 | source | Transport |
| 0344 | Network.framework TLS Protocol Configuration | NETWORK-1 | L1,L2 | source | Transport |
| 0345 | Embedded or Third-party TLS Stack Configuration | NETWORK-1 | L1,L2 | source | Transport |
| 0348 | Insecure TLS Protocols in Network Traffic | NETWORK-1 | L1,L2 | runtime | Transport |
| 0385 | Missing Certificate Pinning in ATS | NETWORK-2 | L2 | source | Transport |
| 0396 | References to URLSessionDelegate Bypassing Certificate Validation | NETWORK-1 | L1,L2 | source | Transport |
| 0397 | References to WKNavigationDelegate Bypassing Certificate Validation | NETWORK-1 | L1,L2 | source | Transport |

### MASVS-PLATFORM

| Test | Title | Controls | Profiles | Checked from | Area in `security.md` |
| --- | --- | --- | --- | --- | --- |
| 0276 | Use of the iOS General Pasteboard | PLATFORM-3 | L2 | source | Pasteboard and keyboards |
| 0277 | Sensitive Data in the iOS General Pasteboard at Runtime | PLATFORM-3 | L2 | runtime | Pasteboard and keyboards |
| 0278 | Pasteboard Contents Not Cleared After Use | PLATFORM-3 | L2 | source | Pasteboard and keyboards |
| 0279 | Pasteboard Contents Not Expiring | PLATFORM-3 | L2 | source | Pasteboard and keyboards |
| 0280 | Pasteboard Contents Not Restricted to Local Device | PLATFORM-3 | L2 | source | Pasteboard and keyboards |
| 0290 | Runtime Verification of Sensitive Content Exposure in Screenshots During App Backgrounding | PLATFORM-3 | L2 | runtime | App lock |
| 0331 | Use of Deprecated WebView APIs | PLATFORM-2 | L1,L2 | source | Web content |
| 0332 | Attacker-Controlled URI in WebViews | PLATFORM-2 | L1,L2 | source | Web content |
| 0333 | Overly Broad File Read Access in WebViews | PLATFORM-2 | L1,L2 | source | Web content |
| 0335 | WebView File Origin Access Relaxed by Configuration | PLATFORM-2 | L1,L2 | source | Web content |
| 0336 | Runtime Setting of Relaxed WebView File Origin Policies | PLATFORM-2 | L1,L2 | runtime | Web content |
| 0346 | References to APIs Hiding Sensitive Data in Text Input Fields | PLATFORM-3 | L2 | source | Pasteboard and keyboards |
| 0347 | Runtime Use of APIs Hiding Sensitive Data in Text Input Fields | PLATFORM-3 | L2 | runtime | Pasteboard and keyboards |
| 0370 | Missing Input Validation in Custom URL Scheme Handlers | PLATFORM-1 | L1,L2 | source | Deep links and URL schemes |
| 0371 | Missing Source Validation in Custom URL Scheme Handlers | PLATFORM-1 | L1,L2 | source | Deep links and URL schemes |
| 0376 | References to Native Bridge APIs in WebViews | PLATFORM-2 | L1,L2 | source | Web content |
| 0377 | References to `evaluateJavaScript` Used as Bridge Reply in `WKScriptMessageHandler` | PLATFORM-2 | L1,L2 | source | Web content |
| 0378 | References to Password Fields in WebView-Loaded HTML | PLATFORM-2 | L1,L2 | source | Web content |
| 0379 | References to `evaluateJavaScript` Without Content World Isolation | PLATFORM-2 | L1,L2 | source | Web content |
| 0380 | References to `evaluateJavaScript` Writing Sensitive Data into WebView DOM | PLATFORM-2 | L1,L2 | source | Web content |
| 0389 | References to the App-Wide Restriction of Custom Keyboards | PLATFORM-1 | L1,L2 | source | Pasteboard and keyboards |
| 0390 | Full Access Requested by a Custom Keyboard Extension | PRIVACY-1 | P | source | Pasteboard and keyboards |
| 0395 | Missing Input Validation in Universal Link Handlers | PLATFORM-1 | L1,L2 | source | Deep links and URL schemes |

### MASVS-CODE

| Test | Title | Controls | Profiles | Checked from | Area in `security.md` |
| --- | --- | --- | --- | --- | --- |
| 0228 | Position Independent Code (PIC) not Enabled | CODE-3, CODE-4 | L2 | build settings | Build hardening |
| 0229 | Stack Canaries Not enabled | CODE-3, CODE-4 | L2 | build settings | Build hardening |
| 0230 | Automatic Reference Counting (ARC) not enabled | CODE-3, CODE-4 | L2 | build settings | Build hardening |
| 0273 | Identify Dependencies with Known Vulnerabilities by Scanning Dependency Managers Artifacts | CODE-3 | L1,L2 | source + advisories | Dependencies and CI |
| 0275 | Dependencies with Known Vulnerabilities in the App's SBOM | CODE-3 | L1,L2 | SBOM | Dependencies and CI |
| 0383 | References to Enforced Updating APIs | CODE-2 | L2 | source | App updates |
| 0384 | Runtime Use of Enforced Updating APIs | CODE-2 | L2 | runtime | App updates |
| 0386 | References to Object Deserialization of Untrusted Data | CODE-4 | L1,L2 | source | Untrusted data parsing |

### MASVS-RESILIENCE

| Test | Title | Controls | Profiles | Checked from | Area in `security.md` |
| --- | --- | --- | --- | --- | --- |
| 0219 | Testing for Debugging Symbols | RESILIENCE-3 | R | build settings | Anti-tampering |
| 0220 | Usage of Outdated Code Signature Format | RESILIENCE-2 | R | binary | Anti-tampering |
| 0240 | Jailbreak Detection in Code | RESILIENCE-1, RESILIENCE-4 | R | source | Anti-tampering |
| 0241 | Runtime Use of Jailbreak Detection Techniques | RESILIENCE-1, RESILIENCE-4 | R | runtime | Anti-tampering |
| 0246 | Runtime Use of Secure Screen Lock Detection APIs | CRYPTO-2 | L2 | runtime | App lock |
| 0248 | References to APIs for Detecting Secure Screen Lock | CRYPTO-2 | L2 | source | App lock |
| 0261 | Debuggable Entitlement Enabled in the entitlements.plist | RESILIENCE-4 | R | source | Anti-tampering |
| 0354 | Runtime Use of Hook Detection Techniques | RESILIENCE-2 | R | runtime | Anti-tampering |
| 0358 | Implementation Details Exposure Through Logging APIs | RESILIENCE-3 | R | source | Anti-tampering |
| 0359 | Implementation Details Exposure in Logs | RESILIENCE-3 | R | runtime | Anti-tampering |
| 0367 | Runtime Use of Virtual Device Detection Techniques | RESILIENCE-1, RESILIENCE-4 | R | runtime | Anti-tampering |
| 0387 | References to Storage Integrity Check APIs | RESILIENCE-2 | R | source | Anti-tampering |
| 0391 | Insufficient Obfuscation of Security-Relevant Native Code | RESILIENCE-3 | R | binary | Anti-tampering |
| 0401 | References to Debugging Detection APIs | RESILIENCE-4 | R | source | Anti-tampering |
| 0402 | Runtime Use of Debugging Detection APIs | RESILIENCE-4 | R | runtime | Anti-tampering |

### MASVS-PRIVACY

| Test | Title | Controls | Profiles | Checked from | Area in `security.md` |
| --- | --- | --- | --- | --- | --- |
| 0281 | Undeclared Known Tracking Domains | PRIVACY-3 | P | source | Privacy manifest and entitlements |
| 0360 | Purpose String Accuracy for Reachable Protected Resource Access | PRIVACY-1 | P | source | Privacy manifest and entitlements |
| 0361 | Runtime Use of Protected Resource APIs Without Accurate Purpose Strings | PRIVACY-1 | P | runtime | Privacy manifest and entitlements |
| 0362 | Entitlements for Unjustified Capability Exposure | PRIVACY-1 | P | source | Privacy manifest and entitlements |
| 0363 | Runtime Use of Entitlement-Backed APIs for Unjustified Capability Exposure | PRIVACY-1 | P | runtime | Privacy manifest and entitlements |
