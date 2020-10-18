import numpy

from ._base import BaseTraveltimeGrid
from ._fteik import interp2d, interp3d


class TraveltimeGrid2D(BaseTraveltimeGrid):
    def __init__(self, grid, gridsize, origin, source, vzero):
        super().__init__(grid, gridsize, origin, source, vzero)

    def __call__(self, points):
        t = interp2d(
            self.zaxis,
            self.xaxis,
            self._grid,
            *points,
            *self._source,
            self._vzero,
        )
        
        return t


class TraveltimeGrid3D(BaseTraveltimeGrid):
    def __init__(self, grid, gridsize, origin, source, vzero):
        super().__init__(grid, gridsize, origin, source, vzero)

    def __call__(self, points):
        t = interp3d(
            self.zaxis,
            self.xaxis,
            self.yaxis,
            self._grid,
            *points,
            *self._source,
            self._vzero,
        )
        
        return t

    @property
    def yaxis(self):
        return self._origin[2] + self._gridsize[2] * numpy.arange(self.shape[2])
