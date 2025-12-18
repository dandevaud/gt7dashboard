from gt7dashboard import gt7helper

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

    raceline_y_throttle, raceline_x_throttle, raceline_z_throttle = gt7helper.get_race_line_coordinates_when_mode_is_active(self, mode=gt7helper.RACE_LINE_THROTTLE_MODE)
    raceline_y_braking, raceline_x_braking, raceline_z_braking = gt7helper.get_race_line_coordinates_when_mode_is_active(self, mode=gt7helper.RACE_LINE_BRAKING_MODE)
    raceline_y_coasting, raceline_x_coasting, raceline_z_coasting = gt7helper.get_race_line_coordinates_when_mode_is_active(self, mode=gt7helper.RACE_LINE_COASTING_MODE)

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
        "ticks": list(range(len(self.data_speed))),
        "coast": self.data_coasting,
        "raceline_y": self.data_position_y,
        "raceline_x": self.data_position_x,
        "raceline_z": self.data_position_z,
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

        "distance": gt7helper.get_x_axis_depending_on_mode(self, distance_mode),
    }

    return data