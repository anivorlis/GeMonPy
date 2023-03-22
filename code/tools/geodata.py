from __future__ import annotations
import numpy as np

import os
import pickle

from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class GeophysicalTimeSeriesRaw:
    
    dates: np.ndarray
    geometry_lookuptable: dict[int, int]  # DPID -> INDEX
    geometry_lookuptable_reverse: dict[int, int]  # INDEX -> DPID
    task_dpid_lookup: dict[int, list[int]]  # TASKID -> List[DPID]
    task_dpid_lookup_reverse: dict[int, int]  # DPID -> TASKID
    dpid_abmn_lookup: dict[int, tuple[float, float, float, float]]  # DPID -> (Ax, Bx, Mx, Nx)
    dpid_geometric_factor_lookup: dict[int, float]  # DPID -> G.Factor
    focus_x: np.ndarray
    focus_z: np.ndarray
    voltage: np.ndarray
    current: np.ndarray
    resistance: np.ndarray
    apres: np.ndarray
    chargeability: np.ndarray
    decay: np.ndarray
    acquisition_settings: dict[str, str] = field(init=False, default_factory=dict)

    def extend(self, other) -> None:
        if not isinstance(other, self.__class__):
            print("Data should be of the same type.")
        else:
            self.dates = np.concatenate( (self.dates, other.dates), axis=0)
            self.voltage = np.concatenate( (self.voltage, other.voltage), axis=1)
            self.current = np.concatenate( (self.current, other.current), axis=1)
            self.resistance = np.concatenate( (self.resistance, other.resistance), axis=1)
            self.apres = np.concatenate( (self.apres, other.apres), axis=1)
            self.chargeability = np.concatenate( (self.chargeability, other.chargeability), axis=1)
            self.decay = np.concatenate( (self.decay, other.decay), axis=1)

@dataclass
class GeophysicalTimeSeriesFiltered:
    
    dates: np.ndarray = field(init=False, default_factory=lambda: np.array([]))
    resistance: np.ndarray = field(init=False, default_factory=lambda: np.array([]))
    apres: np.ndarray = field(init=False, default_factory=lambda: np.array([]))
    chargeability: np.ndarray = field(init=False, default_factory=lambda: np.array([]))

@dataclass 
class GeophysicalTimeSeriesResults:

    dates: np.ndarray = field(default_factory=lambda: np.array([]))
    x: np.ndarray = field(default_factory=lambda: np.array([]))
    depth: np.ndarray = field(default_factory=lambda: np.array([]))
    resistivity: np.ndarray = field(default_factory=lambda: np.array([]))
    chargeability: np.ndarray = field(default_factory=lambda: np.array([]))

    def extend(self, dates: np.ndarray, resistivity: np.ndarray, chargeability: np.ndarray) -> None:
        if len(self.dates) == 1:
            self.dates = np.concatenate( (self.dates, dates), axis=0)
            self.resistivity = np.stack( (self.resistivity, resistivity), axis=1)
            self.chargeability = np.stack( (self.chargeability, chargeability), axis=1)
        elif len(dates) == 1:
            self.dates = np.concatenate( (self.dates, dates), axis=0)
            self.resistivity = np.concatenate( (self.resistivity, resistivity.reshape(-1, 1)), axis=1)
            self.chargeability = np.concatenate( (self.chargeability, chargeability.reshape(-1, 1)), axis=1)
        else:
            self.dates = np.concatenate( (self.dates, dates), axis=0)
            self.resistivity = np.concatenate( (self.resistivity, resistivity), axis=1)
            self.chargeability = np.concatenate( (self.chargeability, chargeability), axis=1)
            

@dataclass
class GeophysicalTimeSeries:
    
    raw: GeophysicalTimeSeriesRaw = field(init=False, default=None)
    filtered: GeophysicalTimeSeriesFiltered = field(init=False, default=GeophysicalTimeSeriesFiltered())
    inverted: dict[int, GeophysicalTimeSeriesResults] = field(init=False, default_factory=lambda: defaultdict(GeophysicalTimeSeriesResults))


    def save(self, filename: str):
        if self is not None:
            with open(filename, 'wb') as pf:
                pickle.dump(self, pf)

    @classmethod
    def load(cls, filename: str) -> GeophysicalTimeSeries:
        if os.path.isfile(filename):
            with open(filename, 'rb') as pf:
                return pickle.load(pf)
