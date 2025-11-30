from bokeh.models import Button, TableColumn, DataTable, ColumnDataSource, TabPanel, Tabs, Select, Row, SelectEditor, CellEditor, Arrow, NormalHead
from bokeh.layouts import layout, row, column
from bokeh.io import curdoc
from bokeh import colors, application
from gt7dashboard import gt7helper
from gt7dashboard.gt7lap import Lap
from gt7dashboard.gt7laphelper import get_data_dict
from tracks.gt7trackanalysis import TrackAnalysis
from gt7dashboard.s3helper import S3Client
import re
from bokeh.plotting import figure
import random

app = application.Application


filename_regex = r'([^_]*)_([^_]*)_([^_]*)_([^_]*).json'  # Placeholder regex to extract date from filename
s3Client = S3Client()
track_analysis = TrackAnalysis(s3client=s3Client)
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
track_list = gt7helper.get_track_list()
car_list = gt7helper.get_car_name_list()

def map_track_name_to_id(track_name):
    if track_name == "Unknown" or track_name == "":
        return -1
    for track_id, name in track_list:
        if name == track_name:
            return track_id
    return None

def map_track_id_to_name(track_id):
    track_id = int(track_id)
    if track_id < 0:
        return "Unknown"
    for tid, name in track_list:
        if tid == track_id:
            return name
    return None

def map_car_id_to_name(car_id):
    car_id = int(car_id)
    if car_id < 0:
        return "Unknown"
    for tid, name in car_list:
        if tid == car_id:
            return name
    return car_id

for obj in object_list:
    match = re.search(filename_regex, obj)
    if match:
        table_data["object_name"].append(obj)
        table_data["date"].append(match.group(1))
        table_data["track_id"].append(map_track_id_to_name(match.group(2)))
        table_data["car_id"].append(map_car_id_to_name(match.group(3)))
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
    TableColumn(field="date", title="Date", editor=CellEditor()),
    TableColumn(field="track_id", title="Track", editor=SelectEditor(options=[track[1] for track in track_list])),
    TableColumn(field="car_id", title="Car", editor=CellEditor()),
    TableColumn(field="lap", title="Lap number", editor=CellEditor()),
    TableColumn(field="cluster_id", title="Cluster ID", editor=CellEditor()),
]

data_table = DataTable(
    source=source,
    columns=columns,
    selectable="checkbox",
    width=800,
    height=600,
    editable=True,    
)

selected_laps = []

analyse_button = Button(label="Analyse Tracks", button_type="primary")
load_button = Button(label="Load selected in race diagrams", button_type="primary")
plot_selection_button = Button(label="Plot Selected Laps", button_type="success")
save_changes_button = Button(label="Save Changes", button_type="success")
save_clusters_button = Button(label="Save Clusters", button_type="light")
cluster_div = Row()


def save_changes():
    print("Saving changes to S3...")
    for i in range(len(source.data["object_name"])):
        obj_name = source.data["object_name"][i]
        new_track_name = source.data["track_id"][i]
        new_track_id = map_track_name_to_id(new_track_name)
        if new_track_id is None:
            print(f"Warning: Track name {new_track_name} not found in track list.")
            continue
        match = re.search(filename_regex, obj_name)
        if match:
            current_track_id = match.group(2)
            if str(new_track_id) != current_track_id and new_track_name != "":
                new_obj_name = re.sub(r'([^_]*)_([^_]*)_([^_]*)_([^_]*)\.json', fr'\g<1>_{new_track_id}_\g<3>_\g<4>.json', obj_name)
                print(f"Renaming object {obj_name} to {new_obj_name}")
                s3Client.rename_object(obj_name, new_obj_name)
                # Update the source data to reflect the change
                source.data["object_name"][i] = new_obj_name
    source.trigger('data', source.data, source.data)  # Refresh the table display
    print("Changes saved.")

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
            color=colors.named.__all__[random.randint(0, len(colors.named.__all__)-1)]

            # Draw an arrow for the first few coordinates to show direction
            coords_x = lap_data.get("raceline_x", [])
            coords_z = lap_data.get("raceline_z", [])
            if len(coords_x) >= 50 and len(coords_z) >= 50:
                # Draw arrow from first to second point
                s_race_line.add_layout(
                    Arrow(
                        x_start=coords_x[0], y_start=coords_z[0],
                        x_end=coords_x[50], y_end=coords_z[50],
                        line_color=color,
                        line_width=2,
                        end=NormalHead(line_color=color, line_width=2, size=10)
                    )
                )
            s_race_line.line(
                x="raceline_x",
                y="raceline_z",
                line_width=1,
                color=color,
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

def load_selected_laps():
    selected_indices = source.selected.indices
    laps = []
    for selected_index in selected_indices:
        obj_name = table_data["object_name"][selected_index]
        print(f"Loading row index: {selected_index}, Object name: {obj_name}")
        lap_data = s3Client.get_object(obj_name)
        if not isinstance(lap_data, Lap):
            print(f"Warning: Object {obj_name} is not a Lap instance.")
            continue
        laps.append(lap_data)
    app.gt7comm.load_laps(laps, replace_other_laps=True)

def create_cluster_dropdown(cluster_ids):
    options = [str(cid) for cid in sorted(cluster_ids)]
    select = Select(title="Select Cluster ID:", value="", options=options)
    return select

def update_object_name_with_track(selected_track, obj_name):
        new_obj_name = re.sub(r'([^_]*)_([^_]*)_([^_]*)_([^_]*)\.json', fr'\g<1>_{selected_track}_\g<3>_\g<4>.json', obj_name)
        print(f"Renaming object {obj_name} to {new_obj_name}")
        s3Client.rename_object(obj_name, new_obj_name)

def create_cluster_trackAssignment_form(cluster_id, cluster_lap_map: dict[int, list[dict[str, Lap | str]]]):
    options = gt7helper.get_track_list()
    select = Select(title="Select Track Assignment:", value="", options=sorted(options, key=lambda x: x[2]))
    track_assignment_save_button = Button(label="Save Track Assignment", button_type="warning")
    def on_track_assignment_save_click():
        selected_track = select.value
        print(f"Assigning Track {selected_track} to Cluster {cluster_id}")
        for lapdata in cluster_lap_map.get(cluster_id, []):
                update_object_name_with_track(selected_track, lapdata["name"])    
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
        cluster_lap_map = track_analysis.analyse_tracks(source, table_data, track_clustering_tab)
        cluster_select = create_cluster_dropdown(cluster_lap_map.keys())
        
        def on_cluster_select_change(attr, old, new):              
            cluster_raceline_figures = []
            track_assignment_form = None         
            print(f"Cluster selected: {new}")
            cluster_div.children = [cluster_select]
            selected_cluster_id = int(new)
            selected_laps = cluster_lap_map.get(selected_cluster_id, [])
            print(f"Loading laps in cluster {selected_cluster_id}")
            loaded_laps = [lapdata["Lap"] for lapdata in selected_laps]
            print(f"Loaded {len(loaded_laps)} laps for cluster {selected_cluster_id}")
            print(f"Generating raceline figure for cluster {selected_cluster_id}")
            cluster_raceline_figures = get_raceline_figure(loaded_laps, title=f"Cluster {selected_cluster_id}")
            print(f"Creating track assignment form for cluster {selected_cluster_id}")
            track_assignment_form = create_cluster_trackAssignment_form(selected_cluster_id, cluster_lap_map)
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
save_changes_button.on_click(save_changes)
save_clusters_button.on_click(track_analysis.save_clusters)
load_button.on_click(load_selected_laps)

track_clustering_tab = layout([
    [analyse_button, load_button, plot_selection_button, save_changes_button, save_clusters_button],
    data_table,
    cluster_div
])


#  Setup the tabs
tab1 = TabPanel(child=track_clustering_tab, title="Analysis")
tab2 = TabPanel(child=track_clustering_tab, title="Clustering")
tracks_tabs = Tabs(tabs=[tab1, tab2], sizing_mode="stretch_both")



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
    #curdoc().add_root(tracks_tabs)