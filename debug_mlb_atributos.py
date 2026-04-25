"""
debug_mlb_atributos.py
======================
Script de diagnóstico — roda na mesma pasta do seu app.py.

Uso:
    python debug_mlb_atributos.py MLB123456789
"""

import sys
import json
import requests

# Inicializa o contexto do Flask antes de qualquer import que dependa dele
from app import app
from token_manager_secure import ml_token_manager

BASE = "https://api.mercadolibre.com"


def get_headers():
    token = ml_token_manager.get_valid_token()
    return {"Authorization": f"Bearer {token}"}


def buscar_item(mlb):
    r = requests.get(
        f"{BASE}/items/{mlb}",
        headers=get_headers(),
        params={"include_internal_attributes": "true"},
        timeout=15,
    )
    print(f"[item] status: {r.status_code}")
    return r.json() if r.status_code == 200 else None


def buscar_atributos_categoria(category_id):
    r = requests.get(
        f"{BASE}/categories/{category_id}/attributes",
        headers=get_headers(),
        timeout=15,
    )
    print(f"[categoria] status: {r.status_code}")
    return r.json() if r.status_code == 200 else []


def buscar_qualidade(mlb):
    r = requests.get(
        f"{BASE}/items/{mlb}/quality",
        headers=get_headers(),
        timeout=15,
    )
    print(f"[quality] status: {r.status_code}")
    return r.json() if r.status_code == 200 else {}


def classificar_nao_se_aplica(cat_attr):
    tags = cat_attr.get("tags", {})
    if isinstance(tags, list):
        tags = {t: True for t in tags}

    eh_readonly    = bool(tags.get("read_only", False))
    valores        = cat_attr.get("values", [])
    tem_lista_fixa = len(valores) > 0
    tem_opcao_na   = any(v.get("id") == "-1" for v in valores)

    if eh_readonly:
        return "NAO - readonly"
    elif tem_opcao_na:
        return "SIM - tem value_id=-1 na lista"
    elif tem_lista_fixa:
        return "NAO - lista fechada"
    else:
        return "SIM - texto livre"


def main():
    mlb = sys.argv[1].strip().upper() if len(sys.argv) > 1 else input("MLB: ").strip().upper()

    print(f"\n{'='*60}")
    print(f"  Diagnostico MLB: {mlb}")
    print(f"{'='*60}\n")

    with app.app_context():

        item = buscar_item(mlb)
        if not item:
            print("ERRO: Item nao encontrado.")
            sys.exit(1)

        category_id = item.get("category_id", "")
        print(f"\nTitulo     : {item.get('title')}")
        print(f"Categoria  : {category_id}")
        print(f"Status     : {item.get('status')}")

        item_attrs = {}
        for a in item.get("attributes", []):
            item_attrs[a["id"]] = {
                "value_id":   a.get("value_id"),
                "value_name": a.get("value_name"),
            }

        print(f"\n[item] Total de atributos no item: {len(item_attrs)}")

        cat_attrs = buscar_atributos_categoria(category_id)
        print(f"[categoria] Total de atributos na categoria: {len(cat_attrs)}\n")

        qualidade = buscar_qualidade(mlb)
        print(f"[quality] Retorno:\n{json.dumps(qualidade, ensure_ascii=False, indent=2)}\n")

        print(f"\n{'='*60}")
        print("  CRUZAMENTO: categoria x item")
        print(f"{'='*60}")

        resultado = []

        for cat in cat_attrs:
            attr_id    = cat.get("id", "")
            attr_nome  = cat.get("name", attr_id)
            value_type = cat.get("value_type", "")
            tags_raw   = cat.get("tags", {})
            if isinstance(tags_raw, list):
                tags_raw = {t: True for t in tags_raw}

            valores    = cat.get("values", [])
            item_val   = item_attrs.get(attr_id, {})

            obrigatorio = bool(tags_raw.get("required") or tags_raw.get("catalog_required"))
            recomendado = bool(tags_raw.get("recommended"))
            readonly    = bool(tags_raw.get("read_only"))

            nao_aplica_class = classificar_nao_se_aplica(cat)

            linha = {
                "id":                     attr_id,
                "nome":                   attr_nome,
                "value_type":             value_type,
                "obrigatorio":            obrigatorio,
                "recomendado":            recomendado,
                "readonly":               readonly,
                "tags":                   tags_raw,
                "qtd_values":             len(valores),
                "values_ids":             [v.get("id") for v in valores[:5]],
                "values_names":           [v.get("name") for v in valores[:5]],
                "valor_atual_value_id":   item_val.get("value_id"),
                "valor_atual_value_name": item_val.get("value_name"),
                "checkbox_na":            nao_aplica_class,
            }

            resultado.append(linha)

            print(f"\n  [{attr_id}] {attr_nome}")
            print(f"    value_type  : {value_type}")
            print(f"    tags        : {tags_raw}")
            print(f"    obrigatorio : {obrigatorio} | recomendado: {recomendado} | readonly: {readonly}")
            print(f"    values      : {len(valores)} opcoes -> {[v.get('name') for v in valores[:8]]}")
            print(f"    tem id=-1   : {any(v.get('id') == '-1' for v in valores)}")
            print(f"    valor item  : value_id={item_val.get('value_id')} | value_name={item_val.get('value_name')}")
            print(f"    checkbox NA : {nao_aplica_class}")

        saida = {
            "mlb":       mlb,
            "titulo":    item.get("title"),
            "categoria": category_id,
            "qualidade": qualidade,
            "atributos": resultado,
        }

        nome_arquivo = f"debug_mlb_{mlb}.json"
        with open(nome_arquivo, "w", encoding="utf-8") as f:
            json.dump(saida, f, ensure_ascii=False, indent=2)

        print(f"\n\nOK - JSON salvo em: {nome_arquivo}")
        print(f"   Total analisados : {len(resultado)}")
        print(f"   Obrigatorios     : {sum(1 for r in resultado if r['obrigatorio'])}")
        print(f"   Recomendados     : {sum(1 for r in resultado if r['recomendado'])}")
        print(f"   Com checkbox N/A : {sum(1 for r in resultado if 'SIM' in r['checkbox_na'])}")
        print(f"   Sem checkbox N/A : {sum(1 for r in resultado if 'NAO' in r['checkbox_na'])}")


if __name__ == "__main__":
    main()