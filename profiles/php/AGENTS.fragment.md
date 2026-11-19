## PHP profile rules

- PHP 8.x with `declare(strict_types=1)` in every source file.
- PSR-12 with PHPCS; do not add style rules that the formatter already owns.
- PHPStan at the highest level the project already passes; do not lower it.
- Composer installs from the lock file; no global packages.
- PHPUnit tests exercise public behaviour; do not mock the class under test.
- No comments in new or modified code; docblocks are API documentation, not
  comments.
