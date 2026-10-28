from gt7dashboard import gt7helper


def _build_race_line_mode_coordinates(lap):
    coordinates_len = len(lap.data_braking)
    cached_len = getattr(lap, "_raceline_coordinates_len", -1)
    cached_value = getattr(lap, "_raceline_coordinates", None)
    if cached_len == coordinates_len and cached_value is not None:
        return cached_value

    throttle_y, throttle_x, throttle_z = [], [], []
    braking_y, braking_x, braking_z = [], [], []
    coasting_y, coasting_x, coasting_z = [], [], []

    for i, brake in enumerate(lap.data_braking):
        throttle = lap.data_throttle[i]
        pos_y = lap.data_position_y[i]
        pos_x = lap.data_position_x[i]
        pos_z = lap.data_position_z[i]

        if brake < throttle:
            throttle_y.append(pos_y)
            throttle_x.append(pos_x)
            throttle_z.append(pos_z)
        else:
            throttle_y.append("NaN")
            throttle_x.append("NaN")
            throttle_z.append("NaN")

        if brake > throttle:
            braking_y.append(pos_y)
            braking_x.append(pos_x)
            braking_z.append(pos_z)
        else:
            braking_y.append("NaN")
            braking_x.append("NaN")
            braking_z.append("NaN")

        if brake == 0 and throttle == 0:
            coasting_y.append(pos_y)
            coasting_x.append(pos_x)
            coasting_z.append(pos_z)
        else:
            coasting_y.append("NaN")
            coasting_x.append("NaN")
            coasting_z.append("NaN")

    result = {
        gt7helper.RACE_LINE_THROTTLE_MODE: (throttle_y, throttle_x, throttle_z),
        gt7helper.RACE_LINE_BRAKING_MODE: (braking_y, braking_x, braking_z),
        gt7helper.RACE_LINE_COASTING_MODE: (coasting_y, coasting_x, coasting_z),
    }
    lap._raceline_coordinates_len = coordinates_len
    lap._raceline_coordinates = result
    return result


def _get_ticks(lap):
    ticks_len = len(lap.data_speed)
    cached_len = getattr(lap, "_ticks_len", -1)
    if cached_len != ticks_len:
        lap._ticks_cache = list(range(ticks_len))
        lap._ticks_len = ticks_len
    return lap._ticks_cache


def _get_distance(lap, distance_mode: bool):
    if not distance_mode:
        return _get_ticks(lap)

    distance_len = len(lap.data_speed)
    cached_len = getattr(lap, "_distance_len", -1)
    if cached_len != distance_len:
        lap._distance_cache = gt7helper.get_x_axis_for_distance(lap)
        lap._distance_len = distance_len
    return lap._distance_cache

def get_speed_peaks_and_valleys(Lap):
    (
        peak_speed_data_x,
        peak_speed_data_y,
        valley_speed_data_x,
        valley_speed_data_y,
    ) = gt7helper.get_speed_peaks_and_valleys(Lap)

    return (
        peak_speed_data_x,
        peak_speed_data_y,
        valley_speed_data_x,
        valley_speed_data_y,
    )

def car_name(self) -> str:
        # FIXME Breaking change. Not all log files up to this point have this attribute, remove this later
        if (not hasattr(self, "car_id")):
            return "Car not logged"
        return gt7helper.get_car_name_for_car_id(self.car_id)

def get_data_dict(self, distance_mode=True) -> dict[str, list]:
    coordinates = _build_race_line_mode_coordinates(self)
    raceline_y_throttle, raceline_x_throttle, raceline_z_throttle = coordinates[gt7helper.RACE_LINE_THROTTLE_MODE]
    raceline_y_braking, raceline_x_braking, raceline_z_braking = coordinates[gt7helper.RACE_LINE_BRAKING_MODE]
    raceline_y_coasting, raceline_x_coasting, raceline_z_coasting = coordinates[gt7helper.RACE_LINE_COASTING_MODE]

    data = {
        "throttle": self.data_throttle,
        "brake": self.data_braking,
        "brake_abs": self.data_braking_abs,
        "speed": self.data_speed,
        "time": self.data_time,
        "tires": self.data_tires,
        "rpm": self.data_rpm,
        "boost": self.data_boost,
        "yaw_rate": self.data_absolute_yaw_rate_per_second,
        "gear": self.data_gear,
        "ticks": _get_ticks(self),
        "coast": self.data_coasting,
        "raceline_y": self.data_position_y,
        "raceline_x": self.data_position_x,
        "raceline_z": self.data_position_z,
        "sway": self.data_g_force_lat,
        "surge": self.data_g_force_lon,
        # For a raceline when throttle is engaged
        "raceline_y_throttle": raceline_y_throttle,
        "raceline_x_throttle": raceline_x_throttle,
        "raceline_z_throttle": raceline_z_throttle,
        # For a raceline when braking is engaged
        "raceline_y_braking": raceline_y_braking,
        "raceline_x_braking": raceline_x_braking,
        "raceline_z_braking": raceline_z_braking,
        # For a raceline when neither throttle nor brake is engaged
        "raceline_y_coasting": raceline_y_coasting,
        "raceline_x_coasting": raceline_x_coasting,
        "raceline_z_coasting": raceline_z_coasting,

        "distance": _get_distance(self, distance_mode),
    }

    return data