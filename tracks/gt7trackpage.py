from bokeh.models import Button, TableColumn, DataTable, ColumnDataSource, TabPanel, Tabs, Select, Row
from bokeh.layouts import layout, row, column
from bokeh.io import curdoc
from bokeh import colors
from gt7dashboard import gt7helper
from gt7dashboard.gt7lap import Lap
from gt7dashboard.gt7laphelper import get_data_dict
from tracks.gt7trackanalysis import analyse_tracks
from gt7dashboard.s3helper import S3Client
import re
from bokeh.plotting import figure
import random
from bokeh.colors import RGB


filename_regex = r'([^_]*)_([^_]*)_([^_]*)_([^_]*).json'  # Placeholder regex to extract date from filename
s3Client = S3Client()
# Get S3 objects using S3Helper
object_list = s3Client.list_objects()  # Assumes this returns a list of object names

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

selected_laps = []

analyse_button = Button(label="Analyse Tracks", button_type="primary")
plot_selection_button = Button(label="Plot Selected Laps", button_type="success")
cluster_div = Row()




def get_raceline_figure(laps: list[Lap], title: str):
        s_race_line = figure(
        title=f"Race Line - {title}",
        x_axis_label="x",
        y_axis_label="z",
        match_aspect=True,
        width=250,
        height=250,
        active_drag="box_zoom",
        )
        for lap in laps:
            lap_data  =  get_data_dict(lap)

            s_race_line.line(
                x="raceline_x",
                y="raceline_z",
                line_width=1,
                color=colors.named.__all__[random.randint(0, len(colors.named.__all__)-1)],
                source=ColumnDataSource(data=lap_data)
            )
        return s_race_line

def on_plot_selection_click():
    selected_indices = source.selected.indices
    laps = []
    for selected_index in selected_indices:
        obj_name = table_data["object_name"][selected_index]
        print(f"Selected row index: {selected_index}, Object name: {obj_name}")
        lap_data = s3Client.get_object(obj_name)
        if not isinstance(lap_data, Lap):
            print(f"Warning: Object {obj_name} is not a Lap instance.")
            continue
        laps.append(lap_data)

    raceline_figure = get_raceline_figure(laps, title=f"Lap # {selected_indices}")
    track_clustering_tab.children[1] = row([data_table, raceline_figure], sizing_mode="stretch_both")


def create_cluster_dropdown(cluster_ids):
    options = [str(cid) for cid in cluster_ids]
    select = Select(title="Select Cluster ID:", value=options[0] if options else "", options=options)
    return select

def create_cluster_trackAssignment_form(cluster_id):
    options = gt7helper.get_track_list()
    select = Select(title="Select Track Assignment:", value="", options=options)
    track_assignment_save_button = Button(label="Save Track Assignment", button_type="warning")
    def on_track_assignment_save_click():
        selected_track = select.value
        print(f"Assigning Track {selected_track} to Cluster {cluster_id}")
    
    track_assignment_save_button.on_click(on_track_assignment_save_click)
    return column([select, track_assignment_save_button], sizing_mode="stretch_both")

def get_lap_data_from_object_names(object_names):
    laps = []
    for obj_name in object_names:
        lap_data = s3Client.get_object(obj_name)
        if isinstance(lap_data, Lap):
            laps.append(lap_data)
        else:
            print(f"Warning: Object {obj_name} is not a Lap instance.")
            continue
    return laps

def on_analyse_button_click():
    try:
        analyse_button.disabled = True
        print("Analysing selected tracks...")
        cluster_lap_map = analyse_tracks(source, table_data, track_clustering_tab)

        cluster_raceline_figures = []
        track_assignment_form = None

        cluster_select = create_cluster_dropdown(cluster_lap_map.keys())
        def on_cluster_select_change(attr, old, new):
            nonlocal cluster_raceline_figures, track_assignment_form
            selected_cluster_id = int(new)
            selected_laps = cluster_lap_map.get(selected_cluster_id, [])
            loaded_laps = get_lap_data_from_object_names(selected_laps)
            cluster_raceline_figures = get_raceline_figure(loaded_laps, title=f"Cluster {selected_cluster_id}")
            track_assignment_form = create_cluster_trackAssignment_form(selected_cluster_id)
            cluster_div.children = [cluster_select, track_assignment_form, cluster_raceline_figures]

        cluster_select.on_change("value", on_cluster_select_change)
        cluster_div.children = [cluster_select]
       
    except Exception as e:
        print(f"Error during analysis: {e}")
    finally:
        analyse_button.disabled = False
        print("Analysis complete.")


analyse_button.on_click(on_analyse_button_click)
plot_selection_button.on_click(on_plot_selection_click)

track_clustering_tab = layout([
    [analyse_button, plot_selection_button],
    data_table,
    cluster_div
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