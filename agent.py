from mesa import Agent
import random
import math

direction_list_moore = [(-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0)]
direction_list_neumann = [(0, 1), (1, 0), (0, -1), (-1, 0)]


def determine_distance(start_node, target_node,
                       direction_node):  # gebruikt om te kijken of de agent niet verder gaat dan de target node
    x1 = start_node[0]
    y1 = start_node[1]
    x2 = target_node[0]
    y2 = target_node[1]
    x3 = round(direction_node[0])
    y3 = round(direction_node[1])

    if (math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)) <= (math.sqrt((x3 - x1) ** 2 + (y3 - y1) ** 2)):
        return False
    else:
        return True


def determine_speed(
        self):  # bepaalt de snelheid (in meter per minuut, gegeven een grid lengte van 100x100) o.b.v. density
    patch = [agent for agent in self.model.grid.get_cell_list_contents(self.pos) if isinstance(agent, Patch)]
    if patch[0].density > self.model.density:
        self.speed = self.speed_base / 1.5 * 16.6667 / 100
    else:
        self.speed = self.speed_base * 16.6667 / 100


def get_direction(self, end_node):  # bepaalt de richting tussen 2 nodes
    x1 = self.pos_float[0]
    x2 = end_node[0]
    y1 = self.pos_float[1]
    y2 = end_node[1]

    deltaX = x2 - x1
    deltaY = y2 - y1

    degrees_temp = (math.atan2(deltaX, deltaY) / math.pi * 180)
    if degrees_temp < 0:
        degrees_temp = degrees_temp + 360
    radians = degrees_temp * (math.pi / 180)

    self.direction = (math.sin(radians), math.cos(radians))


"""
Hider agent fungeert als verdwaald persoon. Loopt randomly rond totdat de agent verdwaald is. Op basis
van leeftijd wordt er een strategie gekozen om te bewegen als verdwaald. 
"""


class Hider(Agent):
    def __init__(self, unique_id, model, pos, profile):
        super().__init__(unique_id, model)
        self.pos = pos
        self.pos_float = pos  # grid position and 'real' floating grid position
        self.found = False  # whether agent is found
        self.direction = ()  # direction that the agent moves in
        self.speed_base = 0
        self.speed = 0

        # attributen die over strategie gaan
        self.profile = profile
        self.energy_expended = 0
        self.max_energy_expended = 0
        self.energy_rate = 4  # kcal/min
        self.exhausted = False

        self.set_profile()
        self.strategy = self.choose_strategy()

        # needed for direction_sampling/direction_traveling
        self.direction_chosen = False
        self.landmark = self.pos
        self.radius = 3
        self.direction_count = 0
        self.going_back = False  # whether agent is going back to landmark
        self.target_node = (0, 0)
        self.sample_complete = False  # whether agent has sampled all direction around a landmark

        # needed for backtracking
        self.cell_history = []
        self.end_nodes = []  # list of target nodes

    def step(self):
        if not self.model.lost:  # when not lost, agent moves randomly
            determine_speed(self)
            self.direction = self.choose_direction_moore()
            self.pos_float = (self.pos_float[0] + self.direction[0], self.pos_float[1] + self.direction[1])
            rounded_pos = ((round(self.pos_float[0])), (round(self.pos_float[1])))
            if self.model.grid.out_of_bounds(rounded_pos):
                return
            else:
                self.model.grid.move_agent(self, rounded_pos)
                self.cell_history.append(self.pos_float)
            if self.random.random() < 0.01:
                self.model.lost = True
                self.direction_chosen = False
                self.model.wait_time = self.model.schedule.steps
        else:
            self.random_walking()
            self.direction_traveling()
            self.staying_put()
            self.backtracking()
            self.direction_sampling()
            determine_speed(self)

        self.energy_expended = self.energy_expended + self.energy_rate * self.model.tick_length
        if self.energy_expended >= self.max_energy_expended:
            self.exhausted = True
            self.strategy = "staying_put"

    def set_profile(self):
        if self.profile == "Child 1-3 y/o":
            self.max_energy_expended = 2250
            self.speed_base = 3.1
        elif self.profile == "Child 3-6 y/o":
            self.max_energy_expended = 2250
            self.speed_base = 3.8
        elif self.profile == "Child 6-12 y/o":
            self.max_energy_expended = 3000
            self.speed_base = 4.1
        elif self.profile == "Elderly >65 y/o":
            self.max_energy_expended = 3250
            self.speed_base = 5.1
        else:
            self.max_energy_expended = 3812.5
            self.speed_base = 5.5

    def choose_direction_moore(self):
        self.direction = random.choice(direction_list_moore)
        new_direction = tuple(self.speed * i for i in self.direction)
        return new_direction

    def choose_direction_neumann(self):
        self.direction = random.choice(direction_list_neumann)
        new_direction = tuple(self.speed * i for i in self.direction)
        return new_direction

    def choose_strategy(self):
        if self.profile == "Child 1-3 y/o":
            return "random_traveling"
        elif self.profile == "Child 3-6 y/o":
            return "backtracking"
        elif self.profile == "Child 6-12 y/o":
            return "direction_traveling"
        elif self.profile == "Elderly >65 y/o":
            return self.random.choice(["random_traveling", "backtracking"])
        elif self.profile == "Mentally disabled":
            return self.random.choice(["direction_traveling", "staying_put"])
        elif self.profile == "Despondent":
            return "staying_put"
        elif self.profile == "Hiker":
            return "direction_sampling"
        elif self.profile == "Hunter":
            return self.random.choice(["direction_traveling", "backtracking"])

    def random_walking(self):
        if self.strategy == "random_walking":
            new_direction = self.choose_direction_moore()
            self.pos_float = (self.pos_float[0] + new_direction[0], self.pos_float[1] + new_direction[1])
            rounded_pos = (round(self.pos_float[0]), round(self.pos_float[1]))
            if self.model.grid.out_of_bounds(rounded_pos):
                self.model.safe = True
                self.model.running = False
                return
            else:
                self.model.grid.move_agent(self, rounded_pos)

    def direction_sampling(self):
        if self.strategy != "direction_sampling":
            return

        if self.sample_complete:  # this function should only run if agent hasn't searched around the landmark yet
            self.sample_completed()
            return

        if not self.direction_chosen and not self.going_back:  # chooses first direction, starting at the landmark
            direction = direction_list_neumann[self.direction_count]  # directions are only north, east, south, west
            self.direction = tuple(self.speed * i for i in direction)
            self.landmark = self.pos_float
            target_node = tuple(self.radius * i for i in direction)
            self.target_node = (self.landmark[0] + target_node[0], self.landmark[1] + target_node[1])
            self.direction_chosen = True

        if not self.direction_chosen and self.going_back:  # if the Hider is going back to the landmark
            get_direction(self, self.landmark)
            self.direction = tuple(self.speed * i for i in self.direction)
            self.direction_chosen = True
            self.direction_count += 1

        self.pos_float = (self.pos_float[0] + self.direction[0], self.pos_float[1] + self.direction[1])  # move agent

        rounded_pos = (round(self.pos_float[0]), round(self.pos_float[1]))  # move function only accepts integers

        if self.model.grid.out_of_bounds(rounded_pos):
            self.model.safe = True
            self.model.running = False
            return

        elif not determine_distance(self.pos, self.target_node, self.pos_float):  # checks if agent overshot the target
            self.model.grid.move_agent(self, ((round(self.target_node[0])), round(self.target_node[1])))
            self.pos_float = self.target_node
            if not self.going_back:
                self.target_node = self.landmark
                self.going_back = True
            else:  # only back at the landmark, another direction can be chosen
                self.going_back = False
            self.direction_chosen = False
        else:
            self.model.grid.move_agent(self, rounded_pos)

        if self.direction_count > 3 and not self.going_back:  # once all directions have been sampled
            self.direction_count = 0
            self.sample_complete = True
            self.direction_chosen = False

    def sample_completed(self):  # sets target node 2x radius from landmark
        if not self.direction_chosen:
            direction = direction_list_neumann[self.direction_count]
            self.direction = tuple(self.speed * i for i in direction)
            target_node = tuple(2 * self.radius * i for i in direction)
            self.target_node = (self.landmark[0] + target_node[0], self.landmark[1] + target_node[1])
            if self.model.grid.out_of_bounds(target_node):
                self.model.safe = True
                self.model.running = False
                return
            self.direction_chosen = True

        self.pos_float = (self.pos_float[0] + self.direction[0], self.pos_float[1] + self.direction[1])
        rounded_pos = (round(self.pos_float[0]), round(self.pos_float[1]))

        if not determine_distance(self.pos, self.target_node,
                                  self.pos_float):  # once at landmark, sampling can begin again
            if self.model.grid.out_of_bounds(((round(self.target_node[0])), round(self.target_node[1]))):
                self.model.safe = True
                self.model.running = False
                return
            self.model.grid.move_agent(self, ((round(self.target_node[0])), round(self.target_node[1])))
            self.pos_float = self.target_node
            self.sample_complete = False
            self.direction_chosen = False
            self.going_back = False
        else:
            if self.model.grid.out_of_bounds(rounded_pos):
                self.model.safe = True
                self.model.running = False
                return
            self.model.grid.move_agent(self, rounded_pos)

    def direction_traveling(self):  # chooses direction and keeps going that way until out of bounds
        if self.strategy == "direction_traveling":
            if not self.direction_chosen:
                self.direction = self.choose_direction_moore()
                self.direction_chosen = True
            if self.direction_chosen:
                self.pos_float = (self.pos_float[0] + self.direction[0], self.pos_float[1] + self.direction[1])
                rounded_pos = (round(self.pos_float[0]), round(self.pos_float[1]))
                if self.model.grid.out_of_bounds(rounded_pos):
                    self.model.safe = True
                    self.model.running = False
                    return
                else:
                    self.model.grid.move_agent(self, rounded_pos)

    def staying_put(self):
        if self.strategy == "staying_put":
            pass

    def backtracking(self):  # agent tries to retrace steps (cell history)
        if self.strategy == "backtracking" and len(self.cell_history) != 0:
            self.end_nodes = self.cell_history[::-1]
            self.pos_float = self.end_nodes[0]
            rounded_pos = (round(self.pos_float[0]), round(self.pos_float[1]))
            self.model.grid.move_agent(self, rounded_pos)
            self.cell_history.pop()


"""
Seeker agent begint met zoeken zodra de Hider verdwaald is. Kiest tussen 2 zoekpatronen en volgt
deze.
"""


class Seeker(Agent):
    def __init__(self, unique_id, model, pos, speed, radius, flight_time, search_pattern):
        super().__init__(unique_id, model)
        self.cell_history = []
        self.pos = pos
        self.pos_float = pos  # positie in grid en echte positie van agent
        self.rounded_pos = pos
        self.flight_time = flight_time
        self.direction = ()  # richting van de agent
        self.speed = 0
        self.speed_base = speed
        self.end_nodes = []  # lijst met end_nodes
        self.end_node_count = 0  # telt bij welk item in de lijst end_nodes_pos zijn
        self.radius = radius  # gezichtsveld van de drone
        self.search_pattern = search_pattern
        self.pattern_finished = False
        self.scanned_patches = []
        self.found = False

        if self.search_pattern == "Parallel Track":
            self.parallel_track()
        if self.search_pattern == "Inverse Parallel Track":
            self.inverse_parallel_track()
        if self.search_pattern == "Expanding Square Search":
            self.expanding_square_search()

    def step(self):
        if self.model.lost:
            if not self.found:
                self.move()
                if not self.model.running or self.pattern_finished:
                    return
                if not determine_distance(self.pos, self.end_nodes[self.end_node_count], self.pos_float):
                    self.model.grid.move_agent(self, self.end_nodes[self.end_node_count])
                    self.pos_float = self.end_nodes[self.end_node_count]
                    self.rounded_pos = self.end_nodes[self.end_node_count]
                else:
                    self.model.grid.move_agent(self, self.rounded_pos)
                if self.pos == self.end_nodes[self.end_node_count]:
                    self.end_node_count += 1
            else:
                self.model.search_time = self.model.schedule.steps
                self.model.running = False
            self.calculate_flight_time()
            self.scanning()

    def move(self):
        if self.end_node_count == len(self.end_nodes) and not self.pattern_finished:
            self.pattern_finished = True
            self.model.pattern_finished += 1
        elif not self.pattern_finished:
            get_direction(self, self.end_nodes[self.end_node_count])
            determine_speed(self)

            new_direction = tuple(self.speed * i for i in self.direction)
            self.pos_float = (self.pos_float[0] + new_direction[0], self.pos_float[1] + new_direction[1])
            self.rounded_pos = (round(self.pos_float[0]), round(self.pos_float[1]))

    def calculate_flight_time(self):
        if self.flight_time == 0:
            self.model.running = False
            self.model.not_found = True
            return
        self.flight_time = self.flight_time - self.model.tick_length

    def inverse_parallel_track(self):
        x_min = 0 + self.radius
        x_max = self.model.width - self.radius - 1
        y_min = 0 + self.radius
        y_max = self.model.height - self.radius - 1
        x = x_max
        y = y_max
        self.end_nodes = [(x_max, y_max)]
        for count, i in enumerate(range(round((y_max - y_min) / self.radius))):
            if count % 4 == 0:
                self.end_nodes.append((x_min, y))
                x = x_min
                y -= 2 * self.radius + 1
            if count % 4 == 1:
                if y < y_min:
                    return
                self.end_nodes.append((x, y))
            if count % 4 == 2:
                self.end_nodes.append((x_max, y))
                x = x_max
                y -= 2 * self.radius + 1
            if count % 4 == 3:
                if y < y_min:
                    return
                self.end_nodes.append((x, y))

    def parallel_track(self):
        x_min = 0 + self.radius
        x_max = self.model.width - self.radius - 1
        y_min = 0 + self.radius
        y_max = self.model.height - self.radius - 1
        x = x_min
        y = y_min
        self.end_nodes = [(x_min, y_min)]
        for count, i in enumerate(range(round((y_max - y_min) / self.radius))):
            if count % 4 == 0:
                self.end_nodes.append((x_max, y))
                y += 2 * self.radius + 1
                x = x_max
            if count % 4 == 1:
                if y >= self.model.height:
                    return
                self.end_nodes.append((x, y))
            if count % 4 == 2:
                self.end_nodes.append((x_min, y))
                x = x_min
                y += 2 * self.radius + 1
            if count % 4 == 3:
                if y >= self.model.height:
                    return
                self.end_nodes.append((x, y))

    def expanding_square_search(self):
        center_node = (round(self.model.width / 2), round(self.model.height / 2))
        self.end_nodes.append(center_node)
        position = center_node
        directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]
        direction_count = 0

        for count, i in enumerate(range(math.floor(self.model.width / self.radius))):
            heading = directions[direction_count]
            heading = tuple((self.radius * i * (count + 1) for i in heading))
            position = (position[0] + heading[0], position[1] + heading[1])
            if not self.model.grid.out_of_bounds(position):
                self.end_nodes.append(position)
                if direction_count == 3:
                    direction_count = 0
                else:
                    direction_count += 1

    def scanning(self):
        for cell in self.model.grid.iter_neighborhood(self.pos, True, True, self.radius):
            if cell not in self.scanned_patches:
                self.scanned_patches.append(cell)

            for agent in self.model.grid.get_cell_list_contents(cell):
                if type(agent) is Patch:
                    agent.seen = True
                if type(agent) is Hider:
                    patch = [agent for agent in self.model.grid.get_cell_list_contents(cell) if
                             isinstance(agent, Patch)]
                    if self.random.random() > patch[0].density:
                        self.model.search_time = self.model.schedule.steps
                        self.found = True
                    else:
                        self.model.missed += 1


class Patch(Agent):
    def __init__(self, pos, model, density):
        super().__init__(pos, model)
        self.pos = pos
        self.seen = False
        self.density = density

    def step(self):
        pass
