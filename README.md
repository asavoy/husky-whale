# husky-whale 🐳

Parses code that sounds like SQL.

## Goals

Enable the building of SQL codemods:

- Parse SQL into a data structure that can be manipulated and output as new SQL
- Preserve original formatting and comments
- Preserve variables in the SQL, e.g. `WHERE date < {{input_date}}`

**Non-goals**

- Completeness: only the subset of SQL we use:
  - `SELECT`
  - Common Table Expressions
  - Window functions
- Compatibility: only PostgreSQL and Redshift
- Strictness: accepts SQL that wouldn't compile
