#!/usr/bin/python3

import string
import random
import itertools

def roll(chance):
    return random.randint(1, 100) <= chance

class Matrix:
    def __init__(self, height, width, cell_value):
        self.height = height
        self.width = width
        self.store = [[cell_value for x in range(width)] for y in range(height)]

    def cells(self, y = 0, x = 0, height = None, width = None):
        if height == None: 
            height = self.height            
        if width == None:
            width = self.width        
        if height <= 0 or width <= 0:
            return []
        for cy in range(max(y, 0), min(max(y + height, 0), self.height)):
            for cx in range(max(x, 0), min(max(x + width, 0), self.width)):
                yield (cy, cx, self.store[cy][cx])
                
    def set(self, value, y = 0, x = 0, height = None, width = None):
        if height == None: 
            height = self.height            
        if width == None:
            width = self.width
        if height <= 0 or width <= 0:
            return
        for cy in range(max(y, 0), min(max(y + height, 0), self.height)):
            for cx in range(max(x, 0), min(max(x + width, 0), self.width)):
                self.store[cy][cx] = value

    def border_cells(self, offset = 0, y = 0, x = 0, height = None, width = None):        
        if height == None: 
            height = self.height            
        if width == None:
            width = self.width            
        if height <= 0 or width <= 0:
            return []
        
        y -= offset
        x -= offset
        width += 2*offset
        height += 2*offset
        
        top_row = self.cells(y, x, 1, width)
        bottom_row = self.cells(y + height - 1, x, 1, width) if height > 1 else []
        left_col = self.cells(y + 1, x, height - 2,  1)
        right_col = self.cells(y + 1, x + width - 1, height - 2, 1) if width > 1 else []
    
        return itertools.chain(top_row, bottom_row, left_col, right_col)
    
    def __getitem__(self, key):
        return self.store[key]

class Zone:
    count = 0
    
    def __init__(self, y, x, height, width):
        self.id = self.new_id()
        self.y = y
        self.x = x
        self.height = height
        self.width = width
        self.neighbours = None
        self.group_id = self.id
    
    @property
    def area(self):
        return self.height * self.width
    
    @classmethod
    def new_id(cls):
        id = cls.count
        cls.count += 1
        return id

    def __str__(self):
        return 'Zone_' + str(self.id)

class Area:
    EMPTY_CELL = 0
    RESERVED_CELLS = 1
    CELL_PICS = ' ' + string.digits + string.ascii_lowercase
    
    ZONE_MIN = 2
    ZONE_MAX = 3
    
    def __init__(self, height, width):
        self.height = height
        self.width = width
        self.matrix = Matrix(height, width, self.EMPTY_CELL)
        self.zones = {}
    
    def empty_cells(self):
        for (y, x, cell) in self.matrix.cells():
            if cell == self.EMPTY_CELL:
                yield (y, x)
        
    def get_max_sizes(self, y, x, height, width):
        max_y = min(height, self.height - y)
        max_x = min(width, self.width - x)
        for (cy, cx, cell) in self.matrix.cells(y, x, height, 1):
            if cell != self.EMPTY_CELL:
                max_y = cy - y
                break
        for (cy, cx, cell) in self.matrix.cells(y, x, 1, width):
            if cell != self.EMPTY_CELL:
                max_x = cx - x
                break
        return (max_y, max_x)
    
    def is_area_empty(self, y, x, height, width):
        return all(map(lambda cc: cc[2] == self.EMPTY_CELL, self.matrix.cells(y, x, height, width)))
    
    def place_zone(self, zone):
        self.matrix.set(self.RESERVED_CELLS + zone.id, zone.y, zone.x, zone.height, zone.width)
        self.zones[zone.id] = zone
    
    def generate_zones(self):
        for (y, x) in self.empty_cells():
            max_height, max_width = self.get_max_sizes(y, x, self.ZONE_MAX, self.ZONE_MAX)
            if max_height >= self.ZONE_MIN and max_width >= self.ZONE_MIN:
                while True:
                    height, width = random.randint(self.ZONE_MIN, max_height), random.randint(self.ZONE_MIN, max_width)
                    if self.is_area_empty(y, x, height, width):
                        break
                self.place_zone(Zone(y, x, height, width))
    
    def calculate_zone_neighbours(self):
        for zone in self.zones.values():
            neighbour_cells = self.matrix.border_cells(1, zone.y, zone.x, zone.height, zone.width)
            neighbour_ids = filter(lambda cell: cell >= 0, { cell - self.RESERVED_CELLS for (y, x, cell) in neighbour_cells })
            zone.neighbours = list(map(self.zones.get, neighbour_ids))
    
    def generate_groups(self):
        for zone in self.zones.values():
            if roll(60):
                neighbour = random.choice(zone.neighbours)
                zone.group_id = neighbour.group_id
        #
        # group shouldn't be shown on map
        #
        """
        for zone in self.zones.values():
            zone.id = zone.group_id
            self.matrix.set(self.RESERVED_CELLS + zone.id, zone.y, zone.x, zone.height, zone.width)
        """
    
    def generate(self):
        self.generate_zones()
        self.calculate_zone_neighbours()
        self.generate_groups()
    
    def draw(self, border = False, cell_pics = None):
        if cell_pics == None: cell_pics = self.CELL_PICS
        vertical_border = '|' if border else ''
        def draw_cell(cell):
            if cell < self.RESERVED_CELLS:
                return cell_pics[cell]
            else:
                zone = self.zones[cell - self.RESERVED_CELLS]
                color = '\033[' + str(90 + zone.group_id % 10) + 'm'
                return color + cell_pics[self.RESERVED_CELLS + (cell - self.RESERVED_CELLS) % (len(cell_pics) - self.RESERVED_CELLS)] + '\033[0m'
        def draw_row(row):
            return vertical_border + ''.join(map(draw_cell, row)) + vertical_border
        drawing = '\n'.join(map(draw_row, self.matrix))
        if border:
            horizontal_borders = '+' + ('-' * self.width) + '+'
            drawing = '\n'.join((horizontal_borders, drawing, horizontal_borders))
        return drawing
    
    def __str__(self):
        return self.draw(True)
    
random.seed(23)
area = Area(10, 20)
area.generate()
print(area)