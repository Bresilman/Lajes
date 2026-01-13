from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsSimpleTextItem, QGraphicsLineItem
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPen, QBrush, QColor, QFont, QTransform, QPainter

class LajeItem(QGraphicsRectItem):
    """Representação gráfica de uma laje."""
    def __init__(self, x, y, lx, ly, nome):
        # CORREÇÃO: Não inverter Y manualmente aqui. A View já faz scale(1, -1).
        # Desenhamos no quadrante positivo do item (0,0 a lx, ly)
        super().__init__(0, 0, lx, ly) 
        self.setPos(x, y) 
        
        # Estilo
        self.setBrush(QBrush(QColor(220, 230, 250))) # Azul claro
        self.setPen(QPen(Qt.GlobalColor.black, 0.05)) # Linha fina (escala em metros)
        
        # Texto (Nome da Laje)
        text = QGraphicsSimpleTextItem(nome, self)
        f = QFont("Arial")
        f.setPointSizeF(0.4) # Tamanho em "metros" visuais
        text.setFont(f)
        
        # Centralizar texto
        br = text.boundingRect()
        text.setPos((lx - br.width()) / 2, (ly - br.height()) / 2)
        
        # O texto precisa ser invertido verticalmente para não aparecer de cabeça para baixo
        # já que o sistema de coordenadas global está invertido (Y+ para cima)
        text.setTransform(QTransform().scale(1, -1).translate(0, -br.height())) 

class ParedeItem(QGraphicsLineItem):
    """Representação visual de uma parede."""
    def __init__(self, x1, y1, x2, y2, carga):
        # CORREÇÃO: Coordenadas cartesianas diretas
        super().__init__(x1, y1, x2, y2)
        
        # Estilo da parede: Vermelha, Grossa
        pen = QPen(Qt.GlobalColor.red, 0.15)
        self.setPen(pen)

class FloorCanvas(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setBackgroundBrush(QBrush(QColor(255, 255, 255)))
        
        # Habilitar Antialiasing
        self.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Escala inicial (Pixels por Metro)
        self.scale(40, 40) 
        # Inverter eixo Y da view para funcionar como cartesiano (Y para cima)
        self.scale(1, -1)

    def draw_grid(self):
        # Grid de 1m em 1m
        pen = QPen(QColor(220, 220, 220), 0) # Cosmetic pen (largura 0)
        pen.setStyle(Qt.PenStyle.DotLine)
        
        # Desenha uma grid grande o suficiente
        size = 50 
        for i in range(-10, size):
            self.scene.addLine(i, -10, i, size, pen) # Verticais
            self.scene.addLine(-10, i, size, i, pen) # Horizontais
            
        # Eixos X e Y destacados
        self.scene.addLine(0, 0, 5, 0, QPen(Qt.GlobalColor.red, 0.05)) # X
        self.scene.addLine(0, 0, 0, 5, QPen(Qt.GlobalColor.green, 0.05)) # Y

    def update_system(self, lajes, paredes):
        self.scene.clear()
        self.draw_grid()
        
        # Desenhar Lajes
        for item in lajes:
            rect = LajeItem(item.x, item.y, item.laje.lx, item.laje.ly, item.id)
            self.scene.addItem(rect)
            
        # Desenhar Paredes
        for p in paredes:
            line = ParedeItem(p.x_inicio, p.y_inicio, p.x_fim, p.y_fim, p.carga_kn_m)
            self.scene.addItem(line)
            
        # Centraliza a vista nos itens se houver
        if lajes:
            self.centerOn(lajes[0].x + lajes[0].laje.lx/2, lajes[0].y + lajes[0].laje.ly/2)