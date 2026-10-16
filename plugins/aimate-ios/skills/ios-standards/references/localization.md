# iOS Localization

Read when a change adds or changes user-facing text, string catalogs or `.strings` files, formatting of dates, numbers, or units, or Info.plist texts, and for a whole-project localization audit.

## Supported Languages

The app's languages are the ones the project ships for its own text: `knownRegions` and `developmentRegion` in the project, the source and target languages of the app's and packages' String Catalogs (`.xcstrings`) and `.lproj` folders, `defaultLocalization` in `Package.swift`, and `CFBundleLocalizations` or `CFBundleDevelopmentRegion` in Info.plist. `.lproj` folders of bundled SDKs and dependencies are not app languages. Project instructions that state the supported languages or a single-language product decision outrank this evidence; report disagreements between the sources.

## Severity

| Label | When |
| --- | --- |
| `request-for-change` | On a reachable path, users of a supported language see text in another language, a raw key, placeholder or test copy, a wrong translation, or broken formatting; or a sentence cannot be translated correctly because it is concatenated or lacks plural forms. |
| `optional` | Catalog hygiene and consistency: stale or unused keys, `needs_review` states without a visible error, duplicate identical keys, tone or terminology inconsistencies, text that is only reachable on paths not yet wired up. |

Localization problems are never `security-violation`. Text that only appears in logs, debug menus compiled out of release, previews, or tests is not a finding.

## Checks

| Area | Check |
| --- | --- |
| Completeness | Per supported language and catalog: keys with no entry for that language, and counts per state (`translated`, `needs_review`, `new`); per `.strings` table: keys missing in a language. A key with no translation shows the source value or the key itself. |
| Keys used in code | Every key looked up in code (`Text`, `String(localized:)`, `LocalizedStringKey`, `NSLocalizedString`, SwiftGen `L10n`) exists in the catalog of the bundle the lookup uses. Compare keys exactly: non-breaking spaces, trailing spaces, and punctuation differences make a lookup miss. |
| Bundles | Code in a Swift package passes `bundle: .module` (or the package's own bundle); a lookup without it goes to `Bundle.main` and silently shows the key. A key translated in one module and looked up from another module's bundle misses. |
| Text outside localization | User-facing literals in code: `Text(verbatim:)`, `Text("…")` without a matching key, UIKit `text`/`title`, alert and button titles, accessibility labels, values, and hints, placeholders, and fallback text in data or networking layers. Language checks in code (`locale.identifier.hasPrefix("nl") ? … : …`) instead of a catalog entry. |
| Wrong language in values | A language's values are written in that language: an `en` value in Dutch, or a Dutch value left in English, is a finding even when its state says `translated`. |
| Sentences and plurals | Sentences built by joining translated pieces, units, or links (`+ " " +`, string interpolation of fragments) instead of one format string; lists joined by hand instead of `ListFormatter` or `.formatted()`; count-based strings without plural variations or `.stringsdict`. Placeholders match in type and position across languages. |
| Formatting | Dates, times, numbers, currencies, file sizes, and units use locale-aware APIs (`FormatStyle`, `DateFormatter` templates, `MeasurementFormatter`, `ByteCountFormatter`); a fixed `dateFormat` or hardcoded separators and unit words are findings for user-facing output. A deliberately pinned locale for a single-language product is not. |
| Info.plist and system texts | Permission usage descriptions, app name, and Siri, App Intent, and widget texts are localized for every supported language (`InfoPlist.xcstrings` or `InfoPlist.strings`, App Intents catalogs), not only set in build settings. |
| Extensions and widgets | Each extension, widget, and intent target has translations for every supported language; notification texts built in extensions are checked like app text. |
| Catalog hygiene | Stale (`extractionState: stale`) and unused keys, duplicate keys in `.strings` (the last value wins), empty values, keys built at runtime that extraction cannot see, and consistent terminology and tone (for example formal "u" against informal "je"). |

## Not In Scope

Server-delivered content, text inside images and animations, translation quality beyond obvious errors, and on-screen layout such as truncation. A static review cannot see layout; say so in the report.
