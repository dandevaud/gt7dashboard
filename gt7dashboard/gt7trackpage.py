from bokeh.models import Button, TableColumn, DataTable, ColumnDataSource
from bokeh.layouts import layout
from bokeh.io import curdoc
from gt7dashboard.gt7trackclustering import cluster_laps
from gt7dashboard.s3helper import get_object, list_objects
import re
from gt7dashboard.gt7lap import Lap
from bokeh.plotting import figure
from bokeh.layouts import column

filename_regex = r'([^_]*)_([^_]*)_([^_]*)_([^_]*).json'  # Placeholder regex to extract date from filename

# Get S3 objects using S3Helper
object_list = list_objects()  # Assumes this returns a list of object names

# Prepare data for DataTable
# Parse object_list using regex and build a list of dicts for each object
table_data = {
    "object_name": [],
    "date": [],
    "track_id": [],
    "car_id": [],
    "lap": [],
}

for obj in object_list:
    match = re.search(filename_regex, obj)
    if match:
        table_data["object_name"].append(obj)
        table_data["date"].append(match.group(1))
        table_data["track_id"].append(match.group(2))
        table_data["car_id"].append(match.group(3))
        table_data["lap"].append(match.group(4))
    else:
        table_data["object_name"].append(obj)
        table_data["date"].append("")
        table_data["track_id"].append("")
        table_data["car_id"].append("")
        table_data["lap"].append("")

source = ColumnDataSource(data=table_data)

columns = [
    TableColumn(field="date", title="Date"),
    TableColumn(field="track_id", title="Track Id"),
    TableColumn(field="car_id", title="Car Id"),
    TableColumn(field="lap", title="Lap number"),
]

data_table = DataTable(
    source=source,
    columns=columns,
    selectable="checkbox",
    width=800,
    height=600,
)

analyse_button = Button(label="Analyse Tracks", button_type="primary")
raceline_plots = []

def get_raceline_figure(lap: Lap, title: str):
        s_race_line = figure(
        title=f"Race Line - {title}",
        x_axis_label="x",
        y_axis_label="z",
        match_aspect=True,
        width=250,
        height=250,
        active_drag="box_zoom",
        )
        lap_data  =  lap.get_data_dict()
        lap_line = s_race_line.line(
            x="raceline_x",
            y="raceline_z",
            line_width=1,
            color="blue",
            source=ColumnDataSource(data={"raceline_x": [], "raceline_z": []})
        )
        lap_line.data_source.data =  lap_data
        return s_race_line





# Vertical layout: button above table
def analyse_tracks():
    # Get selected indices from the DataTable
    selected_indices = source.selected.indices
    if not selected_indices:
        print("No tracks selected.")
        return

    # Get selected object names
    selected_objects = [table_data["object_name"][i] for i in selected_indices]

    loaded_tracks = []
    for obj_name in selected_objects:
        lap_data = get_object(obj_name)
        if not isinstance(lap_data, Lap):
            print(f"Warning: Object {obj_name} is not a Lap instance.")
            continue
        loaded_tracks.append(lap_data)

    print(f"Loaded {len(loaded_tracks)} tracks for analysis.")
    clusters = cluster_laps(loaded_tracks)
    print(f"Clustered into {len(set(clusters))} clusters.")
    for i, obj_name in enumerate(selected_objects):
        print(f"Track: {obj_name}, Cluster: {clusters[i]}") 
   
    unique_clusters = sorted(set(clusters))
    for cluster_id in unique_clusters:
        # Get indices of laps in this cluster
        cluster_indices = [i for i, c in enumerate(clusters) if c == cluster_id]
        if not cluster_indices:
            continue
        # Use the first Lap in the cluster
        lap = loaded_tracks[cluster_indices[0]]
        # Assume lap has attributes 'x' and 'y' for raceline coordinates
        p = get_raceline_figure(lap, title=f"Cluster {cluster_id} ({len(cluster_indices)} laps)")
        raceline_plots.append(p)

    # Add plots below the data_table
    track_tab.children.append(column(*raceline_plots))

analyse_button.on_click(analyse_tracks)

track_tab = layout([
    [analyse_button],
    [data_table]
])



# If running standalone for testing:
if __name__ == "__main__":
    curdoc().add_root(track_tab)