# ui/gui/main_window.py
import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QComboBox, 
                             QPushButton, QTabWidget, QGroupBox, QTextEdit, 
                             QFormLayout, QMessageBox, QCheckBox, QFileDialog)
from PyQt6.QtCore import Qt
import math

from app.models.value_objects import Materiais, Carregamento, ClasseAgressividade
from app.models.solid import LajeMacica
from app.models.ribbed import LajeTrelicada
from app.engines.analytic import AnalyticEngine
from app.controllers.slab_controller import SlabController
from app.services.report_formatter import ReportFormatter
from app.services.catalog_service import catalog_service

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyLaje 2024 - Dimensionamento NBR 6118")
        self.setGeometry(100, 100, 1100, 750)
        self.current_result = None 

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)

        # Painel Esquerdo
        self.left_panel = QWidget()
        self.left_layout = QVBoxLayout(self.left_panel)
        self.left_panel.setFixedWidth(420)
        
        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems(["Laje Maciça", "Laje Treliçada"])
        self.combo_tipo.currentIndexChanged.connect(self.toggle_inputs_por_tipo)
        self.left_layout.addWidget(QLabel("<b>Tipo de Estrutura:</b>"))
        self.left_layout.addWidget(self.combo_tipo)

        self.tabs = QTabWidget()
        self.setup_tab_geometria()
        self.setup_tab_cargas_materiais()
        self.setup_tab_detalhes()
        self.left_layout.addWidget(self.tabs)

        self.btn_calcular = QPushButton("Verificar Laje")
        self.btn_calcular.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px;")
        self.btn_calcular.clicked.connect(self.run_calculation)
        
        self.btn_otimizar = QPushButton("Otimizar Espessura")
        self.btn_otimizar.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; padding: 10px;")
        self.btn_otimizar.clicked.connect(self.run_optimization)

        self.btn_exportar = QPushButton("Exportar JSON para Vigas")
        self.btn_exportar.setStyleSheet("background-color: #FF9800; color: white; font-weight: bold; padding: 10px;")
        self.btn_exportar.clicked.connect(self.export_data)
        self.btn_exportar.setEnabled(False)

        self.left_layout.addWidget(self.btn_calcular)
        self.left_layout.addWidget(self.btn_otimizar)
        self.left_layout.addWidget(self.btn_exportar)
        self.left_layout.addStretch()

        # Painel Direito
        self.right_panel = QWidget()
        self.right_layout = QVBoxLayout(self.right_panel)
        self.text_report = QTextEdit()
        self.text_report.setReadOnly(True)
        self.text_report.setStyleSheet("font-family: 'Consolas', 'Monaco', monospace; font-size: 11px; background-color: #f8f9fa;")
        self.right_layout.addWidget(QLabel("<b>Relatório de Engenharia:</b>"))
        self.right_layout.addWidget(self.text_report)

        self.main_layout.addWidget(self.left_panel)
        self.main_layout.addWidget(self.right_panel)
        self.toggle_inputs_por_tipo()

    def setup_tab_geometria(self):
        self.tab_geo = QWidget()
        layout = QFormLayout()
        self.input_lx = QLineEdit("4.00")
        self.input_ly = QLineEdit("5.00")
        self.group_bordas = QGroupBox("Bordas Engastadas")
        vbox_bordas = QVBoxLayout()
        self.chk_esq = QCheckBox("Esquerda")
        self.chk_dir = QCheckBox("Direita")
        self.chk_top = QCheckBox("Superior")
        self.chk_bot = QCheckBox("Inferior")
        vbox_bordas.addWidget(self.chk_esq); vbox_bordas.addWidget(self.chk_dir)
        vbox_bordas.addWidget(self.chk_top); vbox_bordas.addWidget(self.chk_bot)
        self.group_bordas.setLayout(vbox_bordas)
        layout.addRow("Vão Lx (m):", self.input_lx)
        layout.addRow("Vão Ly (m):", self.input_ly)
        layout.addRow(self.group_bordas)
        self.tab_geo.setLayout(layout)
        self.tabs.addTab(self.tab_geo, "Vãos")

    def setup_tab_cargas_materiais(self):
        self.tab_mat = QWidget()
        layout = QFormLayout()
        self.input_g = QLineEdit("1.0")
        self.input_q = QLineEdit("2.0")
        self.input_fck = QComboBox()
        self.input_fck.addItems(["20", "25", "30", "35", "40"])
        self.input_fck.setCurrentText("25")
        
        # DROPDOWN AGREGADO (Para cálculo de Ecs)
        self.combo_agregado = QComboBox()
        self.combo_agregado.addItem("Basalto (Alfa=1.2)", 1.2)
        self.combo_agregado.addItem("Granito (Alfa=1.0)", 1.0)
        self.combo_agregado.addItem("Calcário (Alfa=0.9)", 0.9)
        self.combo_agregado.addItem("Arenito (Alfa=0.7)", 0.7)
        self.combo_agregado.setCurrentIndex(1)

        self.input_caa = QComboBox()
        self.input_caa.addItems(["I - Fraca", "II - Moderada", "III - Forte", "IV - Muito Forte"])
        self.input_caa.setCurrentText("II - Moderada")

        layout.addRow("Revestimento (kN/m²):", self.input_g)
        layout.addRow("Uso/Acidental (kN/m²):", self.input_q)
        layout.addRow("Concreto fck (MPa):", self.input_fck)
        layout.addRow("Tipo de Agregado:", self.combo_agregado)
        layout.addRow("Agressividade (CAA):", self.input_caa)
        self.tab_mat.setLayout(layout)
        self.tabs.addTab(self.tab_mat, "Materiais/Cargas")

    def setup_tab_detalhes(self):
        self.tab_det = QWidget()
        self.layout_det = QFormLayout()
        self.input_h_macica = QLineEdit("12")
        self.combo_enchimento = QComboBox()
        for e in catalog_service.get_todos_enchimentos():
            self.combo_enchimento.addItem(f"{e['modelo']} ({e['tipo']})", e['modelo'])
        self.input_h_capa = QLineEdit("4")
        self.input_b_sapata = QLineEdit("12")
        self.lbl_h_macica = QLabel("Espessura h (cm):")
        self.lbl_enchimento = QLabel("Bloco Enchimento:")
        self.lbl_capa = QLabel("Capa Concreto (cm):")
        self.lbl_sapata = QLabel("Largura Nervura (cm):")
        self.layout_det.addRow(self.lbl_h_macica, self.input_h_macica)
        self.layout_det.addRow(self.lbl_enchimento, self.combo_enchimento)
        self.layout_det.addRow(self.lbl_capa, self.input_h_capa)
        self.layout_det.addRow(self.lbl_sapata, self.input_b_sapata)
        self.tab_det.setLayout(self.layout_det)
        self.tabs.addTab(self.tab_det, "Detalhamento")

    def toggle_inputs_por_tipo(self):
        is_macica = self.combo_tipo.currentText() == "Laje Maciça"
        self.lbl_h_macica.setVisible(is_macica); self.input_h_macica.setVisible(is_macica)
        self.lbl_enchimento.setVisible(not is_macica); self.combo_enchimento.setVisible(not is_macica)
        self.lbl_capa.setVisible(not is_macica); self.input_h_capa.setVisible(not is_macica)
        self.lbl_sapata.setVisible(not is_macica); self.input_b_sapata.setVisible(not is_macica)

    def get_user_data(self):
        try:
            fck = float(self.input_fck.currentText())
            # Cálculo de Ecs conforme NBR 6118
            alfa_e = self.combo_agregado.currentData()
            eci = alfa_e * 5600 * math.sqrt(fck)
            ecs = 0.85 * eci if fck <= 50 else eci # Simplificação NBR
            
            mat = Materiais(fck=fck, fyk=500, Ecs=ecs/1000.0) # Transforma para GPa p/ o modelo
            cargas = Carregamento(g_revestimento=float(self.input_g.text()), q_acidental=float(self.input_q.text()))
            caa_map = {"I - Fraca": ClasseAgressividade.I, "II - Moderada": ClasseAgressividade.II,
                       "III - Forte": ClasseAgressividade.III, "IV - Muito Forte": ClasseAgressividade.IV}
            caa = caa_map[self.input_caa.currentText()]
            bordas = {
                'esquerda': "engastado" if self.chk_esq.isChecked() else "apoiado",
                'direita': "engastado" if self.chk_dir.isChecked() else "apoiado",
                'topo': "engastado" if self.chk_top.isChecked() else "apoiado",
                'fundo': "engastado" if self.chk_bot.isChecked() else "apoiado",
            }
            lx, ly = float(self.input_lx.text()), float(self.input_ly.text())
            if self.combo_tipo.currentText() == "Laje Maciça":
                h = float(self.input_h_macica.text()) / 100.0
                return LajeMacica(lx=lx, ly=ly, h=h, materiais=mat, caa=caa, bordas=bordas, carregamento=cargas)
            else:
                modelo = self.combo_enchimento.currentData()
                dados_ench = catalog_service.get_modelo_enchimento(modelo)
                return LajeTrelicada(lx=lx, ly=ly, materiais=mat, caa=caa, bordas=bordas, carregamento=cargas,
                                     h_capa=float(self.input_h_capa.text())/100.0, 
                                     largura_sapata=float(self.input_b_sapata.text())/100.0, 
                                     dados_enchimento=dados_ench)
        except Exception as e:
            QMessageBox.warning(self, "Dados Inválidos", f"Erro: {e}")
            return None

    def run_calculation(self):
        laje = self.get_user_data()
        if not laje: return
        self.current_result = SlabController(laje, AnalyticEngine()).run_analysis()
        self.text_report.setText(ReportFormatter.format_as_text(self.current_result))
        self.btn_exportar.setEnabled(True)

    def run_optimization(self):
        laje = self.get_user_data()
        if not laje: return
        self.text_report.setText("Calculando altura ótima...")
        QApplication.processEvents()
        h_opt = SlabController(laje, AnalyticEngine()).optimize_thickness()
        if h_opt:
            self.run_calculation()
            if isinstance(laje, LajeMacica): self.input_h_macica.setText(f"{h_opt*100:.1f}")
        else:
            self.text_report.setText("Não foi possível otimizar nos limites atuais.")

    def export_data(self):
        if not self.current_result: return
        path, _ = QFileDialog.getSaveFileName(self, "Salvar JSON", f"laje_{self.current_result.lx}x{self.current_result.ly}.json", "JSON (*.json)")
        if path: ReportFormatter.save_json(self.current_result, path)