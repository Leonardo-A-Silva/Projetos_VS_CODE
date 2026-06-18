"""
    {'name': 'PE_04_Mb.Paripueira', 'top': 914, 'base': 1210.21},
    {'name': 'PE_04_SALT2', 'top': 934, 'base': 992},
    {'name': 'PE_04_SALT7', 'top': 1051, 'base': 1100},
    {'name': 'PE_04_interlayer7', 'top': 1103, 'base': 1116},
    {'name': 'PE_04_interlayer9', 'top': 1143, 'base': 1165},
"""


import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict
from datetime import datetime
import warnings

warnings.filterwarnings("once")

# ==============================================================
# CONFIGURAÇÕES
# ==============================================================

FILE_PATH = r"C:\Users\leona\Desktop\LEONARDO\TRABALHO\CROSSPLOT_DATA\PE_04.xlsx"
SHEET_NAME = "LOW"

TARGET_STEP = 0.0082
N_POINTS = 100
SEED = 42

EXPORT_FORMATS = ["xlsx"]

LAYERS = [
    
    {'name': 'PE_04_interlayer9-10', 'top': 1143, 'base': 1163},
    
]

LOG_COLS = ['GR_H','RHOZ_H', 'GR_M', 'GR', 'SPHI', 'DTCO', 'VPVS', 'NPHI', 'PHIE_HILT', 'VCL_HILT', 'RXO', 'RT' , 'RHOZ']

TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")


# ==============================================================
# UTIL
# ==============================================================

def log(msg): print(f"\n▶ {msg}")
def ok(msg): print(f"   ✅ {msg}")
def warn(msg): print(f"   ⚠️ {msg}")

# ==============================================================
# LEITURA
# ==============================================================

def load_data(filepath: str) -> pd.DataFrame:
    log("ETAPA 1 — Carregamento")
    df = pd.read_excel(filepath, sheet_name=SHEET_NAME)

    # Limpar nomes de colunas (Maiúsculas e sem espaços)
    df.columns = (
        df.columns
        .str.strip()
        .str.upper()
        .str.replace(" ", "_")
        .str.replace("-", "_")
    )

    # Corrigir vírgula decimal e converter para número
    df = df.replace(",", ".", regex=True)
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    ok(f"Colunas lidas: {list(df.columns)}")
    return df

# ==============================================================
# UNIFICANDO RESOLUÇOES 
# =============================================================

def unify_data(df: pd.DataFrame, step: float) -> pd.DataFrame:
    log(f"ETAPA 3 — Unificando resoluções (Step: {step})")
    
    # Organizamos quais logs pertencem a qual coluna de profundidade
    # AJUSTE OS NOMES ABAIXO SE AS COLUNAS NO SEU EXCEL FOREM DIFERENTES
    mapping = {
        'DEPTH':  ['GR', 'SPHI', 'DTCO', 'VPVS', 'NPHI', 'PHIE_HILT', 'VCL_HILT', 'RXO', 'RT', 'RHOZ'],
        'DEPTH_2': ['GR_M'],
        'DEPTH_3': ['RHOZ_H', 'GR_H']
    }

    resampled_list = []

    for depth_col, logs in mapping.items():
        if depth_col in df.columns:
            # Filtra apenas os logs que realmente existem no seu arquivo
            existing_logs = [l for l in logs if l in df.columns]
            
            if existing_logs:
                # Cria um subset com a profundidade e seus logs
                sub = df[[depth_col] + existing_logs].dropna(subset=[depth_col])
                
                # Cria a "grade" (BIN) para arredondar a profundidade
                sub["BIN"] = (sub[depth_col] / step).round() * step
                
                # Tira a média dos logs para cada degrau (ex: 0.5m)
                res = sub.groupby("BIN")[existing_logs].mean()
                resampled_list.append(res)

    if not resampled_list:
        raise ValueError("Nenhuma coluna de profundidade encontrada!")

    # Junta tudo lateralmente usando o novo DEPTH comum (o index "BIN")
    df_final = pd.concat(resampled_list, axis=1).reset_index()
    df_final.rename(columns={"BIN": "DEPTH"}, inplace=True)
    
    ok(f"Dados unificados. Total de linhas: {len(df_final)}")
    return df_final

# ==============================================================
# FILTRO DE CAMADAS
# ==============================================================

def filter_layers(df: pd.DataFrame, layers: List[Dict]) -> pd.DataFrame:

    log("ETAPA 2 — Filtro de camadas")

    frames = []

    for l in layers:
        top, base = l["top"], l["base"]
        name = l["name"]

        sub = df[(df["DEPTH"] >= top) & (df["DEPTH"] <= base)].copy()

        if sub.empty:
            warn(f"{name}: sem dados")
        else:
            sub["LAYER"] = name
            ok(f"{name}: {len(sub)} pontos")
            frames.append(sub)

    return pd.concat(frames).reset_index(drop=True)

# ==============================================================
# PICKSET
# ==============================================================

def generate_pickset(df, cols, n, seed):

    log(f"ETAPA 4 — Pickset ({n} pontos)")

    valid = [c for c in cols if c in df.columns]
    missing = [c for c in cols if c not in df.columns]

    if missing:
        warn(f"Colunas ausentes: {missing}")
        warn(f"Usando apenas: {valid}")

    df_clean = df.dropna(subset=valid)

    if df_clean.empty:
        raise ValueError("Sem dados válidos")

    if len(df_clean) < n:
        n = len(df_clean)

    pick = df_clean.sample(n=n, random_state=seed)
    pick = pick.sort_values("DEPTH")

    ok(f"Pickset gerado: {len(pick)} pontos")

    return pick

# ==============================================================
# EXPORT
# ==============================================================

def export_data(df, prefix, formats):

    log("ETAPA 5 — Exportação")

    for f in formats:
        path = f"{prefix}_{TIMESTAMP}.{f}"

        if f == "csv":
            df.to_csv(path, index=False)
        elif f == "xlsx":
            df.to_excel(path, index=False)

        ok(f"{f.upper()} → {path}")

# ==============================================================
# PIPELINE
# ==============================================================

def run_pipeline():
    # 1. Carrega o arquivo bruto
    df_raw = load_data(FILE_PATH)

    # 2. Unifica as resoluções (O novo passo mágico)
    df_unified = unify_data(df_raw, TARGET_STEP)

    # 3. Filtra apenas os intervalos das camadas (LAYERS)
    df_filtered = filter_layers(df_unified, LAYERS)

    # 4. Gera o pickset aleatório para o crossplot
    pickset = generate_pickset(df_filtered, LOG_COLS, N_POINTS, SEED)

    # 5. Exporta o resultado
    export_data(pickset, "pickset", EXPORT_FORMATS)

    log("PROCESSO FINALIZADO COM SUCESSO")

# ==============================================================
# EXECUÇÃO
# ==============================================================

if __name__ == "__main__":
    run_pipeline()