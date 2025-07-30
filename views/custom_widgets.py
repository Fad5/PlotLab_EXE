from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from PyQt5.QtWidgets import QLabel

class CustomNavigationToolbar(NavigationToolbar):
    def __init__(self, canvas, parent, coordinates=True):
        super().__init__(canvas, parent, coordinates)
        self.coordinates_label = QLabel("")
        self.addWidget(self.coordinates_label)
        
    def mouse_move(self, event):
        if event.inaxes:
            x, y = event.xdata, event.ydata
        super().mouse_move(event)

class ZoomPanHandler:
    def __init__(self, canvas):
        self.canvas = canvas
        self.ax = None
        self.press = None
        self.cur_xlim = None
        self.cur_ylim = None
        self.xpress = None
        self.ypress = None
        self._id_drag = None
        self._id_scroll = None
        self.connect()

    def connect(self):
        self._id_drag = self.canvas.mpl_connect('button_press_event', self.on_press)
        self._id_scroll = self.canvas.mpl_connect('scroll_event', self.on_scroll)
        self.canvas.mpl_connect('button_release_event', self.on_release)
        self.canvas.mpl_connect('motion_notify_event', self.on_motion)

    def on_scroll(self, event):
        if not event.inaxes or self.ax != event.inaxes:
            return

        base_scale = 1.1
        xdata = event.xdata
        ydata = event.ydata

        if event.button == 'up':
            scale_factor = 1 / base_scale
        elif event.button == 'down':
            scale_factor = base_scale
        else:
            return

        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()

        new_xlim = [
            xdata - (xdata - xlim[0]) * scale_factor,
            xdata + (xlim[1] - xdata) * scale_factor
        ]
        new_ylim = [
            ydata - (ydata - ylim[0]) * scale_factor,
            ydata + (ylim[1] - ydata) * scale_factor
        ]

        self.ax.set_xlim(new_xlim)
        self.ax.set_ylim(new_ylim)
        self.canvas.draw_idle()

    def on_press(self, event):
        if event.inaxes != self.ax or event.button != 1:
            return
            
        self.press = event.xdata, event.ydata
        self.xpress, self.ypress = event.x, event.y
        self.cur_xlim = self.ax.get_xlim()
        self.cur_ylim = self.ax.get_ylim()

    def on_motion(self, event):
        if self.press is None or event.inaxes != self.ax:
            return
            
        dx = event.x - self.xpress
        dy = event.y - self.ypress
        
        dx = dx / self.canvas.width() * (self.cur_xlim[1] - self.cur_xlim[0])
        dy = dy / self.canvas.height() * (self.cur_ylim[1] - self.cur_ylim[0])
        
        new_xlim = self.cur_xlim[0] - dx, self.cur_xlim[1] - dx
        new_ylim = self.cur_ylim[0] + dy, self.cur_ylim[1] + dy
        
        self.ax.set_xlim(new_xlim)
        self.ax.set_ylim(new_ylim)
        self.canvas.draw_idle()

    def on_release(self, event):
        self.press = None
        self.canvas.draw_idle()

    def disconnect(self):
        if self._id_drag:
            self.canvas.mpl_disconnect(self._id_drag)
        if self._id_scroll:
            self.canvas.mpl_disconnect(self._id_scroll)