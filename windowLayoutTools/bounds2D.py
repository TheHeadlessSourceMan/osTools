"""
2-dimensional rectangular bounds
"""

class Bounds2D:
    """
    2-dimensional rectangular bounds

    TODO: I have more complete implementation elsewhere
    """
    def __init__(self,
        x:int,
        y:int,
        w:int,
        h:int):
        """ """
        self.x=x
        self.y=y
        self.w=w
        self.h=h

    def overlaps(self,other:"Bounds2D")->bool:
        """
        TODO: Not interested in implementing this right now
        since I've done it before
        """
        return True

    def copy(self)->"Bounds2D":
        """
        return a copy of these bounds
        """
        return Bounds2D(self.x,self.y,self.w,self.h)
    bounds=copy

    def __repr__(self)->str:
        return f"({self.x},{self.y},{self.w},{self.h})"


class Bounds2DPassthrough:
    """
    A base class that has a bounds member,
    and the variables shadow bounds variables

    Every value set goes through the bounds setter
    so it should be easy to trap events.
    """
    def __init__(self,
        x:int,
        y:int,
        w:int,
        h:int):
        """ """
        self._bounds=Bounds2D(x,y,w,h)

    @property
    def bounds(self):
        """
        bounds value
        """
        return self
    @bounds.setter
    def bounds(self,bounds:Bounds2D):
        self._bounds=bounds

    @property
    def x(self)->int:
        """
        x value
        """
        return self._bounds.x
    @x.setter
    def x(self,x:int):
        b=self._bounds.copy()
        b.x=x
        self.bounds=b

    @property
    def y(self)->int:
        """
        y value
        """
        return self._bounds.y
    @y.setter
    def y(self,y:int):
        b=self._bounds.copy()
        b.y=y
        self.bounds=b

    @property
    def w(self)->int:
        """
        width value
        """
        return self._bounds.w
    @w.setter
    def w(self,w:int):
        b=self._bounds.copy()
        b.w=w
        self.bounds=b

    @property
    def h(self)->int:
        """
        height value
        """
        return self._bounds.h
    @h.setter
    def h(self,h:int):
        b=self._bounds.copy()
        b.h=h
        self.bounds=b
