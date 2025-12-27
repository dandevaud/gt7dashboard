import copy
import logging
import os
import time

from gt7dashboard import gt7communication
from gt7dashboard.gt7lap import Lap
from gt7dashboard.s3helper import S3Client

# set logging level to debug
logger = logging.getLogger('main.py')
logger.setLevel(logging.DEBUG)
s3Uploader = S3Client()
global gt7comm
gt7comm = None


def update_lap_change():
    """
    Is called whenever a lap changes.
    It detects if the telemetry date retrieved is the same as the data displayed.
    If true, it updates all the visual elements.
    """
    global g_laps_stored
    global g_session_stored
    global g_connection_status_stored
    global g_telemetry_update_needed
    global g_reference_lap_selected
    global gt7comm
    
    connect_to_playstation()
    
    laps = gt7comm.get_laps()
   
    if gt7comm.session != g_session_stored:
        g_session_stored = copy.copy(gt7comm.session)

    if gt7comm.is_connected() != g_connection_status_stored:
        g_connection_status_stored = copy.copy(gt7comm.is_connected())

    # This saves on cpu time, 99.9% of the time this is true
    if laps == g_laps_stored:
        return
    
    print("Lap change detected, uploading to S3...")

    logger.debug("Rerendering laps")

    if len(laps) > 0:

        last_lap = laps[0]        

        print("Uploading last lap to S3...")
        try:
            s3Uploader.upload_json_object(last_lap, f"{last_lap.lap_start_timestamp}_{last_lap.track_id}_{last_lap.car_id}_{last_lap.number}.json")
            print("Upload successful.")
        except Exception as e:
            logger.warning(f"Error uploading to S3: {e}, retrying")
            s3Uploader.upload_json_object(last_lap, f"{last_lap.lap_start_timestamp}_{last_lap.track_id}_{last_lap.car_id}_{last_lap.number}.json")
    g_laps_stored = laps.copy()
    g_telemetry_update_needed = False
    
    
    
def connect_to_playstation():
    global gt7comm
        # Share the gt7comm connection between sessions by storing them as an application attribute
    if not gt7comm:
        playstation_ip = os.environ.get("GT7_PLAYSTATION_IP")
        load_laps_path = os.environ.get("GT7_LOAD_LAPS_PATH")

        if not playstation_ip:
            playstation_ip = "255.255.255.255"
            logger.info(f"No IP set in env var GT7_PLAYSTATION_IP using broadcast at {playstation_ip}")

        gt7comm = gt7communication.GT7Communication(playstation_ip)

        gt7comm.start()
    else:
        # Reuse existing thread
        if not gt7comm.is_connected():
            logger.info("Restarting gt7communcation because of no connection")
            gt7comm.restart()
        else:
            # Existing thread has connection, proceed
            pass
   

connect_to_playstation()


g_laps_stored = []
g_session_stored = None
g_connection_status_stored = None
g_reference_lap_selected = None
g_stored_fuel_map = None
g_telemetry_update_needed = False

# This will only trigger once per lap, but we check every second if anything happened
while True:
    time.sleep(1)
    update_lap_change()
    
#curdoc().add_periodic_callback(update_lap_change, 1000)
