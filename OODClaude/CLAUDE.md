# Claude Code — Global Coding Standards
## C:\Users\<user_id>\.claude\CLAUDE.md : apply OOD and design pattern all the time

## Code Style

Always apply OOP principles and design patterns by default:
- Prefer instance methods over `@staticmethod` — enables dependency injection and testability
- Use `__init__` for dependencies (factory, config, logger) — no module-level globals
- Private helpers use underscore prefix (`_method`, `_field`)
- Prefer `X | None` with a default over hardcoded instances

## Design Patterns to Apply

- **Factory** — object creation with swappable implementations; use when the exact class may change
- **Builder** — fluent API for assembling complex objects (e.g. `AgentBuilder().with_tools().build()`)
- **Decorator** — wrap behavior without modifying the original function; use for logging, retry, timing
- **Observer** — hooks/events for lifecycle concerns (logging, timing, error tracking)
- **Chain of Responsibility** — middleware chains; each handler does one thing and passes to the next
- **Template Method** — shared skeleton, subclass or inner function fills in the parts that differ
- **Adapter** — wrap third-party APIs behind a consistent interface so internals don't depend on external SDKs directly
- **Proxy** — control access to another object; use for lazy loading, caching, or access control
- **Strategy** — swap algorithms or behaviors at runtime via injection
- **Singleton** — one shared instance for stateless services (logger, config); use sparingly

When adding new code, ask: which pattern fits here? Prefer patterns already used in the project for consistency.

## What to Avoid

- `@staticmethod` unless the method genuinely has no relationship to instance state
- Module-level mutable globals (use instance variables instead)
- Mixing concerns in one function (logging + business logic + error handling)
- Nested functions when an instance method would be cleaner and testable
