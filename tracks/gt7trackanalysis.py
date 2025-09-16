# Vertical layout: button above table
from gt7dashboard.gt7lap import Lap
from gt7dashboard.s3helper import S3Uploader
from tracks.gt7trackclustering import cluster_laps



def analyse_tracks(source, table_data, track_tab):
    s3Uploader = S3Uploader()  # Initialize S3Uploader instance
    # Get selected indices from the DataTable
    selected_indices = source.selected.indices
    if not selected_indices:
        print("No tracks selected.")
        return

    # Get selected object names
    selected_objects = [table_data["object_name"][i] for i in selected_indices]

    loaded_tracks = []
    for obj_name in selected_objects:
        lap_data = s3Uploader.get_object(obj_name)
        if not isinstance(lap_data, Lap):
            print(f"Warning: Object {obj_name} is not a Lap instance.")
            continue
        loaded_tracks.append(lap_data)

    print(f"Loaded {len(loaded_tracks)} tracks for analysis.")
    clusters = cluster_laps(loaded_tracks)
    print(f"Clustered into {len(set(clusters))} clusters.")
    for i, obj_name in enumerate(selected_objects):
        print(f"Track: {obj_name}, Cluster: {clusters[i]}") 
        # Update the data table with cluster IDs
        source.data["cluster_id"][selected_indices[i]] = clusters[i]
    source.trigger('data', source.data, source.data)  # Refresh the table display

    return clusters, loaded_tracks
  