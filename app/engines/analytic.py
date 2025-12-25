import math
from typing import Dict, Any
from app.engines.interfaces import ICalculationEngine
from app.engines.coefficients import TableSolver
from app.models.base import Laje
from config import settings

class AnalyticEngine(ICalculationEngine):
    """
    Motor analítico NBR 6118:2023.
    Correções: Unidade de Ecs (GPa -> kN/m²) corrigida.
    """

    def calcular_esforcos_elu(self, laje: Laje) -> Dict[str, float]:
        pp = laje.get_peso_proprio()
        pd = (laje.carregamento.g_revestimento + pp) * settings.GAMMA_G + \
             laje.carregamento.q_acidental * settings.GAMMA_Q
        
        lx, ly = laje.lx, laje.ly
        lam = ly / lx
        
        caso = TableSolver.identificar_caso(laje.bordas)
        coeffs = TableSolver.get_coefficients(caso, lam)

        mx = (pd * (lx ** 2)) / coeffs['alpha_x']
        my = (pd * (lx ** 2)) / coeffs['alpha_y']
        
        v_sd_x = coeffs['mu_x'] * pd * lx
        v_sd_y = coeffs['mu_y'] * pd * lx

        # Cálculo de Reações (Método das Áreas/Charneiras)
        if ly >= lx:
            # Ly é o lado maior -> Vigas verticais recebem Trapézio
            reacao_viga_paralela_x = (pd * lx) / 4.0 # Vigas horizontais (Triângulo)
            area_trapezio = (lx * ly / 2.0) - (lx**2 / 4.0)
            reacao_viga_paralela_y = (area_trapezio * pd) / ly 
        else:
            # Lx é o lado maior
            reacao_viga_paralela_y = (pd * ly) / 4.0
            area_trapezio = (lx * ly / 2.0) - (ly**2 / 4.0)
            reacao_viga_paralela_x = (area_trapezio * pd) / lx

        return {
            "mx": round(mx, 2), "my": round(my, 2),
            "mx_neg": 0.0, "my_neg": 0.0,
            "v_sd_x": round(v_sd_x, 2), "v_sd_y": round(v_sd_y, 2),
            "reacao_viga_x": round(reacao_viga_paralela_x, 2),
            "reacao_viga_y": round(reacao_viga_paralela_y, 2)
        }

    def dimensionar_armaduras(self, laje: Laje, esforcos: Dict[str, float]) -> Dict[str, Any]:
        fcd = (laje.materiais.fck / 10.0) / settings.GAMMA_C
        fyd = (laje.materiais.fyk / 10.0) / settings.GAMMA_S
        bw = 100.0 
        d = laje.d * 100.0 
        
        resultados_as = {}
        for pos in ['mx', 'my', 'mx_neg', 'my_neg']:
            md_kNm = esforcos.get(pos, 0.0)
            if md_kNm <= 0:
                resultados_as[pos] = 0.0
                continue
            
            md_kNcm = md_kNm * 100.0
            kmd = md_kNcm / (bw * (d**2) * fcd)
            
            if kmd > 0.377:
                resultados_as[pos] = "REPROVADO (Ductilidade)"
                continue
            
            x = 1.25 * (1 - math.sqrt(1 - 2 * kmd)) * d
            z = d - 0.4 * x
            as_calc = md_kNcm / (z * fyd)
            as_min = 0.0015 * bw * (laje.h * 100.0)
            
            resultados_as[pos] = round(max(as_calc, as_min), 2)
            
        return resultados_as

    def verificar_cisalhamento(self, laje: Laje, as_flexao: Dict[str, float]) -> Dict[str, Any]:
        esforcos = self.calcular_esforcos_elu(laje)
        v_sd = max(esforcos['v_sd_x'], esforcos['v_sd_y'])
        
        fctm = 0.3 * (laje.materiais.fck ** (2/3))
        fctd = (0.7 * fctm) / settings.GAMMA_C
        tau_rd = 0.25 * fctd * 1000 

        d = laje.d
        
        bw = 1.0
        if hasattr(laje, 'intereixo') and hasattr(laje, 'largura_sapata'):
            num_nervuras_por_metro = 1.0 / laje.intereixo
            bw = num_nervuras_por_metro * laje.largura_sapata
            if bw <= 0: bw = 1.0 

        as_validos = [v for v in as_flexao.values() if isinstance(v, (int, float))]
        as_efetivo = max(as_validos) if as_validos else 0.0
        
        rho1 = (as_efetivo / 10000.0) / (bw * d)
        rho1 = min(rho1, 0.02)
        
        k = max(1.0, 1.6 - d)
        v_rd1 = (tau_rd * k * (1.2 + 40 * rho1)) * bw * d
        
        return {
            "v_sd": round(v_sd, 2), 
            "v_rd1": round(v_rd1, 2),
            "ratio": round(v_sd / v_rd1, 3) if v_rd1 > 0 else 0,
            "status": "OK" if v_sd <= v_rd1 else "FALHA",
            "detalhes": f"bw={bw:.2f}m"
        }

    def verificar_fissuracao(self, laje: Laje, esforcos_elu: Dict[str, float], as_adotado: Dict[str, float]) -> Dict[str, Any]:
        pp = laje.get_peso_proprio()
        p_freq = (laje.carregamento.g_revestimento + pp) + (0.4 * laje.carregamento.q_acidental)
        p_elu = (laje.carregamento.g_revestimento + pp) * settings.GAMMA_G + laje.carregamento.q_acidental * settings.GAMMA_Q
        fator_servico = p_freq / p_elu if p_elu > 0 else 1.0
        
        max_wk = 0.0
        status = "OK"
        limites_wk = {"I": 0.4, "II": 0.3, "III": 0.2, "IV": 0.2}
        limite = limites_wk.get(laje.caa.name, 0.3) 

        Es = 210000.0 # MPa
        fctm = 0.3 * (laje.materiais.fck ** (2/3)) # MPa

        for pos in ['mx', 'my', 'mx_neg', 'my_neg']:
            md_elu = esforcos_elu.get(pos, 0.0)
            as_nec = as_adotado.get(pos, 0.0)
            
            if md_elu <= 0 or not isinstance(as_nec, (int, float)) or as_nec <= 0:
                continue
                
            md_serv = md_elu * fator_servico # kNm
            d_m = laje.d
            z_est = 0.85 * d_m 
            
            md_serv_kNcm = md_serv * 100.0
            as_cm2 = as_nec
            z_cm = z_est * 100.0
            
            if z_cm * as_cm2 == 0: continue

            sigma_s = md_serv_kNcm / (z_cm * as_cm2) # kN/cm²
            sigma_s_MPa = sigma_s * 10.0 
            
            eta1 = 2.25 
            phi_est = 10.0
            
            term1 = phi_est / (12.5 * eta1)
            term2 = sigma_s_MPa / Es
            term3 = (3 * sigma_s_MPa) / fctm
            
            wk = term1 * term2 * term3
            if wk > max_wk:
                max_wk = wk
        
        if max_wk > limite:
            status = "ALERTA"

        return {
            "wk_max_mm": round(max_wk, 3),
            "limite_norma_mm": limite,
            "status": status
        }

    def verificar_els(self, laje: Laje) -> Dict[str, Any]:
        """
        Cálculo de Flecha Corrigido.
        """
        pp = laje.get_peso_proprio()
        p_els = laje.carregamento.g_revestimento + pp + (0.3 * laje.carregamento.q_acidental)
        
        # --- CORREÇÃO DE UNIDADE ---
        # Entrada: GPa. Saída desejada: kN/m².
        # 1 GPa = 10^9 Pa = 10^6 kN/m².
        # Antes estava 1000.0 (errado), agora 1e6 (correto).
        Ecs_kNm2 = laje.materiais.Ecs * 1e6
        
        h = laje.h
        Ic = laje.get_inercia_flexao()
        
        fctm_MPa = 0.3 * (laje.materiais.fck ** (2/3))
        y_t = h / 2.0
        w = Ic / y_t
        mr = 1.2 * (fctm_MPa * 1000.0) * w 
        
        ma = (p_els * (laje.lx ** 2)) / 8.0
        i_ii = Ic * 0.25 
        
        if ma > mr:
            ieq = ((mr / ma)**3) * Ic + (1 - (mr / ma)**3) * i_ii
        else:
            ieq = Ic
            
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