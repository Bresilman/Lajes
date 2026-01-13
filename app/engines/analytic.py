import math
from typing import Dict, Any
from app.engines.interfaces import ICalculationEngine
from app.engines.coefficients import TableSolver
from app.models.base import Laje
from config import settings

class AnalyticEngine(ICalculationEngine):
    """
    Motor analítico NBR 6118:2023.
    Suporta: Placas (Marcus/Bares) e Balanços (Isostáticos).
    """

    def calcular_esforcos_elu(self, laje: Laje) -> Dict[str, float]:
        pp = laje.get_peso_proprio()
        # Carga de cálculo (ELU)
        pd = (laje.carregamento.g_revestimento + laje.carregamento.g_paredes + pp) * settings.GAMMA_G + \
             laje.carregamento.q_acidental * settings.GAMMA_Q
        
        # --- DETECÇÃO DE BALANÇO (ISÓSTATICO) ---
        # Verifica se é um caso de Marquise (3 livres, 1 engastada)
        num_livres = sum(1 for b in laje.bordas.values() if b == 'livre')
        num_engastes = sum(1 for b in laje.bordas.values() if b == 'engastado')
        
        if num_livres == 3 and num_engastes == 1:
            return self._calcular_balanco_elu(laje, pd)

        # --- CÁLCULO PADRÃO DE PLACAS (MARCUS) ---
        lx, ly = laje.lx, laje.ly
        lam = ly / lx
        
        caso = TableSolver.identificar_caso(laje.bordas)
        coeffs = TableSolver.get_coefficients(caso, lam)

        mx = (pd * (lx ** 2)) / coeffs['alpha_x']
        my = (pd * (lx ** 2)) / coeffs['alpha_y']
        
        v_sd_x = coeffs['mu_x'] * pd * lx
        v_sd_y = coeffs['mu_y'] * pd * lx

        # Reações nas vigas (Método das Áreas)
        if ly >= lx:
            reacao_viga_paralela_x = (pd * lx) / 4.0 
            area_trapezio = (lx * ly / 2.0) - (lx**2 / 4.0)
            reacao_viga_paralela_y = (area_trapezio * pd) / ly 
        else:
            reacao_viga_paralela_y = (pd * ly) / 4.0
            area_trapezio = (lx * ly / 2.0) - (ly**2 / 4.0)
            reacao_viga_paralela_x = (area_trapezio * pd) / lx

        return {
            "mx": round(mx, 2), "my": round(my, 2),
            "mx_neg": 0.0, "my_neg": 0.0, # Negativos de continuidade (definidos no floor_system)
            "v_sd_x": round(v_sd_x, 2), "v_sd_y": round(v_sd_y, 2),
            "reacao_viga_x": round(reacao_viga_paralela_x, 2),
            "reacao_viga_y": round(reacao_viga_paralela_y, 2)
        }

    def _calcular_balanco_elu(self, laje: Laje, pd: float) -> Dict[str, float]:
        """
        Cálculo específico para lajes em balanço (Marquises).
        M = q * L² / 2 (Negativo).
        """
        # Identificar qual é o lado do engaste e qual é o comprimento do balanço
        l_balanco = 0.0
        eixo_principal = 'x' # x ou y
        
        b = laje.bordas
        reacoes = {"reacao_viga_x": 0.0, "reacao_viga_y": 0.0}
        
        # Mapeamento para saber onde aplicar o momento negativo no retorno
        res = {"mx": 0.0, "my": 0.0, "mx_neg": 0.0, "my_neg": 0.0}

        if b.get('esquerda') == 'engastado' or b.get('direita') == 'engastado':
            l_balanco = laje.lx
            eixo_principal = 'x'
            # A carga vai toda para a viga vertical (que tem comprimento Ly)
            # Reação linear = Carga Total / Ly = (pd * Lx * Ly) / Ly = pd * Lx
            reacoes["reacao_viga_y"] = pd * l_balanco
            
            # Momento Negativo Principal
            m_neg = (pd * l_balanco**2) / 2.0
            res['mx_neg'] = round(m_neg, 2)
            
            # Armadura de distribuição no outro sentido (mínima, mas calculamos fictício)
            res['my'] = round(m_neg * 0.2, 2) # 20% para distribuição

        elif b.get('topo') == 'engastado' or b.get('fundo') == 'engastado':
            l_balanco = laje.ly
            eixo_principal = 'y'
            # A carga vai toda para a viga horizontal (que tem comprimento Lx)
            reacoes["reacao_viga_x"] = pd * l_balanco
            
            m_neg = (pd * l_balanco**2) / 2.0
            res['my_neg'] = round(m_neg, 2)
            res['mx'] = round(m_neg * 0.2, 2)

        # Cisalhamento Máximo (no apoio)
        v_sd = pd * l_balanco
        
        res.update({
            "v_sd_x": round(v_sd, 2) if eixo_principal == 'x' else 0.0,
            "v_sd_y": round(v_sd, 2) if eixo_principal == 'y' else 0.0,
            "reacao_viga_x": round(reacoes['reacao_viga_x'], 2),
            "reacao_viga_y": round(reacoes['reacao_viga_y'], 2)
        })
        
        return res

    def dimensionar_armaduras(self, laje: Laje, esforcos: Dict[str, float]) -> Dict[str, Any]:
        # ... (Manter código existente igual) ...
        # (Copiar o método dimensionar_armaduras da versão anterior)
        fcd = (laje.materiais.fck / 10.0) / settings.GAMMA_C
        fyd = (laje.materiais.fyk / 10.0) / settings.GAMMA_S
        bw = 100.0; d = laje.d * 100.0 
        resultados_as = {}
        for pos in ['mx', 'my', 'mx_neg', 'my_neg']:
            md_kNm = esforcos.get(pos, 0.0)
            if md_kNm <= 0:
                resultados_as[pos] = 0.0
                continue
            md = md_kNm * 100.0
            kmd = md / (bw * (d**2) * fcd)
            if kmd > 0.377:
                resultados_as[pos] = "REPROVADO (Ductilidade)"
                continue
            x = 1.25 * (1 - math.sqrt(1 - 2 * kmd)) * d
            z = d - 0.4 * x
            as_calc = md / (z * fyd)
            as_min = 0.0015 * bw * (laje.h * 100.0)
            resultados_as[pos] = round(max(as_calc, as_min), 2)
        return resultados_as

    def verificar_cisalhamento(self, laje: Laje, as_flexao: Dict[str, float]) -> Dict[str, Any]:
        # ... (Manter código existente igual) ...
        # (Copiar o método verificar_cisalhamento da versão anterior)
        esforcos = self.calcular_esforcos_elu(laje)
        v_sd = max(esforcos['v_sd_x'], esforcos['v_sd_y'])
        fctm = 0.3 * (laje.materiais.fck ** (2/3)); fctd = (0.7 * fctm) / settings.GAMMA_C
        tau_rd = 0.25 * fctd * 1000 
        d = laje.d
        bw = 1.0
        if hasattr(laje, 'intereixo') and hasattr(laje, 'largura_sapata'):
            num = 1.0 / laje.intereixo; bw = num * laje.largura_sapata
            if bw <= 0: bw = 1.0 
        as_efetivo = max([v for v in as_flexao.values() if isinstance(v, (int, float))]) if as_flexao else 0
        rho1 = min((as_efetivo / 10000.0) / (bw * d), 0.02)
        k = max(1.0, 1.6 - d)
        v_rd1 = (tau_rd * k * (1.2 + 40 * rho1)) * bw * d
        return {"v_sd": round(v_sd, 2), "v_rd1": round(v_rd1, 2), "ratio": round(v_sd / v_rd1, 3) if v_rd1>0 else 0, "status": "OK" if v_sd <= v_rd1 else "FALHA", "detalhes": f"bw={bw:.2f}m"}

    def verificar_fissuracao(self, laje: Laje, esforcos_elu: Dict[str, float], as_adotado: Dict[str, float]) -> Dict[str, Any]:
        # ... (Manter código existente igual) ...
        # (Copiar método verificar_fissuracao da versão anterior)
        # Brevidade: Retorna lógica já implementada
        pp = laje.get_peso_proprio()
        p_freq = (laje.carregamento.g_revestimento + laje.carregamento.g_paredes + pp) + (0.4 * laje.carregamento.q_acidental)
        p_elu = (laje.carregamento.g_revestimento + laje.carregamento.g_paredes + pp) * settings.GAMMA_G + laje.carregamento.q_acidental * settings.GAMMA_Q
        fator = p_freq / p_elu if p_elu > 0 else 1.0
        max_wk = 0.0; status = "OK"; lim = 0.3
        Es = 210000.0; fctm = 0.3 * (laje.materiais.fck ** (2/3))
        for pos in ['mx', 'my', 'mx_neg', 'my_neg']:
            md = esforcos_elu.get(pos, 0.0); as_nec = as_adotado.get(pos, 0.0)
            if md <= 0 or not isinstance(as_nec, (int, float)) or as_nec <= 0: continue
            md_s = md * fator * 100; as_cm2 = as_nec; z = 0.85 * laje.d * 100
            sig = md_s / (z * as_cm2); sig_mpa = sig * 10
            wk = (10 / (12.5 * 2.25)) * (sig_mpa / Es) * (3 * sig_mpa / fctm)
            if wk > max_wk: max_wk = wk
        if max_wk > lim: status = "ALERTA"
        return {"wk_max_mm": round(max_wk, 3), "limite_norma_mm": lim, "status": status}

    def verificar_els(self, laje: Laje) -> Dict[str, Any]:
        """
        Cálculo de Flecha para Balanço ou Placa.
        """
        pp = laje.get_peso_proprio()
        p_els = laje.carregamento.g_revestimento + laje.carregamento.g_paredes + pp + (0.3 * laje.carregamento.q_acidental)
        Ecs_kNm2 = laje.materiais.Ecs * 1e6
        h = laje.h
        Ic = laje.get_inercia_flexao()
        
        # Verificar se é Balanço para usar fórmula correta de flecha
        num_livres = sum(1 for b in laje.bordas.values() if b == 'livre')
        num_engastes = sum(1 for b in laje.bordas.values() if b == 'engastado')
        
        if num_livres == 3 and num_engastes == 1:
            # Fórmula flecha elástica balanço (carga distribuída)
            # f = (q * L^4) / (8 * E * I)
            # Identificar L do balanço
            l_balanco = laje.lx if (laje.bordas.get('esquerda')=='engastado' or laje.bordas.get('direita')=='engastado') else laje.ly
            
            # Rigidez equivalente (Branson) simplificada para balanço:
            # Momento máximo no engaste
            ma = (p_els * l_balanco**2) / 2.0
            
            # (Cálculo Ieq igual ao anterior)
            fctm_MPa = 0.3 * (laje.materiais.fck ** (2/3)); w = Ic / (h/2.0); mr = 1.2 * (fctm_MPa * 1000.0) * w
            i_ii = Ic * 0.25
            ieq = ((mr/ma)**3)*Ic + (1-(mr/ma)**3)*i_ii if ma > mr else Ic
            
            flecha_e = (p_els * (l_balanco**4)) / (8 * Ecs_kNm2 * ieq)
            flecha_total = flecha_e * (1 + settings.ALFA_T_INFINITO)
            
            # Limite para balanço é mais rigoroso: L/125 (dobro da deformação visual)
            limite = l_balanco / 125.0 
            
            return {
                "flecha_total_mm": round(flecha_total * 1000.0, 2),
                "limite_norma_mm": round(limite * 1000.0, 2),
                "status": "OK" if flecha_total <= limite else "FALHA"
            }
        
        # --- Cálculo Padrão Placa (Copiado da versão anterior) ---
        fctm_MPa = 0.3 * (laje.materiais.fck ** (2/3))
        w = Ic / (h / 2.0)
        mr = 1.2 * (fctm_MPa * 1000.0) * w 
        ma = (p_els * (laje.lx ** 2)) / 8.0
        i_ii = Ic * 0.25 
        ieq = ((mr / ma)**3) * Ic + (1 - (mr / ma)**3) * i_ii if ma > mr else Ic
        flecha_e = (5/384) * (p_els * (laje.lx**4)) / (Ecs_kNm2 * ieq)
        lam = laje.ly / laje.lx
        k_marcus = (lam**4) / (1 + lam**4)
        flecha_e_2d = flecha_e * k_marcus
        flecha_total = flecha_e_2d * (1 + settings.ALFA_T_INFINITO)
        limite = laje.lx / 250.0
        
        return {
            "flecha_total_mm": round(flecha_total * 1000.0, 2),
            "limite_norma_mm": round(limite * 1000.0, 2),
            "status": "OK" if flecha_total <= limite else "FALHA"
        }