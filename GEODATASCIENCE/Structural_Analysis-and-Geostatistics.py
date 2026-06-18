
import pandas as pd
import matplotlib.pyplot as plt
import mplstereonet
import numpy as np
import glob
import os
from pathlib import Path

# =============================================================================
# 1. MÓDULO DE INGESTÃO E HIGIENIZAÇÃO DE DADOS
# =============================================================================


def carregar_dados_estruturais(caminho_arquivo):
    """Lê arquivos CSV de poço, validando colunas incluindo a Profundidade (Depth)."""
    try:
        df = pd.read_csv(caminho_arquivo, sep=';')
        if len(df.columns) <= 1:
            df = pd.read_csv(caminho_arquivo, sep=',')

        df.columns = df.columns.str.strip()

        # Agora a Profundidade é mandatória para o filtro
        colunas_necessarias = ['Hole ID', 'Depth',
                               'Dip', 'Azimuth', 'Estrutura']

        if not all(col in df.columns for col in colunas_necessarias):
            print(
                f"[Aviso] Colunas ausentes no arquivo: {caminho_arquivo}. Ignorando.")
            return None

        df['Estrutura'] = df['Estrutura'].astype(str).str.strip()
        # Converte a profundidade para número (evita erros de texto acidentais)
        df['Depth'] = pd.to_numeric(df['Depth'], errors='coerce')

        return df.dropna(subset=['Depth', 'Dip', 'Azimuth'])

    except Exception as e:
        print(f"[Erro] Falha ao carregar {caminho_arquivo}: {e}")
        return None

# =============================================================================
# 2. MÓDULO DE CÁLCULO VETORIAL (SIMPLES OU SÊNIOR)
# =============================================================================


def calcular_parametros_direcionais(dip, azimuth, usar_avancado):
    """
    Calcula tendências centrais. Se 'usar_avancado' for True, executa a 
    matriz de tensores de Woodcock e o Fator de dispersão de Fisher.
    """
    N = len(dip)
    strike = (azimuth - 90) % 360

    # 1. Preparação dos Vetores Unitários (Polos no hemisfério inferior)
    trend_polo_rad = np.radians((azimuth + 180) % 360)
    plunge_polo_rad = np.radians(90 - dip)

    x = np.cos(plunge_polo_rad) * np.cos(trend_polo_rad)
    y = np.cos(plunge_polo_rad) * np.sin(trend_polo_rad)
    z = np.sin(plunge_polo_rad)

    # 2. Vetor Resultante (Soma/Média)
    x_m, y_m, z_m = np.mean(x), np.mean(y), np.mean(z)
    plunge_medio_rad = np.arcsin(z_m / np.sqrt(x_m**2 + y_m**2 + z_m**2))
    trend_medio_rad = np.arctan2(y_m, x_m)

    dip_medio = 90 - np.degrees(plunge_medio_rad)
    azimuth_medio = (np.degrees(trend_medio_rad) - 180) % 360
    strike_medio = (azimuth_medio - 90) % 360

    # 3. Medianas (Estatística Descritiva)
    az_rad = np.radians(azimuth)
    azimuth_mediana = np.degrees(np.arctan2(
        np.median(np.sin(az_rad)), np.median(np.cos(az_rad)))) % 360
    dip_mediana = np.median(dip)

    # ====================================================
    # MONTAGEM DA CAIXA DE TEXTO (CONDICIONAL)
    # ====================================================
    texto_stats = (
        "ESTATÍSTICA BÁSICA\n"
        "--------------------------\n"
        f"Amostragem (n): {N}\n\n"
        "MERGULHO (Dip):\n"
        f" • Média Vet.: {dip_medio:.1f}°\n"
        f" • Mediana:    {dip_mediana:.1f}°\n"
        f" • Range:      {np.min(dip):.1f}° a {np.max(dip):.1f}°\n\n"
        "DIREÇÃO (Azimuth):\n"
        f" • Média Vet.: {azimuth_medio:.1f}°\n"
        f" • Mediana:    {azimuth_mediana:.1f}°\n"
        f" • Range:      {np.min(azimuth):.1f}° a {np.max(azimuth):.1f}°\n"
    )

    # Adiciona Módulo Sênior se autorizado pelo usuário
    if usar_avancado and N >= 3:
        # A. CÁLCULO DE FISHER (K e Alpha 95)
        R_vec = np.array([np.sum(x), np.sum(y), np.sum(z)])
        R = np.linalg.norm(R_vec)

        K = 0
        alpha_95 = 0
        if N > R:
            K = (N - 1) / (N - R)
            # Alpha 95 (Cone de confiança de 95%)
            if K > 0:
                p = 0.05
                fator = ((1/p)**(1/(N-1))) - 1
                cos_alpha = 1 - (((N - R) / R) * fator)
                cos_alpha = np.clip(cos_alpha, -1.0, 1.0)
                alpha_95 = np.degrees(np.arccos(cos_alpha))

        # B. CÁLCULO DE WOODCOCK (Autovalores do Tensor)
        matriz_orientacao = np.array([x, y, z])
        tensor = np.dot(matriz_orientacao, matriz_orientacao.T) / N
        autovalores, _ = np.linalg.eig(tensor)
        autovalores_ordenados = np.sort(autovalores)[::-1]  # S1, S2, S3
        S1, S2, S3 = autovalores_ordenados

        # Formatação do texto avançado
        texto_stats += (
            "\n"
            "FISHER & WOODCOCK\n"
            "--------------------------\n"
            f"Fator Concentração (K): {K:.1f}\n"
            f"Cone Confiança (a95):   {alpha_95:.1f}°\n"
            "Autovalores Woodcock:\n"
            f" • S1: {S1:.3f} (Max)\n"
            f" • S2: {S2:.3f} (Int)\n"
            f" • S3: {S3:.3f} (Min)\n"
        )
        # Diagnóstico Inteligente baseado em Woodcock
        if S1 > S2 and S1 > S3 * 5:
            texto_stats += " Geometria: CLUSTER (Ponto)"
        elif S1 >= S2 and S2 > S3 * 3:
            texto_stats += " Geometria: GIRDLE (Faixa)"
        else:
            texto_stats += " Geometria: CAÓTICA"

    return texto_stats, strike, strike_medio, dip_medio

# =============================================================================
# 3. MÓDULO DE RENDERIZAÇÃO GRÁFICA E APROVAÇÃO
# =============================================================================


def processar_prancha_estrutural(df_sub, arquivo, estrutura, id_figura, prof_min, prof_max, calc_avancado):
    """Renderiza a prancha analítica baseada nos filtros de profundidade e estatística."""

    # Destrava os arrays da memória do Pandas
    dip = np.array(df_sub['Dip'].values).copy()
    azimuth = np.array(df_sub['Azimuth'].values).copy()

    texto_stats, strike, strike_medio, dip_medio = calcular_parametros_direcionais(
        dip, azimuth, calc_avancado)

    # Header formatado com a profundidade
    titulo_prof = f" | PROF: {prof_min}m - {prof_max}m" if prof_min is not None else " | PROF: Poço Completo"

    fig = plt.figure(id_figura, figsize=(16, 5.5))
    fig.suptitle(f"POÇO: {arquivo} | ESTRUTURA: {estrutura.upper()}{titulo_prof}",
                 fontweight='bold', fontsize=14)
    plt.subplots_adjust(left=0.22, right=0.95, wspace=0.3)

    fig.text(0.02, 0.5, texto_stats, va='center', ha='left', fontsize=9.5, family='monospace',
             bbox=dict(facecolor='#f8f9fa', edgecolor='black', boxstyle='round,pad=1'))

    # 3.1 - Estereograma de Polos
    ax1 = fig.add_subplot(1, 3, 1, projection='stereonet')
    if len(dip) >= 5:
        ax1.density_contourf(
            strike, dip, measurement='poles', cmap='Reds', alpha=0.6)
    ax1.pole(strike, dip, color='black',
             markersize=3, label='Polos Amostrados')
    ax1.grid(True, color='gray', linestyle=':', alpha=0.7)
    ax1.set_title("Projeção de Polos e Densidade", pad=15)

    # 3.2 - Estereograma de Planos
    ax2 = fig.add_subplot(1, 3, 2, projection='stereonet')
    ax2.plane(strike, dip, color='gray', alpha=0.15, linewidth=0.5)
    ax2.plane(strike_medio, dip_medio, color='blue',
              linewidth=2.5, label='Plano Médio Vetorial')
    ax2.pole(strike_medio, dip_medio, color='blue',
             marker='*', markersize=10, label='Polo Médio')
    ax2.grid(True, color='gray', linestyle=':', alpha=0.7)
    ax2.set_title("Atitude dos Planos Estruturais", pad=15)
    ax2.legend(loc='lower right', fontsize=8)

    # 3.3 - Roseta Direcional
    ax3 = fig.add_subplot(1, 3, 3, projection='polar')
    ax3.set_theta_zero_location('N')
    ax3.set_theta_direction(-1)
    contagem, bordas = np.histogram(azimuth, bins=np.arange(0, 370, 10))
    ax3.bar(np.deg2rad(bordas[:-1]), contagem, width=np.deg2rad(10),
            color='teal', edgecolor='black', alpha=0.7)
    ax3.set_title("Roseta de Direção de Mergulho", pad=15)

    # Loop interativo de Validação
    print(
        f"\n[Analista] Inspecionando '{estrutura}' do arquivo '{arquivo}'...")
    print(" -> A prancha foi aberta. Feche a janela gráfica (X) para continuar.")

    plt.show(block=True)

    resposta = input(
        f" -> Registrar e salvar a prancha de '{estrutura}'? (s/n): ")
    if resposta.strip().lower() in ['s', 'sim', 'y', 'yes']:
        nome_img = f"Estereograma_{arquivo.replace('.csv', '')}_{estrutura.replace(' ', '_')}.png"
        fig.savefig(nome_img, dpi=300, bbox_inches='tight')
        print(f" [OK] Prancha arquivada: {nome_img}")
    else:
        print(" [X] Prancha descartada.")

    plt.close(fig)

# =============================================================================
# 4. EXECUTÁVEL PRINCIPAL E INTERFACE COM O USUÁRIO
# =============================================================================


def executar_analise():
    print("Iniciando Módulo Profissional de Geologia Estrutural...")

    caminho_base = r"C:\Users\leona\Desktop\Cavernas de SAL_BRASKEN\Dados estruturais"
    pasta_alvo = Path(caminho_base)

    if not pasta_alvo.exists():
        print(f"[Falha Crítica] Diretório não encontrado: {caminho_base}")
        return

    os.chdir(pasta_alvo)
    arquivos_csv = glob.glob('*.csv')

    if not arquivos_csv:
        print("[Falha] Nenhum arquivo .csv detectado no diretório base.")
        return

    # 1. INTERAÇÃO: Estruturas
    estruturas = set()
    for arq in arquivos_csv:
        df = carregar_dados_estruturais(arq)
        if df is not None:
            estruturas.update(df['Estrutura'].unique())

    lista_estruturas = sorted(list(estruturas))
    print("\n" + "="*50)
    print(" DOMÍNIO ESTRUTURAL IDENTIFICADO")
    print("="*50)
    for i, est in enumerate(lista_estruturas):
        print(f" [{i}] {est}")

    escolha = input(
        "\nÍndices das estruturas (ex: 0, 2) ou ENTER para todas: ")
    if not escolha.strip():
        estruturas_alvo = lista_estruturas
    else:
        try:
            indices = [int(x.strip()) for x in escolha.split(',')]
            estruturas_alvo = [lista_estruturas[i]
                               for i in indices if i < len(lista_estruturas)]
        except:
            estruturas_alvo = lista_estruturas

    # 2. INTERAÇÃO: Filtro de Profundidade
    print("\n" + "="*50)
    print(" FILTRO ESTRATIGRÁFICO (PROFUNDIDADE)")
    print("="*50)
    prof_escolha = input(
        "Deseja analisar um range específico de profundidade? (ex: 1100, 1200) ou ENTER para todo o poço: ")
    prof_min, prof_max = None, None
    if prof_escolha.strip():
        try:
            p1, p2 = [float(x.strip()) for x in prof_escolha.split(',')]
            prof_min, prof_max = min(p1, p2), max(
                p1, p2)  # Garante a ordem correta
            print(f" -> Filtro Aplicado: de {prof_min}m a {prof_max}m.")
        except:
            print(" -> Entrada inválida. Poço completo será analisado.")

    # 3. INTERAÇÃO: Autorização de Geoestatística Sênior
    print("\n" + "="*50)
    print(" RIGOR ESTATÍSTICO")
    print("="*50)
    calc_avancado = input(
        "Posso realizar o cálculo estatístico de Fisher e Woodcock? (s/n): ").strip().lower() in ['s', 'sim', 'y']

    print(f"\nProcessando dados...")

    id_figura = 1
    for arq in arquivos_csv:
        df_poco = carregar_dados_estruturais(arq)
        if df_poco is None:
            continue

        # Aplica o filtro de profundidade se o usuário escolheu
        if prof_min is not None and prof_max is not None:
            df_poco = df_poco[(df_poco['Depth'] >= prof_min)
                              & (df_poco['Depth'] <= prof_max)]

        for est in estruturas_alvo:
            df_filtrado = df_poco[df_poco['Estrutura'] == est]
            # Só renderiza se sobraram dados daquela estrutura na profundidade alvo
            if not df_filtrado.empty:
                processar_prancha_estrutural(
                    df_filtrado, arq, est, id_figura, prof_min, prof_max, calc_avancado)
                id_figura += 1

    print("\n[Concluído] Processamento finalizado.")


if __name__ == "__main__":
    try:
        executar_analise()
    except KeyboardInterrupt:
        print(
            "\n\n[Interrupção] O analista abortou o processamento do pipeline com sucesso.")
