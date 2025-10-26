from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QComboBox, QPushButton, QFrame, QGraphicsDropShadowEffect,QSizePolicy)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt5.QtGui import QColor, QFont, QPainter, QPainterPath,QPixmap
import os
#certo
class ModernComboBox(QComboBox):
    """ComboBox customizado com animação"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._border_color = QColor("#e0e0e0")
        
    def get_border_color(self):
        return self._border_color
    
    def set_border_color(self, color):
        self._border_color = color
        self.update()
    
    border_color = pyqtProperty(QColor, get_border_color, set_border_color)
    
    def enterEvent(self, event):
        self.animate_border(QColor("#2196f3"))
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        if not self.hasFocus():
            self.animate_border(QColor("#e0e0e0"))
        super().leaveEvent(event)
    
    def animate_border(self, color):
        anim = QPropertyAnimation(self, b"border_color")
        anim.setDuration(200)
        anim.setStartValue(self._border_color)
        anim.setEndValue(color)
        anim.setEasingCurve(QEasingCurve.InOutQuad)
        anim.start()


class ModernButton(QPushButton):
    """Botão customizado com efeitos"""
    def __init__(self, text, primary=False, parent=None):
        super().__init__(text, parent)
        self.primary = primary
        self.setMouseTracking(True)
        self._hover = False
        
    def enterEvent(self, event):
        self._hover = True
        self.update()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        self._hover = False
        self.update()
        super().leaveEvent(event)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = self.rect()
        path = QPainterPath()
        path.addRoundedRect(rect.x(), rect.y(), rect.width(), rect.height(), 10, 10)
        
        if self.primary:
            if self.isDown():
                painter.fillPath(path, QColor("#1565c0"))
            elif self._hover:
                painter.fillPath(path, QColor("#1976d2"))
            else:
                # Gradiente
                from PyQt5.QtGui import QLinearGradient
                gradient = QLinearGradient(0, 0, 0, rect.height())
                gradient.setColorAt(0, QColor("#2196f3"))
                gradient.setColorAt(1, QColor("#1976d2"))
                painter.fillPath(path, gradient)
        else:
            if self.isDown():
                painter.fillPath(path, QColor("#dee2e6"))
            elif self._hover:
                painter.fillPath(path, QColor("#e9ecef"))
            else:
                painter.fillPath(path, QColor("#f8f9fa"))
        
        # Texto
        painter.setPen(QColor("white") if self.primary else QColor("#495057"))
        font = QFont("Segoe UI", 10, QFont.DemiBold)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignCenter, self.text())


class PoligonizadorDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Poligonizador de Linha de Corte")
        self.setFixedSize(500, 500)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.setup_ui()
        self.apply_styles()
        self.load_embasa_logo()
        
    def setup_ui(self):
        # Container principal com sombra
        main_container = QFrame(self)
        main_container.setObjectName("mainContainer")
        main_container.setGeometry(10, 10, 420, 430)
        
        # Sombra
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setXOffset(0)
        shadow.setYOffset(5)
        shadow.setColor(QColor(0, 0, 0, 40))
        main_container.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(main_container)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        

        self.logo_label = QLabel(main_container)
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.logo_label.setMaximumHeight(70)
        self.logo_label.setStyleSheet("background: transparent;")
        layout.addWidget(self.logo_label)
        
        # Header com ícone
        header_layout = QHBoxLayout()
        
        icon_label = QLabel("🗺️")
        icon_label.setStyleSheet("font-size: 32px;")
        
        title_container = QVBoxLayout()
        title_container.setSpacing(4)
        
        title = QLabel("Poligonizador")
        title.setObjectName("title")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
       
       
        
        subtitle = QLabel("Configure a conexão e selecione a área")
        subtitle.setObjectName("subtitle")
        subtitle.setFont(QFont("Segoe UI", 10))
        
        
        title_container.addWidget(title)
        title_container.addWidget(subtitle)
        
        header_layout.addWidget(icon_label)
        header_layout.addLayout(title_container)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Separador
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setObjectName("separator")
        layout.addWidget(separator)
        
        # Label da conexão
        conn_label = QLabel("Conexão PostgreSQL")
        conn_label.setFont(QFont("Segoe UI", 11, QFont.DemiBold))
        conn_label.setStyleSheet("color: #37474f; margin-top: 5px;")
        layout.addWidget(conn_label)
        
        # ComboBox customizado
        self.combo_conexao = ModernComboBox()
        self.combo_conexao.setObjectName("comboBox_conexao")
      
        self.combo_conexao.setFont(QFont("Segoe UI", 10))
        layout.addWidget(self.combo_conexao)
        
        layout.addSpacing(10)
        
        # Botão de selecionar quadra (destaque)
        self.btn_selecionar = ModernButton("📍 Selecionar Quadra no Mapa", primary=True)
        self.btn_selecionar.setObjectName("btnSelecionar")
        self.btn_selecionar.setCursor(Qt.PointingHandCursor)
        self.btn_selecionar.setFont(QFont("Segoe UI", 11, QFont.DemiBold))
        self.btn_selecionar.setFixedHeight(50)
        layout.addWidget(self.btn_selecionar)
        
        layout.addStretch()
        
        # Botões de ação
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(12)
        
        self.btn_cancelar = ModernButton("Cancelar")
        self.btn_cancelar.setObjectName("btnCancelar")
        self.btn_cancelar.setCursor(Qt.PointingHandCursor)
        self.btn_cancelar.setFixedHeight(40)
        self.btn_cancelar.clicked.connect(self.reject)
        
        self.btn_ok = ModernButton("Confirmar", primary=True)
        self.btn_ok.setObjectName("btnOk")
        self.btn_ok.setCursor(Qt.PointingHandCursor)
        self.btn_ok.setFixedHeight(40)
        self.btn_ok.clicked.connect(self.accept)
        
        buttons_layout.addWidget(self.btn_cancelar)
        buttons_layout.addWidget(self.btn_ok)
        
        layout.addLayout(buttons_layout)
        
    def apply_styles(self):
        self.setStyleSheet("""
            QFrame#mainContainer {
                background-color: white;
                border-radius: 16px;
            }
            
            QLabel#title {
                color: #1a1a1a;
            }
            
            QLabel#subtitle {
                color: #78909c;
            }
            
            QFrame#separator {
                background-color: #eceff1;
                max-height: 1px;
                border: none;
            }
            
            QComboBox#comboConexao {
                background-color: #f5f7fa;
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                padding: 12px 16px;
                color: #37474f;
                min-height: 20px;
            }
            
            QComboBox#comboConexao:focus {
                border: 2px solid #2196f3;
                background-color: white;
            }
            
            QComboBox#comboConexao::drop-down {
                border: none;
                width: 30px;
            }
            
            QComboBox#comboConexao::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #78909c;
                margin-right: 8px;
            }
            
            QComboBox#comboConexao QAbstractItemView {
                background-color: white;
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                selection-background-color: #e3f2fd;
                selection-color: #1976d2;
                padding: 5px;
                outline: none;
            }
            
            QComboBox#comboConexao QAbstractItemView::item {
                padding: 10px 16px;
                border-radius: 6px;
            }
            
            QComboBox#comboConexao QAbstractItemView::item:hover {
                background-color: #f0f7ff;
            }
        """)
    
    def load_embasa_logo(self):
        # Caminho relativo ao arquivo Python
        current_dir = os.path.dirname(os.path.abspath(__file__))
        image_path = os.path.join(current_dir, "logo.png")

        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(200, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.logo_label.setPixmap(scaled_pixmap)
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()


# Para testar
