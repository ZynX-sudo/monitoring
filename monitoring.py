# Pastikan Anda telah menginstal pustaka yang diperlukan:
# pip install psutil PyQt6 qtawesome

import sys
import psutil
import qtawesome as fa
from PyQt6.QtWidgets import (
    QApplication, QSystemTrayIcon, QMenu, QWidget, QLabel, QVBoxLayout,
    QHBoxLayout
)
from PyQt6.QtGui import QIcon, QAction, QFont
from PyQt6.QtCore import QTimer, Qt, QPoint, QSize

# File untuk menyimpan posisi jendela
POSITION_FILE = "window_position.txt"

class InfoWidget(QWidget):
    """
    Jendela kecil tanpa bingkai yang menampilkan informasi sistem.
    Jendela ini dapat diseret dan dikunci.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Jendela awalnya dikunci secara default
        self.is_locked = True
        self.drag_position = None

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        
        # --- Mengatur tata letak dan gaya ---
        main_layout = QVBoxLayout()
        # Mengatur margin dan spasi menjadi minimal
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(1)
        self.setLayout(main_layout)

        # Gaya umum untuk label dan font
        label_font = QFont("Inter", 8, QFont.Weight.Bold)
        label_style = "color: white;"
        
        # --- Baris pertama: Unggah dan CPU ---
        line1_layout = QHBoxLayout()
        line1_layout.setSpacing(15) 

        up_layout = QHBoxLayout()
        up_layout.setContentsMargins(0, 0, 0, 0)
        up_layout.setSpacing(2)
        self.up_icon = QLabel()
        self.up_icon.setPixmap(fa.icon('fa5s.arrow-up', color='white').pixmap(QSize(12, 12)))
        self.up_label = QLabel("0.00 KB/s")
        self.up_label.setFont(label_font)
        self.up_label.setStyleSheet(label_style)
        up_layout.addWidget(self.up_icon)
        up_layout.addWidget(self.up_label)

        cpu_layout = QHBoxLayout()
        cpu_layout.setContentsMargins(0, 0, 0, 0)
        cpu_layout.setSpacing(2)
        self.cpu_icon = QLabel()
        self.cpu_icon.setPixmap(fa.icon('fa5s.microchip', color='white').pixmap(QSize(12, 12)))
        self.cpu_label = QLabel("0.00 %")
        self.cpu_label.setFont(label_font)
        self.cpu_label.setStyleSheet(label_style)
        cpu_layout.addWidget(self.cpu_icon)
        cpu_layout.addWidget(self.cpu_label)

        line1_layout.addLayout(up_layout)
        line1_layout.addLayout(cpu_layout)

        # --- Baris kedua: Unduh dan Memori ---
        line2_layout = QHBoxLayout()
        line2_layout.setSpacing(15)

        down_layout = QHBoxLayout()
        down_layout.setContentsMargins(0, 0, 0, 0)
        down_layout.setSpacing(2)
        self.down_icon = QLabel()
        self.down_icon.setPixmap(fa.icon('fa5s.arrow-down', color='white').pixmap(QSize(12, 12)))
        self.down_label = QLabel("0.00 KB/s")
        self.down_label.setFont(label_font)
        self.down_label.setStyleSheet(label_style)
        down_layout.addWidget(self.down_icon)
        down_layout.addWidget(self.down_label)

        mem_layout = QHBoxLayout()
        mem_layout.setContentsMargins(0, 0, 0, 0)
        mem_layout.setSpacing(2)
        self.mem_icon = QLabel()
        self.mem_icon.setPixmap(fa.icon('fa5s.memory', color='white').pixmap(QSize(12, 12)))
        self.mem_label = QLabel("0.00 %")
        self.mem_label.setFont(label_font)
        self.mem_label.setStyleSheet(label_style)
        mem_layout.addWidget(self.mem_icon)
        mem_layout.addWidget(self.mem_label)

        line2_layout.addLayout(down_layout)
        line2_layout.addLayout(mem_layout)

        main_layout.addLayout(line1_layout)
        main_layout.addLayout(line2_layout)

        self.adjustSize()

    def update_labels(self, cpu, mem, up, down):
        """
        Memperbarui teks pada label.
        """
        self.cpu_label.setText(f"{cpu:.2f} %")
        self.mem_label.setText(f"{mem:.2f} %")
        self.up_label.setText(f"{up:.2f} KB/s")
        self.down_label.setText(f"{down:.2f} KB/s")

    def toggle_lock(self):
        """
        Mengubah status kunci/buka kunci.
        """
        self.is_locked = not self.is_locked

    def mousePressEvent(self, event):
        """
        Menyimpan posisi kursor saat mouse ditekan.
        """
        if not self.is_locked and event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.pos()
            event.accept()

    def mouseMoveEvent(self, event):
        """
        Mengubah posisi jendela saat mouse digerakkan.
        """
        if not self.is_locked and self.drag_position is not None:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        """
        Merilis posisi kursor saat mouse dilepas.
        """
        self.drag_position = None
        event.accept()
    
    def contextMenuEvent(self, event):
        """
        Membuat menu saat diklik kanan.
        """
        contextMenu = QMenu(self)
        
        lock_action = QAction("Buka Kunci" if self.is_locked else "Kunci", self)
        lock_action.triggered.connect(self.toggle_lock)
        contextMenu.addAction(lock_action)
        
        contextMenu.addSeparator()

        quit_action = QAction("Keluar", self)
        quit_action.triggered.connect(QApplication.instance().quit)
        contextMenu.addAction(quit_action)
        
        contextMenu.exec(event.globalPos())

class HybridMonitor(QSystemTrayIcon):
    """
    Kelas utama untuk mengelola ikon system tray dan jendela InfoWidget.
    """
    def __init__(self, icon, parent=None):
        super().__init__(icon, parent)
        
        self.info_window = InfoWidget()
        self.last_net_io = psutil.net_io_counters()
        
        self.menu = QMenu(parent)
        self.info_action = QAction("Tampilkan/Sembunyikan Jendela", self)
        self.info_action.triggered.connect(self.toggle_info_window)
        
        self.quit_action = QAction("Keluar", self)
        self.quit_action.triggered.connect(self.quit_app)
        
        self.menu.addAction(self.info_action)
        self.menu.addSeparator()
        self.menu.addAction(self.quit_action)
        self.setContextMenu(self.menu)

        self.activated.connect(self.on_activated)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_data)
        self.timer.start(1000)
        
        # Timer tambahan untuk memastikan jendela selalu di atas
        self.stay_on_top_timer = QTimer(self)
        self.stay_on_top_timer.timeout.connect(self.ensure_on_top)
        self.stay_on_top_timer.start(500) # Periksa setiap 500ms

        self.show()

    def ensure_on_top(self):
        """
        Memastikan jendela berada di posisi paling atas secara berkala.
        """
        if self.info_window.isVisible():
            self.info_window.raise_()
            self.info_window.activateWindow()

    def toggle_info_window(self):
        """
        Menampilkan atau menyembunyikan jendela info.
        """
        if self.info_window.isVisible():
            self.info_window.hide()
        else:
            self.info_window.show()
            self.info_window.setFocus()

    def on_activated(self, reason):
        """
        Menangani event klik pada ikon system tray.
        """
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.toggle_info_window()
        elif reason == QSystemTrayIcon.ActivationReason.Context:
            self.contextMenu().exec(self.geometry().bottomRight())

    def update_data(self):
        """
        Mengambil data sistem dan memperbarui jendela serta tooltip.
        """
        try:
            cpu_usage = psutil.cpu_percent(interval=None)
            mem_usage = psutil.virtual_memory().percent

            current_net_io = psutil.net_io_counters()
            upload_speed = (current_net_io.bytes_sent - self.last_net_io.bytes_sent) / 1024
            download_speed = (current_net_io.bytes_recv - self.last_net_io.bytes_recv) / 1024
            self.last_net_io = current_net_io
            
            if self.info_window.isVisible():
                self.info_window.update_labels(cpu_usage, mem_usage, upload_speed, download_speed)
            
            tooltip_text = f"CPU: {cpu_usage:.2f}%\n" \
                           f"Mem: {mem_usage:.2f}%\n" \
                           f"Unggah: {upload_speed:.2f} KB/s\n" \
                           f"Unduh: {download_speed:.2f} KB/s"
            self.setToolTip(tooltip_text)

        except Exception as e:
            self.setToolTip(f"Error: {e}")

    def save_position(self):
        """
        Menyimpan posisi jendela saat ini ke file.
        """
        try:
            with open(POSITION_FILE, "w") as f:
                pos = self.info_window.pos()
                f.write(f"{pos.x()},{pos.y()}")
        except IOError:
            print("Gagal menyimpan posisi.")

    def load_position(self):
        """
        Memuat posisi jendela dari file.
        Mengembalikan QPoint jika berhasil, atau None jika gagal.
        """
        try:
            with open(POSITION_FILE, "r") as f:
                pos_str = f.read().strip().split(',')
                if len(pos_str) == 2:
                    return QPoint(int(pos_str[0]), int(pos_str[1]))
        except (IOError, ValueError):
            return None
        return None

    def quit_app(self):
        """
        Menutup aplikasi dan menyimpan posisi jendela.
        """
        self.save_position()
        self.info_window.close()
        QApplication.quit()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    icon = fa.icon('fa5s.microchip')
    monitor = HybridMonitor(icon)
    
    # Coba muat posisi yang tersimpan
    last_position = monitor.load_position()
    
    if last_position:
        monitor.info_window.move(last_position)
    else:
        # Jika tidak ada posisi tersimpan, pindahkan ke posisi default (kanan bawah)
        screen_size = QApplication.primaryScreen()
        if screen_size:
            available_geometry = screen_size.availableGeometry()
            pos_x = available_geometry.width() - monitor.info_window.width()
            pos_y = available_geometry.height() - monitor.info_window.height()
            monitor.info_window.move(pos_x, pos_y)
    
    monitor.info_window.show()
        
    sys.exit(app.exec())