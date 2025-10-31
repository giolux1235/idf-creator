"""Curve fitting utilities for mapping manufacturer data to IDF curves."""

from typing import List, Tuple
import numpy as np


def fit_quadratic(x: List[float], y: List[float]) -> List[float]:
    """Fit y = a + b*x + c*x^2. Returns [a,b,c]."""
    X = np.vstack([np.ones(len(x)), x, np.square(x)]).T
    coeffs, *_ = np.linalg.lstsq(X, np.array(y), rcond=None)
    return coeffs.tolist()


def fit_biquadratic(x: List[float], y: List[float], z: List[float]) -> List[float]:
    """Fit f(x,z) = a + b*x + c*x^2 + d*z + e*z^2 + f*x*z. Returns [a,b,c,d,e,f]."""
    X = np.vstack([
        np.ones(len(x)),
        x,
        np.square(x),
        z,
        np.square(z),
        np.multiply(x, z)
    ]).T
    coeffs, *_ = np.linalg.lstsq(X, np.array(y), rcond=None)
    return coeffs.tolist()







