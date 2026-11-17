"""Model 1: the cluster model (fitted k-means, k = 3).

The centroids below were produced by fit_clusters.py on class_dataset.csv
(34 students, four unscaled 1-5 skill ratings). They are plain numbers, so
this file needs no packages. The app never runs fit_clusters.py.

Cluster names (from the centroids):
    0  "All-rounders"     high on everything, strongest in pitch/design
    1  "Technical"        programming + data stats, low design/pitch
    2  "Pitch-first"      strong business pitch, low programming
"""

# Order of the four ratings in every centroid and in `skills`.
SKILL_ORDER = (
    "skill_programming",
    "skill_data_stats",
    "skill_frontend_design",
    "skill_business_pitch",
)

CENTROIDS = [
    [3.875, 4.0, 4.25, 4.625],
    [3.4166666666666665, 3.1666666666666665, 2.166666666666667, 2.4166666666666665],
    [1.7857142857142854, 2.5, 2.428571428571429, 4.285714285714286],
]


def predict_cluster(skills):
    """Return the number of the nearest centroid (squared Euclidean distance).

    `skills` is either a dict with the four SKILL_ORDER keys, or a sequence of
    four numbers in SKILL_ORDER.
    """
    if isinstance(skills, dict):
        values = [float(skills[name]) for name in SKILL_ORDER]
    else:
        values = [float(v) for v in skills]
    if len(values) != len(SKILL_ORDER):
        raise ValueError(f"expected {len(SKILL_ORDER)} skill ratings, got {len(values)}")

    best, best_dist = None, None
    for number, centroid in enumerate(CENTROIDS):
        dist = sum((v - c) ** 2 for v, c in zip(values, centroid))
        if best_dist is None or dist < best_dist:
            best, best_dist = number, dist
    return best
