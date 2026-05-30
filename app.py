import streamlit as st
from supabase import create_client
from core.config import Config
from core.consultant_agent import ConsultantAgent
from core.recipe_manager import RecipeManager
from core.theme import STREAMLIT_CONFIG, APP_NAME, APP_SUBTITLE
from core.logger import get_logger

logger = get_logger("app")

st.set_page_config(
    page_title="Barista IA",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(STREAMLIT_CONFIG, unsafe_allow_html=True)

def init_supabase():
    return create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)

def login_page(supabase):
    st.markdown(f"## {APP_NAME}")
    st.markdown(f"*{APP_SUBTITLE}*")
    st.divider()
    email = st.text_input("Email")
    password = st.text_input("Contraseña", type="password")
    if st.button("Ingresar", use_container_width=True):
        try:
            response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            st.session_state.user = response.user
            st.session_state.session = response.session
            st.rerun()
        except Exception as e:
            st.error("Email o contraseña incorrectos")

def sidebar(supabase, recipe_manager):
    with st.sidebar:
        st.markdown(f"### {APP_NAME}")
        st.caption(APP_SUBTITLE)
        st.divider()

        user_email = st.session_state.user.email
        user_name = user_email.split("@")[0].capitalize()
        st.markdown(f"👤 **{user_name}**")
        st.divider()

        st.markdown("**Menú**")
        page = st.radio(
            label="navegacion",
            options=["💬 Chat", "📋 Mis recetas", "➕ Nueva receta"],
            label_visibility="collapsed"
        )

        st.divider()
        st.markdown("**Consulta rápida**")
        quick_queries = ["V60", "Espresso", "Leche", "Defectos", "Orígenes", "Extracción"]
        cols = st.columns(2)
        for i, q in enumerate(quick_queries):
            if cols[i % 2].button(q, use_container_width=True, key=f"quick_{q}"):
                st.session_state.quick_query = q
                st.session_state.page = "💬 Chat"
                st.rerun()

        st.divider()
        if st.button("↩ Cerrar sesión", use_container_width=True):
            supabase.auth.sign_out()
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    return page

def chat_page(agent):
    st.markdown("#### Asistente barista")
    st.caption("Base de conocimiento activa · SCA · Hoffmann · WCR")
    st.divider()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "quick_query" in st.session_state:
        quick = st.session_state.pop("quick_query")
        st.session_state.messages.append({"role": "user", "content": quick})
        with st.spinner("Preparando respuesta..."):
            answer, sources = agent.chat(quick, st.session_state.messages[:-1])
        st.session_state.messages.append({
            "role": "assistant",
            "content": answer,
            "sources": sources
        })

    for msg in st.session_state.messages:
        if msg["role"] == "user":
            with st.chat_message("user", avatar="👤"):
                st.write(msg["content"])
        else:
            with st.chat_message("assistant", avatar="☕"):
                st.write(msg["content"])
                if msg.get("sources"):
                    st.caption(f"📚 {' · '.join(msg['sources'])}")

    if prompt := st.chat_input("Preguntá sobre técnicas, recetas, orígenes..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👤"):
            st.write(prompt)
        with st.chat_message("assistant", avatar="☕"):
            with st.spinner(""):
                answer, sources = agent.chat(prompt, st.session_state.messages[:-1])
            st.write(answer)
            if sources:
                st.caption(f"📚 {' · '.join(sources)}")
        st.session_state.messages.append({
            "role": "assistant",
            "content": answer,
            "sources": sources
        })

def recipes_page(recipe_manager):
    st.markdown("#### Mis recetas")
    st.divider()

    approved = recipe_manager.get_approved_recipes()
    pending = recipe_manager.get_pending_recipes(
        created_by=st.session_state.user.email
    )

    if pending:
        st.markdown("**Pendientes de aprobación**")
        for r in pending:
            with st.expander(f"⏳ {r['name']}"):
                st.write(f"Método: {r.get('method', '-')}")
                st.write(f"Café: {r.get('coffee_bean', '-')}")
                st.write(f"Dosis: {r.get('dose_g', '-')}g → Agua: {r.get('water_g', '-')}g")
                st.write(f"Temperatura: {r.get('water_temp_c', '-')}°C")
                st.write(f"Notas: {r.get('flavor_notes', '-')}")
                if st.button("✓ Aprobar", key=f"approve_{r['id']}"):
                    recipe_manager.approve_recipe(
                        r["id"],
                        st.session_state.user.email
                    )
                    st.rerun()

    if approved:
        st.markdown("**Recetas aprobadas**")
        for r in approved:
            with st.expander(f"✅ {r['name']}"):
                col1, col2 = st.columns(2)
                col1.metric("Dosis", f"{r.get('dose_g', '-')}g")
                col1.metric("Temperatura", f"{r.get('water_temp_c', '-')}°C")
                col2.metric("Agua", f"{r.get('water_g', '-')}g")
                col2.metric("Tiempo", f"{r.get('brew_time_seconds', '-')}s")
                if r.get("flavor_notes"):
                    st.caption(f"🫖 {r['flavor_notes']}")
                if r.get("tips"):
                    st.info(r["tips"])

    if not approved and not pending:
        st.info("Todavía no hay recetas. ¡Agregá la primera desde el menú!")

def new_recipe_page(recipe_manager):
    st.markdown("#### Nueva receta")
    st.divider()

    with st.form("nueva_receta"):
        name = st.text_input("Nombre de la receta *", placeholder="V60 Etiopía Yirgacheffe")

        col1, col2 = st.columns(2)
        method = col1.selectbox("Método *", [
            "v60", "chemex", "kalita", "aeropress",
            "french_press", "espresso", "cold_brew", "clever", "otro"
        ])
        coffee_bean = col2.text_input("Café", placeholder="Etiopía Yirgacheffe · El Molino")

        col1, col2, col3 = st.columns(3)
        dose_g = col1.number_input("Dosis (g)", min_value=0.0, step=0.5)
        water_g = col2.number_input("Agua (g)", min_value=0.0, step=5.0)
        water_temp_c = col3.number_input("Temperatura (°C)", min_value=0.0, step=0.5)

        col1, col2, col3 = st.columns(3)
        mins = col1.number_input("Tiempo (min)", min_value=0, step=1)
        secs = col2.number_input("Tiempo (seg)", min_value=0, max_value=59, step=1)
        yield_g = col3.number_input("Rendimiento espresso (g)", min_value=0.0, step=0.5)

        grind_notes = st.text_input("Molienda", placeholder="Ajuste 14 en el Mahlkönig")
        flavor_notes = st.text_input("Notas de sabor", placeholder="Jazmín, limón, retrogusto largo")
        tips = st.text_area("Tips y notas", placeholder="Recordá enjuagar bien el filtro...", height=80)

        submitted = st.form_submit_button("Guardar receta", use_container_width=True)

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
                recipe_manager.create_recipe(recipe)
                st.success("✅ Receta guardada. Queda pendiente de aprobación.")

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

if __name__ == "__main__":
    main()
