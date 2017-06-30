# Licensed under a 3-clause BSD style license - see LICENSE.rst
from pathlib import Path

import healpy as hp
import numpy as np
from astropy.coordinates import SkyCoord
from astropy.wcs import WCS
from skimage import transform as tf

from ..utils import boundaries

__all__ = [
    'HipsTileMeta',
]


class HipsTileMeta:
    """HiPS tile metadata.

    Parameters
    ----------
    order : `int`
        HEALPix order
    ipix : `int`
        HEALPix pixel number
    file_format : {'fits', 'jpg', 'png'}
        File format
    frame : {'icrs', 'galactic', 'ecliptic'}
        Sky coordinate frame
    tile_width : `int`
        Tile width (in pixels)

    Examples
    --------
    >>> from hips.tiles import HipsTileMeta
    >>> tile_meta = HipsTileMeta(order=3, ipix=450, file_format='fits', frame='galactic', tile_width=512)
    >>> tile_meta.skycoord_corners
    <SkyCoord (Galactic): (l, b) in deg
    [( 264.375, -24.62431835), ( 258.75 , -30.        ),
     ( 264.375, -35.68533471), ( 270.   , -30.        )]>
    """

    def __init__(self, order: int, ipix: int, file_format: str, frame: str = 'galactic', tile_width: int = 512) -> None:
        self.order = order
        self.ipix = ipix
        self.file_format = file_format
        self.frame = frame
        self.tile_width = tile_width

    def __eq__(self, other: 'HipsTileMeta') -> bool:
        return (
            self.order == other.order and
            self.ipix == other.ipix and
            self.file_format == other.file_format and
            self.tile_width == other.tile_width
        )

    @property
    def path(self) -> Path:
        """Default path for tile storage (`~pathlib.Path`)."""
        return Path('hips', 'tiles', 'tests', 'data')

    @property
    def filename(self) -> str:
        """Filename for HiPS tile (`str`)."""
        return ''.join(['Npix', str(self.ipix), '.', self.file_format])

    @property
    def full_path(self) -> Path:
        """Full path (folder and filename) (`~pathlib.Path`)"""
        return self.path / self.filename

    @property
    def nside(self) -> int:
        """nside of the HEALPix map"""
        return hp.order2nside(self.order)

    @property
    def dst(self) -> np.ndarray:
        """Destination array for projective transform"""
        return np.array(
            [[self.tile_width - 1, 0],
             [self.tile_width - 1, self.tile_width - 1],
             [0, self.tile_width - 1],
             [0, 0]])

    @property
    def skycoord_corners(self) -> SkyCoord:
        """Corner values for a HiPS tile"""
        theta, phi = boundaries(self.nside, self.ipix)
        if self.frame == 'galactic':
            return SkyCoord(l=phi, b=np.pi / 2 - theta, unit='radian', frame=self.frame)
        else:
            return SkyCoord(ra=phi, dec=np.pi / 2 - theta, unit='radian', frame=self.frame)

    def apply_projection(self, wcs: WCS) -> tf.ProjectiveTransform:
        """Apply projective transformation on a HiPS tile"""
        corners = self.skycoord_corners.to_pixel(wcs)
        src = np.array(corners).T.reshape((4, 2))
        dst = self.dst
        pt = tf.ProjectiveTransform()
        pt.estimate(src, dst)
        return pt
