import numpy
from numba import prange

from .._common import dist2d, jitted, norm2d
from .._interp import interp2d
from ._common import shrink


@jitted(
    "Tuple((f8[:, :], i4))(f8[:], f8[:], f8[:, :], f8[:, :], f8, f8, f8, f8, f8, i4, b1)"
)
def _ray2d(z, x, zgrad, xgrad, zend, xend, zsrc, xsrc, stepsize, max_step, honor_grid):
    """Perform a posteriori 2D ray-tracing."""
    condz = z[0] <= zend <= z[-1]
    condx = x[0] <= xend <= x[-1]
    if not (condz and condx):
        raise ValueError("end point out of bound")

    if honor_grid:
        nz, nx = len(z), len(x)

        i = numpy.searchsorted(z, zend, side="right") - 1
        j = numpy.searchsorted(x, xend, side="right") - 1
        zmin = z[max(i - 1, 0)] if zend == z[i] else z[i]
        xmin = x[max(j - 1, 0)] if xend == x[j] else x[j]
        lower = numpy.array([zmin, xmin])
        upper = numpy.array([z[min(i + 1, nz - 1)], x[min(j + 1, nx - 1)]])

        isrc = numpy.searchsorted(z, zsrc, side="right") - 1
        jsrc = numpy.searchsorted(x, xsrc, side="right") - 1

    count = 1
    pcur = numpy.array([zend, xend], dtype=numpy.float64)
    delta = numpy.empty(2, dtype=numpy.float64)
    ray = numpy.empty((max_step, 2), dtype=numpy.float64)
    ray[0] = pcur.copy()
    while dist2d(zsrc, xsrc, pcur[0], pcur[1]) >= stepsize:
        gz = interp2d(z, x, zgrad, pcur)
        gx = interp2d(z, x, xgrad, pcur)
        gn = norm2d(gz, gx)

        if gn > 0.0:
            gni = 1.0 / gn
        else:
            break

        delta[0] = stepsize * gz * gni
        delta[1] = stepsize * gx * gni

        if honor_grid:
            fac = shrink(pcur, delta, lower, upper)
            pcur -= fac * delta
            pcur[0] = min(max(pcur[0], z[0]), z[-1])
            pcur[1] = min(max(pcur[1], x[0]), x[-1])

            if fac < 1.0:
                # Handle precision issues due to fac
                pcur[0] = numpy.round(pcur[0], 8)
                pcur[1] = numpy.round(pcur[1], 8)

                i = numpy.searchsorted(z, pcur[0], side="right") - 1
                j = numpy.searchsorted(x, pcur[1], side="right") - 1
                lower[0] = z[max(i - 1, 0)] if pcur[0] == z[i] else z[i]
                lower[1] = x[max(j - 1, 0)] if pcur[1] == x[j] else x[j]
                upper[0] = z[i + 1]
                upper[1] = x[j + 1]

                ray[count] = pcur.copy()
                count += 1

                if i == isrc and j == jsrc:
                    break

        else:
            pcur -= delta
            pcur[0] = min(max(pcur[0], z[0]), z[-1])
            pcur[1] = min(max(pcur[1], x[0]), x[-1])

            ray[count] = pcur.copy()
            count += 1

        if count >= max_step:
            raise RuntimeError("maximum number of steps reached")

    ray[count] = numpy.array([zsrc, xsrc], dtype=numpy.float64)

    return ray, count


@jitted(parallel=True)
def _ray2d_vectorized(
    z, x, zgrad, xgrad, zend, xend, zsrc, xsrc, stepsize, max_step, honor_grid=False
):
    """Perform ray-tracing in parallel for different points."""
    n = len(zend)
    rays = numpy.empty((n, max_step, 2), dtype=numpy.float64)
    counts = numpy.empty(n, dtype=numpy.int32)
    for i in prange(n):
        rays[i], counts[i] = _ray2d(
            z,
            x,
            zgrad,
            xgrad,
            zend[i],
            xend[i],
            zsrc,
            xsrc,
            stepsize,
            max_step,
            honor_grid,
        )

    return rays, counts


@jitted
def ray2d(z, x, zgrad, xgrad, p, src, stepsize, max_step, honor_grid=False):
    """Perform ray-tracing."""
    if p.ndim == 1:
        ray, count = _ray2d(
            z,
            x,
            zgrad,
            xgrad,
            p[0],
            p[1],
            src[0],
            src[1],
            stepsize,
            max_step,
            honor_grid,
        )
        return ray[count::-1]

    else:
        rays, counts = _ray2d_vectorized(
            z,
            x,
            zgrad,
            xgrad,
            p[:, 0],
            p[:, 1],
            src[0],
            src[1],
            stepsize,
            max_step,
            honor_grid,
        )
        return [ray[count::-1] for ray, count in zip(rays, counts)]
