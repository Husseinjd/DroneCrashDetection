class Segment():
    """Segment instance
    """
    def __init__(self,x0,y0,x1,y1,segmentname=''):
         self.x0 = x0 
         self.x1 = x1
         self.y0 = y0
         self.y1 = y1
         self.segmentname = segmentname #used for description later

    def points(self):
        return (self.x0,self.y0,self.x1,self.y1)