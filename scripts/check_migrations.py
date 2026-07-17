from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAME = re.compile(r"^(\d{4})_[a-z0-9_]+\.sql$")


def main() -> None:
    migrations = sorted((ROOT / "server" / "migrations").glob("*.sql"))
    if not migrations:
        raise SystemExit("no server migrations found")
    numbers: list[int] = []
    for migration in migrations:
        match = NAME.fullmatch(migration.name)
        if match is None:
            raise SystemExit(f"invalid migration name: {migration.name}")
        numbers.append(int(match.group(1)))
        sql = migration.read_text(encoding="utf-8")
        if "Recovery:" not in sql:
            raise SystemExit(f"migration lacks documented recovery: {migration.name}")
        executable_sql = "\n".join(
            line for line in sql.splitlines() if not line.lstrip().startswith("--")
        )
        if re.search(r"\bDROP\s+(TABLE|SCHEMA|COLUMN)\b", executable_sql, re.IGNORECASE):
            raise SystemExit(
                f"destructive migration requires explicit expand/contract review: {migration.name}"
            )
    expected = list(range(1, len(numbers) + 1))
    if numbers != expected:
        raise SystemExit(f"migration sequence must be contiguous: {numbers}")
    print(f"valid: {len(migrations)} migration(s), sequence {numbers[0]:04d}-{numbers[-1]:04d}")


if __name__ == "__main__":
    main()
