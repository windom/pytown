from plane import *

class Town(InfinitePlane):

    def generate(self):
        #self.set_cells(-1,-1,5,5,'x')
        pass
    
    def draw(self):
        return plane_to_html(self.compacted())


town = Town()
town.generate()
print(town.draw())
