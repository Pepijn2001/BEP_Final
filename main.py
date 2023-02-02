import csv

from model import HaS
import mesa
import pandas as pd

width = 50  # in meters
height = 50
density = 0.5  # in percentage
seed = range(10)
tick_length = 1  # in minutes
hider_profiles = ["Child 1-3 y/o", "Child 3-6 y/o", "Child 6-12 y/o", "Elderly >65 y/o", "Mentally disabled", "Despondent", "Hiker", "Hunter"]
seeker_speed = 20  # in km/h
seeker_radius = 2  # per 50 meters
seeker_flight_time = 150  # in minutes
search_patterns = ["Parallel Track", "Expanding Square Search"]
number_drones = 1
params = {"width": width, "height": height, "density": density, "seed": seed, "tick_length": tick_length,
          "hider_profile": hider_profiles, "seeker_speed": seeker_speed,
          "seeker_radius": seeker_radius, "seeker_flight_time": seeker_flight_time, "search_pattern": search_patterns,
          "number_drones": number_drones}

results = mesa.batch_run(
    HaS,
    parameters=params,
    iterations=30,
    max_steps=1000,
    number_processes=1,
    data_collection_period=1,
    display_progress=True,
)

results_df = pd.DataFrame(results)

filtered_results = results_df.filter(items=["RunId", "Step", "iteration", "seed", "density", "hider_profile", "search_pattern", "Search_time", "Near_miss", "Not_found", "Wait_time", "Safe"])


def find_last_step(results):
    results_filtered = pd.DataFrame(columns=list(results.columns))

    for run in list(results["RunId"].unique()):
        results_run = results.loc[results["RunId"] == run]
        last_row_df = pd.DataFrame([results_run.iloc[-1]])

        last_row_df['Not_found'] = last_row_df['Not_found'].astype('boolean')
        last_row_df['Safe'] = last_row_df['Safe'].astype('boolean')
        results_filtered = pd.concat([results_filtered, last_row_df])

    return results_filtered

results_filtered = find_last_step(results_df)


results_filtered.to_csv('Hoofdvraag_1_drone.csv', sep=',', index=False, header=True, quoting=csv.QUOTE_ALL)
