# Design rules

The rubric for Phase 2. Each rule says what it protects, what a violation looks like in real code, when not to flag it, and the usual fix. The "when not to flag" notes matter as much as the signals: a review that flags every idiom of the codebase's framework is noise, and the team will stop reading it.

Cite the rule by its name (for example "Dependency Direction") in the Violation column of the report.

## Contents

1. Architectural Boundaries: Layer Isolation, Dependency Direction, Orchestration
2. Component Responsibility & Cohesion: Single Reason to Change, Extensibility over Modification, Substitutability, Interface Segregation, Abstraction Decoupling
3. Simplicity & Pragmatism: Single Source of Truth, Minimal Necessary Complexity, Build Only What Is Needed
4. When rules pull against each other

---

## 1. Architectural Boundaries

The three layers are:

- **Domain**: business rules, calculations, invariants. What would stay true if you swapped the database, the web framework and the UI.
- **Application**: use cases. Loads what a use case needs, calls the domain, saves the result, handles transactions, sends events.
- **Infrastructure**: everything that talks to the outside: database, ORM, HTTP clients, queues, file system, UI, framework glue.

Not every codebase names these layers. Map what exists onto them before judging (see "Establish the intended architecture" in SKILL.md).

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

Signals (cheap to find with grep across the whole repo, not only hot spots):
- Files in a domain or model folder that import ORM base classes, framework request/response types, HTTP clients, queue clients, `env`/config readers, or logging frameworks.
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

Don't flag: a single-implementation interface that sits on an infrastructure boundary (see section 4).

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

## 4. When rules pull against each other

**Abstraction Decoupling vs. Minimal Necessary Complexity.** Both are right, in different places. An interface at a boundary between layers earns its place even with one implementation, because it keeps infrastructure types out of the domain and gives tests a seam. An interface between two classes in the same layer with one implementation and no test double is usually speculative. Flag the second, not the first.

**Extensibility vs. Minimal Necessary Complexity.** Introduce the extension point when the second or third variant arrives, or when the history shows the conditional being edited again and again. The churn data answers this question, so use it: a `switch` that was edited in 8 of the last 20 changes deserves a strategy, one that was never touched does not.

**Layer Isolation vs. framework idiom.** Judge against the architecture the team intended. A codebase that chose Active Record did not promise a pure domain. Flag the places where mixing layers causes measurable pain (hot spots, hard-to-test rules, repeated edits), not the idiom itself. When the team did declare a layered architecture (folders named Domain/Application/Infrastructure, ADRs, a README section), hold them to it.
