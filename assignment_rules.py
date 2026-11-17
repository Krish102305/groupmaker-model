"""Model 2: the assignment rules.

Takes the whole class, asks the cluster model for each student's cluster,
then deals students round-robin into groups so each group gets a mix:

  1. Order clusters from most students to fewest (ties: lower cluster number first).
  2. Inside a cluster, sort students by `id`.
  3. Deal that one long line to groups 1..n_groups in turn, continuing the
     count across clusters (no restart at group 1 for each cluster).

No packages needed.
"""

try:  # run directly, or with model/ on sys.path
    from cluster_model import SKILL_ORDER, predict_cluster
except ImportError:  # imported as part of the app's model/ package
    from .cluster_model import SKILL_ORDER, predict_cluster


def assign_groups(students, n_groups=8):
    """Assign every student to a group.

    `students`: list of dicts, each with an `id` and the four SKILL_ORDER ratings.
    Returns a list of {"id", "cluster", "group"} dicts (groups numbered from 1),
    in dealing order.
    """
    if n_groups < 1:
        raise ValueError("n_groups must be at least 1")

    by_cluster = {}
    for s in students:
        cluster = predict_cluster({name: s[name] for name in SKILL_ORDER})
        by_cluster.setdefault(cluster, []).append(s["id"])

    cluster_order = sorted(by_cluster, key=lambda c: (-len(by_cluster[c]), c))

    result = []
    position = 0
    for cluster in cluster_order:
        for student_id in sorted(by_cluster[cluster]):
            result.append({"id": student_id, "cluster": cluster, "group": position % n_groups + 1})
            position += 1
    return result


if __name__ == "__main__":
    import csv

    from cluster_model import CENTROIDS

    with open("class_dataset.csv", newline="", encoding="utf-8") as f:
        # netid is stripped and lowercased, the same way the app's migrate.py
        # stores it in Postgres, so the id sort order matches the app.
        students = [
            {"id": row["netid"].strip().lower(), **{name: int(row[name]) for name in SKILL_ORDER}}
            for row in csv.DictReader(f)
        ]

    n_groups = 8
    assignments = assign_groups(students, n_groups)
    clusters = range(len(CENTROIDS))

    print(f"{len(students)} students, {n_groups} groups\n")
    print("group  size  " + "  ".join(f"c{c}" for c in clusters))
    missing = 0
    for g in range(1, n_groups + 1):
        members = [a for a in assignments if a["group"] == g]
        counts = [sum(a["cluster"] == c for a in members) for c in clusters]
        missing += 0 in counts
        print(f"{g:>5}  {len(members):>4}  " + "  ".join(f"{n:>2}" for n in counts))

    print("\ncluster sizes: " + ", ".join(
        f"c{c}={sum(a['cluster'] == c for a in assignments)}" for c in clusters))
    print(f"groups missing a cluster: {missing}")
