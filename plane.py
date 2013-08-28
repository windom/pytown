class Plane:
    def get_cell(self, x, y):
        return None

    def set_cell(self, x, y, value):
        pass

    def get_cells(self, x, y, width, height):
        for cx in range(x, x + width):
            for cy in range(y, y + height):
                yield (cx, cy, self.get_cell(cx, cy))
    
    def set_cells(self, x, y, width, height, value):
        for cx in range(x, x + width):
            for cy in range(y, y + height):
                self.set_cell(cx, cy, value)

    class ColumnWrapper:
        def __init__(self, x, get_handler, set_handler):
            self.x = x
            self.get_handler = get_handler
            self.set_handler = set_handler

        def __getitem__(self, key):
            return self.get_handler(self.x, key)

        def __setitem__(self, key, value):
            self.set_handler(self.x, key, value)

    def __getitem__(self, x):
        return self.ColumnWrapper(x, self.get_cell, self.set_cell)


class FixedPlane(Plane):
    def __init__(self, width, height, empty_cell=None):
        self.width = width
        self.height = height
        self.empty_cell = empty_cell
        self.cell_tab = [[empty_cell for y in range(height)] for x in range(width)]

    def get_cell(self, x, y):
        return self.cell_tab[x][y]

    def set_cell(self, x, y, value):
        self.cell_tab[x][y] = value

    def get_cells(self, x=0, y=0, width=None, height=None):
        if width == None:
            width = self.width
        if height == None:
            height = self.height
        if width <= 0 or height <=0:
            return
        return super().get_cells(x, y, width, height)
        
    def get_extents(self, x=0, y=0, width=None, height=None):
        if width == None:
            width = self.width
        if height == None:
            height = self.height
        if width <= 0 or height <=0:
            return
        min_x = self.width
        min_y = self.height
        max_x = -1
        max_y = -1
        for cx, cy, cc in self.get_cells(x, y, width, height):
            if cc != self.empty_cell:
                min_x = min(min_x, cx)
                min_y = min(min_y, cy)
                max_x = max(max_x, cx)
                max_y = max(max_y, cy)
        return (min_x, min_y, max_x, max_y)


class InfinitePlane(Plane):
    def __init__(self, sector_width=10, sector_height=10, empty_cell=None):
        self.sector_width = sector_width
        self.sector_height = sector_height
        self.empty_cell = empty_cell
        self.sector_map = {}

    def get_cell(self, x, y):
        sx, sy, ix, iy = self.to_icoords(x, y)
        sector = self.get_sector(sx, sy)
        if sector:
            return sector[ix][iy]
        else:
            return self.empty_cell

    def set_cell(self, x, y, value):
        sx, sy, ix, iy = self.to_icoords(x, y)
        sector = self.get_sector(sx, sy, True)
        sector[ix][iy] = value

    def get_sector(self, sx, sy, create=False):
        sector = self.sector_map.get((sx, sy))
        if (not sector) and create:
            sector = FixedPlane(self.sector_width, self.sector_height, self.empty_cell)
            self.sector_map[(sx, sy)] = sector
        return sector

    def to_icoords(self, x, y):
        return (x // self.sector_width,
                y // self.sector_height,
                x % self.sector_width,
                y % self.sector_height)

    def from_icoords(self, sx, sy, ix, iy):
        return (sx * self.sector_width + ix,
                sy * self.sector_height + iy)
    
    def get_extents(self):
        min_sx = min([x for x, y in self.sector_map.keys()])
        min_sy = min([y for x, y in self.sector_map.keys()])
        max_sx = max([x for x, y in self.sector_map.keys()])
        max_sy = max([y for x, y in self.sector_map.keys()])
        
        min_ix = min_iy = max_ix = max_iy = None
        
        for sector in [self.get_sector(sx, min_sy) for sx in range(min_sx, max_sx+1)]:
            if sector:
                _, s_min_iy, _, _ = sector.get_extents()
                min_iy = min(min_iy, s_min_iy) if min_iy != None else s_min_iy

        for sector in [self.get_sector(sx, max_sy) for sx in range(min_sx, max_sx+1)]:
            if sector:
                _, _, _, s_max_iy = sector.get_extents()
                max_iy = max(max_iy, s_max_iy) if max_iy != None else s_max_iy            
    
        for sector in [self.get_sector(min_sx, sy) for sy in range(min_sy, max_sy+1)]:
            if sector:
                s_min_ix, _, _, _ = sector.get_extents()
                min_ix = min(min_ix, s_min_ix) if min_ix != None else s_min_ix
    
        for sector in [self.get_sector(max_sx, sy) for sy in range(min_sy, max_sy+1)]:
            if sector:
                _, _, s_max_ix, _ = sector.get_extents()
                max_ix = max(max_ix, s_max_ix) if max_ix != None else s_max_ix
    
        min_x, min_y = self.from_icoords(min_sx, min_sy, min_ix, min_iy)
        max_x, max_y = self.from_icoords(max_sx, max_sy, max_ix, max_iy)
        
        return (min_x, min_y, max_x, max_y)
    
    def compacted(self):
        min_x, min_y, max_x, max_y = self.get_extents()       
        compact_plane = FixedPlane(max_x - min_x + 1, max_y - min_y + 1, self.empty_cell)
        for x, y, c in self.get_cells(min_x, min_y, compact_plane.width, compact_plane.height):
            compact_plane[x - min_x][y - min_y] = c
        return compact_plane


def plane_to_html(plane):
    def render_cell(cell):
        return str(cell) if cell != None else ''        
    html = []
    html += ("""
        <style>
            table {
                border-collapse:collapse;
            }
            td {
                font-family: Monospace;
                font-size: 9px;
                border: 1px solid lightgrey;
            }
            div {
                width: 20px;
                height: 20px;
                line-height: 20px;
                text-align: center;
            }
        </style>
    """)
    html += '<table cellspacing="0" cellpadding="0">'
    for y in range(plane.height):
        html += '<tr>'
        html += ['<td><div>' + 
                 render_cell(plane.get_cell(x, y)) + 
                 '</div></td>' for x in range(plane.width)]
        html += '</tr>'
    html += '</table>'
    return ''.join(html)

    
    