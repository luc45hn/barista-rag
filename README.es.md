# ☕ Barista IA

Asistente inteligente para baristas en entrenamiento. Combina un RAG (Retrieval-Augmented Generation) con conocimiento técnico de café de fuentes especializadas (SCA, James Hoffmann, WCR, Barista Hustle, Scott Rao) con recetas, calibraciones y documentos propios del café.

---

## Arquitectura

```
barista-rag/
├── app.py                          # UI Streamlit — chat, recetas, calibraciones, documentos
├── core/
│   ├── consultant_agent.py         # Agente RAG — intent detection + generación
│   ├── document_manager.py         # Búsqueda vectorial en Supabase (pgvector)
│   ├── document_ingestor.py        # Subida, ingesta y aprobación de documentos de usuarios
│   ├── recipe_manager.py           # CRUD de recetas en Supabase
│   ├── config.py                   # Variables de entorno y configuración
│   ├── logger.py                   # Logger estándar
│   └── theme.py                    # Paleta de colores y constantes de UI
├── knowledge_base/                 # Documentos Markdown base del RAG (globales)
├── scripts/
│   └── ingest.py                   # Ingesta de documentos base (correr 1 vez)
├── static/
│   ├── icon-192.png                # Ícono PWA (192x192)
│   ├── icon-512.png                # Ícono PWA (512x512)
│   └── manifest.json               # Manifiesto PWA
├── supabase/
│   └── migrations/                 # Migrations SQL
├── tests/                          # 56 tests cubriendo todos los módulos
├── .github/
│   └── workflows/
│       ├── tests.yml               # Tests automáticos en cada push a master
│       └── keep_alive.yml          # Ping a la app cada 6 horas
├── .env.example
├── .streamlit/
│   └── config.toml                 # Tema claro con paleta café
└── requirements.txt
```

## Stack tecnológico

| Capa | Tecnología | Detalle |
|---|---|---|
| Frontend | Streamlit | UI web + mobile-first, instalable como PWA |
| LLM | Groq — Llama 3.3 70B | Generación de respuestas (gratuito) |
| Embeddings | Google Gemini Embedding 001 | Vectorización de documentos (gratuito) |
| Vector DB | Supabase + pgvector | Búsqueda semántica |
| Base de datos | Supabase (PostgreSQL) | Cafeterías, recetas, calibraciones, mensajes, documentos y logs |
| Storage | Supabase Storage | Archivos PDF y Markdown subidos por usuarios |
| Auth | Supabase Auth | Login de baristas con scope por cafetería |
| Sesión | streamlit-local-storage | Sesión persistente entre cierres del browser |
| Deploy | Streamlit Cloud | Hosting gratuito |
| CI | GitHub Actions | Tests automáticos + keep alive |

## Modelo multi-cafetería

Cada usuario pertenece a una cafetería (`cafe_id` en los metadatos del usuario en Supabase Auth):

- **Recetas:** las recetas públicas solo las ven los usuarios de la misma cafetería
- **Calibraciones:** visibles solo dentro de la misma cafetería
- **Documentos de usuario:** los documentos subidos están aislados por cafetería
- **RAG:** los chunks del knowledge base, recetas y documentos de usuarios se filtran por cafetería

## Flujo del RAG

```
Usuario escribe pregunta
        ↓
consultant_agent detecta intent
(recipe / troubleshoot / origin / sensory / general)
        ↓
document_manager busca chunks relevantes (vector search)
— incluye knowledge base global + documentos aprobados de la cafetería
        ↓
Groq genera respuesta con el contexto técnico
        ↓
recipe_manager busca recetas RAG públicas filtradas por cafe_id
        ↓
Respuesta + fuentes + recetas relacionadas (expanders) en el chat
        ↓
Mensajes guardados en Supabase para persistencia entre sesiones
        ↓
Query registrada en query_logs
```

## Base de datos — tablas principales

**`cafes`** — cafeterías registradas
```sql
id uuid primary key, name text, city text, created_at timestamptz
```

**`documents`** — chunks con embeddings (globales + de usuarios)
```sql
id bigserial primary key, content text
metadata jsonb  -- { source, cafe_id?, user_document_id?, approved?, chunk_index }
embedding vector(768)
```

**`user_documents`** — registro de documentos subidos por usuarios
```sql
id uuid primary key, cafe_id uuid, uploaded_by text
filename text, storage_path text
approved boolean, approved_by text, created_at timestamptz
```

**`recipes`** — recetas con modelo de visibilidad por cafetería
```sql
id, cafe_name, name, method, coffee_bean
dose_g, water_g, ratio, water_temp_c, brew_time_seconds, yield_g
grind_notes, flavor_notes, tips
created_by, cafe_id, is_public, made_public_by, use_in_rag, created_at
```

**`calibrations`** — notas de calibración diaria (todos los campos opcionales)
```sql
id, recorded_at, shift_moment, room_temp_c, humidity_pct
coffee_name, roaster_name, roast_date, days_since_roast
varietal, origin, altitude_masl, process
grinder_name, grinder_setting, hopper_level, machine_name, group_temp_c
dose_g, yield_g, brew_time_seconds, ratio, tds
extraction_balance, approved, acidity, sweetness, bitterness
flavor_notes, adjustment_vs_prev, free_notes, created_by, cafe_id
```

**`messages`** — historial de chat persistido por usuario
```sql
id uuid primary key, user_email text, cafe_id uuid
role text, content text, sources text[], related_recipes jsonb
created_at timestamptz
```

**`query_logs`** — registro de consultas por usuario
```sql
id, created_at, user_email, query, intents, chunks_found, had_own_recipes
```

## Supabase Storage

Bucket **`user-documents`** (privado) — almacena archivos PDF y Markdown subidos por usuarios.
Estructura de paths: `{cafe_id}/{filename}`

---

## Setup desde cero

### 1. Clonar y crear entorno

```bash
git clone https://github.com/luc45hn/barista-rag
cd barista-rag
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Crear proyecto en Supabase

En **Project Settings → API** copiar Project URL, Publishable key y Secret key.

### 3. Configurar variables de entorno

```bash
cp .env.example .env
```

```
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=tu-publishable-key
SUPABASE_SERVICE_KEY=tu-service-role-key
GOOGLE_API_KEY=tu-google-ai-studio-key
GROQ_API_KEY=tu-groq-key
```

### 4. Crear bucket de Storage

En Supabase **Storage**, crear un bucket privado llamado `user-documents`.

### 5. Ejecutar migrations en Supabase

En el **SQL Editor**, ejecutar el script completo del README en inglés (sección Setup, paso 5).

### 6. Crear cafeterías

```sql
insert into cafes (name, city) values ('Nombre del café', 'Ciudad') returning id, name;
```

### 7. Crear usuarios y asignarlos a cafeterías

```sql
update auth.users
set raw_user_meta_data = jsonb_set(coalesce(raw_user_meta_data, '{}'), '{cafe_id}', '"uuid-cafeteria"')
where email = 'barista@ejemplo.com';
```

### 8. Ingestar documentos base

```bash
python scripts/ingest.py
```

### 9. Correr la app localmente

```bash
streamlit run app.py
```

---

## Deploy en Streamlit Cloud

1. Ir a [share.streamlit.io](https://share.streamlit.io) → conectar repo → main file: `app.py`
2. En **Advanced settings → Secrets** agregar las 5 variables
3. En **GitHub → Settings → Secrets → Actions** agregar las mismas 5 variables

---

## PWA — Instalación en el celular

- **Android:** menú del browser → "Agregar a pantalla de inicio"
- **iPhone:** botón compartir → "Añadir a pantalla de inicio"

La sesión persiste entre cierres gracias a `streamlit-local-storage`.

---

## Base de conocimiento

Documentos globales (disponibles para todas las cafeterías):

| Archivo | Contenido |
|---|---|
| `01_sca_brewing_water_standards.md` | Golden Cup Standard, parámetros de agua SCA/SCAE |
| `02_sca_cva_cupping_protocol.md` | Sistema CVA 2024, protocolo de cata |
| `03_wcr_sensory_lexicon.md` | 110 atributos sensoriales del café |
| `04_espresso_fundamentos.md` | Parámetros de espresso, dialing in, defectos, leche |
| `05_origenes_cafe.md` | Perfiles de sabor por origen, procesos |
| `07_metodos_pourover.md` | V60 (3 recetas), Chemex, Kalita Wave |
| `08_metodos_inmersion.md` | AeroPress (4 recetas), French Press, Cold Brew |
| `09_ciencia_extraccion.md` | TDS, extracción, tabla de molienda |
| `10_james_hoffmann_tecnicas.md` | Ultimate V60, Ultimate AeroPress, Shakerato |
| `11_barista_hustle_scott_rao.md` | Método 80:20, espresso de alta extracción |

Los usuarios también pueden subir sus propios documentos PDF o Markdown desde la sección **Documentos**. Los documentos subidos están aislados por cafetería y requieren aprobación antes de entrar al RAG.

---

## Tests

```bash
pytest tests/ -v
```

56 tests cubriendo config, document manager, recipe manager, agente y app utils.

---

## CI/CD

- **tests.yml** — corre en cada push a `master`
- **keep_alive.yml** — ping cada 6 horas, ejecutable manualmente desde GitHub Actions

---

## Límites de uso (free tier)

| Servicio | Límite gratuito |
|---|---|
| Groq (Llama 3.3 70B) | ~1.700 requests/día |
| Google Gemini Embedding | 1.500 requests/día |
| Supabase | 500 MB base de datos, 1 GB storage, 2 GB bandwidth |
| Streamlit Cloud | 1 app, ~12h inactividad (mantenida activa por GitHub Actions) |
| GitHub Actions | 2.000 minutos/mes |
