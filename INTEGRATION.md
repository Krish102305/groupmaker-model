# INTEGRATION.md: adding the group model to the app

For an agent working inside the app repo (Flask + Postgres: `app.py`, `schema.sql`,
`migrate.py`, `templates/`, `Dockerfile`). You have not seen the model repo, and
you do not need to. Everything you need is in this file and the two model files.

**Rule: do not edit `model/cluster_model.py` or `model/assignment_rules.py`.
The app adapts to them.**

## 1. What these two files do

`cluster_model.py` is a fitted k-means model (k = 3). It holds three centroids as
plain numbers and puts a student into the cluster whose centroid is nearest to
their four 1–5 skill ratings. `assignment_rules.py` takes the whole class, gets
each student's cluster from `cluster_model.py`, and deals students round-robin
into 8 groups (largest cluster first, sorted by id inside a cluster), so that
every group gets a mix of skillsets. Neither file imports any package.

## 2. Files to copy

| File | Goes to |
|---|---|
| `cluster_model.py` | `model/cluster_model.py` |
| `assignment_rules.py` | `model/assignment_rules.py` |
| `INTEGRATION.md` | `model/INTEGRATION.md` |
| *(new, empty)* | `model/__init__.py`, which makes `model` a package |

Import from `app.py` (which runs from the repo root):

```python
from model.assignment_rules import assign_groups
from model.cluster_model import CENTROIDS, SKILL_ORDER
```

`assignment_rules.py` already falls back to a relative import
(`from .cluster_model import ...`) when it is loaded as `model.assignment_rules`,
so `ModuleNotFoundError: No module named 'cluster_model'` should not happen.
If it does, the fix belongs in `app.py` (the import line above), not in the model files.

## 3. The two functions

**`predict_cluster(skills) -> int`** (in `cluster_model.py`)
- Input: a dict with the four keys in `SKILL_ORDER` (`skill_programming`,
  `skill_data_stats`, `skill_frontend_design`, `skill_business_pitch`), or a list
  of four numbers in that order.
- Output: cluster number `0`, `1` or `2`.

```python
predict_cluster({"skill_programming": 4, "skill_data_stats": 3,
                 "skill_frontend_design": 5, "skill_business_pitch": 3})   # -> 0
predict_cluster([2, 2, 2, 5])                                              # -> 2
```

**`assign_groups(students, n_groups=8) -> list[dict]`** (in `assignment_rules.py`)
- Input: the **whole class** as a list of dicts, each with `id` plus the four skill keys.
- Output: one dict per student: `{"id", "cluster", "group"}`, with groups numbered from 1.

```python
assign_groups([
    {"id": "ab1", "skill_programming": 4, "skill_data_stats": 4, "skill_frontend_design": 4, "skill_business_pitch": 5},
    {"id": "cd2", "skill_programming": 4, "skill_data_stats": 3, "skill_frontend_design": 2, "skill_business_pitch": 2},
    {"id": "ef3", "skill_programming": 2, "skill_data_stats": 2, "skill_frontend_design": 2, "skill_business_pitch": 5},
], n_groups=2)
# -> [{"id": "ab1", "cluster": 0, "group": 1},
#     {"id": "cd2", "cluster": 1, "group": 2},
#     {"id": "ef3", "cluster": 2, "group": 1}]
```

Cluster meaning (from the centroids): **0** all-rounders, **1** technical
(programming + data), **2** pitch-first (strong business pitch).

## 4. Where the data comes from

The models were built from `data/class_dataset.csv`. The app reads Postgres
instead, from the `students` table created by `schema.sql` and filled by `migrate.py`.

| Model input | Table.column | Type in DB | Differences from the CSV |
|---|---|---|---|
| `id` | `students.netid` | `TEXT PRIMARY KEY` | `migrate.py` **strips and lowercases** netid (the CSV has e.g. `Dg4329`, the DB has `dg4329`). The model repo's test run used the lowercased value too, so results match. |
| `skill_programming` | `students.skill_programming` | `SMALLINT` 1–5 | same name, same values |
| `skill_data_stats` | `students.skill_data_stats` | `SMALLINT` 1–5 | same name, same values |
| `skill_frontend_design` | `students.skill_frontend_design` | `SMALLINT` 1–5 | same name, same values |
| `skill_business_pitch` | `students.skill_business_pitch` | `SMALLINT` 1–5 | same name, same values |
| *(for the response)* `name` | `students.name` | `TEXT NOT NULL` | stripped by `migrate.py` |

The `tools` and `availability` CSV columns live in separate tables
(`student_tools`, `student_availability`). The models do not use them.

Query:

```sql
SELECT netid, name, skill_programming, skill_data_stats,
       skill_frontend_design, skill_business_pitch
FROM students
```

## 5. Backend: `GET /api/groups`

Add to `app.py`, using the same `psycopg2.connect(os.environ["DATABASE_URL"])`
pattern as `get_names()`. Steps:

1. Read every student with the query above.
2. Build `students = [{"id": netid, <four skills>}, ...]` and call `assign_groups(students, n_groups=8)`.
3. Map `id` back to `name` and return:

```json
{
  "n_groups": 8,
  "groups": [
    {"group": 1, "members": ["Name A", "Name B", "..."], "cluster_counts": {"0": 1, "1": 2, "2": 2}}
  ],
  "clusters": [
    {"cluster": 0, "students": 8, "centroid": {"skill_programming": 3.88, "skill_data_stats": 4.0, "skill_frontend_design": 4.25, "skill_business_pitch": 4.62}}
  ],
  "groups_missing_a_cluster": 0
}
```

- `groups`: one entry for each group, 1..8, with `members` sorted by name. `cluster_counts` lists every cluster (0, 1, 2), including zeros.
- `clusters`: one entry for each cluster in `CENTROIDS`. `students` is the class-wide count, and `centroid` is rounded to 2 decimals and keyed by `SKILL_ORDER`.
- `groups_missing_a_cluster`: the number of groups with a 0 in `cluster_counts`.
- **Never return any one person's cluster** (no netid → cluster mapping, and no cluster inside `members`).

## 6. Frontend: nothing yet

Do not change `templates/` or `/`. A page built later can use the JSON above:
draw one card for each entry in `groups`, show its `members` names and a small
bar of `cluster_counts`, and use `clusters[].centroid` as a legend that explains
what each cluster means.

## 7. Packaging

- `Dockerfile` copies only `app.py` and `templates/`. Add `COPY model model` after
  `COPY templates templates`, or the deployed app fails with `ModuleNotFoundError: No module named 'model'`.
- `.dockerignore` excludes `data/` but not `model/`, so it needs no change.
- `requirements.txt` needs **no** change. The model files use only the standard library.
  Do not add scikit-learn, pandas or numpy.

## 8. Test

Run the app as usual (`python app.py`, port 5000 unless `PORT` is set), then:

```bash
curl http://localhost:5000/api/groups
```

Expected, with the 34 students from `class_dataset.csv` loaded by `migrate.py`:

| group | size | c0 | c1 | c2 |
|---|---|---|---|---|
| 1 | 5 | 1 | 2 | 2 |
| 2 | 5 | 1 | 2 | 2 |
| 3 | 4 | 1 | 1 | 2 |
| 4 | 4 | 1 | 1 | 2 |
| 5 | 4 | 1 | 1 | 2 |
| 6 | 4 | 1 | 1 | 2 |
| 7 | 4 | 1 | 2 | 1 |
| 8 | 4 | 1 | 2 | 1 |

- Cluster sizes: c0 = 8, c1 = 12, c2 = 14.
- `groups_missing_a_cluster`: **0**.
- `/` should look exactly as it did before.
