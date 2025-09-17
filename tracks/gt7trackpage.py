from bokeh.models import Button, TableColumn, DataTable, ColumnDataSource, TabPanel, Tabs, DataCube, GroupingInfo
from bokeh.layouts import layout
from bokeh.io import curdoc
from bokeh import colors
from gt7dashboard.gt7lap import Lap
from gt7dashboard.gt7laphelper import get_data_dict
from tracks.gt7trackanalysis import analyse_tracks
from gt7dashboard.s3helper import S3Client
import re
from bokeh.plotting import figure
from bokeh.layouts import column
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

def on_row_selection(attr, old, new):
    laps = []
    for selected_index in new:
        obj_name = table_data["object_name"][selected_index]
        print(f"Selected row index: {selected_index}, Object name: {obj_name}")
        lap_data = s3Client.get_object(obj_name)
        if not isinstance(lap_data, Lap):
            print(f"Warning: Object {obj_name} is not a Lap instance.")
            continue
        laps.append(lap_data)

    selected_raceline_figure = get_raceline_figure(laps, title=f"Lap # {new}")
    track_clustering_tab.children[1] = column([data_table, selected_raceline_figure], sizing_mode="stretch_both")

source.selected.on_change('indices', on_row_selection)

analyse_button = Button(label="Analyse Tracks", button_type="primary")
cluster_data_cube = DataCube()

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




def on_analyse_button_click():
    try:
        analyse_button.disabled = True
        print("Analysing selected tracks...")
        cluster_lap_map = analyse_tracks(source, table_data, track_clustering_tab)
        cluster_table_data = {
            "cluster_index": [],
            "objectname": [],
        }

        for cluster_lap in enumerate(cluster_lap_map):
            cluster_table_data["cluster_index"].append(cluster_lap[0])
            cluster_table_data["objectname"].append(cluster_lap[1])

        cluster_source = ColumnDataSource(data=cluster_table_data)
        cluster_columns = [
            TableColumn(field="objectname", title="Object Names"),
        ]  
        grouping = [
            GroupingInfo(getter="cluster_index")
        ]
        target = ColumnDataSource(data=dict(row_indices=[], labels=[]))
        cluster_data_cube = DataCube(
            source=cluster_source,
            columns=cluster_columns,
            grouping=grouping,
            target=target,
            selectable=True,
            width=800,
            height=600,
        )
        track_clustering_tab.children.append(cluster_data_cube)        
       
    except Exception as e:
        print(f"Error during analysis: {e}")
    finally:
        analyse_button.disabled = False
        print("Analysis complete.")


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