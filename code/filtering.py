from dataclasses import dataclass
from abc import ABC, abstractmethod

import numpy as np
import pandas as pd

from scipy.signal import butter, lfilter, freqz
from scipy.signal import medfilt
from scipy.interpolate import interp1d
from scipy.interpolate import InterpolatedUnivariateSpline


class FilteringStrategy(ABC):

    @abstractmethod
    def filter(values):
        pass


@dataclass
class FillMissingData(FilteringStrategy):

    interval: tuple = (3, 'h')
    kind: str = 'cubic'

    def filter(self, dates: np.ndarray, values: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """_summary_

        Args:
            dates (np.ndarray): dates
            values (np.ndarray): values to be filtered [resistance, app.resistivity, chargeability]

        Returns:
            tuple[np.ndarray, np.ndarray]: Return a tuple of interpolated values
        """

        number_of_measurements, number_of_days = values.shape

        # Round the dates and get the missing dates
        dates_rounded = np.array(dates, dtype='datetime64[h]')
        dates_all = np.arange(min(dates_rounded), max(dates_rounded)+1, np.timedelta64(*self.interval))
        dates_mapper = {key: value for value, key in enumerate(dates_all)}
        
        # Interpolations requires numbers instead of 'dates'
        number_of_days_interp = len(dates_all)
        x = [dates_mapper[date_round] for date_round in dates_rounded]
        xnew = np.arange(0, number_of_days_interp)
        
        values_filtered = np.empty([number_of_measurements, number_of_days_interp])
        for meas_id in range(number_of_measurements):
            f = interp1d(x, values[meas_id, :], kind=self.kind)
            values_filtered[meas_id, :] = f(xnew)
        return dates_all, values_filtered
    

@dataclass
class Median(FilteringStrategy):

    window_length: int = 7

    def filter(self, values: np.ndarray):
        """_summary_

        Args:
            values (np.ndarray): values to be filtered [resistance, app.resistivity, chargeability]

        Returns:
            _type_: Return a numpy array with the filtered values
        """

        number_of_measurements, number_of_days = values.shape
        values_filtered = np.empty([number_of_measurements, number_of_days])
        for meas_id in range(number_of_measurements):
            values_filtered[meas_id, :] = medfilt(values[meas_id, :], self.window_length)
        return values_filtered


@dataclass
class Butterworth(FilteringStrategy):
    
    # Filtering parameters.
    order: int = 2
    fs: float = 1 / 3600     # sample rate, Hz
    cutoff: float = 3.667 / 30 / 3600  # desired cutoff frequency of the filter, Hz

    def filter(self, values: np.ndarray) -> np.ndarray:
        """_summary_

        Args:
            values (np.ndarray): values to be filtered [resistance, app.resistivity, chargeability]

        Returns:
            np.ndarray: Return a numpy array with the filtered values
        """

        nyq = 0.5 * self.fs
        normal_cutoff = self.cutoff / nyq
        b, a = butter(self.order, normal_cutoff, btype='low', analog=False)

        number_of_measurements, number_of_days = values.shape
        values_filtered_forward = np.empty([number_of_measurements, number_of_days])
        values_filtered_reverse = np.empty([number_of_measurements, number_of_days])
        for meas_id in range(number_of_measurements):
            values_filtered_forward[meas_id, :] = lfilter(b, a, values[meas_id, :])
            values_filtered_reverse[meas_id, :] = lfilter(b, a, values[meas_id, ::-1])
        values_filtered_reverse = values_filtered_reverse[:, ::-1]
        values_filtered = (values_filtered_forward+values_filtered_reverse) / 2
        values_filtered[:, :20] = values_filtered_reverse[:, :20]
        values_filtered[:, -20:] = values_filtered_reverse[:, -20:]
        return values_filtered

    def frequency_response(self) -> np.ndarray:
        b, a = self.butter_lowpass(self.cutoff, self.fs, self.order)
        w, h = freqz(b, a, worN=8000)

        xf, yf = 0.5*self.fs*w/np.pi, np.abs(h)
        return np.array(xf, yf)
    
