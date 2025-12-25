# ui/gui/main_window.py
import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QComboBox, 
                             QPushButton, QTabWidget, QGroupBox, QTextEdit, 
                             QFormLayout, QMessageBox, QCheckBox)
from PyQt6.QtCore import Qt

# Importações do Core do PyLaje
from app.models.value_objects import Materiais, Carregamento, ClasseAgressividade, CondicaoContorno
from app.models.solid import LajeMacica
from app.models.ribbed import LajeTrelicada
from app.engines.analytic import AnalyticEngine
from app.controllers.slab_controller import SlabController
from app.services.report_formatter import ReportFormatter
from app.services.catalog_service import catalog_service
from config import settings

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyLaje 2024 - Dimensionamento NBR 6118")
        self.setGeometry(100, 100, 1000, 700)
        
        # Estrutura Principal
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget) # Dividido em Esq (Inputs) e Dir (Resultados)

        # === PAINEL ESQUERDO: INPUTS ===
        self.left_panel = QWidget()
        self.left_layout = QVBoxLayout(self.left_panel)
        self.left_panel.setFixedWidth(400) # Largura fixa para inputs
        
        # 1. Seleção do Tipo de Laje
        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems(["Laje Maciça", "Laje Treliçada"])
        self.combo_tipo.currentIndexChanged.connect(self.toggle_inputs_por_tipo)
        self.left_layout.addWidget(QLabel("<b>Tipo de Laje:</b>"))
        self.left_layout.addWidget(self.combo_tipo)

        # 2. Abas de Configuração
        self.tabs = QTabWidget()
        self.setup_tab_geometria()
        self.setup_tab_cargas_materiais()
        self.setup_tab_detalhes() # Aba dinâmica
        self.left_layout.addWidget(self.tabs)

        # 3. Botões de Ação
        self.btn_calcular = QPushButton("Verificar (Calcular)")
        self.btn_calcular.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px;")
        self.btn_calcular.clicked.connect(self.run_calculation)
        
        self.btn_otimizar = QPushButton("Otimizar Altura (h)")
        self.btn_otimizar.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; padding: 10px;")
        self.btn_otimizar.clicked.connect(self.run_optimization)

        self.left_layout.addWidget(self.btn_calcular)
        self.left_layout.addWidget(self.btn_otimizar)
        self.left_layout.addStretch()

        # === PAINEL DIREITO: RESULTADOS ===
        self.right_panel = QWidget()
        self.right_layout = QVBoxLayout(self.right_panel)
        
        self.text_report = QTextEdit()
        self.text_report.setReadOnly(True)
        self.text_report.setStyleSheet("font-family: Consolas; font-size: 12px;")
        self.text_report.setPlaceholderText("Os resultados da análise aparecerão aqui...")
        
        self.right_layout.addWidget(QLabel("<b>Relatório de Análise:</b>"))
        self.right_layout.addWidget(self.text_report)

        # Adicionar painéis ao layout principal
        self.main_layout.addWidget(self.left_panel)
        self.main_layout.addWidget(self.right_panel)

        # Inicialização
        self.toggle_inputs_por_tipo() # Ajusta visibilidade inicial

    def setup_tab_geometria(self):
        self.tab_geo = QWidget()
        layout = QFormLayout()
        
        self.input_lx = QLineEdit("4.00")
        self.input_ly = QLineEdit("5.00")
        
        # Bordas (Topologia)
        self.group_bordas = QGroupBox("Condições de Contorno")
        vbox_bordas = QVBoxLayout()
        # Simplificação: Checkbox marcado = Engastado, desmarcado = Apoiado
        self.chk_esq = QCheckBox("Engaste Esquerdo")
        self.chk_dir = QCheckBox("Engaste Direito")
        self.chk_top = QCheckBox("Engaste Superior")
        self.chk_bot = QCheckBox("Engaste Inferior")
        
        vbox_bordas.addWidget(self.chk_esq)
        vbox_bordas.addWidget(self.chk_dir)
        vbox_bordas.addWidget(self.chk_top)
        vbox_bordas.addWidget(self.chk_bot)
        self.group_bordas.setLayout(vbox_bordas)

        layout.addRow("Vão Menor Lx (m):", self.input_lx)
        layout.addRow("Vão Maior Ly (m):", self.input_ly)
        layout.addRow(self.group_bordas)
        
        self.tab_geo.setLayout(layout)
        self.tabs.addTab(self.tab_geo, "Geometria")

    def setup_tab_cargas_materiais(self):
        self.tab_mat = QWidget()
        layout = QFormLayout()

        # Cargas
        self.input_g = QLineEdit("1.0") # Revestimento
        self.input_q = QLineEdit("2.0") # Acidental

        # Materiais
        self.input_fck = QComboBox()
        self.input_fck.addItems(["20", "25", "30", "35", "40"])
        self.input_fck.setCurrentText("25")

        self.input_caa = QComboBox()
        self.input_caa.addItems(["I - Fraca", "II - Moderada", "III - Forte", "IV - Muito Forte"])
        self.input_caa.setCurrentText("II - Moderada")

        layout.addRow(QLabel("<b>Cargas (kN/m²):</b>"))
        layout.addRow("Revestimento (Perm):", self.input_g)
        layout.addRow("Acidental (Uso):", self.input_q)
        layout.addRow(QLabel("<b>Materiais:</b>"))
        layout.addRow("Fck (MPa):", self.input_fck)
        layout.addRow("Agressividade (CAA):", self.input_caa)

        self.tab_mat.setLayout(layout)
        self.tabs.addTab(self.tab_mat, "Cargas e Materiais")

    def setup_tab_detalhes(self):
        """Aba dinâmica: Muda campos dependendo se é Maciça ou Treliçada"""
        self.tab_det = QWidget()
        self.layout_det = QFormLayout()

        # Campos Maciça
        self.input_h_macica = QLineEdit("12") # cm
        
        # Campos Treliçada
        self.combo_enchimento = QComboBox()
        # Popula com dados do JSON via CatalogService
        enchimentos = catalog_service.get_todos_enchimentos()
        for e in enchimentos:
            self.combo_enchimento.addItem(f"{e['modelo']} ({e['tipo']})", e['modelo'])
            
        self.input_h_capa = QLineEdit("4") # cm
        self.input_b_sapata = QLineEdit("12") # cm

        # Adiciona tudo ao layout e esconde/mostra depois
        self.lbl_h_macica = QLabel("Espessura h (cm):")
        self.lbl_enchimento = QLabel("Bloco de Enchimento:")
        self.lbl_capa = QLabel("Altura Capa (cm):")
        self.lbl_sapata = QLabel("Largura Nervura (cm):")

        self.layout_det.addRow(self.lbl_h_macica, self.input_h_macica)
        self.layout_det.addRow(self.lbl_enchimento, self.combo_enchimento)
        self.layout_det.addRow(self.lbl_capa, self.input_h_capa)
        self.layout_det.addRow(self.lbl_sapata, self.input_b_sapata)

        self.tab_det.setLayout(self.layout_det)
        self.tabs.addTab(self.tab_det, "Detalhamento")

    def toggle_inputs_por_tipo(self):
        is_macica = self.combo_tipo.currentText() == "Laje Maciça"
        
        # Visibilidade Maciça
        self.lbl_h_macica.setVisible(is_macica)
        self.input_h_macica.setVisible(is_macica)
        
        # Visibilidade Treliçada
        self.lbl_enchimento.setVisible(not is_macica)
        self.combo_enchimento.setVisible(not is_macica)
        self.lbl_capa.setVisible(not is_macica)
        self.input_h_capa.setVisible(not is_macica)
        self.lbl_sapata.setVisible(not is_macica)
        self.input_b_sapata.setVisible(not is_macica)

    def get_user_data(self):
        """Coleta dados da GUI e instancia os Objetos de Domínio."""
        try:
            # 1. Materiais e Cargas Comuns
            fck = float(self.input_fck.currentText())
            mat = Materiais(fck=fck, fyk=500, Ecs=5600 * (fck**0.5)) # Ecs simplificado NBR
            
            cargas = Carregamento(
                g_revestimento=float(self.input_g.text()),
                q_acidental=float(self.input_q.text())
            )
            
            caa_map = {"I - Fraca": ClasseAgressividade.I, "II - Moderada": ClasseAgressividade.II,
                       "III - Forte": ClasseAgressividade.III, "IV - Muito Forte": ClasseAgressividade.IV}
            caa = caa_map[self.input_caa.currentText()]

            # 2. Topologia (Bordas)
            bordas = {
                'esquerda': CondicaoContorno.ENGASTADO if self.chk_esq.isChecked() else CondicaoContorno.APOIADO,
                'direita': CondicaoContorno.ENGASTADO if self.chk_dir.isChecked() else CondicaoContorno.APOIADO,
                'topo': CondicaoContorno.ENGASTADO if self.chk_top.isChecked() else CondicaoContorno.APOIADO,
                'fundo': CondicaoContorno.ENGASTADO if self.chk_bot.isChecked() else CondicaoContorno.APOIADO,
            }

            # Conversão para string p/ compatibilidade com TableSolver antigo (se necessário)
            bordas_str = {k: "engastado" if v == CondicaoContorno.ENGASTADO else "apoiado" for k, v in bordas.items()}

            lx = float(self.input_lx.text())
            ly = float(self.input_ly.text())

            # 3. Instanciação Específica
            if self.combo_tipo.currentText() == "Laje Maciça":
                h = float(self.input_h_macica.text()) / 100.0
                return LajeMacica(lx=lx, ly=ly, h=h, materiais=mat, caa=caa, bordas=bordas_str, carregamento=cargas)
            else:
                # Treliçada
                h_capa = float(self.input_h_capa.text()) / 100.0
                larg_sapata = float(self.input_b_sapata.text()) / 100.0
                modelo_enchimento = self.combo_enchimento.currentData() # ID do modelo
                dados_enchimento = catalog_service.get_modelo_enchimento(modelo_enchimento)
                
                return LajeTrelicada(lx=lx, ly=ly, materiais=mat, caa=caa, bordas=bordas_str, carregamento=cargas,
                                     h_capa=h_capa, largura_sapata=larg_sapata, dados_enchimento=dados_enchimento)

        except ValueError:
            QMessageBox.warning(self, "Erro de Entrada", "Verifique se todos os campos numéricos estão preenchidos corretamente.")
            return None

    def run_calculation(self):
        laje = self.get_user_data()
        if not laje: return
        
        engine = AnalyticEngine()
        controller = SlabController(laje, engine)
        
        result = controller.run_analysis()
        text = ReportFormatter.format_as_text(result)
        self.text_report.setText(text)

    def run_optimization(self):
        laje = self.get_user_data()
        if not laje: return
        
        engine = AnalyticEngine()
        controller = SlabController(laje, engine)
        
        self.text_report.setText("Otimizando espessura... aguarde.")
        QApplication.processEvents() # Atualiza UI
        
        h_opt = controller.optimize_thickness()
        
        if h_opt:
            result = controller.last_result
            text = f"=== OTIMIZAÇÃO BEM SUCEDIDA ===\nAltura ideal encontrada: h = {h_opt*100:.1f} cm\n\n"
            text += ReportFormatter.format_as_text(result)
            self.text_report.setText(text)
            
            # Atualiza o campo de input com o valor otimizado
            if isinstance(laje, LajeMacica):
                self.input_h_macica.setText(f"{h_opt*100:.1f}")
        else:
            self.text_report.setText("Não foi possível encontrar uma altura válida dentro dos limites configurados.")

# Bloco para rodar a GUI diretamente para testes
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())