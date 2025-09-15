import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

from gt7dashboard.gt7lap import Lap

def lap_to_feature_vector(lap: Lap, sample_points=5000):
    x = np.array(lap.data_position_x)
    y = np.array(lap.data_position_y)
    z = np.array(lap.data_position_z)
    coords = np.stack([x, y, z], axis=1)
    idx = np.linspace(0, len(coords)-1, sample_points).astype(int)
    sampled = coords[idx]
    # Add start and end points to help distinguish direction
    start = coords[0]
    end = coords[-1]
    feature = np.concatenate([sampled.flatten(), start, end])
    return feature

def estimate_best_k(laps, max_k=10, sample_points=10000):
    features = [lap_to_feature_vector(lap, sample_points=sample_points) for lap in laps]
    best_k = 2
    best_score = -1
    for k in range(2, min(max_k, len(features))):
        kmeans = KMeans(n_clusters=k, random_state=42)
        labels = kmeans.fit_predict(features)
        score = silhouette_score(features, labels)
        if score > best_score:
            best_score = score
            best_k = k
    return best_k

# Currently 118 tracks in GT7: https://github.com/ddm999/gt7info/blob/web-new/_data/db/course.csv
def cluster_laps(laps, n_tracks=118):
    features = [lap_to_feature_vector(lap) for lap in laps]
    best_k = estimate_best_k(laps, max_k=n_tracks)
    kmeans = KMeans(n_clusters=best_k, random_state=42)
    labels = kmeans.fit_predict(features)
    return labels  # List of cluster indices for each lap