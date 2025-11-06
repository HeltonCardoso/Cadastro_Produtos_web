import http.client
import json
import os
from datetime import datetime

class AnyMarketEtiquetas:
    def __init__(self, gumga_token):
        self.gumga_token = gumga_token
    
    def processar_pedidos(self, pedidos_str):
        """Processa string de pedidos separados por ; ou ,"""
        pedidos_limpos = pedidos_str.replace(',', ';').replace(' ', '')
        lista_pedidos = pedidos_limpos.split(';')
        
        pedidos_validos = []
        for pedido in lista_pedidos:
            if pedido.strip().isdigit():
                pedidos_validos.append(int(pedido.strip()))
        
        return pedidos_validos
    
    def gerar_etiqueta_pdf_individual(self, order_id):
        """Gera PDF para UM pedido por vez"""
        conn = http.client.HTTPSConnection("api.anymarket.com.br")
        
        payload = json.dumps({"orders": [order_id]})
        
        headers = {
            'Content-Type': "application/json",
            'Authorization': f"Bearer {self.gumga_token}",
            'gumgaToken': self.gumga_token
        }
        
        try:
            print(f"  📄 Gerando PDF para pedido {order_id}...")
            conn.request("POST", "/v2/printtag/PDF", payload, headers)
            res = conn.getresponse()
            data = res.read()
            
            if res.status != 200:
                print(f"  ❌ Erro no pedido {order_id}: {res.status}")
                return None
            
            nome_arquivo = f"etiqueta_{order_id}.pdf"
            with open(nome_arquivo, "wb") as f:
                f.write(data)
            
            print(f"  ✅ PDF salvo: {nome_arquivo}")
            return nome_arquivo
            
        except Exception as e:
            print(f"  ❌ Erro no pedido {order_id}: {e}")
            return None
        finally:
            conn.close()
    
    def gerar_etiqueta_zpl_individual(self, order_id):
        """Gera ZPL para UM pedido por vez"""
        conn = http.client.HTTPSConnection("api.anymarket.com.br")
        
        payload = json.dumps({"orders": [order_id]})
        
        headers = {
            'Content-Type': "application/json",
            'Authorization': f"Bearer {self.gumga_token}",
            'gumgaToken': self.gumga_token
        }
        
        try:
            print(f"  🖨️ Gerando ZPL para pedido {order_id}...")
            conn.request("POST", "/v2/printtag/ZPL2?file=TXT", payload, headers)
            res = conn.getresponse()
            data = res.read()
            
            if res.status != 200:
                print(f"  ❌ Erro no pedido {order_id}: {res.status}")
                return None
            
            response_json = json.loads(data.decode("utf-8"))
            zpl_content = response_json["content"]
            
            nome_arquivo = f"etiqueta_{order_id}.zpl"
            with open(nome_arquivo, "w", encoding="utf-8") as f:
                f.write(zpl_content)
            
            print(f"  ✅ ZPL salvo: {nome_arquivo}")
            return zpl_content
            
        except Exception as e:
            print(f"  ❌ Erro no pedido {order_id}: {e}")
            return None
        finally:
            conn.close()
    
    def processar_etiquetas(self, pedidos_str, formato="PDF"):
        """
        Função principal - processa cada pedido individualmente
        """
        print("=" * 50)
        print("🏷️  GERADOR DE ETIQUETAS MERCADO LIVRE")
        print("=" * 50)
        
        # Processar lista de pedidos
        pedidos = self.processar_pedidos(pedidos_str)
        
        if not pedidos:
            print("❌ Nenhum pedido válido encontrado!")
            return False
        
        print(f"📦 Pedidos identificados: {len(pedidos)}")
        print(f"🔢 IDs: {', '.join(map(str, pedidos))}")
        print(f"📄 Formato escolhido: {formato}")
        print("\n🚀 Processando pedidos individualmente...")
        
        resultados = []
        sucessos = 0
        erros = 0
        
        for i, pedido_id in enumerate(pedidos, 1):
            print(f"\n[{i}/{len(pedidos)}] Processando pedido {pedido_id}...")
            
            if formato.upper() == "PDF":
                resultado = self.gerar_etiqueta_pdf_individual(pedido_id)
            else:  # ZPL
                resultado = self.gerar_etiqueta_zpl_individual(pedido_id)
            
            if resultado:
                resultados.append(resultado)
                sucessos += 1
            else:
                erros += 1
        
        # Resumo final
        print("\n" + "=" * 50)
        print("📊 RESUMO DO PROCESSAMENTO")
        print("=" * 50)
        print(f"✅ Sucessos: {sucessos}")
        print(f"❌ Erros: {erros}")
        print(f"📁 Arquivos gerados: {sucessos}")
        
        if sucessos > 0:
            print(f"🎉 Processamento concluído! {sucessos} etiqueta(s) gerada(s).")
            return True
        else:
            print("💥 Falha total no processamento.")
            return False

# 🚀 USO RÁPIDO PARA TESTAR
def testar_sistema():
    """Teste com os mesmos exemplos que você usou"""
    GUMGA_TOKEN = "MjU5MDYzNTUwLg==.BS2OnGYhSD2nuXU5KRe59Iht02xoxdpAjpAuFORzs9EUbCHj9z16jYdLqCLwndvvaRd+jr+GlgmUMUEjIFYKdg=="
    
    gerador = AnyMarketEtiquetas(GUMGA_TOKEN)
    
    print("🚀 TESTANDO COM A SOLUÇÃO CORRIGIDA:")
    
    # Teste 1: Pedido único em PDF (já sabemos que funciona)
    print("\n📦 Teste 1 - Pedido único (PDF):")
    gerador.processar_etiquetas("261227418", "PDF")
    
    # Teste 2: Múltiplos pedidos em PDF (agora processando individualmente)
    print("\n📦 Teste 2 - Múltiplos pedidos (PDF) - PROCESSAMENTO INDIVIDUAL:")
    gerador.processar_etiquetas("261227418;261227419;261227420", "PDF")
    
    # Teste 3: Múltiplos pedidos em ZPL (agora processando individualmente)  
    print("\n📦 Teste 3 - Múltiplos pedidos (ZPL) - PROCESSAMENTO INDIVIDUAL:")
    gerador.processar_etiquetas("261227418;261227419;261227420", "ZPL")

if __name__ == "__main__":
    testar_sistema()