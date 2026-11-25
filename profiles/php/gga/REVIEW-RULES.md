# GGA rules — PHP 8 profile

These rules are appended to the DevAgentKit core GGA rules. They add the PHP 8 contract for
this profile: strict types, PSR-12, PHPStan, PHPCS, PHPUnit, Composer and application
security. The company rule and the core rules still apply.

The profile is a skeleton: the repository's own `phpcs.xml`, `phpstan.neon` and
`phpunit.xml` are the source of the exact paths and levels. Once those files exist, the
gates below are mandatory; a missing tool is `ENV-FAIL`, not a pass.

## BLOCKING — PHP 8

### Quality gates and evidence

- `composer validate --strict` passed with the committed `composer.lock`; a diff that
  changes `composer.json` without the corresponding lock change is `FAILED`.
- `vendor/bin/phpcs` ran with the repository's PSR-12 ruleset on every changed `.php`
  file and passed.
- `vendor/bin/phpstan analyse` ran at the level the repository already passes on every
  changed `.php` file and passed. Do not lower the level or add a baseline entry to make a
  change green; a new `ignoreErrors` entry needs a written reason and a linked issue.
- `vendor/bin/phpunit` ran the affected suite and passed. A test that is skipped,
  not discovered, marked incomplete or made green by a changed `phpunit.xml` filter is
  not evidence.
- A gate that fails because a tool is absent, the PHP version differs or Composer cannot
  install is `ENV-FAIL`, not `PASS`; rerun in the pinned PHP image.
- The pipeline evidence is the pipeline id and status for the head SHA of the merge
  request, with every required job in `success`. A pipeline for an older SHA, `skipped`,
  `canceled` or a green local run is not evidence.

### PHP correctness and language level

- A PHP source file without `declare(strict_types=1);`. The only exceptions are templates
  that are not executed as PHP and files the framework generates.
- Syntax or a function newer than the PHP version pinned by `composer.json` or the runtime
  image. Verify the pinned version before reporting.
- A type error hidden with `@`, a cast to `mixed`, `(array)` on an object, or a `null`
  passed where the signature does not allow it.
- `eval`, `create_function`, `assert` with a string, `extract`, `parse_str` without a
  result array, `unserialize` on request data, or variable variables on input.
- A dynamic property on a class without the property declared, or a magic method that
  hides a contract the caller relies on.
- A public method that changes its signature, return type or thrown exceptions without a
  deprecation path.
- A `catch` that swallows an exception, catches `Throwable` and continues, or logs and
  returns a success value without a test for the failure path.

### End-to-end evidence

- A browser, UI or user-flow change without an E2E spec that starts at the public entry
  point, exercises the real application and asserts the visible or persisted outcome. The
  smoke probe is not E2E.
- The E2E command did not run, exited non-zero, skipped or deselected the flow, or produced
  no evidence for the head commit.
- Evidence for a browser flow must include the command, exit code `0`, commit SHA and the
  Playwright HTML report, JUnit/JSON results, and the trace, screenshot or video for a
  failure. The files belong under `evidence/<run-id>/e2e/`; a screenshot pasted elsewhere
  is not the evidence set.
- `E2E_BASE_URL` points at production, a shared environment or a database that is not
  disposable. The suite must be able to create and clean its own data.
- A test that mocks the application under test, calls only an internal endpoint or asserts
  that a request was made instead of the user-visible result.
- A green E2E run for an older commit, a local run without the same commit SHA, or a run
  whose artifacts were not retained.

### Security

- SQL built by concatenating or interpolating request data; a query without prepared
  statements and bound parameters. `PDO::query` with user input is blocking.
- Input used without validation and normalisation: a request field, header, cookie,
  path, uploaded file name or JSON body trusted as a scalar, array key, class name or
  include path.
- Output written without escaping in the context used (HTML, attribute, JavaScript, URL,
  shell). A template engine's auto-escape is not a reason to pass raw input to a raw
  filter.
- A state-changing route without CSRF protection, an authorization check and the correct
  HTTP method; a check that can be bypassed by a request parameter or a hidden field.
- A file upload accepted without an allowlist of extension and MIME type, a size limit, a
  generated name and a directory outside the web root.
- A credential, token, password, private key, session id or connection string in code, a
  log, a test fixture, a capture or a commit message. Use environment variables or a
  secret store.
- `display_errors` enabled, a stack trace returned to the client, or a debug dump in
  production code.
- A cookie or session without `HttpOnly`, `Secure` and the project's `SameSite` policy; a
  session id regenerated incorrectly after login.
- A dependency installed from a branch, a path repository in production, or a version
  range that ignores `composer.lock`.
- An unsafe deserialization of a session, cache or queue payload that an external party
  can write.

### Tests and evidence

- A behaviour change with no test that fails without it and passes with it, when a
  deterministic test is possible.
- A test that mocks the class under test or asserts only that an internal method was
  called. Mocks are allowed for HTTP, clock, filesystem and other external boundaries.
- A test that passes without the change, depends on execution order, uses a real network
  or a shared database without isolation, or relies on `sleep` for synchronisation.
- A changed test expectation that weakens the assertion instead of proving the new rule.
- A success claim without the command, exit code, commit SHA and output or artifact path
  under `evidence/<run-id>/`.

### Data, compatibility and hygiene

- A schema or data migration without a reversible path, a backup, a bounded scope and a
  test on a clean database.
- A destructive `DELETE`/`UPDATE` without a bounded `WHERE` and explicit authorization.
- A public API, CLI option, config key or response field changed or removed without a
  deprecation path.
- Explanatory comments in new or modified code; docblocks are API documentation, not
  comments. Legal headers and tool directives are allowed.
- Dead or commented-out code, a `var_dump`, `print_r`, `dd`, `dump`, a temporary script, a
  `.bak`, a capture or a work file that reaches the diff.
- An unrelated refactor, a whole-file reformat, a dependency bump or another ticket mixed
  into the change.
- A suppression (`@phpstan-ignore`, `// phpcs:ignore`, `@psalm-suppress`) without the
  exact rule and a written reason. A suppression of a gate enabled by this profile is
  blocking.
- The same extraction, parsing, regex or business expression written twice or more in the
  diff; it must be a single helper reused by all callers.

## ADVISORY

- Naming, readability, duplication or a simpler structure that does not change behaviour.
- A missing docblock on a public API when the project's documentation convention asks for
  it; a missing comment is not advisory by itself.
- Broader test coverage, a slow query outside a hot path, or a performance improvement on
  a bounded collection with no correctness risk.
- A framework-specific idiom that is equivalent and already used by the repository.
