# Célula 2 — busca e mostra os preços

import requests
import re
import json
from bs4 import BeautifulSoup

# ---------------------------------------------------------------
# 👉 COLE AQUI OS LINKS DO PRODUTO (um para cada loja)
# Copie o link direto da página do produto (não da busca) em cada site.
# ---------------------------------------------------------------
LINK_AMAZON = "https://www.amazon.com.au/Apple-MacBook-13-inch-6%E2%80%91core-Unified/dp/B0GR6V43V4/ref=asc_df_B0GR79XJNM?mcid=85ac20a1991b313ba5a53df41dae4e4e&tag=googleshopdsk-22&linkCode=df0&hvadid=712244421528&hvpos=&hvnetw=g&hvrand=11201868277863062815&hvpone=&hvptwo=&hvqmt=&hvdev=c&hvdvcmdl=&hvlocint=&hvlocphy=9068984&hvtargid=pla-2470778764734&hvocijid=11201868277863062815-B0GR79XJNM-&hvexpln=0&gad_source=1&th=1$0"
LINK_JBHIFI = "https://www.jbhifi.com.au/products/apple-macbook-neo-13-inch-with-a18-pro-chip-256gb-8gb-blush?store=211&gad_source=1&gad_campaignid=17413981572&gbraid=0AAAAAD23EqqlJzfcWa4-B46SB9tgpow8v&gclid=CjwKCAjwqonVBhA4EiwA9wYJ3Ra_EC0KihWh9ZEHFYsDCl4-_D6o2e6V4E9KLpliv3EIEuIyOyuAAhoCxtYQAvD_BwE$0"
LINK_OFFICEWORKS = "https://www.officeworks.com.au/shop/officeworks/p/macbook-neo-13-a18-pro-6-core-cpu-5-core-gpu-8-256gb-blush-mbn8pt82bh?cm_mmc=Google:SEM:Always_on:OW%7CAU+%7CTechnology%7CApple_Supplier%7CNA%7CSEM%7CGoogle%7CPMax%7CNA-OFFTHE270725&s_kwcid=AL!12073!3!!!!x!!&gclsrc=aw.ds&gad_source=1&gad_campaignid=19856019508&gbraid=0AAAAAD1FgQYVyizIGyuc2o_iu-tm03Nfp&gclid=CjwKCAjwqonVBhA4EiwA9wYJ3am-6cUhNVDw5OyOdpV6W7P48bZx_TyfZTDgohorHMnLVEh4vfPqnBoCFFQQAvD_BwE$0"


# ---------------------------------------------------------------
# Cabeçalhos (headers) — fazem o robô se parecer mais com um navegador
# comum (Chrome no Windows), o que reduz a chance de bloqueio simples.
# A Amazon costuma checar mais detalhes, então ela recebe um conjunto
# mais completo de cabeçalhos do que as outras lojas.
# ---------------------------------------------------------------
HEADERS_PADRAO = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
}

HEADERS_AMAZON = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-AU,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    # Fingir que viemos de uma busca no Google também ajuda em alguns casos
    "Referer": "https://www.google.com/",
}


# =================================================================
# Funções auxiliares para encontrar preço sem depender de um
# seletor CSS fixo (que quebra fácil quando o site muda o layout)
# =================================================================

def _procurar_preco_recursivo(dado, chaves):
    """
    Percorre um dicionário/lista aninhado (típico de JSON-LD ou do
    'estado' que sites em React/Next.js/Nuxt guardam numa tag <script>)
    procurando por uma chave que pareça ser o preço.
    """
    if isinstance(dado, dict):
        for chave, valor in dado.items():
            if chave in chaves and isinstance(valor, (str, int, float)):
                return str(valor)
            resultado = _procurar_preco_recursivo(valor, chaves)
            if resultado:
                return resultado
    elif isinstance(dado, list):
        for item in dado:
            resultado = _procurar_preco_recursivo(item, chaves)
            if resultado:
                return resultado
    return None


def extrair_de_json_ld(soup):
    """
    Método 1 (mais confiável): procura preço dentro de blocos JSON-LD
    (<script type="application/ld+json">). Muitos e-commerces colocam
    esse bloco pronto no HTML para aparecer no Google Shopping —
    ou seja, não depende de JavaScript ser executado.
    """
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            dados = json.loads(script.string)
        except (TypeError, ValueError):
            continue
        candidatos = dados if isinstance(dados, list) else [dados]
        for item in candidatos:
            preco = _procurar_preco_recursivo(item, chaves=("price", "lowPrice", "highPrice"))
            if preco:
                return preco
    return None


def extrair_de_estado_embutido(html):
    """
    Método 2: sites em React/Next.js/Nuxt costumam colocar os dados da
    página (incluindo o preço) dentro de uma tag <script> só com JSON
    puro (ex.: __NEXT_DATA__, __INITIAL_STATE__, __NUXT__). Isso também
    já vem pronto na resposta do requests — só precisa ser localizado
    com regex e depois lido com json.loads.
    """
    padroes = [
        r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>',
        r'window\.__INITIAL_STATE__\s*=\s*(\{.*?\});',
        r'window\.__NUXT__\s*=\s*(\{.*?\});',
    ]
    for padrao in padroes:
        m = re.search(padrao, html, re.DOTALL)
        if not m:
            continue
        try:
            dados = json.loads(m.group(1))
        except ValueError:
            continue
        preco = _procurar_preco_recursivo(
            dados,
            chaves=("price", "currentPrice", "sellingPrice", "salePrice", "value"),
        )
        if preco:
            return preco
    return None


def extrair_preco_por_regex_simples(html):
    """
    Método 3 (último recurso): procura qualquer coisa parecida com um
    preço em dólar (ex.: $1,299.00) em qualquer lugar do HTML. Menos
    confiável — pode pegar o valor errado se a página tiver vários
    preços (frete, produtos relacionados, parcelamento etc.).
    """
    m = re.search(r"\$\s?\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})", html)
    return m.group(0) if m else None


# =================================================================
# Funções principais — uma para cada loja
# =================================================================

def buscar_preco_amazon(url):
    nome_loja = "Amazon"
    if not url or url.startswith("COLE_O_LINK"):
        return f"⚠️  {nome_loja}: nenhum link foi colado ainda."

    try:
        resposta = requests.get(url, headers=HEADERS_AMAZON, timeout=15)
        resposta.raise_for_status()
    except Exception as erro:
        return f"❌ {nome_loja}: não foi possível acessar a página ({erro})"

    html = resposta.text
    soup = BeautifulSoup(html, "html.parser")

    # Seletores conhecidos da Amazon (mudam de tempos em tempos)
    seletores = [
        ("class", "a-price-whole"),
        ("id", "priceblock_ourprice"),
        ("id", "priceblock_dealprice"),
        ("class", "a-offscreen"),
    ]
    for tipo, valor in seletores:
        elemento = soup.find(id=valor) if tipo == "id" else soup.find(class_=valor)
        if elemento and elemento.get_text(strip=True):
            return f"✅ {nome_loja}: {elemento.get_text(strip=True)}"

    # Se não achou pelos seletores, tenta pelos dados estruturados
    preco = extrair_de_json_ld(soup)
    if preco:
        return f"✅ {nome_loja} (dados estruturados): {preco}"

    if "captcha" in html.lower() or "robot check" in html.lower() or "api-services-support@amazon.com" in html.lower():
        return (
            f"🚫 {nome_loja}: a página devolveu uma verificação anti-robô. "
            f"Não é um erro do código — é um bloqueio da própria Amazon."
        )

    return f"⚠️  {nome_loja}: preço não encontrado."


def buscar_preco_generico(url, nome_loja):
    """Usada para JB Hi-Fi e Officeworks: tenta os 3 métodos, em ordem."""
    if not url or url.startswith("COLE_O_LINK"):
        return f"⚠️  {nome_loja}: nenhum link foi colado ainda."

    try:
        resposta = requests.get(url, headers=HEADERS_PADRAO, timeout=15)
        resposta.raise_for_status()
    except Exception as erro:
        return f"❌ {nome_loja}: não foi possível acessar a página ({erro})"

    html = resposta.text
    soup = BeautifulSoup(html, "html.parser")

    preco = extrair_de_json_ld(soup)
    if preco:
        return f"✅ {nome_loja} (dados estruturados / JSON-LD): {preco}"

    preco = extrair_de_estado_embutido(html)
    if preco:
        return f"✅ {nome_loja} (estado embutido no HTML): {preco}"

    preco = extrair_preco_por_regex_simples(html)
    if preco:
        return f"✅ {nome_loja} (regex simples — confira se é o preço certo): {preco}"

    return (
        f"⚠️  {nome_loja}: preço não encontrado por nenhum dos 3 métodos. "
        f"Provavelmente o preço só existe depois que o JavaScript roda no "
        f"navegador — nesse caso só Selenium/Playwright resolveriam."
    )


# ---------------------------------------------------------------
# Executa a busca e mostra o resultado de cada loja
# ---------------------------------------------------------------
print(buscar_preco_amazon(LINK_AMAZON))
print(buscar_preco_generico(LINK_JBHIFI, "JB Hi-Fi"))
print(buscar_preco_generico(LINK_OFFICEWORKS, "Officeworks"))
