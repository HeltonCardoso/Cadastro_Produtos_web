import pandas as pd
import os
from datetime import datetime
from bs4 import BeautifulSoup
import re
import logging
from typing import Dict, List, Tuple, Optional

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExtratorAtributos:
    """Classe principal para extração de atributos de produtos"""
    
    def __init__(self):
        self.logs: List[str] = []
        self.colunas_saida = [
            "EAN", "Nome", "Largura", "Altura", "Profundidade", "Peso", "Cor", 
            "Modelo", "Fabricante", "Volumes", "Material da Estrutura", "Material", 
            "Peso Suportado", "Acabamento", "Possui Portas", "Quantidade de Portas",
            "Tipo de Porta", "Possui Prateleiras", "Quantidade de Prateleiras", 
            "Conteúdo da Embalagem", "Quantidade de Gavetas", "Possui Gavetas", 
            "Revestimento", "Quantidade de lugares", "Possui Nicho",
            "Quantidade de Assentos", "Tipo de Assento", "Sugestão de Lugares", 
            "Tipo de Encosto"
        ]
        self.colunas_necessarias = ["EAN", "NOMEE-COMMERCE", "DESCRICAOHTML", "MODMPZ", "COR"]

    def processar_arquivo(self, caminho_arquivo: str) -> Tuple[str, int, float]:
        """Processa o arquivo de entrada e retorna o caminho do arquivo de saída"""
        inicio = datetime.now()
        self._log(f"Iniciando processamento em {inicio.strftime('%d/%m/%Y %H:%M:%S')}")
        
        try:
            # 1. Carregar e validar arquivo
            df = self._carregar_arquivo(caminho_arquivo)
            
            # 2. Processar cada linha
            dados_extraidos = []
            for idx, row in df.iterrows():
                try:
                    dados_produto = self._processar_linha(row)
                    dados_extraidos.append(dados_produto)
                    self._log(f"Processado: {row['NOMEE-COMMERCE']}")
                except Exception as e:
                    self._log(f"Erro na linha {idx+1}: {str(e)}", tipo="erro")
                    continue
            
            # 3. Gerar arquivo de saída
            caminho_saida = self._gerar_saida(dados_extraidos)
            
            # 4. Finalizar
            fim = datetime.now()
            duracao = (fim - inicio).total_seconds()
            qtd_itens = len(dados_extraidos)
            
            self._log(f"Processamento concluído - {qtd_itens} itens em {duracao:.2f}s")
            return caminho_saida, qtd_itens, duracao
            
        except Exception as e:
            self._log(f"ERRO: {str(e)}", tipo="erro")
            raise

    def _carregar_arquivo(self, caminho: str) -> pd.DataFrame:
        """Carrega e valida o arquivo de entrada"""
        self._log(f"Carregando arquivo: {os.path.basename(caminho)}")
        
        if not os.path.exists(caminho):
            raise FileNotFoundError("Arquivo não encontrado")
        
        if not caminho.lower().endswith(('.xlsx', '.xls')):
            raise ValueError("Formato inválido. Apenas arquivos Excel são aceitos")
        
        try:
            df = pd.read_excel(caminho)
        except Exception as e:
            raise ValueError(f"Erro ao ler arquivo: {str(e)}")
        
        # Validar colunas necessárias
        colunas_faltando = [col for col in self.colunas_necessarias if col not in df.columns]
        if colunas_faltando:
            raise ValueError(f"Colunas faltando: {', '.join(colunas_faltando)}")
        
        return df

    def _processar_linha(self, row: pd.Series) -> List:
        """Processa uma linha individual do DataFrame"""
        ean = str(row.get("EAN", "")).strip()
        nome = row.get("NOMEE-COMMERCE", "Desconhecido")
        descricao_html = row.get("DESCRICAOHTML", "")
        modelo = str(row.get("MODMPZ", "")).strip()
        cor = str(row.get("COR", "")).strip()
        fabricante = nome.split("-")[-1].strip() if "-" in nome else ""
        
        atributos = self._extrair_atributos(descricao_html)
        atributos["Cor"] = cor
        atributos["Modelo"] = modelo
        atributos["Fabricante"] = fabricante
        
        return [ean, nome] + list(atributos.values())

    def _extrair_atributos(self, descricao_html: str) -> Dict[str, str]:
        """Extrai atributos da descrição HTML"""
        atributos = {col: "" for col in self.colunas_saida[2:]}  # Pula EAN e Nome
        
        if pd.isna(descricao_html):
            return atributos
            
        try:
            soup = BeautifulSoup(descricao_html, "html.parser")
            texto_limpo = soup.get_text()
        except Exception:
            texto_limpo = descricao_html

        # Extrai medidas (largura, altura, profundidade)
        atributos.update(self._extrair_medidas(texto_limpo))
        
        # Extrai pesos
        atributos.update(self._extrair_pesos(texto_limpo))
        
        # Extrai outros atributos
        atributos.update(self._extrair_outros_atributos(texto_limpo))
        
        return atributos

    def _extrair_medidas(self, texto: str) -> Dict[str, str]:
        """Extrai medidas (largura, altura, profundidade)"""
        medidas = {
            "Largura": "", 
            "Altura": "", 
            "Profundidade": ""
        }
        
        # Função auxiliar para formatar
        def formatar(valor: float) -> str:
            return f"{int(valor)} cm" if valor.is_integer() else f"{valor:.1f} cm".replace(".", ",")

        # 1. Busca por medidas explícitas
        for medida in medidas.keys():
            padrao = rf"{medida}[:\s]*([\d,\.]+)\s*cm"
            match = re.search(padrao, texto, re.IGNORECASE)
            if match:
                try:
                    valor = float(match.group(1).replace(",", "."))
                    medidas[medida] = formatar(valor)
                except ValueError:
                    continue

        # 2. Fallback: formato "L x A x P"
        if not any(medidas.values()):
            padrao = r"\b(\d+[,\.]?\d*)\s*(?:cm\s*)?x\s*(\d+[,\.]?\d*)\s*(?:cm\s*)?x\s*(\d+[,\.]?\d*)\s*cm\b"
            matches = re.findall(padrao, texto, re.IGNORECASE)
            if matches:
                try:
                    larguras = [float(m[0].replace(",", ".")) for m in matches]
                    alturas = [float(m[1].replace(",", ".")) for m in matches]
                    profundidades = [float(m[2].replace(",", ".")) for m in matches]
                    
                    medidas["Largura"] = formatar(max(larguras))
                    medidas["Altura"] = formatar(max(alturas))
                    medidas["Profundidade"] = formatar(max(profundidades))
                except ValueError:
                    pass

        return medidas

    def _extrair_pesos(self, texto: str) -> Dict[str, str]:
        """Extrai informações de peso conforme sua lógica original"""
        pesos = {
            "Peso": "", 
            "Peso Suportado": ""
        }
        
        def formatar(valor: float) -> str:
            return f"{int(valor)} kg" if valor.is_integer() else f"{valor:.1f} kg".replace(".", ",")

        # 1. Peso normal
        padrao_peso = re.compile(r"Peso[:\s]*([\d,\.]+)\s*kg", re.IGNORECASE)
        match = padrao_peso.search(texto)
        if match:
            try:
                valor = float(match.group(1).replace(",", "."))
                pesos["Peso"] = formatar(valor)
            except ValueError:
                pass

        # 2. Peso Suportado
        padrao_bloco = re.compile(r"Peso\s*Suportado\s*Distribuído[:\s]*([^/\n]+(?:\/[^/\n]+)*)", re.IGNORECASE)
        padrao_valor = re.compile(r"([\d,\.]+)\s*kg", re.IGNORECASE)
        
        blocos = padrao_bloco.finditer(texto)
        valores = []
        
        for bloco in blocos:
            partes = bloco.group(1).split("/")
            for parte in partes:
                match = padrao_valor.search(parte)
                if match:
                    try:
                        valores.append(float(match.group(1).replace(",", ".")))
                    except ValueError:
                        continue

        if valores:
            pesos["Peso Suportado"] = formatar(max(valores))
        else:
            # Fallback para peso suportado simples
            padrao = r"(?:Peso\s*Suportado|Suporta|Carga\s*Máxima)[:\s]*([\d,\.]+)\s*kg"
            match = re.search(padrao, texto, re.IGNORECASE)
            if match:
                try:
                    valor = float(match.group(1).replace(",", "."))
                    pesos["Peso Suportado"] = formatar(valor)
                except ValueError:
                    pass

        return pesos

    def _extrair_outros_atributos(self, texto: str) -> Dict[str, str]:
        """Extrai os demais atributos conforme suas regras originais"""
        atributos = {}
        
        # Padrões para extração
        padroes = {
            "Cor": r"Cor[:\s]*([\w\s]+)",
            "Modelo": r"Modelo[:\s]*([\w\s]+)",
            "Fabricante": r"Fabricante[:\s]*([\w\s]+)",
            "Volumes": r"Volumes[:\s]*(\d+)",
            "Material da Estrutura": r"Material da Estrutura[:\s]*([\w\s]+)",
            "Possui Portas": r"Possui Portas[:\s]*(Sim|Não)",
            "Quantidade de Portas": r"Quantidade de Portas[:\s]*(\d+)",
            "Tipo de Porta": r"Tipo de Porta[:\s]*([\w\s]+)",
            "Possui Prateleiras": r"Possui Prateleiras[:\s]*(Sim|Não)",
            "Quantidade de Prateleiras": r"Quantidade de Prateleiras[:\s]*(\d+)",
            "Conteúdo da Embalagem": r"Conteúdo da Embalagem[:\s]*([\w\s,]+)",
            "Quantidade de Gavetas": r"Quantidade de Gavetas[:\s]*(\d+)",
            "Possui Gavetas": r"Possui Gavetas[:\s]*(Sim|Não)",
            "Quantidade de lugares": r"Quantidade de lugares[:\s]*(\d+)",
            "Sugestão de Lugares": r"Sugestão de Lugares[:\s]*(\d+)",
            "Quantidade de Assentos": r"Quantidade de Assentos[:\s]*(\d+)",
            "Tipo de Assento": r"Tipo de Assento[:\s]*([\w\s,]+)",
            "Possui Nicho": r"Possui Nicho[:\s]*(Sim|Não)",
            "Tipo de Encosto": r"Tipo de Encosto[:\s]*([\w\s,]+)",
            "Material": r"Material[:\s]*([\w\s]+)",
            "Acabamento": r"Acabamento[:\-]?\s*([\w\s\-,]+)",
            "Revestimento": r"Revestimento[:\s]*([\w\s,]+)"
        }
        
        # Extrai a seção de características primeiro (se existir)
        secao = re.search(r"Características do Produto[:\-]?\s*([\s\S]+?)(?:\n\n|\Z)", texto, re.IGNORECASE)
        texto_principal = secao.group(1) if secao else texto
        
        for atributo, padrao in padroes.items():
            # Procura primeiro na seção específica (se existir)
            match = re.search(padrao, texto_principal, re.IGNORECASE)
            if not match and secao:
                # Fallback: procura em todo o texto
                match = re.search(padrao, texto, re.IGNORECASE)
            
            if match:
                atributos[atributo] = match.group(1).strip()

        return atributos

    def _gerar_saida(self, dados: List[List]) -> str:
        """Gera o arquivo Excel de saída"""
        if not dados:
            raise ValueError("Nenhum dado para exportar")
            
        df = pd.DataFrame(dados, columns=self.colunas_saida)
        
        # Nome do arquivo de saída
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_arquivo = f"Atributos_Extraidos_{timestamp}.xlsx"
        caminho_saida = os.path.join("uploads", nome_arquivo)
        
        # Garante que o diretório existe
        os.makedirs(os.path.dirname(caminho_saida), exist_ok=True)
        
        # Salva o arquivo
        df.to_excel(caminho_saida, index=False)
        self._log(f"Arquivo gerado: {nome_arquivo}")
        
        return caminho_saida

    def _log(self, mensagem: str, tipo: str = "info") -> None:
        """Registra mensagem de log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {mensagem}"
        
        self.logs.append(log_entry)
        logger.info(log_entry) if tipo == "info" else logger.error(log_entry)

def extrair_atributos_processamento(caminho_arquivo: str) -> Tuple[str, int, float, list]:
    """Função pública para integração com Flask"""
    extrator = ExtratorAtributos()
    try:
        caminho_saida, qtd_itens, tempo_segundos = extrator.processar_arquivo(caminho_arquivo)
        
        # Obter os dados reais processados
        itens_processados = []
        df_resultado = pd.read_excel(caminho_saida)  # Lê o arquivo gerado
        
        for _, row in df_resultado.iterrows():
            itens_processados.append({
                    'ean': str(row['EAN']),
                    'nome': row['Nome'],
                    'atributos_extraidos': {
                    'largura': row['Largura'],
                    'altura': row['Altura'],
                    'profundidade': row['Profundidade'],
                    'peso': row['Peso'],
                    # Adicione outros atributos conforme necessário
                },
                'status': 'sucesso'  # Ou defina status baseado em alguma regra
            })
        
        # Salva logs em arquivo
        with open('uploads/logs_atributos.txt', 'w', encoding='utf-8') as f:
            f.write("\n".join(extrator.logs))
        
        return caminho_saida, qtd_itens, tempo_segundos, itens_processados
        
    except Exception as e:
        # Garante que o erro seja registrado
        with open('uploads/logs_atributos.txt', 'a', encoding='utf-8') as f:
            f.write(f"\nERRO: {str(e)}")
        raise