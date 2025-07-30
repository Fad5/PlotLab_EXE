import numpy as np
import pandas as pd
from scipy.ndimage import median_filter, gaussian_filter1d
from scipy.interpolate import interp1d
from scipy.signal import find_peaks
import math

class DataProcessor:
    def __init__(self):
        self.df = None
        self.young_modulus_final = None
        self.stress = None
        self.strain = None
        self.time = None
        self.time_ = None
        self.strain_ = None
        self.form_factor = None
        self.locs = []
        self.peaks_upper = []
        self.peaks_lower = []
        self.selected_peaks = []
        self.linear_regions = []
        self.median_filter_size = 50
        self.gaussian_sigma = 2
        self.median_filter_size_dist = 1
        self.gaussian_sigma_dist_value = 0.1

    def load_data(self, file_path):
        try:
            self.df = pd.read_csv(file_path, sep="\t", header=None)
            self.df.replace(",", ".", regex=True, inplace=True)
            self.df = self.df.astype(float)
            return True
        except Exception as e:
            raise Exception(f"Не удалось загрузить файл: {str(e)}")

    def process_data(self, width, length, initial_height):
        try:
            self.form_factor = width / initial_height

            # Данные со столбцов
            force = self.df[0].values  # нагрузка (Н)
            displacement = self.df[2].values  # перемещение (мм)
            self.time_ = self.df[3].values  # время (с)

            # Параметры образца
            area = width * length  # мм²
            area_m2 = area * 1e-6  # м²

            # Расчет деформации и напряжения
            with np.errstate(divide='ignore', invalid='ignore'):
                self.strain_ = displacement / initial_height  # относительная деформация
                stress = (force / area_m2) * 1e-6  # удельное давление (Па)
            
            strain_ = displacement / initial_height  # удельное давление (Па)
            
            # Фильтрация некорректных значений
            valid_mask = (self.strain_ > 0) & (stress > 0) & ~np.isnan(self.strain_) & ~np.isnan(stress)
            
            # Применяем маску ко всем соответствующим массивам
            self.strain = strain_
            self.stress = stress
            self.time = self.time_

            self.strain = self.interpolate_nans(self.strain)
            self.stress = self.interpolate_nans(self.stress)

            # Расчет модуля Юнга (производная σ по ε)
            with np.errstate(divide='ignore', invalid='ignore'):
                young_modulus = np.gradient(self.stress, self.strain)

            young_modulus_interp = self.interpolate_nans(young_modulus)
            
            window_size = min(self.median_filter_size, len(young_modulus_interp)//4 or 1)
            young_modulus_median = median_filter(young_modulus_interp, size=window_size)
            self.young_modulus_final = young_modulus_median
           
            # Находим циклы нагружения
            self.find_loading_cycles()
            self.find_peaks()

            return True
        except Exception as e:
            raise Exception(f"Ошибка при обработке данных: {str(e)}")

    def find_loading_cycles(self):
        """Находит циклы нагружения в данных"""
        peaks, _ = find_peaks(self.df[0].values, prominence=np.std(self.df[0].values)/2)
        self.locs = peaks.tolist()
        
        if len(self.locs) > 5:
            self.locs = self.locs[:5]

    def find_peaks(self):
        """Находит пики в данных"""
        self.peaks_upper, _ = find_peaks(self.strain_, prominence=np.nanstd(self.strain_)/2)
        
        adjusted_peaks = []
        for peak in self.peaks_lower:
            grad = np.gradient(self.strain_)
            rise_point = np.where(grad[peak:] > 0)[0]
            if len(rise_point) > 0:
                adjusted_peaks.append(peak + rise_point[0])

        self.peaks_lower = np.array(adjusted_peaks)
        self.peaks_lower = np.insert(self.peaks_lower, 0, 0)

    def interpolate_nans(self, data):
        mask = ~np.isnan(data)
        indices = np.arange(len(data))
        interp = interp1d(indices[mask], data[mask], kind='linear', fill_value="extrapolate")
        return interp(indices)

    def translate_units(self, data, units):
        return np.array([i * units for i in data])

    def apply_filters(self, data):
        window_size = min(self.median_filter_size_dist, len(data)//4 or 1)
        data_median = median_filter(data, size=window_size)
        return gaussian_filter1d(data_median, sigma=self.gaussian_sigma_dist_value)