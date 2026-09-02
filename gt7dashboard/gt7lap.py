from array import array
from datetime import datetime


# Per-tick telemetry attributes and the array typecode they are stored with.
# Storing these as Python lists uses a boxed PyObject per entry (~28 bytes each);
# using array.array reduces this to the raw value size and keeps memory bounded.
FLOAT_DATA_ATTRIBUTES = (
    "data_throttle",
    "data_braking",
    "data_braking_abs",
    "data_steering",
    "data_coasting",
    "data_speed",
    "data_time",
    "data_rpm",
    "data_tires",
    "data_position_x",
    "data_position_y",
    "data_position_z",
    "data_boost",
    "data_rotation_yaw",
    "data_absolute_yaw_rate_per_second",
)
INT_DATA_ATTRIBUTES = (
    "data_gear",
)

# Attribute name to array typecode
DATA_ATTRIBUTE_TYPECODES = {name: "d" for name in FLOAT_DATA_ATTRIBUTES}
DATA_ATTRIBUTE_TYPECODES.update({name: "i" for name in INT_DATA_ATTRIBUTES})


class Lap:
    def __init__(self):
        # Nice title for lap
        self.title = ""
        # Number of all lap ticks
        self.lap_ticks = 1
        # Lap time after crossing the finish line
        self.lap_finish_time = 0
        # Live time during a live lap
        self.lap_live_time = 0
        # Total number of laps
        self.total_laps = 0
        # Number of current lap
        self.number = 0

        # trackId
        self.track_id = -1
        
        # Aggregated number of instances where condition is true
        self.throttle_and_brake_ticks = 0
        self.no_throttle_and_no_brake_ticks = 0
        self.full_brake_ticks = 0
        self.full_throttle_ticks = 0
        self.tires_overheated_ticks = 0
        self.tires_spinning_ticks = 0
        # Data points with value for every tick
        # Stored as array.array to save memory (see DATA_ATTRIBUTE_TYPECODES)
        for _name, _typecode in DATA_ATTRIBUTE_TYPECODES.items():
            setattr(self, _name, array(_typecode))
        # Fuel
        self.fuel_at_start = 0
        self.fuel_at_end = -1
        self.fuel_consumed = -1
        # Car
        self.car_id = 0

        # Always record was set when recording the lap, likely a replay
        self.is_replay = False
        self.is_manual = False

        self.lap_start_timestamp = datetime.now()
        self.lap_end_timestamp = -1

    def __str__(self):
        return "\n %s, %2d, %1.f, %4d, %4d, %4d" % (
            self.title,
            self.number,
            self.fuel_at_end,
            self.full_throttle_ticks,
            self.full_brake_ticks,
            self.no_throttle_and_no_brake_ticks,
        )

    def format(self):
        return "Lap %2d, %s (%d Ticks)" % (
            self.number,
            self.title,
            len(self.data_speed),
        )

   

    
