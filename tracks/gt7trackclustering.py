import os
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

from gt7dashboard.gt7lap import Lap
from gt7dashboard.s3helper import S3Client

class TrackClusterer:
    def __init__(self, n_tracks=118, centers_file=None):
        self.n_tracks = n_tracks
        self.centers_file = centers_file
        self.centers = None
        self.kmeans = None
        self.s3Uploader = S3Client()
        try:
            self.centers = np.load(self.centers_file)
        except FileNotFoundError:
            print(f"Cluster centers file {self.centers_file} not found. Please run save_cluster_centers first.")

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

    def estimate_best_k(self, laps, max_k=10, sample_points=10000):
        features = [self.lap_to_feature_vector(lap, sample_points=sample_points) for lap in laps]
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
    def cluster_laps(self, laps, n_tracks=118):
        features = [self.lap_to_feature_vector(lap) for lap in laps]
        best_k = self.estimate_best_k(laps, max_k=n_tracks)
        self.kmeans = KMeans(n_clusters=best_k, random_state=42)
        labels = self.kmeans.fit_predict(features)
        return labels  # List of cluster indices for each lap

    def save_cluster_centers(self, cluster_track_map) :
        centers = self.kmeans.cluster_centers_
        for i, center in enumerate(centers):
            filename = f"cluster_{i}_{cluster_track_map[i]}.npy"           
            # Save center to a temporary file
            tmp_filename = f"/tmp/{filename}"
            np.save(tmp_filename, center)
            # Upload to S3
            cluster_bucketName = os.environ.get("S3_CLUSTER_BUCKET")
            if cluster_bucketName is None:
                print("S3_CLUSTER_BUCKET environment variable not set. Skipping upload.")
                cluster_bucketName = "gt7dashboard/track/clusters"            

            self.s3Uploader.upload_file(tmp_filename, filename,cluster_bucketName )
    
    def load_cluster_centers_from_s3(self, cluster_track_map):
        centers = []
        for i, track_name in cluster_track_map.items():
            filename = f"cluster_{i}_{track_name}.npy"
            tmp_filename = f"/tmp/{filename}"
            cluster_bucketName = os.environ.get("S3_CLUSTER_BUCKET")
            if cluster_bucketName is None:
                print("S3_CLUSTER_BUCKET environment variable not set. Skipping download.")
                cluster_bucketName = "gt7dashboard/track/clusters"
            # Download file from S3
            self.s3Uploader.download_file(filename, tmp_filename, cluster_bucketName)
            center = np.load(tmp_filename)
            centers.append(center)
        self.kmeans.cluster_centers_ = np.array(centers)

    def categorize_lap(self,lap, centers_file="cluster_centers.npy", sample_points=5000):
        feature = self.lap_to_feature_vector(lap, sample_points=sample_points)
        centers = np.load(centers_file)
        distances = np.linalg.norm(centers - feature, axis=1)
        return np.argmin(distances)