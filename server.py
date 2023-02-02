from model import HaS
from agent import Seeker, Patch, Hider
import mesa


def agent_portrayal(agent):
    if type(agent) is Hider:
        portrayal = {"Shape": "circle",
                     "Filled": "true",
                     "Layer": 2,
                     "Color": "red",
                     "r": 0.5}
        return portrayal

    if type(agent) is Seeker:
        portrayal = {"Shape": "circle",
                     "Filled": "true",
                     "Layer": 2,
                     "Color": "blue",
                     "r": 0.5}
        return portrayal

    if type(agent) is Patch:
        portrayal = {}
        if agent.seen:
            portrayal["Color"] = "#D6F5D6"
        elif agent.density > 0.6:
            portrayal["Color"] = "#023020"
        elif agent.density < 0.4:
            portrayal["Color"] = "#AFE1AF"
        else:
            portrayal["Color"] = "#097969"

        portrayal["Shape"] = "rect"
        portrayal["Filled"] = "True"
        portrayal["Layer"] = 0
        portrayal["w"] = 1
        portrayal["h"] = 1
        return portrayal


width = 50  # in meters
height = 50
density = 0.5  # in percentage
seed = 1
tick_length = 1  # in minutes
hider_profiles = ["Child 1-3 y/o"]
seeker_speed = 20  # in km/h
seeker_radius = 2  # per 50 meters
seeker_flight_time = 250  # in minutes
search_patterns = None
number_drones = 3
params = {"width": width, "height": height, "density": density, "seed": seed, "tick_length": tick_length,
          "hider_profile": "Child 1-3 y/o", "seeker_speed": seeker_speed,
          "seeker_radius": seeker_radius, "seeker_flight_time": seeker_flight_time, "search_pattern": search_patterns,
          "number_drones": number_drones}

grid = mesa.visualization.CanvasGrid(agent_portrayal, width, height, 750, 750)
server = mesa.visualization.ModularServer(
    HaS, [grid], "Hide and Seek", params)

model = HaS(height, width, density, seed, tick_length, "Child 1-3 y/o", seeker_speed, seeker_radius, seeker_flight_time, search_patterns, number_drones)

server.port = 8521  # The default
server.launch()