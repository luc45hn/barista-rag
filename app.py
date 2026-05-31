import streamlit as st
from supabase import create_client
from core.config import Config
from core.consultant_agent import ConsultantAgent
from core.recipe_manager import RecipeManager
from core.logger import get_logger

logger = get_logger("app")

SOURCE_LABELS = {
    "01_sca_brewing_water_standards.md": "SCA Brewing Standards",
    "02_sca_cva_cupping_protocol.md": "SCA Cupping Protocol",
    "03_wcr_sensory_lexicon.md": "WCR Sensory Lexicon",
    "04_espresso_fundamentos.md": "Espresso Fundamentos",
    "05_origenes_cafe.md": "Orígenes del Café",
    "06_recetario_propio_TEMPLATE.md": "Recetario Propio",
    "07_metodos_pourover.md": "Métodos Pour Over",
    "08_metodos_inmersion.md": "Métodos Inmersión",
    "09_ciencia_extraccion.md": "Ciencia de Extracción",
    "10_james_hoffmann_tecnicas.md": "James Hoffmann",
    "11_barista_hustle_scott_rao.md": "Barista Hustle · Scott Rao",
    "Recetas propias": "Recetas del café",
}

def format_sources(sources: list[str]) -> str:
    labels = [SOURCE_LABELS.get(s, s) for s in sources]
    return " · ".join(labels)

st.set_page_config(
    page_title="Barista IA",
    page_icon="☕",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    /* Fondo general */
    .stApp { background-color: #FAF6F0; }

    /* Ocultar header de Streamlit */
    header[data-testid="stHeader"] { background-color: #3D2314; }

    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #3D2314; }
    [data-testid="stSidebar"] * { color: #F0E0C8 !important; }
    [data-testid="stSidebar"] .stButton > button {
        background-color: rgba(196,149,106,0.2) !important;
        color: #F0E0C8 !important;
        border: 1px solid rgba(196,149,106,0.3) !important;
        border-radius: 10px !important;
        font-size: 15px !important;
        padding: 10px !important;
        margin-bottom: 4px !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background-color: rgba(196,149,106,0.35) !important;
    }
    [data-testid="stSidebar"] .stRadio label { color: #F0E0C8 !important; }

    /* Chat messages */
    [data-testid="stChatMessage"] {
        background-color: #FFFFFF;
        border: 1px solid rgba(107,58,42,0.1);
        border-radius: 16px;
        padding: 12px 16px;
    }
    [data-testid="stChatMessage"] p {
        color: #2C1810 !important;
        font-size: 15px !important;
        line-height: 1.6 !important;
    }

    /* Input de chat */
    [data-testid="stChatInput"] {
        background-color: #FFFFFF;
        border-top: 1px solid rgba(107,58,42,0.15);
        padding: 12px;
    }
    [data-testid="stChatInput"] textarea {
        background-color: #F5ECD7 !important;
        border: 1px solid #E8D5B0 !important;
        border-radius: 22px !important;
        color: #2C1810 !important;
        font-size: 15px !important;
        padding: 12px 16px !important;
    }

    /* Pills de consulta rápida */
    .pill-container {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin: 8px 0 16px 0;
    }
    .pill {
        background: #F0D9C0;
        color: #6B3A2A;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 14px;
        font-weight: 500;
        cursor: pointer;
        border: 1px solid rgba(107,58,42,0.15);
        display: inline-block;
    }

    /* Botones generales */
    .stButton > button {
        background-color: #6B3A2A !important;
        color: #F5ECD7 !important;
        border: none !important;
        border-radius: 10px !important;
        font-size: 15px !important;
        padding: 10px 20px !important;
    }
    .stButton > button:hover {
        background-color: #2C1810 !important;
    }

    /* Login */
    .login-container {
        max-width: 360px;
        margin: 60px auto;
        padding: 32px;
        background: #FFFFFF;
        border-radius: 20px;
        border: 1px solid rgba(107,58,42,0.15);
    }
    .login-title {
        font-size: 28px;
        font-weight: 700;
        color: #2C1810;
        text-align: center;
        margin-bottom: 4px;
    }
    .login-subtitle {
        font-size: 14px;
        color: #A07860;
        text-align: center;
        margin-bottom: 24px;
    }

    /* Source badge */
    .source-badge {
        font-size: 12px;
        color: #A07860;
        margin-top: 6px;
        padding: 4px 10px;
        background: #F5ECD7;
        border-radius: 10px;
        display: inline-block;
    }

    /* Inputs */
    .stTextInput input, .stTextArea textarea {
        border-radius: 10px !important;
        border: 1px solid #E8D5B0 !important;
        background-color: #FFFFFF !important;
        color: #2C1810 !important;
        font-size: 15px !important;
    }
    .stSelectbox select {
        border-radius: 10px !important;
        color: #2C1810 !important;
    }

    /* Métricas */
    [data-testid="stMetric"] {
        background: #F5ECD7;
        border-radius: 10px;
        padding: 10px;
    }
    [data-testid="stMetricValue"] { color: #6B3A2A !important; }
    [data-testid="stMetricLabel"] { color: #A07860 !important; }

    /* Ocultar elementos de Streamlit */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    [data-testid="collapsedControl"] { display: none; }

    /* Flecha del sidebar siempre blanca */
    [data-testid="collapsedControl"],
    [data-testid="collapsedControl"] *,
    [data-testid="collapsedControl"] button,
    [data-testid="collapsedControl"] button * {
        display: block !important;
        color: #F0E0C8 !important;
        fill: #F0E0C8 !important;
        stroke: #F0E0C8 !important;
        background: transparent !important;
    }

    /* Pills de consulta rápida en el chat */
    div[data-testid="column"] .stButton > button {
        background-color: #F0D9C0 !important;
        color: #6B3A2A !important;
        border: 1px solid rgba(107,58,42,0.2) !important;
        border-radius: 20px !important;
        font-size: 13px !important;
        padding: 6px 8px !important;
        font-weight: 500 !important;
    }
    div[data-testid="column"] .stButton > button:hover {
        background-color: #E8C9A8 !important;
    }
            /* Flecha del sidebar - forzar con atributo */
span[data-testid="stIconMaterial"],
span[data-testid="stIconMaterial"][color] {
    color: #F0E0C8 !important;
    -webkit-text-fill-color: #F0E0C8 !important;
}
</style>
""", unsafe_allow_html=True)

def init_supabase():
    return create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)

def login_page(supabase):
    st.markdown("""
    <div class="login-container">
        <div class="login-title">☕ Barista IA</div>
        <div class="login-subtitle">Asistente de entrenamiento</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        email = st.text_input("Email", placeholder="tu@email.com")
        password = st.text_input("Contraseña", type="password")
        if st.button("Ingresar ☕", use_container_width=True):
            try:
                response = supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })
                st.session_state.user = response.user
                st.session_state.session = response.session
                st.rerun()
            except Exception:
                st.error("Email o contraseña incorrectos")

def sidebar(supabase, recipe_manager):
    with st.sidebar:
        user_email = st.session_state.user.email
        user_name = user_email.split("@")[0].capitalize()

        st.markdown(f"### ☕ Barista IA")
        st.markdown(f"👤 **{user_name}**")
        st.divider()

        st.markdown("**Menú**")
        if st.button("💬  Chat", use_container_width=True, key="nav_chat"):
            st.session_state.current_page = "💬 Chat"
            st.rerun()
        if st.button("📋  Mis recetas", use_container_width=True, key="nav_recetas"):
            st.session_state.current_page = "📋 Mis recetas"
            st.rerun()
        if st.button("➕  Nueva receta", use_container_width=True, key="nav_nueva"):
            st.session_state.current_page = "➕ Nueva receta"
            st.rerun()
        if st.button("🎯  Nueva calibración", use_container_width=True, key="nav_calibracion"):
            st.session_state.current_page = "🎯 Nueva calibración"
            st.rerun()
        if st.button("📖  Historial", use_container_width=True, key="nav_historial"):
            st.session_state.current_page = "📖 Historial"
            st.rerun()

        st.divider()
        if st.button("↩  Cerrar sesión", use_container_width=True):
            supabase.auth.sign_out()
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

        st.divider()
        st.markdown("**📚 Base de conocimiento**")
        if st.button("Ver documentos", use_container_width=True, key="ver_docs"):
            st.session_state.show_docs = not st.session_state.get("show_docs", False)

        if st.session_state.get("show_docs", False):
            docs = [
                "SCA Brewing & Water Standards",
                "SCA CVA Cupping Protocol",
                "WCR Sensory Lexicon",
                "Espresso Fundamentos",
                "Orígenes del Café",
                "Métodos Pour Over",
                "Métodos Inmersión",
                "Ciencia de Extracción",
                "James Hoffmann Técnicas",
                "Barista Hustle · Scott Rao",
            ]
            for doc in docs:
                st.caption(f"• {doc}")

    return st.session_state.get("current_page", "💬 Chat")

def chat_page(agent):
    user_name = st.session_state.user.email.split("@")[0].capitalize()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "quick_query" in st.session_state:
        quick = st.session_state.pop("quick_query")
        st.session_state.messages.append({"role": "user", "content": quick})
        with st.spinner(""):
            answer, sources = agent.chat(quick, st.session_state.messages[:-1], user_email=st.session_state.user.email)
        st.session_state.messages.append({
            "role": "assistant",
            "content": answer,
            "sources": sources
        })

    if not st.session_state.messages:
        st.markdown(f"#### Hola {user_name} 👋")
        st.caption("Preguntame sobre técnicas, recetas u orígenes")
        st.markdown("<br>", unsafe_allow_html=True)

        quick_queries = [
            ("☕ Espresso", "Espresso"),
            ("🫗 V60", "V60"),
            ("🥛 Leche", "Leche"),
            ("⚠️ Defectos", "Defectos"),
            ("🌍 Orígenes", "Orígenes"),
            ("🔬 Extracción", "Extracción"),
        ]
        for label, q in quick_queries:
            if st.button(label, use_container_width=True, key=f"main_quick_{q}"):
                st.session_state.quick_query = q
                st.rerun()

    for msg in st.session_state.messages:
        if msg["role"] == "user":
            with st.chat_message("user", avatar="👤"):
                st.write(msg["content"])
        else:
            with st.chat_message("assistant", avatar="☕"):
                st.write(msg["content"])
                if msg.get("sources"):
                    st.markdown(
                        f'<div class="source-badge">📚 {format_sources(msg["sources"])}</div>',
                        unsafe_allow_html=True
                    )

    if prompt := st.chat_input("Preguntá algo..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👤"):
            st.write(prompt)
        with st.chat_message("assistant", avatar="☕"):
            with st.spinner(""):
                answer, sources = agent.chat(prompt, st.session_state.messages[:-1], user_email=st.session_state.user.email)
            st.write(answer)
            if sources:
                st.markdown(
                    f'<div class="source-badge">📚 {format_sources(sources)}</div>',
                    unsafe_allow_html=True
                )
        st.session_state.messages.append({
            "role": "assistant",
            "content": answer,
            "sources": sources
        })

def recipes_page(recipe_manager):
    st.markdown("#### 📋 Mis recetas")
    st.divider()

    approved = recipe_manager.get_approved_recipes()
    pending = recipe_manager.get_pending_recipes(
        created_by=st.session_state.user.email
    )

    if pending:
        st.markdown("**⏳ Pendientes de aprobación**")
        for r in pending:
            with st.expander(f"{r['name']}"):
                st.write(f"**Método:** {r.get('method', '-')}")
                st.write(f"**Café:** {r.get('coffee_bean', '-')}")
                col1, col2 = st.columns(2)
                col1.write(f"**Dosis:** {r.get('dose_g', '-')}g")
                col2.write(f"**Agua:** {r.get('water_g', '-')}g")
                col1.write(f"**Temperatura:** {r.get('water_temp_c', '-')}°C")
                if r.get("flavor_notes"):
                    st.caption(f"🫖 {r['flavor_notes']}")
                if st.button("✓ Aprobar receta", key=f"approve_{r['id']}", use_container_width=True):
                    token = st.session_state.session.access_token
                    recipe_manager.supabase.postgrest.auth(token)
                    recipe_manager.approve_recipe(r["id"], st.session_state.user.email)
                    st.rerun()

    if approved:
        st.markdown("**✅ Recetas aprobadas**")
        for r in approved:
            with st.expander(f"{r['name']}"):
                col1, col2 = st.columns(2)
                col1.metric("Dosis", f"{r.get('dose_g', '-')}g")
                col2.metric("Agua", f"{r.get('water_g', '-')}g")
                col1.metric("Temp.", f"{r.get('water_temp_c', '-')}°C")
                if r.get("brew_time_seconds"):
                    mins = r["brew_time_seconds"] // 60
                    secs = r["brew_time_seconds"] % 60
                    col2.metric("Tiempo", f"{mins}:{secs:02d}")
                if r.get("flavor_notes"):
                    st.caption(f"🫖 {r['flavor_notes']}")
                if r.get("tips"):
                    st.info(r["tips"])

    if not approved and not pending:
        st.info("Todavía no hay recetas. ¡Agregá la primera desde el menú!")

def new_recipe_page(recipe_manager):
    st.markdown("#### ➕ Nueva receta")
    st.divider()

    with st.form("nueva_receta"):
        name = st.text_input("Nombre *", placeholder="V60 Etiopía Yirgacheffe")

        col1, col2 = st.columns(2)
        method = col1.selectbox("Método *", [
            "v60", "chemex", "kalita", "aeropress",
            "french_press", "espresso", "cold_brew", "clever", "otro"
        ])
        coffee_bean = col2.text_input("Café", placeholder="Etiopía · El Molino")

        col1, col2, col3 = st.columns(3)
        dose_g = col1.number_input("Dosis (g)", min_value=0.0, step=0.5)
        water_g = col2.number_input("Agua (g)", min_value=0.0, step=5.0)
        water_temp_c = col3.number_input("Temp. (°C)", min_value=0.0, step=0.5)

        col1, col2, col3 = st.columns(3)
        mins = col1.number_input("Tiempo (min)", min_value=0, step=1)
        secs = col2.number_input("Tiempo (seg)", min_value=0, max_value=59, step=1)
        yield_g = col3.number_input("Rendimiento (g)", min_value=0.0, step=0.5)

        grind_notes = st.text_input("Molienda", placeholder="Ajuste 14 en el Mahlkönig")
        flavor_notes = st.text_input("Notas de sabor", placeholder="Jazmín, limón, retrogusto largo")
        tips = st.text_area("Tips", placeholder="Recordá enjuagar bien el filtro...", height=80)

        submitted = st.form_submit_button("💾 Guardar receta", use_container_width=True)

        if submitted:
            if not name:
                st.error("El nombre es obligatorio")
            else:
                brew_time = (mins * 60) + secs
                ratio = f"1:{round(water_g/dose_g, 1)}" if dose_g > 0 and water_g > 0 else None
                recipe = {
                    "cafe_name": "Barista IA",
                    "name": name,
                    "method": method,
                    "coffee_bean": coffee_bean or None,
                    "dose_g": dose_g or None,
                    "water_g": water_g or None,
                    "ratio": ratio,
                    "water_temp_c": water_temp_c or None,
                    "brew_time_seconds": brew_time or None,
                    "yield_g": yield_g or None,
                    "grind_notes": grind_notes or None,
                    "flavor_notes": flavor_notes or None,
                    "tips": tips or None,
                    "created_by": st.session_state.user.email,
                    "approved": False,
                }
                token = st.session_state.session.access_token
                recipe_manager.supabase.postgrest.auth(token)
                recipe_manager.create_recipe(recipe)
                st.success("✅ Receta guardada. Queda pendiente de aprobación.")

def calibration_page(supabase):
    st.markdown("#### 🎯 Nueva calibración")
    st.caption("Completá lo que tengas disponible — ningún campo es obligatorio")
    st.divider()

    with st.form("nueva_calibracion"):

        st.markdown("**☁️ Condiciones ambientales**")
        col1, col2, col3 = st.columns(3)
        shift_moment = col1.selectbox("Momento del turno",
            ["", "Apertura", "Media jornada", "Tarde", "Cierre"],
            index=0)
        room_temp_c = col2.number_input("Temperatura (°C)", min_value=0.0, step=0.5, value=0.0)
        humidity_pct = col3.number_input("Humedad (%)", min_value=0.0, max_value=100.0, step=1.0, value=0.0)

        st.divider()
        st.markdown("**☕ El café**")
        col1, col2 = st.columns(2)
        coffee_name = col1.text_input("Nombre del café", placeholder="Etiopía Yirgacheffe")
        roaster_name = col2.text_input("Tostador", placeholder="El Molino")

        col1, col2, col3 = st.columns(3)
        roast_date = col1.date_input("Fecha de tueste", value=None)
        varietal = col2.text_input("Varietal", placeholder="Heirloom")
        process = col3.selectbox("Proceso", ["", "Lavado", "Natural", "Honey", "Anaeróbico", "Otro"])

        col1, col2 = st.columns(2)
        origin = col1.text_input("Origen / Región", placeholder="Gedeo Zone, Etiopía")
        altitude_masl = col2.number_input("Altitud (msnm)", min_value=0, step=50, value=0)

        st.divider()
        st.markdown("**⚙️ Equipo**")
        col1, col2, col3 = st.columns(3)
        grinder_name = col1.text_input("Molino", placeholder="Mahlkönig EK43")
        grinder_setting = col2.text_input("Ajuste de molienda", placeholder="14 / 3 clicks más fino")
        hopper_level = col3.selectbox("Nivel del hopper", ["", "Lleno", "Mitad", "Bajo"])

        col1, col2 = st.columns(2)
        machine_name = col1.text_input("Máquina", placeholder="La Marzocco Linea")
        group_temp_c = col2.number_input("Temperatura de grupo (°C)", min_value=0.0, step=0.5, value=0.0)

        st.divider()
        st.markdown("**📊 Parámetros encontrados**")
        col1, col2, col3, col4 = st.columns(4)
        dose_g = col1.number_input("Dosis (g)", min_value=0.0, step=0.5, value=0.0)
        yield_g = col2.number_input("Rendimiento (g)", min_value=0.0, step=0.5, value=0.0)
        brew_time_secs = col3.number_input("Tiempo (s)", min_value=0, step=1, value=0)
        tds = col4.number_input("TDS (%)", min_value=0.0, step=0.01, value=0.0)

        st.divider()
        st.markdown("**👅 Evaluación sensorial**")
        col1, col2 = st.columns(2)
        extraction_balance = col1.selectbox("Balance",
            ["", "Subextraído", "Balanceado", "Sobreextraído"])
        approved = col2.checkbox("✓ Calibración aprobada")

        col1, col2, col3 = st.columns(3)
        acidity = col1.slider("Acidez", 0, 5, 0)
        sweetness = col2.slider("Dulzura", 0, 5, 0)
        bitterness = col3.slider("Amargor", 0, 5, 0)

        flavor_notes = st.text_input("Notas de sabor",
            placeholder="Jazmín, limón, chocolate...")
        adjustment_vs_prev = st.text_input("Ajuste respecto a calibración anterior",
            placeholder="Molí 2 clicks más fino por humedad alta")
        free_notes = st.text_area("Notas libres",
            placeholder="Cualquier observación del día...", height=80)

        submitted = st.form_submit_button("💾 Guardar calibración", use_container_width=True)

        if submitted:
            days_since_roast = None
            if roast_date:
                from datetime import date
                days_since_roast = (date.today() - roast_date).days

            ratio = f"1:{round(yield_g/dose_g, 1)}" if dose_g > 0 and yield_g > 0 else None

            data = {
                "shift_moment": shift_moment or None,
                "room_temp_c": room_temp_c or None,
                "humidity_pct": humidity_pct or None,
                "coffee_name": coffee_name or None,
                "roaster_name": roaster_name or None,
                "roast_date": roast_date.isoformat() if roast_date else None,
                "days_since_roast": days_since_roast,
                "varietal": varietal or None,
                "process": process or None,
                "origin": origin or None,
                "altitude_masl": altitude_masl or None,
                "grinder_name": grinder_name or None,
                "grinder_setting": grinder_setting or None,
                "hopper_level": hopper_level or None,
                "machine_name": machine_name or None,
                "group_temp_c": group_temp_c or None,
                "dose_g": dose_g or None,
                "yield_g": yield_g or None,
                "brew_time_seconds": brew_time_secs or None,
                "ratio": ratio,
                "tds": tds or None,
                "extraction_balance": extraction_balance or None,
                "approved": approved,
                "acidity": acidity or None,
                "sweetness": sweetness or None,
                "bitterness": bitterness or None,
                "flavor_notes": flavor_notes or None,
                "adjustment_vs_prev": adjustment_vs_prev or None,
                "free_notes": free_notes or None,
                "created_by": st.session_state.user.email,
            }
            token = st.session_state.session.access_token
            supabase.postgrest.auth(token)
            supabase.table("calibrations").insert(data).execute()
            st.success("✅ Calibración guardada.")

def calibrations_history_page(supabase):
    st.markdown("#### 📖 Historial de calibraciones")
    st.divider()

    token = st.session_state.session.access_token
    supabase.postgrest.auth(token)
    response = supabase.table("calibrations").select("*").order("recorded_at", desc=True).limit(20).execute()
    calibrations = response.data or []

    if not calibrations:
        st.info("Todavía no hay calibraciones guardadas.")
        return

    for c in calibrations:
        from datetime import datetime
        dt = datetime.fromisoformat(c["recorded_at"].replace("Z", "+00:00"))
        label = f"{dt.strftime('%d/%m %H:%M')} — {c.get('coffee_name') or 'Sin nombre'}"
        if c.get("approved"):
            label = "✅ " + label
        with st.expander(label):
            col1, col2, col3 = st.columns(3)
            if c.get("shift_moment"):
                col1.write(f"**Turno:** {c['shift_moment']}")
            if c.get("room_temp_c"):
                col2.write(f"**Temp ambiente:** {c['room_temp_c']}°C")
            if c.get("humidity_pct"):
                col3.write(f"**Humedad:** {c['humidity_pct']}%")
            if c.get("grinder_setting"):
                col1.write(f"**Molienda:** {c['grinder_setting']}")
            if c.get("dose_g") and c.get("yield_g"):
                col2.write(f"**Ratio:** {c.get('ratio', '-')}")
            if c.get("brew_time_seconds"):
                col3.write(f"**Tiempo:** {c['brew_time_seconds']}s")
            if c.get("extraction_balance"):
                st.write(f"**Balance:** {c['extraction_balance']}")
            if c.get("flavor_notes"):
                st.caption(f"🫖 {c['flavor_notes']}")
            if c.get("free_notes"):
                st.info(c["free_notes"])
            if c.get("adjustment_vs_prev"):
                st.caption(f"🔧 {c['adjustment_vs_prev']}")

def main():
    Config.validate()
    supabase = init_supabase()

    if "user" not in st.session_state:
        login_page(supabase)
        return

    recipe_manager = RecipeManager()
    agent = ConsultantAgent()

    page = sidebar(supabase, recipe_manager)

    if page == "💬 Chat":
        chat_page(agent)
    elif page == "📋 Mis recetas":
        recipes_page(recipe_manager)
    elif page == "➕ Nueva receta":
        new_recipe_page(recipe_manager)
    elif page == "🎯 Nueva calibración":
        calibration_page(supabase)
    elif page == "📖 Historial":
        calibrations_history_page(supabase)

if __name__ == "__main__":
    main()
