from bokeh.models import Button, TableColumn, DataTable, ColumnDataSource, TabPanel, Tabs
from bokeh.layouts import layout
from bokeh.io import curdoc
from tracks.gt7trackanalysis import analyse_tracks
from gt7dashboard.s3helper import S3Client
import re
from gt7dashboard.gt7lap import Lap
from bokeh.plotting import figure
from bokeh.layouts import column

filename_regex = r'([^_]*)_([^_]*)_([^_]*)_([^_]*).json'  # Placeholder regex to extract date from filename
s3Uploader = S3Client()
# Get S3 objects using S3Helper
object_list = s3Uploader.list_objects()  # Assumes this returns a list of object names

# Prepare data for DataTable
# Parse object_list using regex and build a list of dicts for each object
table_data = {
    "object_name": [],
    "date": [],
    "track_id": [],
    "car_id": [],
    "lap": [],
    "cluster_id": [],  # Placeholder for cluster IDs
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
    table_data["cluster_id"].append("")  # Initialize with empty cluster IDs

source = ColumnDataSource(data=table_data)

columns = [
    TableColumn(field="date", title="Date"),
    TableColumn(field="track_id", title="Track Id"),
    TableColumn(field="car_id", title="Car Id"),
    TableColumn(field="lap", title="Lap number"),
    TableColumn(field="cluster_id", title="Cluster ID"),
]

data_table = DataTable(
    source=source,
    columns=columns,
    selectable="checkbox",
    width=800,
    height=600,
)

def on_row_selection(attr, old, new):
    # Find the newly selected row(s)
    new_selection = set(new) - set(old)
    if not new_selection:
        return

    # Get the first newly selected index
    selected_index = list(new_selection)[0]
    obj_name = table_data["object_name"][selected_index]
    lap_data = get_object(obj_name)
    if not isinstance(lap_data, Lap):
        print(f"Warning: Object {obj_name} is not a Lap instance.")
        return

    selected_raceline_figure = get_raceline_figure(lap_data, title=f"Lap # {selected_index}")
    track_clustering_tab.children[1] = column([data_table, selected_raceline_figure], sizing_mode="stretch_both")

source.selected.on_change('indices', on_row_selection)

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
        s_race_line.line(
            x="raceline_x",
            y="raceline_z",
            line_width=1,
            color="blue",
            source=ColumnDataSource(data=lap_data)
        )
        return s_race_line




def on_analyse_button_click():
    clusters, loaded_tracks = analyse_tracks(source, table_data, track_clustering_tab)
     
    unique_clusters = sorted(set(clusters))
    for cluster_id in unique_clusters:
        # Get indices of laps in this cluster
        cluster_indices = [i for i, c in enumerate(clusters) if c == cluster_id]
        if not cluster_indices:
            continue
        # Plot raceline for all laps in the cluster
        for idx in cluster_indices:
            lap = loaded_tracks[idx]
            p = get_raceline_figure(lap, title=f"Cluster {cluster_id} - Lap {idx}")
            raceline_plots.append(p)

    # Add plots below the data_table    
    track_clustering_tab.children.append(column(*raceline_plots, sizing_mode="scale_width"))


analyse_button.on_click(on_analyse_button_click)

track_clustering_tab = layout([
    [analyse_button],
    data_table
])


#  Setup the tabs
tab1 = TabPanel(child=track_clustering_tab, title="Analysis")
tab2 = TabPanel(child=track_clustering_tab, title="Clustering")
tabs = Tabs(tabs=[tab1, tab2], sizing_mode="stretch_both")



# If running standalone for testing:
if __name__ == "__main__":    
    curdoc().template =  """
    {% block contents %}
        {{ embed(doc) }}
        <div style="display: inline-block; width: 100%; height: 100%">
            {{ embed(doc.roots[0]) }}
        </div>
    {% endblock %}
    """
    curdoc().title = "Track Analysis"
    curdoc().add_root(track_clustering_tab)