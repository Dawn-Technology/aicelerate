# Design rules

The rubric for Phase 2. Each rule says what it protects, what a violation looks like in real code, when not to flag it, and the usual fix. The "when not to flag" notes matter as much as the signals: a review that flags every idiom of the codebase's framework is noise, and the team will stop reading it.

Cite the rule by its name (for example "Dependency Direction") on the Rule line of each finding. Cite one rule per finding. When one problem fits several rules, cite the rule whose fix you propose. If two rules give the same fix, cite the one that comes first in this file. Example: domain code that calls `new` on an HTTP client breaks Dependency Direction, Abstraction Decoupling and Layer Isolation; the fix is a port owned by the domain, so cite Dependency Direction.

Where a rule says "many", "large" or "wide", count, and put the number in the finding so the reader can disagree with it. The rules do not set thresholds, because the right number depends on the codebase.

If someone asks for a SOLID review, the mapping is: single responsibility = Single Reason to Change; open/closed = Extensibility over Modification; Liskov = Substitutability; interface segregation = Interface Segregation; dependency inversion = Dependency Direction and Abstraction Decoupling.

The rules do not depend on a design pattern. They apply on top of whichever patterns the codebase uses (layered, MVC, Active Record, hexagonal, CQRS, and so on). A pattern says how the team chose to arrange the code. The rules ask whether that arrangement keeps change cheap and safe. Judge both, and say in section 1 of the report, in a sentence each, where the patterns hold and where the rules break.

## Contents

1. Architectural Boundaries: Layer Isolation, Dependency Direction, Orchestration, Acyclic Dependencies, Module Encapsulation, Cross-Cutting Concerns, Error Handling
2. Component Responsibility & Cohesion: Single Reason to Change, Extensibility over Modification, Substitutability, Interface Segregation, Abstraction Decoupling
3. Simplicity & Pragmatism: Single Source of Truth, Minimal Necessary Complexity, Build Only What Is Needed
4. Change Safety, Platform & Dependencies: Tested Where It Changes, Supported Platform, Dependency Health
5. When rules pull against each other

---

## 1. Architectural Boundaries

The three layers are:

- **Domain**: business rules, calculations, invariants. What would stay true if you swapped the database, the web framework and the UI.
- **Application**: use cases. Loads what a use case needs, calls the domain, saves the result, handles transactions, sends events.
- **Infrastructure**: everything that talks to the outside: database, ORM, HTTP clients, queues, file system, UI, framework glue.

Not every codebase names these layers. Map what exists onto them before judging (see "Establish the intended architecture" in SKILL.md).

**In a frontend or mobile app**, map by what the code does, not by folder names:

- Domain: types, validation and calculations that stay true without a screen or a server (price rules, schemas, state transitions). Often a small `domain/` or `models/` folder, or nothing.
- Application: the use cases of a screen or flow. Hooks, stores, services, thunks and server actions that load data, call the domain, and decide what to show next.
- Infrastructure: API clients, storage, the router, framework glue, and the components themselves. To the domain, rendering is infrastructure.

Dependency Direction applies unchanged: the domain must not import React, a router or an HTTP client. Signals that belong to frontends: a component that fetches data or holds a business rule (price, eligibility, form validity beyond the shape of the input); the same rule in a component and in the API layer (Single Source of Truth); state copied into several stores or hooks; one component or hook that fetches, applies rules and renders (Single Reason to Change). Don't flag: components that only render props, or a form library's own field validation.

### Layer Isolation

Protects: the ability to change a database query, API format or UI without touching business rules, and to test business rules without booting infrastructure.

Signals:

- A controller, route handler, CLI command or UI component that contains business decisions (pricing, eligibility, state transitions, validation beyond input shape).
- SQL, ORM query builders or HTTP calls inside code that also makes business decisions.
- One file whose imports span web framework, ORM and domain types at once.

Don't flag: thin CRUD screens with no business rules. There is nothing to isolate. Also framework-idiomatic code in small apps (a Rails or Laravel app with logic in models) when it is not causing pain in the hot spots.

Fix: move the decision into a domain function or object that takes plain data and returns plain data. Leave the caller to fetch, call and persist.

### Dependency Direction

Protects: the domain's independence. If the domain imports infrastructure, every infrastructure change can break business rules, and domain tests need a database.

Signals (`scripts/deps.py` finds these across the whole repo, not only hot spots, when you give it the layer mapping; for languages it does not read, grep):

- Files in a domain or model folder that import ORM base classes, framework request/response types, HTTP clients, queue clients, `env`/config readers, or logging frameworks.
- Imports that point from an inner layer to an outer one (domain to application or infrastructure). Application to infrastructure counts only where the declared architecture puts ports between them.
- Domain objects annotated with persistence mapping (ORM decorators, attributes, annotations). Weigh this by the framework: in some stacks this is the accepted trade-off.
- Domain code that catches or throws infrastructure exceptions (database errors, HTTP errors).

Don't flag: imports of the language's standard library, small pure utility libraries (dates, money, UUIDs), or a shared kernel the team deliberately put in the domain.

Fix: define the need as an interface (port) inside the domain or application layer, implement it in infrastructure, and pass it in.

### Orchestration

Protects: one obvious place per use case, and domain logic that can be tested without mocks.

Signals:

- Application services that compute business results themselves (loops with business conditions, arithmetic on money, status rules) instead of asking the domain.
- The opposite: domain objects that open transactions, save themselves, or send email.
- The same use case steps (load, check, save, notify) scattered across controller, service and model.

Don't flag: a use case so small that a separate domain object would just be a wrapper around one `if`.

Fix: application service does load → call domain → save → publish. The rule itself moves into the domain object or a pure function.

### Acyclic Dependencies

Protects: the ability to change, test and release one module without the others. When module A imports B and B imports A, they are one module with two names: neither can be understood, tested or moved alone.

Signals:

- Import cycles between modules, packages or features, found with `scripts/deps.py`, with the repo's own tool (`madge`, `dependency-cruiser`, `import-linter`, `deptrac`), or, for languages the script does not read, by tracing imports of hot spots and their coupled partners (say that this covers only those files).
- A "utils", "common" or "shared" module that imports from the features that use it.
- Two modules that appear together in the coupling data and import each other.

Don't flag: cycles inside one module (two classes in the same package that know each other), or cycles between a module and its own tests.

Fix: break the cycle at its weakest edge. Move the shared piece into a third module both can import, or invert one edge with an interface owned by the side that needs it.

### Module Encapsulation

Protects: freedom to change a module's insides. If other modules import its internals, every internal rename is a breaking change for them.

Signals:

- Imports that reach past a module's public entry point (`feature/internal/...`, deep paths into another package, a repository class used directly by another feature's controller).
- A module with no declared public surface (no index or barrel file, no `internal` or package-private use) where many other modules import its files.
- Another module reading or writing this module's database tables directly.

Don't flag: a deliberately flat codebase that never declared module boundaries and has no pain from it, or shared kernel types the team agreed are public.

Fix: name the public surface (an index file, a facade or an interface), move callers onto it, then make the internals private or move them behind the module boundary.

### Cross-Cutting Concerns

Protects: one place per concern (authorization, validation, transactions, caching, audit, mapping errors), so a change to the rule is one edit and one test.

Signals:

- The same authorization or role check repeated at the top of many handlers, instead of in a guard, policy or middleware.
- Transactions opened by hand in many services, or nowhere in code that writes to several tables.
- Input validation split between controllers, services and models, with different rules in each.
- Caching or audit code copied around the code that needs it.
- Coupling data: a group of files that all change together whenever the concern changes.

Don't flag: a concern used in two or three places that stay simple. Framework-provided mechanisms such as `@Transactional`, `[Authorize]` or route middleware: using the central mechanism is the right shape.

Fix: move the concern into one mechanism (middleware, policy, decorator, base handler, interceptor) and let each call site declare that it needs it.

### Error Handling

Protects: callers who can trust what a failure looks like, and people on call who can see what failed.

Signals (count them, with `file:line` for the worst):

- Empty or log-only catch blocks that hide a failure (`catch {}`, `except: pass`, `.catch(() => {})`).
- More than one error shape at the same boundary: some endpoints return a message string, some an object, some throw.
- Business failures signalled by `null`, `false` or a magic value that callers forget to check.
- Infrastructure exceptions that reach the user or the domain unchanged (see Dependency Direction).
- A catch-all in the middle of the code that turns different failures into one.

Don't flag: deliberate best-effort code (cache warm-up, telemetry) where ignoring the failure is the point and a comment says so. Top-level handlers whose job is to catch everything.

Fix: choose one error model per boundary (exception types, a result type, or an error response shape), translate at the edge, and let everything inside fail loudly.

---

## 2. Component Responsibility & Cohesion

### Single Reason to Change

Protects: small, safe changes. A file with many reasons to change is where merge conflicts, regressions and slow reviews come from.

Signals:

- Hot spot files whose recent commits have unrelated subjects (check with `git log --format=%s -- <file>`).
- A class whose methods fall into groups that share no fields.
- A file that both formats an external payload and decides business outcomes.
- Coupling data: a file that changes together with many files in different modules.

Don't flag: a large file that only grows by adding similar cases of the same responsibility (a route table, a mapping registry). That is a registry, and the question is whether it should be split for readability, which is Low at most.

Fix: split along the groups of methods and fields. Name each new component after the one concern it keeps.

### Extensibility over Modification

Protects: adding a variant (payment method, provider, file type, tenant rule) without editing, and possibly breaking, the existing ones.

Signals:

- `switch`/`if-else` chains on a type, provider or kind field, repeated in more than one place.
- Hot spot history where each new integration or variant edited the same central file.
- Boolean flags on functions that select between variants.

Don't flag: a single `switch` in one place with two or three stable cases. Replacing it with a strategy pattern adds files and indirection for no gain.

Fix: one interface for the variant, one implementation per case, and one place (a registry or the DI container) that picks the implementation.

### Substitutability

Protects: callers that trust the contract. When an implementation behaves differently, every caller needs special cases.

Signals:

- Implementations or subclasses that throw "not supported" or "not implemented" for contract methods.
- Overrides that add stricter input checks, return `null` where the base returns a value, or skip a side effect (saving, event dispatch) that the base performs.
- Callers that check the concrete type (`instanceof`, `is`, type switches) before calling a method on the abstraction.

Don't flag: test doubles.

Fix: narrow the contract so every implementation can honour it, or split it (see Interface Segregation), or stop inheriting and compose instead.

### Interface Segregation

Protects: clients from changes to methods they never call, and implementations from having to stub methods they cannot support.

Signals:

- Interfaces with many methods where most clients use two or three.
- Repository or service interfaces that grew one method per screen.
- Implementations with empty or throwing method bodies to satisfy the interface.

Don't flag: a wide interface with a single client that uses all of it.

Fix: split by client need, for example a read interface and a write interface.

### Abstraction Decoupling

Protects: testability and the freedom to swap an implementation.

Signals:

- High-level code (use cases, domain services) that calls `new` on infrastructure classes (database clients, HTTP clients, mailers) or reaches for static service locators and global singletons.
- Hard-coded clock, random, or environment access inside business logic, which makes it untestable.

Don't flag: creating value objects, DTOs or domain entities with `new`. Those are data, not dependencies.

Fix: accept the dependency through the constructor, typed as an interface, and let the framework's DI container supply it.

---

## 3. Simplicity & Pragmatism

### Single Source of Truth

Protects: consistent behaviour. Duplicated rules drift, and then the system gives two answers to one question.

Signals:

- The same calculation or validation in backend and frontend, or in two services, with slightly different code.
- Mapping code that converts the same shape in several layers (entity → DTO → view model → response) with each step renaming fields but adding nothing.
- Enum or status lists maintained in more than one place. Coupling data often shows this: two files in different modules that always change together.

Don't flag: deliberate duplication across a service or bounded-context boundary, where sharing code would couple deployments. Input-shape validation on the client for user experience, when the server is still the authority.

Fix: pick the owner, move the rule there, and have the others call it or generate from it.

### Minimal Necessary Complexity

Protects: readability and onboarding. Every layer of indirection is a place a reader has to jump to.

Signals:

- Interfaces with exactly one implementation and no test double, inside a single layer.
- Wrappers that only forward calls. Factories that build one thing one way.
- Generic frameworks built in-house (plugin systems, rule engines, generic repositories) used by one or two callers.

Don't flag: a single-implementation interface that sits on an infrastructure boundary (see section 5).

Fix: inline the wrapper or interface. Keep the concrete class.

### Build Only What Is Needed

Protects: the reader's attention and the build's speed. Dead code still has to be read, compiled, upgraded and secured.

Signals:

- Functions, classes, routes or config keys with no callers (confirm with a repo-wide search, including dynamic references by string).
- Parameters that every caller passes the same value for, or that the function ignores.
- Feature flags that have been fully on or fully off for a long time.
- Configuration options nobody sets.

Don't flag: public API of a library that external consumers may call. Code reached through reflection, dependency injection by name, or framework conventions, unless you have ruled that out.

Fix: delete it. Version control keeps the history.

---

## 4. Change Safety, Platform & Dependencies

Evidence for Tested Where It Changes comes from the "Tests by name" numbers of `scripts/hotspots.py` and from reading the tests. Evidence for the other two comes from `scripts/packages.py`: versions and lockfile facts, with end-of-life status fetched from endoflife.date. Churn does not decide these two: a runtime past its end of life is a problem whether or not anyone edits the code that runs on it. Known vulnerabilities and how far each package is behind its latest release are not checked here; use `asvs-audit` or the package manager's audit command.

### Tested Where It Changes

Protects: the ability to change the code that changes most without breaking it.

Signals:

- A top-10 hot spot with no test by name and none found by searching the test folders for its main class or function.
- A top module where few source files have a test by name. Give the numbers ("3 of 40 files").
- Tests for a pure business rule that need the framework, a database or the network to run.
- Tests that cannot fail when the rule changes: no assertion on the result, or assertions that copy the implementation.

Don't flag: registries, routes and config; generated code; code covered by a higher-level test that you name (a feature or end-to-end test that exercises it). A missing test next to a stable file nobody changes.

Fix: write tests that pin down today's behaviour around the hot spot before restructuring it. Pull the pure rule out of the code that talks to infrastructure, so it can be tested without it.

### Supported Platform

Protects: the ability to get security and bug fixes, and to hire and onboard people for a stack that is still in use.

Signals:

- A runtime or the main framework past its end of life. This is High from the end-of-life date: patches stop that day, and every flaw found after it stays open. The script prints "end of life since DATE (N months ago)"; give N.
- A database, base image, CI image or tool past its end of life. Medium, unless the repo shows production running on it; then treat it as the runtime.
- A runtime or framework that ends within six months. Medium: it is a dated deadline, not a gap yet.
- The same runtime declared at different versions in different places (`.nvmrc` says 20, the Dockerfile says 16, CI tests 14): the team does not know what runs.
- Images without a version tag (`FROM node`, `image: redis`), which move under the team.
- A declared minimum (an `engines` or `require` floor) that is already past its end of life: the code claims to support what nobody supports. Say it is a minimum, not what runs.

Don't flag: a version the data marks "no end date set" (React, for example) on that ground alone. An old version inside a folder that is clearly a fixture or an archived example. A minimum below the pinned runtime when the pinned one is supported: mention it in one line.

Grouping: one finding per severity. Put the components that are already past their end of life and make it High in one finding, the other past-end-of-life components in a second, and the ones ending soon in a third. A date that is still ahead must not soften the rating of one that has passed.

Fix: upgrade the runtime first, one major version at a time, with the existing tests as the safety net. Keep the version in one file (for example `.tool-versions`) and have the Dockerfile and CI read it.

### Dependency Health

Protects: the ability to upgrade, and to trust what is installed.

Signals:

- Packages the lockfile marks as deprecated (`package-lock.json`) or abandoned (`composer.lock`), direct ones first. Give the replacement when the lockfile names one.
- A lockfile that has not changed for many months while the source kept changing, and no Dependabot or Renovate config.
- A manifest and lockfile that disagree (declared but not locked), or no lockfile for an application.
- Versions pinned to `*`, `latest`, a branch or `dev-master`.
- The same package locked in three or more versions (npm), which usually means a big upgrade was skipped.

Don't flag: deprecated packages that are only dev tools and do not touch the shipped app, unless the build depends on them. Transitive deprecated packages: name the direct dependency that brings them. Duplicates of small utility packages.

Fix: replace deprecated and abandoned direct packages first (the lockfile often names the successor), turn on automated update pull requests, and commit the lockfile.

---

## 5. When rules pull against each other

**Abstraction Decoupling vs. Minimal Necessary Complexity.** Both are right, in different places. An interface at a boundary between layers earns its place even with one implementation, because it keeps infrastructure types out of the domain and gives tests a seam. An interface between two classes in the same layer with one implementation and no test double is usually speculative. Flag the second, not the first.

**Extensibility vs. Minimal Necessary Complexity.** Introduce the extension point when the second or third variant arrives, or when the history shows the conditional being edited again and again. The churn data answers this question, so use it: a `switch` that was edited in 8 of the last 20 changes deserves a strategy, one that was never touched does not.

**Layer Isolation vs. framework idiom.** Judge against the architecture the team intended. A codebase that chose Active Record did not promise a pure domain. Flag the places where mixing layers causes measurable pain (hot spots, hard-to-test rules, repeated edits), not the idiom itself. When the team did declare a layered architecture, hold them to it.

**What "declared" means.** The team wrote the architecture down (an ADR, a README or docs section, or the config of a boundary tool such as deptrac or dependency-cruiser) and most of the code follows it. Folder names such as `Domain/Application/Infrastructure` count only if most files respect them. If the declaration is stale, meaning most of the code ignores it, treat the architecture as undeclared: report the gap as one finding, and judge everything else against the conventions the code does follow.
