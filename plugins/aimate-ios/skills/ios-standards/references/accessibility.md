# iOS Accessibility

Read when a change touches user interface, text styles, colors, images, controls, gestures, media, forms, or navigation, and for a whole-app accessibility audit.

## Standard

Validate against **WCAG 2.2 Level A and AA**, applied to native screens as the W3C note [Guidance on Applying WCAG 2.2 to Mobile Applications (WCAG2Mobile)](https://www.w3.org/TR/wcag2mobile-22/) describes. Sources: [WCAG 2.2](https://www.w3.org/TR/WCAG22/), WCAG2Mobile (Group Draft Note, 6 May 2025; informative, several mobile sections still placeholders), and [WCAG 2.1](https://www.w3.org/TR/WCAG21/). Level AAA is out of scope.

- The unit of evaluation is a **screen** (a view the user navigates to, a sheet, an alert, or a full-screen state). Criteria about a "set of web pages" apply to the set of screens in the app.
- The column `2.1` marks the criteria of WCAG 2.1 AA. EN 301 549, which the European Accessibility Act and Dutch government rules use for apps, requires WCAG 2.1 AA. Report a failure on such a criterion as part of that legal baseline; whether the law applies to a project is for the team to confirm, not for the audit to decide.
- Content inside a `WKWebView` or `SFSafariViewController` is web content: WCAG 2.2 for the web applies to it as written. Name those screens and their URLs in the report; the native checks below do not cover them.
- 4.1.1 Parsing is obsolete in WCAG 2.2 and is not checked.

## Severity

| Label | When |
| --- | --- |
| `request-for-change` | A Level A or AA criterion fails on a screen that is reachable in release builds, so a user of VoiceOver, Voice Control, Switch Control, Full Keyboard Access, large text, or with low vision or limited dexterity cannot perceive, operate, or understand it. |
| `optional` | A platform best practice beyond WCAG A/AA (see Platform Settings), a failure only on a path not reachable in release, or a borderline case that needs a person to decide. |

Accessibility problems are never `security-violation`. Previews, debug menus compiled out of release, and tests are not findings.

## How Criteria Are Checked

- `source`: search the tracked sources, storyboards and XIBs, asset catalogs, and Info.plists. A pattern is a candidate; trace it to a screen before reporting it.
- `audit:<type>`: Apple's automated audit in XCUITest (`XCUIApplication.performAccessibilityAudit(for:_:)`, iOS 17 and later) can confirm it. The iOS audit types are `contrast`, `elementDetection`, `hitRegion`, `sufficientElementDescription`, `dynamicType`, `textClipped`, and `trait`.
  Map an audit issue to a criterion with its type: `contrast` to 1.4.3 (text) or 1.4.11 (other elements), `elementDetection` to 1.1.1 and 4.1.2, `hitRegion` to 2.5.8, `sufficientElementDescription` to 1.1.1 and 2.4.6, `dynamicType` to 1.4.4, `textClipped` to 1.4.4 and 1.4.10, and `trait` to 1.3.1 and 4.1.2. The audit only sees the screens a test opens, in the state and appearance the test sets.
- `manual`: needs a person with VoiceOver, Voice Control, Switch Control, or a hardware keyboard, or judgment of content such as video. List these for a tester; never mark them passed from source alone.

## Criteria

| SC | Level | 2.1 | iOS check | Checked by |
| --- | --- | --- | --- | --- |
| 1.1.1 Non-text Content | A | yes | Meaningful images and icon-only buttons have an `accessibilityLabel` (a `Label` or `Button` with text, `.accessibilityLabel`, or `accessibilityLabel` in UIKit and Interface Builder). Decorative images are hidden: `Image(decorative:)`, `.accessibilityHidden(true)`, or `isAccessibilityElement = false`. An SF Symbol name or file name is not a label. | source, audit:sufficientElementDescription, audit:elementDetection |
| 1.2.1 Audio-only and Video-only (Prerecorded) | A | yes | Prerecorded audio-only or video-only content has a text or audio alternative. | manual |
| 1.2.2 Captions (Prerecorded) | A | yes | The player shows caption tracks: `AVPlayerViewController` or a custom player that exposes the legible `AVMediaSelectionGroup` and respects `MACaptionAppearance`. A custom player without a captions control is a finding when the content has captions. | source, manual |
| 1.2.3 Audio Description or Media Alternative (Prerecorded) | A | yes | Audio description tracks, when the content has them, can be selected in the player. | source, manual |
| 1.2.4 Captions (Live) | AA | yes | Live streams show the stream's captions (CEA-608/708 or WebVTT). | source, manual |
| 1.2.5 Audio Description (Prerecorded) | AA | yes | As 1.2.3, for all prerecorded video. | manual |
| 1.3.1 Info and Relationships | A | yes | Headings have the header trait (`.accessibilityAddTraits(.isHeader)`, `.accessibilityHeading`, `.header` in UIKit); related elements are grouped (`.accessibilityElement(children: .combine)`, list and table semantics); tappable views that act as buttons use `Button` or the button trait, not a bare `onTapGesture`. | source, audit:trait |
| 1.3.2 Meaningful Sequence | A | yes | VoiceOver reads in a meaningful order; custom order uses `accessibilitySortPriority` or `accessibilityElements`. Layouts built with `ZStack`, overlays, or absolute positions are checked. | source, manual |
| 1.3.3 Sensory Characteristics | A | yes | Instructions do not rely only on shape, color, size, position, or sound ("tap the green button on the right"). | source, manual |
| 1.3.4 Orientation | AA | yes | `UISupportedInterfaceOrientations` (and `~ipad`) and `supportedInterfaceOrientations` overrides do not lock one orientation unless it is essential (for example a camera scanner or a game). WCAG2Mobile treats supporting every orientation as best practice. | source |
| 1.3.5 Identify Input Purpose | AA | yes | Fields that collect the user's own data set `textContentType` (`.name`, `.emailAddress`, `.telephoneNumber`, `.postalCode`, `.username`, `.password`, `.oneTimeCode`, and so on). | source |
| 1.4.1 Use of Color | A | yes | Color is not the only way to show state, errors, links, or chart series; add text, an icon, or a shape, and honor `accessibilityDifferentiateWithoutColor`. | source, manual |
| 1.4.2 Audio Control | A | yes | Audio that plays automatically for more than 3 seconds can be paused or stopped, or its volume set separately. | source |
| 1.4.3 Contrast (Minimum) | AA | yes | Text contrast is at least 4.5:1, or 3:1 for large text, in light and dark appearance. WCAG's large text (18 pt, or 14 pt bold) is measured in print points; in iOS points, which match CSS pixels, that is about 24 pt, or 19 pt bold. Check named colors in asset catalogs and design tokens against the backgrounds they are used on. | source, audit:contrast |
| 1.4.4 Resize Text | AA | yes | Text scales with Dynamic Type: text styles (`.font(.body)`, `UIFont.preferredFont(forTextStyle:)`), custom fonts through `Font.custom(_:size:relativeTo:)` or `UIFontMetrics`, `adjustsFontForContentSizeCategory = true` in UIKit, and sizes from `@ScaledMetric`. Fixed sizes (`.font(.system(size:))`, `UIFont.systemFont(ofSize:)`) and caps such as `.dynamicTypeSize(...DynamicTypeSize.large)` without a reason are findings. | source, audit:dynamicType, audit:textClipped |
| 1.4.5 Images of Text | AA | yes | Text is rendered as text, not baked into images (banners, buttons, onboarding art), except logos. | source, manual |
| 1.4.10 Reflow | AA | yes | At accessibility text sizes, content stays readable without clipping or two-way scrolling: no fixed heights around text, `lineLimit(1)` only where truncation is acceptable, scroll views for long content, and layouts that switch axis for `dynamicTypeSize.isAccessibilitySize` (or `ViewThatFits`). | source, audit:textClipped |
| 1.4.11 Non-text Contrast | AA | yes | Control boundaries, icons that carry meaning, focus indicators, and chart elements have at least 3:1 contrast against adjacent colors. | source, audit:contrast, manual |
| 1.4.12 Text Spacing | AA | yes | Not applicable to native text, because iOS does not let users override text spacing (WCAG2Mobile). Applies to web content in web views. | — |
| 1.4.13 Content on Hover or Focus | AA | yes | Custom popovers or tooltips shown on pointer hover or focus (iPad pointer) can be dismissed, hovered, and stay visible. Tooltips controlled by the platform, such as `.help()`, are exempt. | source |
| 2.1.1 Keyboard | A | yes | All functions work with a hardware keyboard, Full Keyboard Access, and Switch Control. Standard controls do; custom gesture-only controls need an `accessibilityAction`, focusability (`.focusable()`), or a button alternative. | source, manual |
| 2.1.2 No Keyboard Trap | A | yes | Keyboard and Switch Control focus can always leave a view; custom focus handling (`@FocusState`, `UIFocusGuide`) does not lock it in. | manual |
| 2.1.4 Character Key Shortcuts | A | yes | Single-key shortcuts (`.keyboardShortcut` or `UIKeyCommand` without a modifier) can be turned off or remapped, or only work when their control has focus. | source |
| 2.2.1 Timing Adjustable | A | yes | Time limits (session timeouts with unsaved input, auto-dismissing messages with actions, timed one-time codes) can be extended, turned off, or adjusted, or warn before expiring. | source, manual |
| 2.2.2 Pause, Stop, Hide | A | yes | Content that moves, scrolls, or updates automatically for more than 5 seconds (auto-advancing carousels, tickers, looping animation) can be paused, and respects Reduce Motion (`accessibilityReduceMotion`, `UIAccessibility.isReduceMotionEnabled`). | source |
| 2.3.1 Three Flashes or Below Threshold | A | yes | Nothing flashes more than three times per second (animations, video content). | source, manual |
| 2.4.1 Bypass Blocks | A | yes | Usually met by the platform: VoiceOver's rotor navigates by headings, so 1.3.1 header traits matter. Check long repeated blocks above main content and web views. | source, manual |
| 2.4.2 Page Titled | A | yes | Every screen has a title that describes it: `.navigationTitle`, `title` or `navigationItem.title` in UIKit, or an accessible heading for screens without a navigation bar, and modal screens too. | source |
| 2.4.3 Focus Order | A | yes | When a screen, sheet, alert, or custom overlay appears, VoiceOver focus moves into it and stays there: `@AccessibilityFocusState`, `UIAccessibility.post(notification: .screenChanged, argument:)`, and `accessibilityViewIsModal` on custom modals. | source, manual |
| 2.4.4 Link Purpose (In Context) | A | yes | Link and button text says where it goes; "read more" or "click here" without context is a finding unless the label adds it. | source |
| 2.4.5 Multiple Ways | AA | yes | For an app's set of screens: content-heavy apps offer more than one way to find a screen (navigation and search, for example). Usually met or not applicable; say which. | source, manual |
| 2.4.6 Headings and Labels | AA | yes | Headings and accessibility labels describe the topic or purpose; no labels such as "button", "image", or duplicates for different actions. | source, audit:sufficientElementDescription |
| 2.4.7 Focus Visible | AA | yes | Keyboard focus is visible; custom controls do not remove the focus effect (`.focusEffectDisabled()`) without their own indicator. | source, manual |
| 2.4.11 Focus Not Obscured (Minimum) | AA | 2.2 | The focused element is not fully hidden by sticky headers, bottom bars, banners, or the on-screen keyboard (keyboard avoidance, `safeAreaInset`). | manual |
| 2.5.1 Pointer Gestures | A | yes | Multi-finger and path-based gestures (pinch, rotate, custom swipe or drawing paths) have a single-tap alternative or an `accessibilityAction`. Standard `swipeActions` are exposed to VoiceOver and pass. | source |
| 2.5.2 Pointer Cancellation | A | yes | Actions run on touch up, not touch down: no `UIControl.Event.touchDown` actions, and no `DragGesture(minimumDistance: 0)` or zero-duration long press used as a button. | source |
| 2.5.3 Label in Name | A | yes | The accessibility label contains the visible text, so Voice Control can activate it by what is on screen; add `accessibilityInputLabels` for icon-only controls. | source |
| 2.5.4 Motion Actuation | A | yes | Shake (`motionEnded`) or tilt (Core Motion) actions have an on-screen alternative and can be turned off. | source |
| 2.5.7 Dragging Movements | AA | 2.2 | Dragging (reordering with `onMove` or `.draggable`, custom sliders, bottom sheets) has a tap alternative, such as edit buttons, `accessibilityAdjustableAction`, or detents with buttons. | source |
| 2.5.8 Target Size (Minimum) | AA | 2.2 | Touch targets are at least 24 × 24 pt or spaced so a 24 pt circle around each does not overlap another target. Apple's guideline of 44 × 44 pt is best practice: below 24 pt is `request-for-change`, between 24 and 44 pt is `optional`. Check `.frame`, `contentShape`, and small custom buttons. | source, audit:hitRegion |
| 3.1.1 Language of Page | A | yes | The app's language matches its content: `CFBundleDevelopmentRegion` and the localizations shipped (see `localization.md`). | source |
| 3.1.2 Language of Parts | AA | yes | Text in another language than the surrounding UI (English terms in a Dutch app, names of foreign programs) sets `accessibilityLanguage` or an `AttributedString` language attribute so VoiceOver pronounces it correctly. | source, manual |
| 3.2.1 On Focus | A | yes | Moving focus to a field or control does not navigate, submit, or open something by itself. | source, manual |
| 3.2.2 On Input | A | yes | Changing a picker, toggle, segmented control, or text field does not navigate or submit unexpectedly without warning. | source, manual |
| 3.2.3 Consistent Navigation | AA | yes | Navigation that repeats across screens (tab bar, menu, toolbar) keeps the same relative order. | source |
| 3.2.4 Consistent Identification | AA | yes | The same function has the same label and icon on every screen. | source |
| 3.2.6 Consistent Help | A | 2.2 | When help or contact options exist on several screens, they are in the same relative place. | source |
| 3.3.1 Error Identification | A | yes | Input errors are described in text and announced (`AccessibilityNotification.Announcement`, `UIAccessibility.post(notification: .announcement, …)`), not only shown with a red border. | source |
| 3.3.2 Labels or Instructions | A | yes | Fields have a visible label or instruction; a placeholder alone disappears when typing and is a finding for required or formatted input. | source |
| 3.3.3 Error Suggestion | AA | yes | Error messages say how to fix the input when that is known. | source |
| 3.3.4 Error Prevention (Legal, Financial, Data) | AA | yes | Purchases, payments, legal agreements, and deleting data or accounts can be reviewed, confirmed, or undone. | source |
| 3.3.7 Redundant Entry | A | 2.2 | Information already entered in the same flow is filled in or selectable, not asked again. | source, manual |
| 3.3.8 Accessible Authentication (Minimum) | AA | 2.2 | Sign-in needs no cognitive test without an alternative: paste is not blocked in password and code fields, password managers and AutoFill work (`textContentType` `.username`, `.password`, `.newPassword`, `.oneTimeCode`), and passkeys or Sign in with Apple are allowed where offered. Puzzle CAPTCHAs need an alternative. | source |
| 4.1.2 Name, Role, Value | A | yes | Custom controls expose a label, the right traits (button, selected, toggle, adjustable), a value (`accessibilityValue`), and actions (`accessibilityAdjustableAction`, `accessibilityAction`); state changes update them. | source, audit:trait, audit:elementDetection |
| 4.1.3 Status Messages | AA | yes | Status messages that do not move focus (toasts, "saved", loading finished, result counts, errors) are announced with an accessibility announcement. | source |

## Platform Settings

Beyond WCAG A/AA, check that the app respects the iOS accessibility settings users rely on; report gaps as `optional` unless a WCAG criterion above fails: Reduce Motion, Reduce Transparency (`accessibilityReduceTransparency`), Increase Contrast (`colorSchemeContrast`), Bold Text (`legibilityWeight`), Smart Invert (`accessibilityIgnoresInvertColors` on photos and video), Button Shapes, and Differentiate Without Color. These are also the features the App Store's Accessibility Nutrition Labels ask about, so the report helps the team fill them in.

## Search Hints

Useful `git grep` starting points: `onTapGesture`, `accessibilityLabel`, `accessibilityHidden`, `Image(`, `.font(.system(size:`, `systemFont(ofSize:`, `dynamicTypeSize`, `lineLimit`, `.frame(width:`, `minimumScaleFactor`, `UISupportedInterfaceOrientations`, `supportedInterfaceOrientations`, `textContentType`, `isSecureTextEntry`, `canPerformAction`, `keyboardShortcut`, `UIKeyCommand`, `Timer`, `MagnificationGesture`, `DragGesture`, `touchDown`, `motionEnded`, `onMove`, `.draggable`, `AVPlayer`, `WKWebView`, `accessibilityViewIsModal`, `.announcement`, `accessibilityLanguage`, and in storyboards and XIBs `isAccessibilityElement` and `accessibilityLabel`.
