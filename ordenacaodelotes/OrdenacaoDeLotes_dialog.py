# -*- coding: utf-8 -*-
"""
Interface Premium para o plugin Organizador de Lotes
Estrutura similar ao exemplo - Compatível com QGIS
Tema: Embasa
"""

from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QPushButton, QLineEdit, QFrame, QGraphicsDropShadowEffect, QSizePolicy
)
from qgis.PyQt.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty
from qgis.PyQt.QtGui import QColor, QFont, QPainter, QPainterPath, QLinearGradient, QPixmap, QImage
import os


class ModernComboBox(QComboBox):
    """ComboBox customizado com animação"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._border_color = QColor("#dee2e6")
        
    def get_border_color(self):
        return self._border_color
    
    def set_border_color(self, color):
        self._border_color = color
        self.update()
    
    border_color = pyqtProperty(QColor, get_border_color, set_border_color)
    
    def enterEvent(self, event):
        self.animate_border(QColor("#4fa3d1"))
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        if not self.hasFocus():
            self.animate_border(QColor("#dee2e6"))
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
    def __init__(self, text, button_style="primary", parent=None):
        super().__init__(text, parent)
        self.button_style = button_style
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
        path.addRoundedRect(rect.x(), rect.y(), rect.width(), rect.height(), 12, 12)
        
        if self.button_style == "primary":
            # Gradiente Embasa - Azul
            gradient = QLinearGradient(0, 0, 0, rect.height())
            if self.isDown():
                gradient.setColorAt(0, QColor("#002d5c"))
                gradient.setColorAt(1, QColor("#003d7a"))
            elif self._hover:
                gradient.setColorAt(0, QColor("#0056a8"))
                gradient.setColorAt(1, QColor("#4fa3d1"))
            else:
                gradient.setColorAt(0, QColor("#003d7a"))
                gradient.setColorAt(1, QColor("#4fa3d1"))
            painter.fillPath(path, gradient)
            
        elif self.button_style == "danger":
            # Gradiente Embasa - Azul escuro para restaurar
            gradient = QLinearGradient(0, 0, 0, rect.height())
            if self.isDown():
                gradient.setColorAt(0, QColor("#001f3f"))
                gradient.setColorAt(1, QColor("#002d5c"))
            elif self._hover:
                gradient.setColorAt(0, QColor("#003d7a"))
                gradient.setColorAt(1, QColor("#0056a8"))
            else:
                gradient.setColorAt(0, QColor("#002d5c"))
                gradient.setColorAt(1, QColor("#003d7a"))
            painter.fillPath(path, gradient)
            
        else:  # secondary
            gradient = QLinearGradient(0, 0, 0, rect.height())
            if self.isDown():
                gradient.setColorAt(0, QColor("#4fa3d1"))
                gradient.setColorAt(1, QColor("#7dc8e8"))
            elif self._hover:
                gradient.setColorAt(0, QColor("#7dc8e8"))
                gradient.setColorAt(1, QColor("#a8d8f0"))
            else:
                gradient.setColorAt(0, QColor("#7dc8e8"))
                gradient.setColorAt(1, QColor("#b8e3f5"))
            painter.fillPath(path, gradient)
        
        # Texto
        if self.button_style in ["primary", "danger"]:
            painter.setPen(QColor("white"))
        elif self.button_style == "secondary":
            painter.setPen(QColor("#003d7a"))  # Azul escuro Embasa
        else:
            painter.setPen(QColor("#495057"))
        font = QFont("Segoe UI", 10, QFont.DemiBold)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignCenter, self.text())


class OrganizadorDeLotesDialog(QDialog):
    """Interface Premium do Organizador de Lotes"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Organizador de Lotes")
        self.setFixedSize(530, 530)
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        
        self.setup_ui()
        self.apply_styles()
        self.load_logo()
        
    def setup_ui(self):
        """Configura a interface do usuário"""
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Container principal
        main_container = QFrame(self)
        main_container.setObjectName("mainContainer")
        
        container_layout = QVBoxLayout(main_container)
        container_layout.setSpacing(0)
        container_layout.setContentsMargins(0, 0, 0, 0)
        
        # ===== HEADER COM GRADIENTE =====
        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")
        header_frame.setFixedHeight(90)
        
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(25, 20, 25, 20)
        header_layout.setSpacing(8)
        
        # Logo em marca d'água no header
        self.logo_background = QLabel(header_frame)
        self.logo_background.setStyleSheet("background: transparent:")
        self.logo_background.setAlignment(Qt.AlignCenter)
    
        self.logo_background.setGeometry(0, 0, 480, 150)
        self.logo_background.lower()
        self.logo_background.setAttribute(Qt.WA_TransparentForMouseEvents)
        
        # Título com ícone
        title_layout = QHBoxLayout()
        title_layout.setSpacing(12)
        
        icon_label = QLabel("📋")
        icon_label.setStyleSheet("font-size: 40px; background: transparent;")
        
        title_text_layout = QVBoxLayout()
        title_text_layout.setSpacing(3)
        
        title = QLabel("Organizador de Lotes")
        title.setObjectName("headerTitle")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        
        subtitle = QLabel("Sistema de gerenciamento de ordem de lotes")
        subtitle.setObjectName("headerSubtitle")
        subtitle.setFont(QFont("Segoe UI", 9))
        
        title_text_layout.addWidget(title)
        title_text_layout.addWidget(subtitle)
        
        title_layout.addWidget(icon_label)
        title_layout.addLayout(title_text_layout)
        title_layout.addStretch()
        
        header_layout.addLayout(title_layout)
        
        container_layout.addWidget(header_frame)
        
        # ===== CONTEÚDO PRINCIPAL =====
        content_frame = QFrame()
        content_frame.setObjectName("contentFrame")
        
        content_layout = QVBoxLayout(content_frame)
        content_layout.setSpacing(18)
        content_layout.setContentsMargins(5, 5, 5, 5)
        
        # ===== CARD 1: CONEXÃO =====
        conexao_card = self.create_input_card(
            "🔌",
            "Conexão PostgreSQL",
            "Selecione a conexão com o banco de dados"
        )
        
        self.cmbConexao = ModernComboBox()
        self.cmbConexao.setObjectName("cmbConexao")
        self.cmbConexao.setFont(QFont("Segoe UI", 8))
        self.cmbConexao.setMinimumHeight(30)
        self.cmbConexao.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        conexao_card.layout().addWidget(self.cmbConexao)
        
        content_layout.addWidget(conexao_card)
        
        # ===== CARD 2: NOVA ORDEM =====
        ordem_card = self.create_input_card(
            "🔢",
            "Nova Ordem Inicial",
            "Informe qual será a primeira ordem"
        )
        
        self.lineOrdemPrimeira = QLineEdit()
        self.lineOrdemPrimeira.setObjectName("lineOrdemPrimeira")
        self.lineOrdemPrimeira.setPlaceholderText("0")
        self.lineOrdemPrimeira.setFont(QFont("Segoe UI", 8))
        self.lineOrdemPrimeira.setMinimumHeight(30)
        self.lineOrdemPrimeira.setMaximumHeight(30)
        self.lineOrdemPrimeira.setText("0")
        self.lineOrdemPrimeira.setAlignment(Qt.AlignCenter)
        self.lineOrdemPrimeira.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        ordem_card.layout().addWidget(self.lineOrdemPrimeira)
        
        content_layout.addWidget(ordem_card)
        
        # ===== CARD 3: QUADRA =====
        quadra_card = self.create_input_card(
            "📍",
            "Quadra Selecionada",
            "Clique no botão abaixo para selecionar"
        )
        
        self.lineInsQuadra = QLineEdit()
        self.lineInsQuadra.setObjectName("lineInsQuadra")
        self.lineInsQuadra.setPlaceholderText("Nenhuma quadra selecionada")
        self.lineInsQuadra.setFont(QFont("Segoe UI", 8))
        self.lineInsQuadra.setMinimumHeight(30)
        self.lineInsQuadra.setMaximumHeight(30)
        self.lineInsQuadra.setReadOnly(True)
        self.lineInsQuadra.setAlignment(Qt.AlignCenter)
        self.lineInsQuadra.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        quadra_card.layout().addWidget(self.lineInsQuadra)
        
        # Botão selecionar dentro do card
        self.btnSelecionarQuadra = ModernButton("🗺️  Selecionar no Mapa", "secondary")
        self.btnSelecionarQuadra.setObjectName("btnSelecionarQuadra")
        self.btnSelecionarQuadra.setCursor(Qt.PointingHandCursor)
        self.btnSelecionarQuadra.setFont(QFont("Segoe UI", 8, QFont.DemiBold))
        self.btnSelecionarQuadra.setMinimumHeight(30)
        self.btnSelecionarQuadra.setMaximumHeight(30)
        quadra_card.layout().addWidget(self.btnSelecionarQuadra)
        
        content_layout.addWidget(quadra_card)   
        
        content_layout.addSpacing(5)
        
        # ===== BOTÕES PRINCIPAIS =====
        self.btnExecutar = ModernButton("✅  Organizar Ordem dos Lotes", "primary")
        self.btnExecutar.setObjectName("btnExecutar")
        self.btnExecutar.setCursor(Qt.PointingHandCursor)
        self.btnExecutar.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.btnExecutar.setMinimumHeight(30)
        self.btnExecutar.setMaximumHeight(30)
        content_layout.addWidget(self.btnExecutar)
        
        self.btnExcluirNovaOrdem = ModernButton("↩️  Restaurar Ordem Original", "danger")
        self.btnExcluirNovaOrdem.setObjectName("btnExcluirNovaOrdem")
        self.btnExcluirNovaOrdem.setCursor(Qt.PointingHandCursor)
        self.btnExcluirNovaOrdem.setFont(QFont("Segoe UI", 10, QFont.DemiBold))
        self.btnExcluirNovaOrdem.setMinimumHeight(30)
        self.btnExcluirNovaOrdem.setMaximumHeight(30)
        content_layout.addWidget(self.btnExcluirNovaOrdem)
        
        content_layout.addStretch()
        
        container_layout.addWidget(content_frame)
        main_layout.addWidget(main_container)
    
    def create_input_card(self, icon, title, description):
        """Cria card de input estilizado"""
        card = QFrame()
        card.setObjectName("inputCard")
        
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(2)
        card_layout.setContentsMargins(5, 5, 5, 5)
        
        # Header
        header = QHBoxLayout()
        header.setSpacing(5)
        
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 20px;")
        
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        
        title_label = QLabel(title)
        title_label.setObjectName("cardTitle")
        title_label.setFont(QFont("Segoe UI", 9, QFont.Bold))
        
        desc_label = QLabel(description)
        desc_label.setObjectName("cardDesc")
        desc_label.setFont(QFont("Segoe UI", 9))
        
        text_layout.addWidget(title_label)
        text_layout.addWidget(desc_label)
        
        header.addWidget(icon_label)
        header.addLayout(text_layout)
        header.addStretch()
    
        card_layout.addLayout(header)
        
        return card
    
    def apply_styles(self):
        """Aplica estilos CSS"""
        self.setStyleSheet("""
            QDialog {
                background-color: #f0f2f5;
            }
            
            QFrame#mainContainer {
                background-color: white;
                border-radius: 0px;
            }
            
            /* Header com gradiente Embasa */
            QFrame#headerFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #003d7a, stop:0.4 #0056a8, stop:0.7 #4fa3d1, stop:1 #7dc8e8);
            }
            
            QLabel#headerTitle {
                color: white;
                background: transparent;
            }
            
            QLabel#headerSubtitle {
                color: rgba(255, 255, 255, 0.95);
                background: transparent;
            }
            
            QFrame#contentFrame {
                background-color: white;
            }
            
            /* Cards de Input */
            QFrame#inputCard {
                background-color: #f8f9fa;
                border: 2px solid #e9ecef;
                border-radius: 12px;
            }
            
            QFrame#inputCard:hover {
                background-color: white;
                border: 2px solid #dee2e6;
            }
            
            QLabel#cardTitle {
                color: #212529;
            }
            
            QLabel#cardDesc {
                color: #6c757d;
            }
            
            /* ComboBox */
            QComboBox#cmbConexao {
                background-color: white;
                border: 2px solid #dee2e6;
                border-radius: 10px;
                padding: 8px 8px;
                color: #495057;
            }
            
            QComboBox#cmbConexao:hover {
                border: 2px solid #4fa3d1;
            }
            
            QComboBox#cmbConexao:focus {
                border: 2px solid #003d7a;
                background-color: #f0f8ff;
            }
            
            QComboBox#cmbConexao::drop-down {
                border: none;
                width: 30px;
            }
            
            QComboBox#cmbConexao::down-arrow {
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #6c757d;
                margin-right: 10px;
            }
            
            QComboBox#cmbConexao QAbstractItemView {
                background-color: white;
                border: 2px solid #dee2e6;
                border-radius: 10px;
                selection-background-color: #e3f2fd;
                selection-color: #003d7a;
                padding: 6px;
                outline: none;
            }
            
            QComboBox#cmbConexao QAbstractItemView::item {
                padding: 8px 8px;
                border-radius: 6px;
            }
            
            QComboBox#cmbConexao QAbstractItemView::item:hover {
                background-color: #e3f2fd;
            }
            
            /* LineEdit */
            QLineEdit#lineOrdemPrimeira {
                background-color: white;
                border: 2px solid #dee2e6;
                border-radius: 10px;
                padding: 8px 8px;
                color: #495057;
            }
            
            QLineEdit#lineOrdemPrimeira:hover {
                border: 2px solid #4fa3d1;
            }
            
            QLineEdit#lineOrdemPrimeira:focus {
                border: 2px solid #003d7a;
                background-color: #f0f8ff;
            }
            
            QLineEdit#lineInsQuadra {
                background-color: #fff8e1;
                border: 2px solid #ffb74d;
                border-radius: 10px;
                padding: 8px 8px;
                color: #f57c00;
            }
            
            QLineEdit#lineInsQuadra:read-only {
                background-color: #f8f9fa;
                border: 2px solid #dee2e6;
                color: #adb5bd;
            }
            
            /* Botão Secundário dentro do card */
            QPushButton#btnSelecionarQuadra {
                background-color: white;
                border: 2px solid #dee2e6;
                border-radius: 10px;
                color: #495057;
                padding: 8px;
            }
            
            QPushButton#btnSelecionarQuadra:hover {
                background-color: #f8f9fa;
                border: 2px solid #4fa3d1;
                color: #003d7a;
            }
        """)
    
    def load_logo(self):
        """Carrega logo no header com transparência real"""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            image_path = os.path.join(current_dir, "logo.png")

            if os.path.exists(image_path):
                # Carrega imagem com suporte a canal alfa
                image = QImage(image_path).convertToFormat(QImage.Format_ARGB32)
                if not image.isNull():
                    # Redimensiona mantendo transparência
                    scaled_image = image.scaled(
                        180, 70,
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    )

                    # Converte para pixmap preservando alfa
                    transparent_pixmap = QPixmap.fromImage(scaled_image)

                    # Aplica opacidade sobre um fundo transparente
                    final_pixmap = QPixmap(transparent_pixmap.size())
                    final_pixmap.fill(Qt.transparent)

                    painter = QPainter(final_pixmap)
                    painter.setOpacity(0.15)  # 15% de opacidade
                    painter.drawPixmap(0, 0, transparent_pixmap)
                    painter.end()

                    # Define o label com fundo transparente
                    self.logo_background.setPixmap(final_pixmap)
                    self.logo_background.setStyleSheet("background: transparent; border: none;")
                
        except Exception as e:
            print(f"Erro ao carregar logo: {e}")