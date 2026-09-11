"""
Rastreador MacBook AU — app Streamlit
======================================

Site local para registrar e comparar preços de MacBook em lojas da Austrália.
O histórico é salvo em um arquivo CSV (macbook_prices.csv), criado
automaticamente na mesma pasta deste script — armazenamento local, sem
depender de Google Colab, Drive ou qualquer serviço externo.

Como rodar:
    pip install streamlit pandas plotly
    streamlit run app.py

O navegador abre sozinho em http://localhost:8501
"""

import uuid
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ----------------------------------------------------------------------------
# Configuração e "banco de dados" local (CSV)
# ----------------------------------------------------------------------------

DATA_FILE = Path(__file__).parent / "macbook_prices.csv"

COLUMNS = [
    "id", "model", "retailer", "retailer_url", "price_aud",
    "condition", "in_stock", "logged_at", "note", "created_at",
]

COMMON_RETAILERS = [
    "Apple Store", "JB Hi-Fi", "Officeworks", "Harvey Norman",
    "The Good Guys", "Amazon AU", "Kogan", "Catch", "eBay AU",
]

COMMON_MODELS = [
    'MacBook Air 13" M3 (8GB/256GB)',
    'MacBook Air 13" M3 (16GB/256GB)',
    'MacBook Air 15" M3 (8GB/256GB)',
    'MacBook Air 13" M4 (16GB/256GB)',
    'MacBook Air 15" M4 (16GB/256GB)',
    'MacBook Pro 14" M4 (16GB/512GB)',
    'MacBook Pro 14" M4 Pro (24GB/512GB)',
]

SEED_MODEL = 'Exemplo — MacBook Air 13" M3 (8GB/256GB)'

# Paleta (validada para leitura por daltônicos — ver skill de dataviz)
ACCENT = "#2a78d6"       # azul — linha/série principal
ACCENT_2 = "#eb6834"     # laranja
GOOD = "#0ca30c"
CRITICAL = "#d03b3b"
LINE_COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#4a3aa7", "#e34948"]


def _seed_dataframe() -> pd.DataFrame:
    """Algumas linhas de exemplo, claramente marcadas, para a tela não
    aparecer vazia na primeira execução."""
    today = date.today()
    rows = [
        {
            "id": str(uuid.uuid4()), "model": SEED_MODEL, "retailer": "Apple Store",
            "retailer_url": "https://www.apple.com/au/shop/buy-mac/macbook-air",
            "price_aud": 1899, "condition": "novo", "in_stock": True,
            "logged_at": today - pd.Timedelta(days=18), "note": "preço oficial (exemplo)",
            "created_at": datetime.now().isoformat(timespec="seconds"),
        },
        {
            "id": str(uuid.uuid4()), "model": SEED_MODEL, "retailer": "JB Hi-Fi",
            "retailer_url": "", "price_aud": 1799, "condition": "novo", "in_stock": True,
            "logged_at": today - pd.Timedelta(days=10), "note": "exemplo",
            "created_at": datetime.now().isoformat(timespec="seconds"),
        },
        {
            "id": str(uuid.uuid4()), "model": SEED_MODEL, "retailer": "Officeworks",
            "retailer_url": "", "price_aud": 1729, "condition": "novo", "in_stock": False,
            "logged_at": today - pd.Timedelta(days=2), "note": "exemplo — promoção",
            "created_at": datetime.now().isoformat(timespec="seconds"),
        },
    ]
    return pd.DataFrame(rows, columns=COLUMNS)


def load_data() -> pd.DataFrame:
    """Carrega o histórico do CSV local; cria o arquivo com dados de
    exemplo se ele ainda não existir."""
    if DATA_FILE.exists():
        df = pd.read_csv(DATA_FILE)
    else:
        df = _seed_dataframe()
        save_data(df)

    for col in COLUMNS:
        if col not in df.columns:
            df[col] = None

    df["logged_at"] = pd.to_datetime(df["logged_at"], errors="coerce")
    df["price_aud"] = pd.to_numeric(df["price_aud"], errors="coerce")
    df["in_stock"] = df["in_stock"].fillna(True).astype(bool)
    df["retailer_url"] = df["retailer_url"].fillna("")
    df["note"] = df["note"].fillna("")
    return df.dropna(subset=["model", "retailer", "price_aud", "logged_at"])


def save_data(df: pd.DataFrame) -> None:
    out = df.copy()
    out["logged_at"] = pd.to_datetime(out["logged_at"]).dt.strftime("%Y-%m-%d")
    out.to_csv(DATA_FILE, index=False, columns=COLUMNS)


def add_entry(**fields) -> None:
    df = st.session_state.df
    new_row = {
        "id": str(uuid.uuid4()),
        "created_at": datetime.now().isoformat(timespec="seconds"),
        **fields,
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_data(df)
    st.session_state.df = load_data()


def delete_entry(entry_id: str) -> None:
    df = st.session_state.df
    df = df[df["id"] != entry_id]
    save_data(df)
    st.session_state.df = load_data()


def format_aud(value: float) -> str:
    if pd.isna(value):
        return "—"
    if float(value).is_integer():
        return f"$ {value:,.0f}"
    return f"$ {value:,.2f}"


# ----------------------------------------------------------------------------
# Página
# ----------------------------------------------------------------------------

st.set_page_config(
    page_title="Rastreador MacBook AU",
    page_icon="💻",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Fraunces:wght@600;700&family=Inter:wght@400;500;600;700&display=swap');

      html, body, [class*="css"]  { font-family: 'Inter', sans-serif; }
      h1, h2, h3 { font-family: 'Fraunces', Georgia, serif !important; }

      .hero-title { font-family:'Fraunces', Georgia, serif; font-weight:700; font-size:2.1rem; margin-bottom:0.1rem; }
      .hero-sub { color:#6b7a75; font-size:0.98rem; max-width:70ch; margin-bottom:0.6rem; }
      .private-note{
        display:inline-flex; align-items:center; gap:7px; font-size:0.8rem; color:#6b7a75;
        border:1px solid rgba(16,31,28,0.12); border-radius:999px; padding:4px 12px; margin-bottom:1.2rem;
      }
      .private-note .dot{ width:6px; height:6px; border-radius:50%; background:#0ca30c; }

      div[data-testid="stMetric"]{
        background: rgba(42,120,214,0.06); border:1px solid rgba(16,31,28,0.08);
        border-radius:14px; padding: 14px 16px 10px;
      }
      div[data-testid="stMetricLabel"] { font-size:0.8rem; color:#6b7a75; }

      .stButton>button[kind="primary"]{ background-color:#2a78d6; border-color:#2a78d6; }
      .stButton>button[kind="primary"]:hover{ background-color:#2266bb; border-color:#2266bb; }
    </style>
    """,
    unsafe_allow_html=True,
)

if "df" not in st.session_state:
    st.session_state.df = load_data()

df = st.session_state.df

st.markdown('<div class="hero-title">💻 Rastreador MacBook AU</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-sub">Registre o preço do MacBook em cada loja que você conferir na Austrália, '
    'acompanhe a variação ao longo do tempo e descubra a melhor hora e o melhor lugar para comprar — '
    'para levar de presente pra sua mãe.</div>',
    unsafe_allow_html=True,
)
st.markdown('<div class="private-note"><span class="dot"></span> Dados salvos localmente em macbook_prices.csv</div>', unsafe_allow_html=True)

if SEED_MODEL in df["model"].unique():
    st.info(
        "As linhas com **Exemplo** no nome são só demonstração. Use \"Remover um registro\" "
        "na barra lateral para apagá-las e comece a registrar os preços reais que você encontrar.",
        icon="💡",
    )

# ---------------------------------------------------------------- sidebar ---

with st.sidebar:
    st.header("Registrar novo preço")

    with st.form("add_form", clear_on_submit=True):
        existing_models = sorted(m for m in df["model"].unique() if not m.startswith("Exemplo"))
        model_options = existing_models + [m for m in COMMON_MODELS if m not in existing_models]

        model_choice = st.selectbox("Modelo", options=["— selecione —"] + model_options)
        model_custom = st.text_input("Ou digite um modelo novo", placeholder='ex.: MacBook Pro 16" M4 Max (36GB/1TB)')

        existing_retailers = sorted(df["retailer"].unique())
        retailer_options = existing_retailers + [r for r in COMMON_RETAILERS if r not in existing_retailers]
        retailer_choice = st.selectbox("Loja", options=["— selecione —"] + retailer_options)
        retailer_custom = st.text_input("Ou digite outra loja")

        price = st.number_input("Preço (AUD)", min_value=0, step=10, value=0)
        col_a, col_b = st.columns(2)
        with col_a:
            condition = st.radio("Condição", options=["novo", "recondicionado"], format_func=lambda v: "Novo" if v == "novo" else "Recondicionado")
        with col_b:
            in_stock = st.checkbox("Em estoque", value=True)
        logged_at = st.date_input("Data", value=date.today())
        retailer_url = st.text_input("Link do produto (opcional)")
        note = st.text_input("Nota (opcional)", placeholder="ex.: cupom de 10%, Black Friday...")

        submitted = st.form_submit_button("Salvar preço", type="primary", use_container_width=True)

        if submitted:
            final_model = model_custom.strip() or (model_choice if model_choice != "— selecione —" else "")
            final_retailer = retailer_custom.strip() or (retailer_choice if retailer_choice != "— selecione —" else "")
            if not final_model or not final_retailer or price <= 0:
                st.error("Preencha ao menos modelo, loja e um preço maior que zero.")
            else:
                add_entry(
                    model=final_model, retailer=final_retailer, retailer_url=retailer_url.strip(),
                    price_aud=price, condition=condition, in_stock=in_stock,
                    logged_at=logged_at, note=note.strip(),
                )
                st.success("Preço salvo!")
                st.rerun()

    st.divider()
    st.subheader("Remover um registro")
    if df.empty:
        st.caption("Nenhum registro ainda.")
    else:
        df_sorted = df.sort_values("logged_at", ascending=False)
        labels = {
            row.id: f'{row.logged_at.strftime("%d/%m/%Y")} · {row.retailer} · {format_aud(row.price_aud)} — {row.model}'
            for row in df_sorted.itertuples()
        }
        to_remove = st.selectbox("Selecione o registro", options=list(labels.keys()), format_func=lambda i: labels[i])
        if st.button("Excluir registro selecionado", use_container_width=True):
            delete_entry(to_remove)
            st.success("Registro removido.")
            st.rerun()

# ----------------------------------------------------------------- main -----

if df.empty:
    st.warning("Nenhum preço registrado ainda. Use o formulário na barra lateral para começar.")
    st.stop()

models = sorted(df["model"].unique(), key=lambda m: (m.startswith("Exemplo"), m))
selected_model = st.radio("Modelo", options=models, horizontal=True, label_visibility="collapsed")

filtered = df[df["model"] == selected_model].sort_values("logged_at")

# --- KPIs ---
cheapest = filtered.loc[filtered["price_aud"].idxmin()]
latest = filtered.iloc[-1]
first = filtered.iloc[0]
savings = max(0.0, first["price_aud"] - cheapest["price_aud"])
n_stores = filtered["retailer"].nunique()

k1, k2, k3, k4 = st.columns(4)
k1.metric("Menor preço encontrado", format_aud(cheapest["price_aud"]), f'{cheapest["retailer"]} · {cheapest["logged_at"].strftime("%d/%m")}')
k2.metric("Preço mais recente", format_aud(latest["price_aud"]), f'{latest["retailer"]} · {latest["logged_at"].strftime("%d/%m")}')
k3.metric("Economia encontrada", format_aud(savings) if savings > 0 else "—", "vs. primeiro preço registrado" if savings > 0 else "sem variação ainda")
k4.metric("Lojas comparadas", n_stores, ", ".join(sorted(filtered["retailer"].unique())[:3]))

st.markdown("### Preços atuais")
st.caption("Preço mais recente registrado em cada loja para este modelo.")

current = (
    filtered.sort_values("logged_at")
    .groupby("retailer", as_index=False)
    .last()
    .sort_values("price_aud")
)
current_display = current[["retailer", "price_aud", "condition", "in_stock", "logged_at", "retailer_url", "note"]].rename(
    columns={
        "retailer": "Loja", "price_aud": "Preço", "condition": "Condição",
        "in_stock": "Em estoque", "logged_at": "Atualizado em", "retailer_url": "Link", "note": "Nota",
    }
)
current_display["Condição"] = current_display["Condição"].map({"novo": "Novo", "recondicionado": "Recondicionado"}).fillna(current_display["Condição"])

st.dataframe(
    current_display,
    hide_index=True,
    use_container_width=True,
    column_config={
        "Preço": st.column_config.NumberColumn("Preço (AUD)", format="$ %.0f"),
        "Atualizado em": st.column_config.DateColumn("Atualizado em", format="DD/MM/YYYY"),
        "Em estoque": st.column_config.CheckboxColumn("Em estoque"),
        "Link": st.column_config.LinkColumn("Link", display_text="abrir ↗"),
    },
)

st.markdown("### Histórico de preços")
st.caption("Cada ponto é um preço registrado; o marcador em destaque mostra o menor preço encontrado.")

fig = go.Figure()
for i, (retailer, group) in enumerate(filtered.groupby("retailer")):
    group = group.sort_values("logged_at")
    color = LINE_COLORS[i % len(LINE_COLORS)]
    fig.add_trace(
        go.Scatter(
            x=group["logged_at"], y=group["price_aud"], mode="lines+markers", name=retailer,
            line=dict(width=2, color=color), marker=dict(size=8, color=color, line=dict(width=2, color="#ffffff")),
            hovertemplate="<b>%{fullData.name}</b><br>%{x|%d/%m/%Y}<br>$ %{y:,.0f}<extra></extra>",
        )
    )

fig.add_trace(
    go.Scatter(
        x=[cheapest["logged_at"]], y=[cheapest["price_aud"]], mode="markers", name="Menor preço",
        marker=dict(size=16, color="rgba(0,0,0,0)", line=dict(width=2, color=GOOD)),
        hoverinfo="skip", showlegend=False,
    )
)

fig.update_layout(
    template="plotly_white",
    height=420,
    margin=dict(l=10, r=10, t=10, b=10),
    hovermode="closest",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    xaxis=dict(title="Data", showgrid=False),
    yaxis=dict(title="Preço (AUD)", tickprefix="$ ", gridcolor="rgba(16,31,28,0.08)"),
    font=dict(family="Inter, sans-serif", color="#101f1c"),
)

st.plotly_chart(fig, use_container_width=True)

with st.expander("Ver histórico completo (todas as lojas e datas)"):
    history_display = filtered.sort_values("logged_at", ascending=False)[
        ["logged_at", "retailer", "price_aud", "condition", "in_stock", "note"]
    ].rename(columns={
        "logged_at": "Data", "retailer": "Loja", "price_aud": "Preço",
        "condition": "Condição", "in_stock": "Em estoque", "note": "Nota",
    })
    history_display["Condição"] = history_display["Condição"].map({"novo": "Novo", "recondicionado": "Recondicionado"}).fillna(history_display["Condição"])
    st.dataframe(
        history_display, hide_index=True, use_container_width=True,
        column_config={
            "Data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
            "Preço": st.column_config.NumberColumn("Preço (AUD)", format="$ %.0f"),
            "Em estoque": st.column_config.CheckboxColumn("Em estoque"),
        },
    )

st.caption("Rastreador MacBook AU · dados salvos em " + DATA_FILE.name)
