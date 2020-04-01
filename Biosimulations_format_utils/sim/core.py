""" Utilities for working with simulations

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-03-22
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

import abc

__all__ = ['SimWriter', 'SimReader']


class SimWriter(abc.ABC):
    pass


class SimReader(abc.ABC):
    pass
