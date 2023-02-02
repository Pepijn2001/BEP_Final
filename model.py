from mesa import Model
from mesa.space import MultiGrid
from mesa.time import RandomActivation
from mesa import DataCollector
import numpy

from agent import Hider, Seeker, Patch


class HaS(Model):
    def __init__(self, height, width, density, seed, tick_length, hider_profile, seeker_speed, seeker_radius, seeker_flight_time, search_pattern, number_drones):
        super().__init__(seed=seed)

        self.tick_length = tick_length
        self.density = density
        self.grid = MultiGrid(width, height, torus=False)
        self.width = width
        self.height = height

        self.wait_time = 0
        self.search_time = 0
        self.not_found = False
        self.safe = False
        self.lost = False
        self.missed = 0
        self.pattern_finished = 0
        self.number_drones = number_drones

        self.schedule = RandomActivation(self)
        self.running = True
        self.datacollector = DataCollector(
            model_reporters={"Search_time": "search_time", "Near_miss": "missed", "Not_found": "not_found", "Wait_time": "wait_time", "Safe": "safe"})

        cell_list = []
        for i, x, y in self.grid.coord_iter():  # patches maken
            pos = (x, y)
            if ((5/6)*self.width > x > (1/6)*self.width) and ((5/6)*self.height > y > (1/6)*self.height):
                cell_list.append(pos)
            agent_patch = Patch(pos, self, density)
            agent_patch.density = numpy.random.triangular(density - 0.2, density, density + 0.2)
            self.grid.place_agent(agent_patch, pos)

        pos_hider = self.random.choice(cell_list)
        pos_seeker = (3, 3)

        if number_drones > 1:
            for id in range(number_drones):
                if id == 0:
                    search_pattern = "Parallel Track"
                elif id == 1:
                    search_pattern = "Expanding Square Search"
                elif id == 2:
                    search_pattern = "Inverse Parallel Track"
                seeker_agent = Seeker(id, self, pos_seeker, seeker_speed, seeker_radius, seeker_flight_time,
                                      search_pattern)
                self.schedule.add(seeker_agent)
                self.grid.place_agent(seeker_agent, pos_seeker)
        else:
            seeker_agent = Seeker(1, self, pos_seeker, seeker_speed, seeker_radius, seeker_flight_time,
                                  search_pattern)
            self.schedule.add(seeker_agent)
            self.grid.place_agent(seeker_agent, pos_seeker)

        hider_agent = Hider(5, self, pos_hider, hider_profile)
        self.schedule.add(hider_agent)
        self.grid.place_agent(hider_agent, pos_hider)

    def step(self):
        """
        Run one step of the model.
        """
        self.schedule.step()
        if self.pattern_finished == self.number_drones:
            self.not_found = True
            self.running = False
        self.datacollector.collect(self)
