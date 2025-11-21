#!/bin/bash

exec python ./update_Lap_only.py &
exec bokeh serve .