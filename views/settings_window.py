from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QGroupBox, QHBoxLayout, QLabel,
    QSpinBox, QDoubleSpinBox, QRadioButton, QButtonGroup, QPushButton, QComboBox, QAbstractSpinBox
) 

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QToolTip 
from PyQt5.QtGui import QFont, QPalette




class SettingsDialog(QDialog):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.setGeometry(300, 300, 300, 900)
        self.setWindowTitle("Настройки")
        self.main_window = main_window
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Настройки фильтрации
        filter_group = QGroupBox("Параметры фильтрации")
        filter_layout = QVBoxLayout()
        filter_group.setLayout(filter_layout)
        
        # Median filter
        median_layout = QHBoxLayout()
        median_layout.addWidget(QLabel("Размер окна медианного фильтра для модуля упругости:"))
        self.median_filter_spin = QSpinBox()
        self.median_filter_spin.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.median_filter_spin.setRange(1, 1000)
        self.median_filter_spin.setValue(self.main_window.median_filter_size)
        median_layout.addWidget(self.median_filter_spin)
        filter_layout.addLayout(median_layout)
        
        # Gaussian filter
        gaussian_layout = QHBoxLayout()
        gaussian_layout.addWidget(QLabel("Степень сглаживания для модуля упругости"))
        self.gaussian_sigma_spin = QDoubleSpinBox()
        self.gaussian_sigma_spin.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.gaussian_sigma_spin.setRange(0.1, 10.0)
        self.gaussian_sigma_spin.setSingleStep(0.1)
        self.gaussian_sigma_spin.setValue(self.main_window.gaussian_sigma)
        gaussian_layout.addWidget(self.gaussian_sigma_spin)
        filter_layout.addLayout(gaussian_layout)
        
        # Настройки графиков
        plot_group = QGroupBox("Настройки графиков")
        plot_layout = QVBoxLayout()
        plot_group.setLayout(plot_layout)

        # Группа для вспомогательных линий
        line_group = QGroupBox("Вспомогательные линии на графике модуля упругости")
        line_layout = QHBoxLayout()
        line_group.setLayout(line_layout)
        
        self.line_radio_yes = QRadioButton("Да")
        self.line_radio_no = QRadioButton("Нет")
        
        if self.main_window.radio_button_line_modul_y:
            self.line_radio_yes.setChecked(True)
        else:
            self.line_radio_no.setChecked(True)
            
        line_layout.addWidget(self.line_radio_yes)
        line_layout.addWidget(self.line_radio_no)
        plot_layout.addWidget(line_group)



        # Отображения title в графиках
        title_seek_group = QGroupBox("Отображать title в графиках:")
        title_seek_layout = QHBoxLayout()
        title_seek_group.setLayout(title_seek_layout)

        self.title_seek_radio_yes = QRadioButton("Да")
        self.title_seek_radio_no = QRadioButton("Нет")

        if self.main_window.is_title:
            self.title_seek_radio_yes.setChecked(True)
        else:
            self.title_seek_radio_no.setChecked(True)
            
        title_seek_layout.addWidget(self.title_seek_radio_yes)
        title_seek_layout.addWidget(self.title_seek_radio_no)
        plot_layout.addWidget(title_seek_group)

        # Заливка в циклах 
        fill_seek_group = QGroupBox("Закрасить внутреннюю часть циклов:")
        fill_seek_layout = QHBoxLayout()
        fill_seek_group.setLayout(fill_seek_layout)

        self.fill_seek_radio_yes = QRadioButton("Да")
        self.fill_seek_radio_no = QRadioButton("Нет")

        if self.main_window.is_filling:
            self.fill_seek_radio_yes.setChecked(True)
        else:
            self.fill_seek_radio_no.setChecked(True)
            
        fill_seek_layout.addWidget(self.fill_seek_radio_yes)
        fill_seek_layout.addWidget(self.fill_seek_radio_no)
        plot_layout.addWidget(fill_seek_group)

        # Толщина линий
        linewidth_layout = QHBoxLayout()
        linewidth_layout.addWidget(QLabel("Толщина линий графиков:"))
        self.linewidth_spin = QDoubleSpinBox()
        self.linewidth_spin.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.linewidth_spin.setRange(0.1, 10.0)
        self.linewidth_spin.setSingleStep(0.1)
        self.linewidth_spin.setValue(self.main_window.linewidth)
        linewidth_layout.addWidget(self.linewidth_spin)
        plot_layout.addLayout(linewidth_layout)
        
        # Размер шрифта
        fontsize_layout = QHBoxLayout()
        fontsize_layout.addWidget(QLabel("Размер шрифта подписей:"))
        self.fontsize_spin = QSpinBox()
        self.fontsize_spin.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.fontsize_spin.setRange(6, 20)
        self.fontsize_spin.setValue(self.main_window.fontsize)
        fontsize_layout.addWidget(self.fontsize_spin)
        plot_layout.addLayout(fontsize_layout)
        
        # Размеры графиков
        size_group = QGroupBox("Размеры графиков")
        size_layout = QVBoxLayout()
        size_group.setLayout(size_layout)
        
        # Ширина
        width_layout = QHBoxLayout()
        width_layout.addWidget(QLabel("Ширина графиков (дюймы):"))
        self.width_spin = QDoubleSpinBox()
        self.width_spin.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.width_spin.setRange(5, 20)
        self.width_spin.setSingleStep(0.5)
        self.width_spin.setValue(self.main_window.figure_width)
        width_layout.addWidget(self.width_spin)
        size_layout.addLayout(width_layout)
        
        # Высота
        height_layout = QHBoxLayout()
        height_layout.addWidget(QLabel("Высота графиков (дюймы):"))
        self.height_spin = QDoubleSpinBox()
        self.height_spin.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.height_spin.setRange(3, 15)
        self.height_spin.setSingleStep(0.5)
        self.height_spin.setValue(self.main_window.figure_height)
        height_layout.addWidget(self.height_spin)
        size_layout.addLayout(height_layout)

        # Настройки Word
        setting_word = QGroupBox("Настройка word файлов")
        setting_word_layout = QVBoxLayout()
        setting_word.setLayout(setting_word_layout)

        # Шаблон сохранения
        self.template_label = QLabel("Шаблон сохранения:")
        self.select_template = QComboBox()
        self.select_template.addItem("ДС")
        self.select_template.addItem("НИИСФ")
        self.select_template.setCurrentText(self.main_window.selected_template)
        setting_word_layout.addWidget(self.template_label)
        setting_word_layout.addWidget(self.select_template)

        # Автооткрытие файлов
        open_group = QGroupBox("Автоматическое открытие файлов после сохранения")
        open_layout = QHBoxLayout()
        open_group.setLayout(open_layout)
        
        self.open_radio_yes = QRadioButton("Да")
        self.open_radio_no = QRadioButton("Нет")



        
        # Устанавливаем текущее значение
        if self.main_window.auto_open_file:
            self.open_radio_yes.setChecked(True)
        else:
            self.open_radio_no.setChecked(True)
            
        open_layout.addWidget(self.open_radio_yes)
        open_layout.addWidget(self.open_radio_no)
        setting_word_layout.addWidget(open_group)


        C_stat_group = QGroupBox("Расчитывать C stat?")
        C_stat_layout = QHBoxLayout()
        C_stat_group.setLayout(C_stat_layout)
        
        self.C_stat_radio_yes = QRadioButton("Да")
        self.C_stat_radio_no = QRadioButton("Нет")


                # Устанавливаем текущее значение
        if self.main_window.save_C_stat:
            self.C_stat_radio_yes.setChecked(True)
        else:
            self.C_stat_radio_no.setChecked(True)
            
        C_stat_layout.addWidget(self.C_stat_radio_yes)
        C_stat_layout.addWidget(self.C_stat_radio_no)
        setting_word_layout.addWidget(C_stat_group)


        # Кнопка применения
        self.apply_button = QPushButton("Применить настройки")
        self.apply_button.clicked.connect(self.apply_settings)
        
        # Добавление всех групп
        main_layout.addWidget(filter_group)
        main_layout.addWidget(plot_group)
        main_layout.addWidget(size_group)
        main_layout.addWidget(setting_word)
        main_layout.addWidget(self.apply_button)
        main_layout.addStretch()

    def update_figure_height(self, value):
        """Обновляет высоту графиков"""
        self.main_window.figure_height = value
    
    def apply_settings(self):
        """Применяет все настройки с корректным управлением фокусом"""
        try:
            # Сохраняем текущий фокус
            current_focus = self.main_window.focusWidget()
            
            # Сохраняем все параметры
            self.main_window.median_filter_size = self.median_filter_spin.value()
            self.main_window.gaussian_sigma = self.gaussian_sigma_spin.value()
            self.main_window.linewidth = self.linewidth_spin.value()
            self.main_window.fontsize = self.fontsize_spin.value()
            self.main_window.figure_width = self.width_spin.value()
            self.main_window.figure_height = self.height_spin.value()
            self.main_window.selected_template = self.select_template.currentText()
            self.main_window.radio_button_line_modul_y = self.line_radio_yes.isChecked()
            self.main_window.auto_open_file = self.open_radio_yes.isChecked()
            self.main_window.is_title = self.title_seek_radio_yes.isChecked()
            self.main_window.is_title = self.title_seek_radio_yes.isChecked()
            self.main_window.is_filling = self.fill_seek_radio_yes.isChecked()
            self.main_window.save_C_stat = self.C_stat_radio_yes.isChecked()

            

            # Блокируем обновление интерфейса
            self.main_window.setUpdatesEnabled(False)
            
            # Пересоздаем фигуры
            self.main_window.create_figures()
            
            # Перерисовываем данные
            if hasattr(self.main_window, 'df') and self.main_window.df is not None:
                self.main_window.plot_data()
            
            # Восстанавливаем обновление
            self.main_window.setUpdatesEnabled(True)
            
            # Вариант 1: Восстанавливаем предыдущий фокус
            if current_focus:
                current_focus.setFocus()
            
            # Вариант 2: Явно устанавливаем фокус на canvas с задержкой
            # if hasattr(self.main_window, 'canvas'):
            #     QTimer.singleShot(100, self.main_window.canvas.setFocus)
            
            # Вариант 3: Убираем фокус вообще
            # self.main_window.setFocus()
            
        except Exception as e:
            print(f"Ошибка при применении настроек: {str(e)}")
        finally:
            self.accept()