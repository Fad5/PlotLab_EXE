import os
import numpy as np
import pandas as pd
from PyQt5.QtWidgets import QAction 
import math
from docxtpl import DocxTemplate, InlineImage
from docx.shared import Cm
import datetime
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QFileDialog, QTabWidget,
                             QGroupBox, QMessageBox, QCheckBox, QComboBox, QSpinBox, QDoubleSpinBox,
                             QGridLayout, QDialog, QRadioButton,QButtonGroup)
from PyQt5.QtGui import QIcon, QPalette, QColor
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QShortcut
from PyQt5.QtGui import QKeySequence
from models.data_processor import DataProcessor
from models.report_generator import VibraTableReportGenerator
from views.custom_widgets import CustomNavigationToolbar
from scipy.ndimage import median_filter, gaussian_filter1d
from scipy.signal import find_peaks
from pathlib import Path
from utils.helpers import interpolate_nans
from views.settings_window import SettingsDialog



class YoungModulusApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Plotlab")
        self.setGeometry(100, 100, 1400, 900)
        self.setWindowIcon(QIcon('Logo.png'))
        
        self.processor = DataProcessor()
        self.report_generator = VibraTableReportGenerator()
        
        # UI settings
        self.fontsize = 10
        self.linewidth = 2
        self.fontweight = 'bold'
        self.show_peaks = False
        self.setup_hotkeys()
        self.radio_button_line_modul_y  = False
        self.auto_open_file = False
        self.is_title = True
        self.is_filling = True

        # Основные переменные
        self.file_path = ""
        self.selected_template = "ДС"
        self.save_C_stat = False
        self.df = None
        self.young_modulus_final = None
        self.stress = None
        self.strain = None
        self.time = None
        self.time_ = None
        self.strain_ = None
        self.pic_data = self.strain_
        self.form_factor = None
        self.locs = []
        self.fontsize = 10
        self.linewidth = 2
        self.fontweight = 'bold'
        self.show_peaks = False
        self.median_filter_size = 50
        self.gaussian_sigma = 2
        self.median_filter_size_dist = 1
        self.gaussian_sigma_dist_value = 0.1
        self.figure_width = 16
        self.figure_height = 11
        self.cycle_figures = []
        
        self.initUI()
        self.apply_styles()


    def open_settings_dialog(self):
        dialog = SettingsDialog(self, main_window=self)
        dialog.exec_()  # Модальное окно

    def setup_hotkeys(self):
        # Ctrl + → (Следующая вкладка)
        next_tab_shortcut = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_Right), self)
        next_tab_shortcut.activated.connect(self.next_tab)
        
        # Ctrl + ← (Предыдущая вкладка)
        prev_tab_shortcut = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_Left), self)
        prev_tab_shortcut.activated.connect(self.prev_tab)
    
    def next_tab(self):
        current = self.tabs.currentIndex()
        if current < self.tabs.count() - 1:
            self.tabs.setCurrentIndex(current + 1)
    
    def prev_tab(self):
        current = self.tabs.currentIndex()
        if current > 0:
            self.tabs.setCurrentIndex(current - 1)

    def initUI(self):
        # Создаем строку меню
        menubar = self.menuBar()

        # 1. Меню "Файл"
        file_menu = menubar.addMenu('Файл')

        # Действие "Открыть"
        open_action = QAction(QIcon('folder.png'), 'Открыть', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.browse_file)
        file_menu.addAction(open_action)

        # Действие "Сохранить"
        save_action = QAction(QIcon('save.png'), 'Сохранить', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_plots)
        file_menu.addAction(save_action)

        # Разделитель
        file_menu.addSeparator()

        # Действие "Выход"
        exit_action = QAction('Выход', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 2. Пункт "Настройки" (не меню, а действие)
        settings_action = QAction('Настройки', self)
        settings_action.triggered.connect(self.open_settings_dialog)
        menubar.addAction(settings_action)  # Добавляем прямо в menubar

        # 3. Меню "Справка"
        help_menu = menubar.addMenu('Справка')

        # Действие "О программе"
        about_action = QAction('О программе', self)
        help_menu.addAction(about_action)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)

        # Панель управления
        control_group = QGroupBox("Параметры анализа")
        control_layout = QHBoxLayout()
        control_group.setLayout(control_layout)
        
        # Элементы управления файлом
        self.file_label = QLabel("Файл данных:")
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setReadOnly(True)
        self.browse_button = QPushButton("Обзор...")
        self.browse_button.setIcon(QIcon('folder.png'))
        self.browse_button.clicked.connect(self.browse_file)

        # Группа управления пиками
        peaks_group = QGroupBox("Управление пиками")
        peaks_layout = QVBoxLayout()
        peaks_group.setLayout(peaks_layout)
        
        self.peak_combo_upper = QComboBox()
        self.peak_combo_lower = QComboBox()
        self.peak_combo_upper.currentIndexChanged.connect(self.on_peak_selected)
        self.peak_combo_lower.currentIndexChanged.connect(self.on_peak_selected)
        
        self.plot_selected_peak_button = QPushButton("Отрисовать выбранный пик")
        self.plot_selected_peak_button.clicked.connect(self.plot_selected_peak)

        self.plot_selected_peak_button.setEnabled(False)
        
        self.peaks_checkbox = QCheckBox("Показывать пики")
        self.peaks_checkbox.setChecked(False)
        self.peaks_checkbox.stateChanged.connect(self.toggle_peaks)
        
        peaks_layout.addWidget(QLabel("Верхние пики:"))
        peaks_layout.addWidget(self.peak_combo_upper)
        peaks_layout.addWidget(QLabel("Нижние пики:"))
        peaks_layout.addWidget(self.peak_combo_lower)
        peaks_layout.addWidget(self.plot_selected_peak_button)
        peaks_layout.addWidget(self.peaks_checkbox)

        # Параметры образца
        sample_group = QGroupBox("Геометрия образца")
        sample_layout = QGridLayout()
        sample_group.setLayout(sample_layout)

        # Параметры образца
        sample_group = QGroupBox("Геометрия образца")
        sample_layout = QGridLayout()
        sample_group.setLayout(sample_layout)

        # Добавляем переключатель типа образца в первую строку
        self.sample_type = QComboBox()
        self.sample_type.addItems(["Прямоугольный", "Круглый"])
        self.sample_type.currentIndexChanged.connect(self.update_sample_fields)

        sample_layout.addWidget(QLabel("Тип образца:"), 0, 0)
        sample_layout.addWidget(self.sample_type, 0, 1)

        # Поля для прямоугольного образца (как у вас)
        self.width_label = QLabel("Ширина (мм):")
        self.width_edit = QLineEdit("100.54")
        self.length_label = QLabel("Длина (мм):")
        self.length_edit = QLineEdit("100.83")
        self.height_label = QLabel("Высота (мм):")
        self.height_edit = QLineEdit("28.83")

        # Поля для круглого образца (скрытые изначально)
        self.diameter_label = QLabel("Диаметр (мм):")
        self.diameter_edit = QLineEdit("100.00")
        self.diameter_label.hide()
        self.diameter_edit.hide()

        # Общие поля (как у вас)
        self.mass_label = QLabel("Масса:")
        self.mass_sample = QLineEdit("101.2")
        self.num_protocol_label = QLabel("Номер протокола:")
        self.num_protocol = QLineEdit("1")
        self.name_label = QLabel("Название образца:")
        self.name_sample = QLineEdit("ПБМ")

        # Расположение элементов с учетом вашей сетки
        sample_layout.addWidget(self.name_label, 1, 0)
        sample_layout.addWidget(self.name_sample, 1, 1)

        # Для прямоугольного образца
        sample_layout.addWidget(self.width_label, 1, 2)
        sample_layout.addWidget(self.width_edit, 1, 3)
        sample_layout.addWidget(self.length_label, 2, 0)
        sample_layout.addWidget(self.length_edit, 2, 1)
        sample_layout.addWidget(self.height_label, 2, 2)
        sample_layout.addWidget(self.height_edit, 2, 3)

        # Для круглого образца (те же позиции)
        sample_layout.addWidget(self.diameter_label, 1, 2)
        sample_layout.addWidget(self.diameter_edit, 1, 3)
        # Высота остается на том же месте

        sample_layout.addWidget(self.num_protocol_label, 3, 0)
        sample_layout.addWidget(self.num_protocol, 3, 1)
        sample_layout.addWidget(self.mass_label, 3, 2)
        sample_layout.addWidget(self.mass_sample, 3, 3)

        # Кнопки управления
        button_group = QGroupBox("Действия")
        button_layout = QVBoxLayout()
        button_group.setLayout(button_layout)
        control_layout.setSpacing(5)
        control_layout.setContentsMargins(1, 1, 1, 1)
        
        self.plot_button = QPushButton("Построить графики")
        self.plot_button.setIcon(QIcon('chart.png'))
        self.plot_button.clicked.connect(self.plot_data)

        self.save_button = QPushButton("Сохранить графики")
        self.save_button.setIcon(QIcon('save.png'))
        self.save_button.clicked.connect(self.save_plots)
        self.save_button.setEnabled(False)
        
        button_layout.addWidget(self.plot_button)
        button_layout.addWidget(self.save_button)


        # Добавление элементов на панель управления
        control_layout.addWidget(self.file_label)
        control_layout.addWidget(self.file_path_edit)
        control_layout.addWidget(self.browse_button)

        control_layout.addWidget(button_group)
        control_layout.addWidget(sample_group)
        control_layout.addWidget(peaks_group)
        
        # Создание вкладок
        self.tabs = QTabWidget()
        self.settings_tab = QWidget()
 
        # Создаем фигуры и холсты
        self.create_figures()
        
        # Добавление вкладок в главный layout
        main_layout.addWidget(control_group)
        main_layout.addWidget(self.tabs)

    def update_sample_fields(self):
        """Переключает видимость полей в зависимости от типа образца"""
        if self.sample_type.currentText() == "Прямоугольный":
            self.width_label.show()
            self.width_edit.show()
            self.length_label.show()
            self.length_edit.show()
            self.height_label.show()
            self.height_edit.show()
            
            self.diameter_label.hide()
            self.diameter_edit.hide()
        else:
            self.width_label.hide()
            self.width_edit.hide()
            self.length_label.hide()
            self.length_edit.hide()
            
            self.diameter_label.show()
            self.diameter_edit.show()
            # Высота остается видимой для обоих типов

    def load_templates(self):
        """Загрузка доступных шаблонов из папки"""
        templates_folder = "templates"  # Папка с шаблонами
        template_files = [f for f in os.listdir(templates_folder) if f.endswith('.tpl')]
        
        self.select_template.clear()
        self.select_template.addItem("Стандартный шаблон")
        for template in template_files:
            self.select_template.addItem(template.replace('.tpl', ''))

        
    def create_figures(self):
        """Создает фигуры с текущими размерами и добавляет тулбары"""
        # Удаляем старые вкладки (кроме настроек)
        for i in range(self.tabs.count()-1, -1, -1):
            if self.tabs.widget(i) != self.settings_tab:
                self.tabs.removeTab(i)

        # Создаем новые фигуры и холсты
        self.figure1 = Figure(figsize=(self.figure_width, self.figure_height))
        self.canvas1 = FigureCanvas(self.figure1)
        self.toolbar1 = CustomNavigationToolbar(self.canvas1, self)

        self.figure3 = Figure(figsize=(self.figure_width, self.figure_height))
        self.canvas3 = FigureCanvas(self.figure3)
        self.toolbar3 = CustomNavigationToolbar(self.canvas3, self)

        self.figure4 = Figure(figsize=(self.figure_width, self.figure_height))
        self.canvas4 = FigureCanvas(self.figure4)
        self.toolbar4 = CustomNavigationToolbar(self.canvas4, self)

        self.figure6 = Figure(figsize=(self.figure_width, self.figure_height))
        self.canvas6 = FigureCanvas(self.figure6)
        self.toolbar6 = CustomNavigationToolbar(self.canvas6, self)

        # Создаем контейнеры для вкладок
        self.tabs.addTab(self.create_tab_container(self.canvas1, self.toolbar1), "Основные графики")
        self.tabs.addTab(self.create_tab_container(self.canvas6, self.toolbar6), "Нагрузочные циклы")
        self.tabs.addTab(self.create_tab_container(self.canvas3, self.toolbar3), "Модуль упругости")
        self.tabs.addTab(self.create_tab_container(self.canvas4, self.toolbar4), "Полные")

        if self.df is not None:
            self.plot_data()    

    def create_tab_container(self, canvas, toolbar):
        """Создает контейнер для вкладки с графиком"""
        tab = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(toolbar)
        layout.addWidget(canvas)
        tab.setLayout(layout)
        return tab
    
    def on_peak_selected(self):
        """Обработчик выбора пика в выпадающем списке"""
        pass  

    def browse_file(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, 
            "Открыть файл данных", 
            "", 
            "Текстовые файлы (*.txt);;Все файлы (*)"
        )
        if file_name:
            self.file_path = file_name
            self.file_path_edit.setText(file_name)
            
    def load_data(self):
        try:
            self.df = pd.read_csv(self.file_path, sep="\t", header=None)
            self.df.replace(",", ".", regex=True, inplace=True)
            self.df = self.df.astype(float)
            return True
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Ошибка", 
                f"Не удалось загрузить файл:\n{str(e)}"
            )
            return False
            
    def save_exel(self, E1, Eps1, Pr, file_name):
        """
        Сохраняет данные в Excel файл
        :param E1: Удельная нагрузка (МПа)
        :param Eps1: Относительная деформация (%)
        :param Pr: Модуль упругости (Estat, МПа)
        """
        try:
            # Создаем DataFrame с данными
            data = {
                'Удельная нагрузка, МПа': E1,
                'Отн. деф-я, %': Eps1,
                'Estat, МПа': Pr
            }
            df = pd.DataFrame(data)
            
            # Задаем формат чисел (2 знака после запятой)
            df = df
            
            if file_name:
                # Добавляем расширение, если его нет
                if not file_name.endswith('.xlsx'):
                    file_name += '.xlsx'
                
                # Сохраняем в Excel
                df.to_excel(file_name, index=False)
                if self.auto_open_file:
                    # Открываем файл после сохранения
                    if os.path.exists(file_name):
                        os.startfile(file_name)
                        return True
            return False
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл:\n{str(e)}")
            return False
            
        
    def toggle_peaks(self, state):
        """Переключает отображение пиков на графиках"""
        self.show_peaks = state == Qt.Checked
        if self.df is not None:  # Если данные уже загружены, перерисовываем графики
            self.plot_data()
        
    def plot_selected_peak(self):
        """Отрисовывает график с выбранным пиком"""
        self.tabs.setCurrentIndex(0)
        if not hasattr(self, 'stress') or not hasattr(self, 'strain'):
            return
            
        # Получаем выбранные пики
        upper_idx = self.peak_combo_upper.currentIndex()
        lower_idx = self.peak_combo_lower.currentIndex()

        # Очищаем предыдущие графики
        self.figure1.clear()
        ax1 = self.figure1.add_subplot(211)
        ax3 = self.figure1.add_subplot(212)
        
        l =  self.peaks_lower
        u =  self.peaks_upper

        uu = u[upper_idx]
        ll = l[lower_idx]

        if lower_idx == -1:
            ll = None
        
        if self.form_factor is not None:
            q_str = f"{self.form_factor:.2f}"
        else:
            q_str = "—"
        # Отрисовываем основной график
        if self.is_title:
            ax1.set_title(f'{self.name_sample.text()} Коэффициент формы q = {self.form_factor:.2f}', fontsize=self.fontsize, fontweight=self.fontweight)
        ax1.plot(self.stress[ll:uu], self.strain_pocent[ll:uu], 'k-', linewidth=self.linewidth, label="Данные")
        
        # Отрисовываем выбранные пики
        if self.show_peaks:
            ax1.legend()
            if upper_idx >= 0 and upper_idx < len(self.peaks_upper):
                peak = self.peaks_upper[upper_idx]
                ax1.plot(self.stress[peak], self.strain_pocent[peak], 'ro', 
                       label=f"Верхний пик {upper_idx+1}")
            
            if lower_idx >= 0 and lower_idx < len(self.peaks_lower):
                peak = self.peaks_lower[lower_idx]
                ax1.plot(self.stress[peak], self.strain_pocent[peak], 'go', 
                       label=f"Нижний пик {lower_idx+1}")
        
        # Настраиваем график
        ax1.set_xlabel('Удельное давление, МПа', fontsize=self.fontsize, fontweight=self.fontweight)
        ax1.set_ylabel('Относительная деформация, %', fontsize=self.fontsize, fontweight=self.fontweight)
        
        ax1.grid(True)
        

        ax3.plot(self.stress[ll:uu], self.young_modulus_final[ll:uu], 'k-', linewidth=self.linewidth, label="Данные")
        # Отрисовываем выбранные пики
        if self.show_peaks:
            ax3.legend()
            if upper_idx >= 0 and upper_idx < len(self.peaks_upper):
                peak = self.peaks_upper[upper_idx]
                ax3.plot(self.stress[peak], self.young_modulus_final[peak], 'ro', 
                       label=f"Верхний пик {upper_idx+1}")

            if lower_idx >= 0 and lower_idx < len(self.peaks_lower):
                peak = self.peaks_lower[lower_idx]
                ax3.plot(self.stress[peak], self.young_modulus_final[peak], 'go', 
                       label=f"Нижний пик {lower_idx+1}")
        
        ax3.set_ylabel('Модуль упругости, МПа', fontsize=self.fontsize, fontweight=self.fontweight)
        ax3.set_xlabel('Удельное давление, МПа', fontsize=self.fontsize, fontweight=self.fontweight)
        ax3.grid(True)

        self.canvas1.draw()


    def find_coordinat(self, target_values, stress, strain):
            stress_array = np.array(strain)
            for target in target_values:
                inx = np.where(np.abs(stress_array - target) < 1)[0]  # Ищем близкие к target (±0.1)
                if len(inx) > 0:
                    inx_50 = inx[0]
                    y_7 = stress[inx_50]
                    x_7 = strain[inx_50]
                    return y_7, x_7


    def save_plots(self):
        tamplate = ''
        index_save_tamplate = self.selected_template
        ABS_PATH = Path(__file__).parent
        list_cycle = []
        if index_save_tamplate == 'ДС':
            tamplate = 'VibraTable_Template_DS.docx'
        else:
            tamplate = 'VibraTable_Template_NIISF.docx'
            self.selected_template = 'НИИСФ'
        template = ABS_PATH / tamplate
        doc = DocxTemplate(template)
        if not hasattr(self, 'figure1') or not self.file_path:
            return
        
        options = QFileDialog.Options()
        save_dir = QFileDialog.getExistingDirectory(
            self,
            "Выберите папку для сохранения графиков",
            "",
            options=options
        )

        

        
        if not save_dir:
            return
            
        # Создаем подпапку с именем файла
        file_name = os.path.splitext(os.path.basename(self.file_path))[0]
        save_path = os.path.join(save_dir, f"Результаты_{file_name}")
        os.makedirs(save_path, exist_ok=True) 
        if self.save_C_stat:
            self.C_stat(save_path)          
        # Сохраняем все графики
        fig_size = (14, 9)
        self.figure1.set_size_inches(fig_size)
        self.figure1.savefig(os.path.join(save_path, "Основные_графики.png"), dpi=300, bbox_inches='tight')
        self.figure6.set_size_inches(fig_size)
        self.figure6.savefig(os.path.join(save_path, "Циклы_нагружения.png"), dpi=300, bbox_inches='tight')
        self.figure3.set_size_inches(fig_size)
        self.figure3.savefig(os.path.join(save_path, "Модуль_упругости.png"), dpi=300, bbox_inches='tight')
        self.figure4.set_size_inches(fig_size)
        self.figure4.savefig(os.path.join(save_path, "Нагруж.png"), dpi=300, bbox_inches='tight')     
        # Сохранение в word файл   
        if hasattr(self, 'cycle_figures'):
            for i, fig in enumerate(self.cycle_figures, 1):

                cycle_path = os.path.join(save_path, f"Цикл_{i}.png")
                fig.set_size_inches(fig_size)
                fig.savefig(cycle_path, dpi=300, bbox_inches='tight')
                list_cycle.append({'image':InlineImage(doc, cycle_path, width=Cm(20)), 'count':i})  # Уменьшил ширину для лучшего размещения

                        
        def transform_date(date):
            months = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
                'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']
            year,month,day = date.split('-')
            return f'«{day}» {months[int(month) - 1]} {year}'
                
        def number_protocol(date):
            year,month,day = date.split('-')
            if index_save_tamplate == 'ДС':
                return f'ДС-0{month}-{year}-'
            else:       
                return f'0{month}-{year}-'
            
        current_date = datetime.datetime.now().strftime('%Y-%m-%d')
        def vibraTable_DocGenerator(name,
                            a,
                            b,
                            h,
                            mass,
                            protocol,
                            savedir):
            test_date = datetime.datetime.now().strftime('%Y-%m-%d')
            name_pic = ['Модуль_упругости', 'Основные_графики', 'Нагруж']
            context = {
                'name':name,
                'test_date': transform_date(test_date),
                'a':a,
                'b':b,
                'h':h,
                'mass': mass,
                'loads':name_pic,
                'protocol': protocol,
                'num_protocol': (number_protocol(current_date)),
                'load_pic' : InlineImage(doc, savedir + f'/Модуль_упругости.png', width=Cm(20)),  #, height=Cm(10)
                'cycles_pic': InlineImage(doc, savedir + f'/Нагруж.png', width=Cm(20)),  #, height=Cm(10)
                'elastic_pic': InlineImage(doc, savedir + f'/Основные_графики.png', width=Cm(20)),
                'list_cyrcle' : list_cycle,           
            }           
            doc.render(context=context)
            if protocol != None:
                doc.save(f'{savedir}/ДС-003-{test_date[:4]}-В{protocol}.docx')
                if self.auto_open_file:
                    os.startfile(f'{savedir}/ДС-003-{test_date[:4]}-В{protocol}.docx')
            else:
                doc.save(f'{savedir}/ДС-003-{test_date[:4]}-В_{name}.docx')         
        name = self.name_sample.text()
        a = float(self.width_edit.text().replace(',', '.'))
        b = float(self.length_edit.text().replace(',', '.'))
        h = float(self.height_edit.text().replace(',', '.'))
        mass = float(self.mass_sample.text().replace(',', '.'))
        protocol = self.num_protocol.text()     
        savedir = save_path         

        self.save_exel(self.E1, self.Eps1,self.Pr, (savedir + '/' + file_name))
        vibraTable_DocGenerator(name, a, b, h, mass,protocol, savedir)

        # Сообщение об успешном сохранении
        QMessageBox.information(
            self,
            "Сохранение завершено",
            f"Все графики успешно сохранены в папку:\n{save_path}"
        )


    def process_data_(self):
        if self.df is None:
            print("Данные не загружены!")
            return False
        
        width_edit = self.width_edit.text()
        length_edit = self.length_edit.text()
        height_edit = self.height_edit.text()

        width = float(width_edit.replace(',', '.'))
        length = float(length_edit.replace(',', '.'))
        initial_height = float(height_edit.replace(',', '.'))



        area = float(width) * float(length)

        k = np.argmax(self.df[0].values > 0)
        M = self.df.values[k:, :4] - self.df.values[k, :4]
        sr = len(M) / M[-1, 3] if M[-1, 3] != 0 else 10

        print(sr, 'Частота дискедитации')

        F = M[:, 0]
        S = M[:, 2]
        T = np.arange(len(F)) / sr

        peaks, _ = find_peaks(S, height=0.5 * np.max(S))
        if len(peaks) < 3:
            print("Недостаточно пиков для анализа (3 минимум)")
            return False

        Defl = S[peaks[0]]
        V = Defl / T[peaks[0]]

        if len(peaks) >= 4:
            cycle_index = 3
        else:
            cycle_index = 2

        cycle_index = 1

        cycle_length = peaks[cycle_index] - peaks[cycle_index - 1]
        Start = peaks[cycle_index] - cycle_length + 1
        Finish = peaks[cycle_index]

        print(Start, 'Start')
        print(Finish, 'Finish')

        F1 = F[Start:Finish + 1]
        S1 = S[Start:Finish + 1]

        w = int(np.ceil(sr * 2))
        n = len(F1) // w
        
        print(w, 'Ширина окна')
        print(n, 'Количество циклов')

        Pr = np.zeros(n)
        E1 = np.zeros(n)
        Eps1 = np.zeros(n)

        for i in range(n):
            idx1 = i * w
            idx2 = (i + 1) * w - 1
            if idx2 >= len(F1):
                idx2 = len(F1) - 1
            Pr[i] = (F1[idx1] + F1[idx2]) / 2 / area * 1e-6
            delta_F = F1[idx2] - F1[idx1]
            delta_S = S1[idx2] - S1[idx1]
            if delta_S != 0:
                E1[i] = (delta_F / area * 1e-6) / (delta_S / initial_height)
            Eps1[i] = (S1[idx1] + S1[idx2]) / 2 / initial_height

        if len(Pr) > 0:
            Pr = Pr - Pr[0]

        Pr, E1, Eps1 = Pr[3:], E1[3:], Eps1[3:]
        f = 0
        self.Eps1 = Eps1[int(len(Eps1)/2)+f:] 
        self.E1 = E1[int(len(E1)/2)+f:]  
        self.Pr = Pr[int(len(Pr)/2)+f:] 

        if self.Pr.size > 2:
            min_Pr = np.min(self.Pr)
            self.Eps1 = self.Eps1 - self.Eps1[0]
            Pr_ = self.Pr + (-min_Pr)
        else:
            Pr_ = self.Pr

        print(len(Pr), 'Pr')


        self.E1 = self.E1[:] * 1_000_000
        self.Eps1 = self.Eps1[:] * 100 
        self.Pr = Pr_[:] * 1_000_000


    def find_loading_starts(self, data, threshold, min_interval=10):
        """Находит индексы начала всех циклов нагружения"""
        above_threshold = data > threshold
        start_indices = []
        i = 0
        n = len(data)
        
        while i < n:
            # Ищем первый переход через порог
            while i < n and not above_threshold[i]:
                i += 1
            
            if i >= n:
                break
                
            # Запоминаем начало цикла
            start_indices.append(i)
            
            # Пропускаем текущий цикл
            while i < n and above_threshold[i]:
                i += 1
            
            # Пропускаем минимальный интервал между циклами
            i += min_interval
        
        return start_indices



    def plot_data(self):
        if not self.file_path:
            QMessageBox.warning(self, "Внимание", "Сначала выберите файл данных")
            return

        if not self.load_data():
            return

        if not self.process_data():
            return

  
        self.stress = self.stress

        self.time = self.time   
        self.pic_data = self.strain_    
        # Получение всех пиков с дополнительными параметрами для лучшего обнаружения
        self.peaks_upper, _ = find_peaks(self.pic_data, prominence=np.nanstd(self.pic_data)/2)  
        # Сначала находим впадины как обычно
        self.peaks_lower, _ = find_peaks(-self.pic_data, prominence=np.nanstd(self.pic_data)/2) 
                    # Точки пересечения нуля снизу вверх
        zero_crossings = np.where((self.pic_data[:-1] <= 0) & (self.pic_data[1:] > 0))[0]   
        # Локальные минимумы
        local_minima, _ = find_peaks(-self.pic_data, prominence=np.nanstd(self.pic_data)/2) 
        # Объединяем и удаляем дубликаты
        self.peaks_lower_ = np.unique(np.concatenate((zero_crossings, local_minima)))   

        window_size = 5 
        # Для каждой впадины ищем ближайшую точку подъёма

        adjusted_peaks = []
        for peak in self.peaks_lower:
            # Ищем первую точку после peak, где производная становится положительной
            grad = np.gradient(self.pic_data)
            rise_point = np.where(grad[peak:] > 0)[0]
            if len(rise_point) > 0:
                adjusted_peaks.append(peak + rise_point[0])  # сдвигаем пик к подъёму   
        self.peaks_lower = np.array(adjusted_peaks)
        self.peaks_lower = np.insert(self.peaks_lower, 0, 0)   
        # Обновляем выпадающие списки пиков
        self.update_peaks_comboboxes()      
        # Фильтрация NaN и бесконечных значений
        # valid = ~np.isnan(self.stress) & ~np.isnan(self.strain_) & ~np.isinf(self.stress) & ~np.isinf(self.strain)        
        strain__ = self.translate_units(self.strain, 100)
        window_size = min(self.median_filter_size_dist, len(strain__)//4 or 1)
        strain_median = median_filter(strain__, size=window_size)
        self.strain_pocent = gaussian_filter1d(strain_median, sigma=self.gaussian_sigma_dist_value)

        # Очистка всех фигур
        self.figure1.clear()
        self.figure3.clear()
        self.figure4.clear()        

        # График 2: Относительная деформация vs Время (все данные)
        ax3 = self.figure1.add_subplot(211)
        ax8 = self.figure1.add_subplot(212)
        ax8.plot(self.time, self.strain * 100, 'k-', linewidth=self.linewidth)            
        if self.show_peaks and len(self.peaks_upper) > 0 and len(self.peaks_lower) > 0:
            peaks_upper = [p for p in self.peaks_upper if p < len(self.strain* 100)]
            peaks_lower = [p for p in self.peaks_lower if p < len(self.strain* 100)]
            ax8.plot(self.time[peaks_upper], self.strain[peaks_upper], 
                    'ro', label='Верхние пики')
            ax8.plot(self.time[peaks_lower], self.strain[peaks_lower], 
                    'go', label='Нижние пики')
            ax8.legend()        
        ax8.set_xlabel('Время, С', fontsize=self.fontsize, fontweight=self.fontweight)
        ax8.set_ylabel('Относительная деформация, %', fontsize=self.fontsize, fontweight=self.fontweight)
        ax8.grid(True, linestyle='--', alpha=0.6)   
        if self.is_title:
            ax3.set_title(f'{self.name_sample.text()} Коэффициент формы q = {self.form_factor:.2f}', fontsize=self.fontsize, fontweight=self.fontweight)  
        ax3.plot(self.time, self.stress, 'k-', linewidth=self.linewidth)     
        if self.show_peaks and len(self.peaks_upper) > 0 and len(self.peaks_lower) > 0:
            peaks_upper = [p for p in self.peaks_upper if p < len(self.stress)]
            peaks_lower = [p for p in self.peaks_lower if p < len(self.stress)]
            ax3.plot(self.time[peaks_upper], self.stress[peaks_upper], 
                    'ro', label='Верхние пики')
            ax3.plot(self.time[peaks_lower], self.stress[peaks_lower], 
                    'go', label='Нижние пики')
            ax3.legend()        
        ax3.set_xlabel('Время, С', fontsize=self.fontsize, fontweight=self.fontweight)
        ax3.set_ylabel('Удельное давление, МПа', fontsize=self.fontsize, fontweight=self.fontweight)
        ax3.grid(True, linestyle='--', alpha=0.6)           
        # График 3: Дополнительные графики
        ax4 = self.figure3.add_subplot(211)
        ax5 = self.figure3.add_subplot(212)     
        self.process_data_() 
        # График 3.1: Модуль Юнга vs Время
        ax4.plot(self.Pr, self.E1,'k-', linewidth=self.linewidth)
        if self.is_title:
            ax4.set_title(f'{self.name_sample.text()} Коэффициент формы q = {self.form_factor:.2f}', fontsize=self.fontsize, fontweight=self.fontweight)  
        ax4.set_xlabel('Удельное давление, МПа', fontsize=self.fontsize, fontweight=self.fontweight)
        ax4.set_ylabel('Модуль упругости, МПа', fontsize=self.fontsize, fontweight=self.fontweight)
        ax4.grid(True, linestyle='--', alpha=0.6)
        ax4.set_xlim(left=0)
        ax4.set_ylim(bottom=0)      
        # График 3.2: Относительная деформация vs Удельное давление (все данные)
        ax5.plot(self.Pr, self.Eps1, 'k-', linewidth=self.linewidth)
        ax5.set_xlabel('Удельное давление, МПа', fontsize=self.fontsize, fontweight=self.fontweight)
        ax5.set_ylabel('Относительная деформация, %', fontsize=self.fontsize, fontweight=self.fontweight)
        ax5.grid(True, linestyle='--', alpha=0.6)

        if self.radio_button_line_modul_y:
            if self.Eps1.size > 0:
                if max(self.Eps1) > 30 and self.Eps1.size > 15:
                    stress = self.Pr
                    strain = self.Eps1  
                    x_7, y_7 = self.find_coordinat([7,8,9,10,11,12,6,13,5],stress, strain)
                    x_20, y_20 = self.find_coordinat([20, 19, 18, 21,22,23],stress, strain)
                    ax5.axvline(x=x_20)
                    ax5.axvline(x=x_7)  
                    end_graff_x = stress[-1]
                    end_graff_y = strain[-1]
                    start_graff_x = stress[0]
                    start_graff_y = strain[0]
                    ax5.plot([x_7,x_20], [y_7, y_20], 'r')
                    ax5.plot([x_20,end_graff_x], [y_20, end_graff_y], 'g'  )
                    ax5.plot([start_graff_x,x_7], [start_graff_y,y_7], 'y') 
        ax5.set_xlim(left=0)
        ax5.set_ylim(bottom=0)      
        self.figure3.tight_layout()     
        # График 4: Циклы нагружения
        self.plot_overview()  
        self.plot_w()      
        # Обновление всех холстов
        self.canvas1.draw()

        self.canvas3.draw()
        self.canvas4.draw() 

        # Активируем кнопку сохранения
        self.save_button.setEnabled(True)

 
    def translate_units(self, data, utits):
        current_data = []
        for i in data:
            current_data.append(i * utits)
        return np.array(current_data)
    
    def plot_overview(self):
       if len(self.locs) < 1:
           print(f"Недостаточно данных для построения графика {os.path.basename(self.file_path)}")
           return   
       def colors_labels(locs):
           base_colors = ['k', 'g', 'r', 'b', 'm', 'c', 'c', 'c']
           n = min(len(locs)+2, len(base_colors)+2)
           labels = [f'Цикл {i+1}' for i in range(n)]
           return base_colors[:n], labels       
       Forse, Disp, Time = self.forse__, self.displacement__, self.time
       delta_l = [np.max(Disp)]     
       n_locs_rang = min(6, len(self.locs))
       colors, labels = colors_labels(self.locs)
       base_len = self.locs[0] if len(self.locs) > 0 else len(Disp)     
       # Очищаем фигуру перед построением
       self.figure4.clear() 
       self.figure6.clear() 
       # Создаем 2 subplot'а: верхний для временных данных, нижний для циклов
       ax1 = self.figure4.add_subplot(1, 1, 1)  # верхний график
       ax2 = self.figure6.add_subplot(1, 1, 1)  # верхний график
       ax1.plot(Time, Disp, 'b', label='Смещение (мм)', linewidth=self.linewidth)
       ax1.set_ylabel('Перемещение, мм', fontsize=self.fontsize, 
                     fontweight=self.fontweight, color='blue')
       ax1.set_xlabel('Время, с', fontsize=self.fontsize, fontweight=self.fontweight)
       ax1.grid(True)
       ax1.set_ylim([0, math.ceil(delta_l[0] + 0.5)])   
       # График силы на той же оси (дополнительная ось Y)
       ax1_force = ax1.twinx()
       ax1_force.plot(Time, Forse, 'r', label='Нагрузка (Н)', linewidth=self.linewidth)
       ax1_force.set_ylabel('Нагрузка, Н', fontsize=self.fontsize, 
                           fontweight=self.fontweight, color='red') 
       # Общий заголовок для верхнего графика
       if self.is_title:
        ax1.set_title(f'{self.name_sample.text()} Коэффициент формы q = {self.form_factor:.2f}', fontsize=self.fontsize, fontweight=self.fontweight)  
       # ======= НИЖНЯЯ ЧАСТЬ: Циклы нагружения =======
       lower_ =  (self.peaks_lower)
       upper_ =  (self.peaks_upper)

       for i in range(len(upper_) + 1):

           if i == 0:
               pass
           else:
               # Создаем новую фигуру и холст для каждого цикла
               figure = Figure(figsize=(self.figure_width, self.figure_height))
           
               if i == len(upper_):
                   start_idx = lower_[i-1]
                   x = self.displacement__[start_idx:]
                   y = self.forse__[start_idx:]
                   ax2.plot(x, y, colors[i-1], label=labels[i-1], linewidth=self.linewidth)  
               else:
                   start_idx = lower_[i-1]
                   end_idx = lower_[i]
                   x = self.displacement__[start_idx:end_idx]
                   y = self.forse__[start_idx:end_idx]
                   ax2.plot(x, y, colors[i-1], label=labels[i-1], linewidth=self.linewidth)  
 

       ax2.set_xlabel('Перемещение, мм', fontsize=self.fontsize, fontweight=self.fontweight)
       ax2.set_ylabel('Нагрузка, Н', fontsize=self.fontsize, fontweight=self.fontweight)
       ax2.grid(True, linestyle='--', alpha=0.6)
       ax2.legend(loc='lower right')
       if self.is_title:
          ax2.set_title('Циклы нагружения', fontsize=self.fontsize, fontweight=self.fontweight)   
       # Общий заголовок для всей фигуры    
       # Регулировка расположения элементов

       self.canvas6.draw()
       self.canvas4.draw()
    
    def plot_w(self):
        self.cycle_figures = []
        if len(self.locs) < 1:
            print(f"Недостаточно данных для построения графика {os.path.basename(self.file_path)}")
            return

        def colors_labels(locs):
            base_colors = ['k', 'g', 'r', 'b', 'm', 'c','y','w']
            n = min(len(locs)+1, len(base_colors))
            labels = [f'Цикл {i+1}' for i in range(n)]
            return base_colors[:n], labels

        # Получаем данные из DataFrame
        Force = self.df[0].values  # Сила
        Disp = self.df[2].values   # Перемещение

        # Удаляем старые вкладки циклов
        for i in range(self.tabs.count()-1, -1, -1):
            if self.tabs.tabText(i).startswith("Цикл"):
                self.tabs.removeTab(i)

        colors, labels = colors_labels(self.locs)
        
        # Базовый размер окна для каждого цикла

        lower_ =  (self.peaks_lower)
        upper_ =  (self.peaks_upper)

        x = []
        y = []

        for i in range(len(upper_) + 1):
            if i == 0:
                pass
            else:
                # Создаем новую фигуру и холст для каждого цикла
                figure = Figure(figsize=(self.figure_width, self.figure_height))
                canvas = FigureCanvas(figure)
                toolbar = CustomNavigationToolbar(canvas, self)
            

                if i == len(upper_):
                    start_idx = lower_[i-1]
                    x = self.displacement__[start_idx:]
                    y = self.forse__[start_idx:]
                else:
                    start_idx = lower_[i-1]
                    end_idx = lower_[i]
                    x = self.displacement__[start_idx:end_idx]
                    y = self.forse__[start_idx:end_idx]
                    
                
                ax = figure.add_subplot(111)

                ax.plot(x, y, color=colors[i-1], label=labels[i-1], linewidth=self.linewidth)
                x = list(x)
                x.append(x[0])
                y = list(y) 
                y.append(y[0])

                if self.is_filling:
                    # Заливка с дополнительными точками
                    ax.fill_between(x, y, color=colors[i-1], alpha=0.2, linewidth=0)
                
                # Вычисляем площадь по оригинальным точкам
                area = abs(np.trapezoid(y, x))
                
 
                # Настройки графика
                if self.is_title:
                    ax.set_title(f'Цикл {i} (Площадь: {area:.2f})', fontsize=self.fontsize, fontweight=self.fontweight)
                ax.set_xlabel('Перемещение, мм', fontsize=self.fontsize, fontweight=self.fontweight)
                ax.set_ylabel('Сила, Н', fontsize=self.fontsize, fontweight=self.fontweight)
                 
                ax.grid(True, linestyle='--', alpha=0.7)

                # Оптимизируем расположение
                figure.tight_layout(pad=3.0)
                self.cycle_figures.append(figure)
                
                # Создаем контейнер и добавляем вкладку
                tab_container = self.create_tab_container(canvas, toolbar)
                self.tabs.addTab(tab_container, f"Цикл {i}")
  


    def apply_styles(self):
        self.setStyleSheet( """
        QMainWindow {
            background-color: #f5f5f5;
        }
        QGroupBox {
            border: 1px solid #ccc;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 15px;
            font-weight: bold;
        }
        QPushButton {
            background-color: #2196F3;  /* Синий вместо зеленого */
            color: white;
            border: none;
            padding: 8px 16px;
            text-align: center;
            text-decoration: none;
            font-size: 14px;
            margin: 4px 2px;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #1976D2;  /* Темно-синий при наведении */
        }
        QPushButton:disabled {
            background-color: #cccccc;
        }
        QLineEdit {
            padding: 5px;
            border: 1px solid #ccc;
            border-radius: 4px;
        }
        QLabel {
            font-size: 14px;
        }
        QTabWidget::pane {
            border: 1px solid #ccc;
            top: -1px;
            background: white;
        }
        QTabBar::tab {
            background: #e1e1e1;
            border: 1px solid #ccc;
            padding: 8px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }
        QTabBar::tab:selected {
            background: white;
            border-bottom-color: white;
        }
        QSpinBox, QDoubleSpinBox {
            padding: 3px;
            border: 1px solid #ccc;
            border-radius: 4px;
            min-width: 60px;
        }
    """)

    def process_data(self):
            # Получение параметров образца
            width_edit = self.width_edit.text()
            length_edit = self.length_edit.text()
            height_edit = self.height_edit.text()

            width = float(width_edit.replace(',', '.'))
            length = float(length_edit.replace(',', '.'))
            initial_height = float(height_edit.replace(',', '.'))

            self.form_factor = float( width / initial_height)
            
            # Данные со столбцов
            force = self.df[0].values  # нагрузка (Н)
            displacement = self.df[2].values  # перемещение (мм)
            self.time_ = self.df[3].values  # время (с)

            threshold = 20  # порог нагрузки в Ньютонах

            # Находим первый индекс, где нагрузка превышает порог И продолжает расти
            start_index = 0
            for i in range(1, len(force)):
                if force[i] > threshold and np.all(force[i:i+5] > threshold):  # проверяем 5 следующих точек
                    start_index = i
                    break

            # Обрезаем все данные до start_index
            self.time_ = self.time_[start_index:]
            displacement = displacement[start_index:]
            force = force[start_index:]

            self.time_ =  self.time_  - self.time_[0]
            displacement =  displacement - displacement[0]
            force =  force - force[0]
            self.forse__ = force
            self.displacement__ = displacement
            print(len(self.displacement__), 'displacement__')

            print(f"Обрезано {start_index} начальных точек. Начальная нагрузка: {force[0]:.2f} Н")

            # Параметры образца
            area = width * length  # мм²
            area_m2 = area * 1e-6  # м²
            self.area = area
    

            # Расчет деформации и напряжения
            with np.errstate(divide='ignore', invalid='ignore'):
                self.strain_ = displacement / initial_height  # относительная деформация
                
                stress = (force / area_m2) * 1e-6  # удельное давление (Па)
            strain_ = displacement / initial_height  # удельное давление (Па)
            
            # Применяем маску ко всем соответствующим массивам
            self.strain = strain_
            self.stress = stress
            self.time = self.time_

            self.strain = (self.strain)
            self.stress = (self.stress)
            # Проверяем, что все массивы имеют одинаковую длину

            # Расчет модуля Юнга (производная σ по ε)
            with np.errstate(divide='ignore', invalid='ignore'):
                young_modulus = np.gradient(self.stress, self.strain)

            young_modulus_interp = interpolate_nans(young_modulus)
            # Сглаживание
            
            window_size = min(self.median_filter_size, len(young_modulus_interp)//4 or 1)
            young_modulus_median = median_filter(young_modulus_interp, size=window_size)
            young_modulus_smooth = gaussian_filter1d(young_modulus_median, sigma=self.gaussian_sigma)
            self.young_modulus_final = young_modulus_smooth
           
            # Находим циклы нагружения
            self.find_loading_cycles()

            return True
        
    def find_loading_cycles(self):
        """Находит циклы нагружения в данных"""
        # Находим пики в данных силы
        peaks, _ = find_peaks(self.df[0].values, prominence=np.std(self.df[0].values)/2)
        self.locs = peaks.tolist()
        
        # Если пиков слишком много, берем только первые 5
        if len(self.locs) > 5:
            self.locs = self.locs[:5]

    def update_peaks_comboboxes(self):
        """Обновляет выпадающие списки пиков"""
        self.peak_combo_upper.clear()
        self.peak_combo_lower.clear()
        
        if len(self.peaks_upper) > 0:
            for i, peak in enumerate(self.peaks_upper):
                # Преобразуем numpy.int64 в int и форматируем строку
                peak_idx = int(peak)
                if peak_idx < len(self.stress):
                    self.peak_combo_upper.addItem(f"Пик {i+1} (x={peak_idx}, y={self.stress[peak_idx]:.2f})")
        
        if len(self.peaks_lower) > 0:
            for i, peak in enumerate(self.peaks_lower):
                # Преобразуем numpy.int64 в int и форматируем строку
                peak_idx = int(peak)
                if peak_idx < len(self.stress):
                    self.peak_combo_lower.addItem(f"Пик {i+1} (x={peak_idx}, y={self.stress[peak_idx]:.2f})")
        
        self.plot_selected_peak_button.setEnabled(len(self.peaks_upper) > 0 or len(self.peaks_lower) > 0)


    def C_stat(self, save_dir):
        low = self.peaks_lower
        low = np.insert(low, 0, 0) 
        lower_p = list(low)
        upper_p = list(self.peaks_upper)
        force = self.forse__
        displacement = self.displacement__
        
        # Создаем список для хранения результатов всех циклов
        results = []
        
        for io in range(len(upper_p)):
            force__ = force[lower_p[io]:upper_p[io]]
            displacement__ = displacement[lower_p[io]:upper_p[io]]
            threshold_GOST = 625  # порог нагрузки в Ньютонах
            
            # Находим первый индекс, где нагрузка превышает порог И продолжает расти
            start_index_GOST = None
            for i in range(1, len(force__) - 5):
                if force__[i] > threshold_GOST and np.all(force__[i:i+5] > threshold_GOST):
                    start_index_GOST = i
                    break
                    
            if len(upper_p) == io+1:
                list_max = force[lower_p[io]:]
            else:
                list_max = force[lower_p[io]:lower_p[io+1]]
                
            # max_forse = (max(list_max))
            max_forse = int(8750)

            max_forse_ = None
            for i in range(1, len(force__) - 5):
                if force__[i] > max_forse and np.all(force__[i:i+5] > max_forse):
                    max_forse_ = i
                    break

            pp = (max_forse - threshold_GOST) / ((displacement__[max_forse_] - displacement__[start_index_GOST]) * self.area)
            
            # Добавляем результат цикла в список
            results.append(pp)
            
            print(f"Цикл: {str(io+1)}", pp, 'H/mm2\nЗначение находится когда нагрузка возрастает')
        
            try:
                # Создаем DataFrame с двумя столбцами
                df = pd.DataFrame({
                    'Результат': [f"{result:.3f}".replace('.', ',') for result in results]
                })
                
                
                # Сохранение в Excel
                save_path = save_dir + '/результаты_циклов.xlsx'
                df.to_excel(save_path, index=False)
                
            except PermissionError as e:
                print(f"Ошибка доступа к файлу: {e}")
