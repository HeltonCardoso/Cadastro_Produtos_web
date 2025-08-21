import xml.etree.ElementTree as ET

def validar_xml_nfe(arquivo_xml):
    """Valida XML de NF-e ou NFC-e e retorna informações principais"""
    try:
        tree = ET.parse(arquivo_xml)
        root = tree.getroot()
        ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}

        resultado = {}

        # -------------------------
        # INFO BÁSICA
        # -------------------------
        infNFe = root.find('.//nfe:infNFe', ns)
        if infNFe is not None:
            resultado['chave'] = infNFe.attrib.get('Id', '')[3:]

        ide = root.find('.//nfe:ide', ns)
        if ide is not None:
            numero = ide.find('nfe:nNF', ns)
            serie = ide.find('nfe:serie', ns)
            modelo = ide.find('nfe:mod', ns)

            resultado['numero'] = numero.text if numero is not None else None
            resultado['serie'] = serie.text if serie is not None else None
            if modelo is not None:
                resultado['modelo'] = "NFC-e (65)" if modelo.text == "65" else "NF-e (55)"
            else:
                resultado['modelo'] = "Desconhecido"

        # Ambiente
        tpAmb = root.find('.//nfe:tpAmb', ns)
        if tpAmb is not None:
            resultado['ambiente'] = "Produção" if tpAmb.text == "1" else "Homologação"

        # -------------------------
        # EMITENTE
        # -------------------------
        emit = root.find('.//nfe:emit', ns)
        if emit is not None:
            resultado['emitente'] = {
                "nome": emit.findtext('nfe:xNome', default='', namespaces=ns),
                "cnpj": emit.findtext('nfe:CNPJ', default='', namespaces=ns),
                "cpf": emit.findtext('nfe:CPF', default='', namespaces=ns),
            }

        # -------------------------
        # DESTINATÁRIO
        # -------------------------
        dest = root.find('.//nfe:dest', ns)
        if dest is not None:
            endereco = dest.find('nfe:enderDest', ns)
            resultado['destinatario'] = {
                "nome": dest.findtext('nfe:xNome', default='', namespaces=ns),
                "cnpj": dest.findtext('nfe:CNPJ', default='', namespaces=ns),
                "cpf": dest.findtext('nfe:CPF', default='', namespaces=ns),
                "endereco": {
                    "logradouro": endereco.findtext('nfe:xLgr', default='', namespaces=ns) if endereco is not None else '',
                    "numero": endereco.findtext('nfe:nro', default='', namespaces=ns) if endereco is not None else '',
                    "bairro": endereco.findtext('nfe:xBairro', default='', namespaces=ns) if endereco is not None else '',
                    "municipio": endereco.findtext('nfe:xMun', default='', namespaces=ns) if endereco is not None else '',
                    "uf": endereco.findtext('nfe:UF', default='', namespaces=ns) if endereco is not None else '',
                    "cep": endereco.findtext('nfe:CEP', default='', namespaces=ns) if endereco is not None else '',
                } if endereco is not None else {}
            }

        # -------------------------
        # QRCODE (apenas NFC-e)
        # -------------------------
        if resultado.get('modelo') == "NFC-e (65)":
            qrCode = root.find('.//nfe:qrCode', ns)
            resultado['qrcode'] = qrCode.text if qrCode is not None else "Não encontrado"
        else:
            resultado['qrcode'] = "Não aplicável (NF-e)"

        # -------------------------
        # PROTOCOLO
        # -------------------------
        cStat = root.find('.//nfe:cStat', ns)
        if cStat is not None and cStat.text == "100":
            resultado['autorizada'] = True
        else:
            resultado['autorizada'] = False

        return {"sucesso": True, "dados": resultado}

    except Exception as e:
        return {"sucesso": False, "erro": str(e)}