# RBAC Constraint Model — NIST Alignment

## What changed

The constraint model was restructured from a pairwise design (`role_id_1`, `role_id_2`, `max_users` on a single table) to a set-based design using two tables:

**Before:**
```
rbac_role_constraint
├── role_id_1       FK → rbac_role.id
├── role_id_2       FK → rbac_role.id  (nullable)
├── max_users       INTEGER            (nullable)
└── constraint_type VARCHAR
```

**After:**
```
rbac_constraint
├── constraint_type VARCHAR
└── threshold       INTEGER  (NOT NULL)

rbac_constraint_role  (junction table)
├── constraint_id   FK → rbac_constraint.id
└── role_id         FK → rbac_role.id
```

## Why

The previous design stored Separation of Duties (SoD) constraints as pairs of roles. This made it impossible to express a constraint over more than two roles in a single row. For example, "a user can hold at most 1 of roles A, B, C" required three rows (A-B, A-C, B-C) that had to be kept in sync manually.

The new design follows the NIST RBAC standard (ANSI/INCITS 359-2004), which defines SoD constraints as:

> **SSD(role_set, n):** No user may be assigned to `n` or more roles from `role_set`.

The role set is stored in the `rbac_constraint_role` junction table, and `n` is stored as `threshold` on `rbac_constraint`. This generalizes all three constraint types with a single column:

| Constraint | Example | `threshold` meaning |
|---|---|---|
| Static SoD | SSD({contributor, approver}, 2) | User can't hold 2+ of these roles |
| Dynamic SoD | DSD({manager, auditor}, 2) | User can't activate 2+ per session |
| Cardinality | Card({owner}, 3) | At most 3 users can hold Owner |

A single row now replaces N-choose-2 rows for multi-role conflicts, and the nullable `max_users` / `role_id_2` columns are eliminated in favor of the unified `threshold`.

## Reference

NIST RBAC Standard: https://csrc.nist.gov/projects/role-based-access-control
