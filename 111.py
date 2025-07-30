import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
import os
from tkinter import filedialog, Tk
from openpyxl import Workbook
import xlsxwriter

class YoungModulusAnalyzer:
    def __init__(self):
        self.root = Tk()
        self.root.withdraw()
        self.file_path = None
        self.df = None
        self.sample_name = "11"
        self.width = 128.07  # мм
        self.length = 108.01  # мм
        self.initial_height = 28.25  # мм
        self.area = self.width * self.length  # мм²
        self.q = self.area / (2 * self.initial_height * (self.width + self.length))
        self.results_dir = None

    def load_data(self):
        self.file_path = filedialog.askopenfilename(title="Выберите файл с данными")
        if not self.file_path:
            return False

        try:
            self.results_dir = os.path.join(os.path.dirname(self.file_path), "Результаты")
            os.makedirs(self.results_dir, exist_ok=True)

            self.df = pd.read_csv(self.file_path, sep="\t", header=None, decimal=",")
            self.df = self.df.replace(",", ".", regex=True).astype(float)
            return True
        except Exception as e:
            print(f"Ошибка загрузки данных: {e}")
            return False

    def process_data(self):
        if self.df is None:
            print("Данные не загружены!")
            return False

        k = np.argmax(self.df[0].values > 0)
        M = self.df.values[k:, :4] - self.df.values[k, :4]
        sr = len(M) / M[-1, 3] if M[-1, 3] != 0 else 10

        F = M[:, 0]
        S = M[:, 2]
        T = np.arange(len(F)) / sr

        peaks, _ = find_peaks(S, height=0.5 * np.max(S))
        if len(peaks) < 3:
            print("Недостаточно пиков для анализа (3 минимум)")
            return False

        Defl = S[peaks[0]]
        V = Defl / T[peaks[0]]

        # self.plot_loading_1(T, F, S, peaks, Defl)
        # self.plot_loading_2(S, F, peaks)
        # self.plot_loading_3(S, F, peaks)

        if len(peaks) >= 4:
            cycle_index = 3
        else:
            cycle_index = 2

        cycle_length = peaks[cycle_index] - peaks[cycle_index - 1]
        Start = peaks[cycle_index] - cycle_length + 1
        Finish = peaks[cycle_index]

        F1 = F[Start:Finish + 1]
        S1 = S[Start:Finish + 1]

        w = 2 * int(np.ceil(sr))
        n = len(F1) // w

        Pr = np.zeros(n)
        E1 = np.zeros(n)
        Eps1 = np.zeros(n)

        for i in range(n):
            idx1 = i * w
            idx2 = (i + 1) * w - 1
            if idx2 >= len(F1):
                idx2 = len(F1) - 1

            Pr[i] = (F1[idx1] + F1[idx2]) / 2 / self.area * 1e-6
            delta_F = F1[idx2] - F1[idx1]
            delta_S = S1[idx2] - S1[idx1]

            if delta_S != 0:
                E1[i] = (delta_F / self.area * 1e-6) / (delta_S / self.initial_height)

            Eps1[i] = (S1[idx1] + S1[idx2]) / 2 / self.initial_height

        if len(Pr) > 0:
            Pr = Pr - Pr[0]

        self.plot_results(Pr[3:], E1[3:], Eps1[3:])

        return True

    def plot_loading_1(self, T, F, S, peaks, Defl):
        plt.figure(figsize=(15, 14), dpi=100)
        plt.suptitle(f"{self.sample_name}  Коэффициент формы q={self.q:.4f}", fontsize=14, fontweight='bold')

        plt.subplot(2, 1, 1)
        plt.plot(T, S, 'b')
        plt.ylim(0, np.ceil(Defl + 0.5))
        plt.xlabel('Time, s')
        plt.ylabel('Displacement, mm')
        plt.grid(True)

        ax2 = plt.twinx()
        ax2.plot(T, F, 'r')
        ax2.set_ylabel('Force, N')
        print(peaks)
        plt.subplot(2, 1, 2)
        cycle_len = peaks[1] - peaks[0]
        colors = ['k', 'g', 'r', 'b','p']
        labels = ['Cycle 1', 'Cycle 2', 'Cycle 3', 'Cycle 4','Cycle 5']
        for i in range(min(5, len(peaks))):
            print(i)
            start = peaks[i] - cycle_len + 1 if i > 0 else 0
            end = peaks[i] + cycle_len if i < len(peaks) - 1 else len(S)
            print(start, end)
            plt.grid(True)
            plt.plot(S[start:end], F[start:end], colors[i], label=labels[i])

            plt.show()
        plt.xlabel('Displacement, mm')
        plt.ylabel('Force, N')
        plt.grid(True)
        plt.close()

    def plot_loading_2(self, S, F, peaks):
        plt.figure(figsize=(15, 7), dpi=100)
        cycle_len = peaks[1] - peaks[0]
        colors = ['k', 'g', 'r', 'b']
        labels = ['Cycle 1', 'Cycle 2', 'Cycle 3', 'Cycle 4']
        for i in range(min(4, len(peaks))):
            start = peaks[i] - cycle_len + 1 if i > 0 else 0
            end = peaks[i] + cycle_len if i < len(peaks) - 1 else len(S)
            plt.plot(S[start:end], F[start:end], colors[i], linewidth=2, label=labels[i])

        plt.xlabel('Displacement, mm')
        plt.ylabel('Force, N')
        plt.title(f"{self.sample_name}  q={self.q:.4f}", fontsize=14)
        plt.grid(True)
        plt.close()

    def plot_loading_3(self, S, F, peaks):
        if len(peaks) < 3:
            return
        plt.figure(figsize=(7, 15), dpi=100)
        cycle_len = peaks[1] - peaks[0]
        i = 2
        start = peaks[i] - cycle_len + 1
        end = peaks[i] + cycle_len
        plt.plot(S[start:end], F[start:end], 'k', linewidth=2)
        plt.xlabel('Displacement, mm')
        plt.ylabel('Force, N')
        plt.title(f"{self.sample_name}  q={self.q:.4f}", fontsize=14)
        plt.grid(True)
        plt.close()

    def plot_results(self, Pr, E1, Eps1):
        # Pr = np.abs(Pr)
        Pr = (Pr - Pr[0]) * 1e6
        print(Pr * 1e6)
        print(Pr[int(len(Pr)/2):])


        x = Pr[int(len(Pr)/2):]

        min_x = np.min(x)

        x = x + (-min_x)
        y = E1[int(len(E1)/2):]
        print(x, 'x')
        print(y, 'y')
        plt.figure(figsize=(12, 8), dpi=100)
        plt.subplot(2, 1, 1)
        plt.plot(x, y, 'k', linewidth=2)
        plt.xlabel('Stress, MPa')
        plt.ylabel('Young\'s Modulus, MPa')
        plt.grid(True)

        plt.subplot(2, 1, 2)
        plt.plot(x, Eps1[int(len(Eps1)/2):]* 100, 'k', linewidth=2)
        plt.xlabel('Stress, MPa')
        plt.ylabel('Strain, %')
        plt.grid(True)

        plt.show()
        plt.close()

    def save_to_excel(self, Pr, E1, Eps1):
        Result = pd.DataFrame({
            'Stress, MPa': Pr,
            'Strain, %': Eps1 * 100,
            'Young\'s Modulus, MPa': E1
        })

        def find_nearest(value):
            idx = (np.abs(Eps1 * 100 - value)).argmin()
            return Pr[idx], Eps1[idx] * 100, E1[idx]

        p5, eps5, e5 = find_nearest(5)
        p10, eps10, e10 = find_nearest(10)
        p20, eps20, e20 = find_nearest(20)

        Result2 = pd.DataFrame({
            '%': [5, 10, 20],
            'MPa': [e5, e10, e20]
        })

if __name__ == "__main__":
    analyzer = YoungModulusAnalyzer()
    if analyzer.load_data():
        analyzer.process_data()
