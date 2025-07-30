import numpy as np
from scipy.interpolate import interp1d

def interpolate_nans(data):
    """Интерполяция NaN значений в массиве"""
    mask = ~np.isnan(data)
    indices = np.arange(len(data))
    interp = interp1d(indices[mask], data[mask], kind='linear', fill_value="extrapolate")
    return interp(indices)

def remove_spikes(data, threshold=0.2):
    """Удаление выбросов из данных"""
    temp_data = data.copy()
    temp_data[np.isinf(temp_data)] = np.nan
    interpolated = np.copy(temp_data)
    nans = np.isnan(interpolated)

    interpolated[nans] = np.interp(
        np.flatnonzero(nans),
        np.flatnonzero(~nans),
        interpolated[~nans])
    return temp_data