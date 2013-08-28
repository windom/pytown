from plane import *

class Town(InfinitePlane):
    pass

    def draw(self):
        return plane_to_html(self.compacted())
        

print(Town().draw())
