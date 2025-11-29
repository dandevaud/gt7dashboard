# Vertical layout: button above table
from gt7dashboard.gt7lap import Lap
from gt7dashboard.s3helper import S3Client
from tracks.gt7trackclustering import TrackClusterer

class TrackAnalysis:
        
    def __init__(self, s3client=None):
        if s3client is None:
            self.s3Uploader = S3Client()  # Initialize S3Uploader instance
        else:
            self.s3Uploader = s3client
        self.clusterer = TrackClusterer()

    def load_lap_from_s3(self, loaded_tracks, obj_name):
        lap_data = self.s3Uploader.get_object(obj_name)
        if not isinstance(lap_data, Lap):
            print(f"Warning: Object {obj_name} is not a Lap instance.")
            return   
        loaded_tracks.append(lap_data)


    def analyse_tracks(self, source, table_data, track_tab):
        # Get selected indices from the DataTable
        selected_indices = source.selected.indices
        if not selected_indices:
            print("No tracks selected.")
            return

        # Get selected object names
        selected_objects = [table_data["object_name"][i] for i in selected_indices]

        loaded_tracks = []
        cluster_lap_map = {}   
        print(f"Loading {len(selected_objects)} selected tracks from S3...") 
        i = 0
        for obj_name in selected_objects:
            print(f"Progress {'{:.0%}'.format(i / len(selected_objects))}")
            i += 1            
            self.load_lap_from_s3(loaded_tracks, obj_name)

        print(f"Loaded {len(loaded_tracks)} tracks for analysis.")
        clusters = self.clusterer.cluster_laps(loaded_tracks)
        print(f"Clustered into {len(set(clusters))} clusters.")
        for i, obj_name in enumerate(selected_objects):
            # Update the data table with cluster IDs
            source.data["cluster_id"][selected_indices[i]] = clusters[i]
            cluster_id = clusters[i].item()
            if cluster_id not in cluster_lap_map:
                cluster_lap_map[cluster_id] = []
            cluster_lap_map[cluster_id].append(obj_name)
        source.trigger('data', source.data, source.data)  # Refresh the table display

        return cluster_lap_map
    
    def save_clusters(self):
        self.clusterer.save_clusters()
  