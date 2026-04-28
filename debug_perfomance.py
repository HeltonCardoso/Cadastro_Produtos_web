"""
debug_performance.py
====================
Script de diagnóstico do endpoint /item/{mlb}/performance do Mercado Livre.
Roda na mesma pasta do app.py.

Uso:
    python debug_performance.py MLB123456789

Salva o retorno completo em debug_performance_MLB123456789.json
"""

import sys
import json
import requests
from app import app
from token_manager_secure import ml_token_manager

BASE = "https://api.mercadolibre.com"


def get_headers():
    token = ml_token_manager.get_valid_token()
    return {"Authorization": f"Bearer {token}"}


def main():
    mlb = sys.argv[1].strip().upper() if len(sys.argv) > 1 else input("MLB: ").strip().upper()

    print(f"\n{'='*60}")
    print(f"  Performance MLB: {mlb}")
    print(f"{'='*60}\n")

    with app.app_context():

        # ── 1. Endpoint principal de performance ──────────────────────
        url = f"{BASE}/item/{mlb}/performance"
        r   = requests.get(url, headers=get_headers(), timeout=15)

        print(f"[performance] status: {r.status_code}")
        print(f"[performance] url: {url}\n")

        if r.status_code != 200:
            print(f"ERRO: {r.text[:500]}")
            sys.exit(1)

        dados = r.json()

        # ── 2. Mostra estrutura de alto nível ─────────────────────────
        print("CHAVES DE ALTO NÍVEL:")
        for k, v in dados.items():
            tipo = type(v).__name__
            if isinstance(v, list):
                print(f"  {k}: list ({len(v)} itens)")
            elif isinstance(v, dict):
                print(f"  {k}: dict → chaves: {list(v.keys())}")
            else:
                print(f"  {k}: {tipo} = {v}")

        # ── 3. Detalha cada bucket ────────────────────────────────────
        buckets = dados.get('buckets', [])
        print(f"\n{'='*60}")
        print(f"  BUCKETS ({len(buckets)} encontrados)")
        print(f"{'='*60}")

        for i, bucket in enumerate(buckets):
            b_key    = bucket.get('key',    f'bucket_{i}')
            b_title  = bucket.get('title',  '')
            b_status = bucket.get('status', '')
            b_score  = bucket.get('score',  '')
            variables = bucket.get('variables', [])

            print(f"\n[BUCKET {i+1}] key={b_key} | title={b_title} | status={b_status} | score={b_score}")
            print(f"  Variables: {len(variables)}")

            for j, var in enumerate(variables):
                v_key    = var.get('key',    '')
                v_title  = var.get('title',  '')
                v_status = var.get('status', '')
                v_type   = var.get('type',   '')
                rules    = var.get('rules',  [])

                print(f"\n  [{j+1}] key={v_key} | title={v_title} | status={v_status} | type={v_type}")

                for rule in rules:
                    r_status   = rule.get('status',   '')
                    r_wordings = rule.get('wordings', {})
                    r_label    = r_wordings.get('label') or r_wordings.get('title', '')
                    r_action   = r_wordings.get('action', '')
                    print(f"       rule: status={r_status} | label={r_label} | action={r_action}")

                # Campos extras da variable
                extras = {k: v for k, v in var.items()
                          if k not in ('key','title','status','type','rules','wordings')}
                if extras:
                    print(f"       extras: {extras}")

        # ── 4. Salva JSON completo ────────────────────────────────────
        nome = f"debug_performance_{mlb}.json"
        with open(nome, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)

        print(f"\n\n✅ JSON completo salvo em: {nome}")
        print(f"   score       : {dados.get('score')}")
        print(f"   level       : {dados.get('level')}")
        print(f"   level_wording: {dados.get('level_wording')}")
        print(f"   buckets     : {len(buckets)}")


if __name__ == "__main__":
    main()