---
description: Scan the Django and React codebase for SQL injection vulnerabilities
allowed-tools: Read, Grep, Glob, Bash(find:*)
---

Perform a thorough SQL injection vulnerability audit of this Django + React project.

## Scope

- Django backend: `server/` (all `.py` files, excluding migrations and `__pycache__`)
- React frontend: `server/frontend/src/` (all `.js`, `.jsx`, `.ts`, `.tsx` files)

---

## Phase 1 — Django: Raw SQL

Search for every use of raw SQL execution. Check each one for unsanitized user input.

### 1a. `cursor.execute()` calls

Grep for `cursor.execute` in all Python files under `server/`. For each match:
- Read the surrounding 10 lines
- Check if the SQL string is built via f-string, `%` formatting, `.format()`, or concatenation using request data
- **VULNERABLE** if: query is built from `request.data`, `request.query_params`, `request.POST`, `request.GET`, kwargs, or any variable that originates from user input without parameterisation
- **SAFE** if: parameters are passed as the second argument to `cursor.execute(sql, [params])`

### 1b. `Model.objects.raw()` calls

Grep for `\.raw\(` in all Python files under `server/`. For each match:
- Read surrounding context
- **VULNERABLE** if: raw SQL string is constructed from user-controlled data
- **SAFE** if: user data is passed as the `params` list argument

### 1c. `extra()` queryset method

Grep for `\.extra\(` — this method is deprecated and dangerous. For each match:
- Check if `where`, `tables`, `select`, or `order_by` arguments contain user input
- Any use of `.extra()` with dynamic user data is **HIGH RISK**

### 1d. `RawSQL()` expressions

Grep for `RawSQL(` — check if the SQL template string embeds user data directly vs using params.

### 1e. String formatting into ORM filters

Grep for patterns like `filter(` or `exclude(` where values come from f-strings or `.format()` calls — these are generally safe (Django ORM parameterises them) but flag any `__in`, `__contains`, or similar lookups built from raw user input strings.

---

## Phase 2 — Django: Serializers and Views

Read these files in full and audit them for injection risks:
- `server/authentication/views.py`
- `server/authentication/serializers.py`
- `server/authentication/models.py`
- `server/authentication/helpers.py`
- `server/server/urls.py`

Look for:
- Any `validate_*` methods that do DB lookups using unescaped user data
- Any `perform_create` / `perform_update` that calls raw SQL
- URL patterns using regex groups fed into raw queries

---

## Phase 3 — React Frontend: API Call Construction

Scan all files in `server/frontend/src/`. For each `fetch(`, `axios.get(`, `axios.post(`, or similar HTTP call:

- Check if the URL or query string is built by concatenating/interpolating user-controlled state (form values, URL params, `location.search`, `useParams`, etc.)
- **Flag** any template literal or string concat that embeds raw user input into a URL path or query param without encoding
- **Note**: React/JS SQL injection via the frontend is indirect (the Django backend is the real defence), but unencoded user data in URLs can bypass server-side validation if the backend trusts URL shape

---

## Phase 4 — Report

Produce a structured report:

```
## SQL Injection Audit Report

### Critical Findings
(direct raw SQL with unsanitised user input — needs immediate fix)

### High Risk
(raw SQL methods like .extra(), RawSQL() with dynamic data)

### Medium Risk
(indirect risks: URL construction, ORM misuse patterns)

### Low / Informational
(safe patterns that are worth noting, e.g. parameterised raw SQL)

### No Issues Found
(files / patterns confirmed clean)

### Recommendations
(specific code changes with before/after examples)
```

For each finding include:
- File path and line number
- The vulnerable code snippet
- Why it is vulnerable
- The fix (with corrected code example)
