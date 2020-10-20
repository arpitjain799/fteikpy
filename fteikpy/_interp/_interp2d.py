import numpy

from numba import prange

from .._common import jitted


@jitted("f8(f8[:], f8[:], f8[:, :], f8, f8)")
def _interp2d(x, y, v, xq, yq):
    nx, ny = numpy.shape(v)
    nx -= 1
    ny -= 1

    i1 = numpy.nonzero(x <= xq)[0][-1]
    j1 = numpy.nonzero(y <= yq)[0][-1]
    i2 = i1 + 1
    j2 = j1 + 1

    if i1 == nx and j1 != ny:
        x1 = x[i1]
        x2 = 2.0 * x1 - x[-2]
        y1 = y[j1]
        y2 = y[j2]

        v11 = v[i1, j1]
        v21 = 1.0
        v12 = v[i1, j2]
        v22 = 1.0

    elif i1 != nx and j1 == ny:
        x1 = x[i1]
        x2 = x[i1]
        y1 = y[j1]
        y2 = 2.0 * y1 - y[-2]

        v11 = v[i1, j1]
        v21 = v[i2, j1]
        v12 = 1.0
        v22 = 1.0

    elif i1 == nx and j1 == ny:
        x1 = x[i1]
        x2 = 2.0 * x1 - x[-2]
        y1 = y[j1]
        y2 = 2.0 * y1 - y[-2]

        v11 = v[i1, j1]
        v21 = 1.0
        v12 = 1.0
        v22 = 1.0

    else:
        x1 = x[i1]
        x2 = x[i2]
        y1 = y[j1]
        y2 = y[j2]

        v11 = v[i1, j1]
        v21 = v[i2, j1]
        v12 = v[i1, j2]
        v22 = v[i2, j2]

    ax = numpy.array([x2, x1, x2, x1])
    ay = numpy.array([y2, y2, y1, y1])
    av = numpy.array([v11, v21, v12, v22])
    N = numpy.abs((ax - xq) * (ay - yq)) / numpy.abs((x2 - x1) * (y2 - y1))
    vq = numpy.dot(av, N)

    return vq


@jitted(parallel=True)
def interp2d(x, y, v, q):
    if q.ndim == 1:
        return _interp2d(x, y, v, q[0], q[1])

    elif q.ndim == 2:
        nq = len(q)
        out = numpy.empty(nq, dtype=numpy.float64)
        for i in prange(nq):
            out[i] = _interp2d(x, y, v, q[i, 0], q[i, 1])

        return out

    else:
        raise ValueError()
