"""Fit k-means on the four skill ratings in class_dataset.csv.

Stage 1: inertia for k = 1..6 and an elbow plot (elbow.png).
Stage 2: the final fit with K, its centroids, counts and a `cluster` column.

The four ratings are all on the same 1-5 scale, so they are not scaled.
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.cluster import KMeans

CSV_PATH = "class_dataset.csv"
SKILLS = ["skill_programming", "skill_data_stats", "skill_frontend_design", "skill_business_pitch"]
K_RANGE = range(1, 7)
K = 3  # chosen from the elbow plot
SEED = 42

df = pd.read_csv(CSV_PATH)
X = df[SKILLS].to_numpy(dtype=float)
print(f"Students: {len(df)}")

# ---- Stage 1: elbow ---------------------------------------------------------
print("\nk  inertia")
inertias = []
for k in K_RANGE:
    km = KMeans(n_clusters=k, n_init=10, random_state=SEED).fit(X)
    inertias.append(km.inertia_)
    print(f"{k}  {km.inertia_:.2f}")

plt.plot(list(K_RANGE), inertias, marker="o")
plt.xlabel("k (number of clusters)")
plt.ylabel("inertia")
plt.title("Elbow plot: k-means on the four skill ratings")
plt.xticks(list(K_RANGE))
plt.grid(alpha=0.3)
plt.savefig("elbow.png", dpi=120, bbox_inches="tight")
print("Saved elbow.png")

# ---- Stage 2: final fit -----------------------------------------------------
km = KMeans(n_clusters=K, n_init=10, random_state=SEED).fit(X)
df["cluster"] = km.labels_

print(f"\nk = {K}: centroids and counts")
centroids = pd.DataFrame(km.cluster_centers_, columns=SKILLS).round(2)
centroids["students"] = df["cluster"].value_counts().sort_index()
centroids.index.name = "cluster"
print(centroids.to_string())

print("\nCentroids as plain numbers (for cluster_model.py):")
for c in km.cluster_centers_:
    print("    [" + ", ".join(repr(float(v)) for v in c) + "],")
