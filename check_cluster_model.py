"""Check cluster_model.predict_cluster against the k-means fit, student by student."""

import pandas as pd
from sklearn.cluster import KMeans

from cluster_model import SKILL_ORDER, predict_cluster

df = pd.read_csv("class_dataset.csv")
X = df[list(SKILL_ORDER)].to_numpy(dtype=float)
labels = KMeans(n_clusters=3, n_init=10, random_state=42).fit(X).labels_

matches = sum(predict_cluster(row) == label for row, label in zip(X, labels))
print(f"{matches} of {len(df)} students match the k-means labels")
