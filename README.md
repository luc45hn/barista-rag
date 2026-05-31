# ☕ Barista IA

Asistente inteligente para baristas en entrenamiento. Combina un RAG (Retrieval-Augmented Generation) con conocimiento técnico de café de fuentes especializadas (SCA, James Hoffmann, WCR, Barista Hustle, Scott Rao) con recetas y calibraciones propias del café.

---

## Arquitectura

```
barista-rag/
├── app.py                          # UI Streamlit — chat, recetas, calibraciones
├── core/
│   ├── consultant_agent.py         # Agente RAG — intent detection + generación
│   ├── document_manager.py         # Búsqueda vectorial en Supabase (pgvector)
│   ├── recipe_manager.py           # CRUD de recetas en Supabase
│   ├── config.py                   # Variables de entorno y configuración
│   ├── logger.py                   # Logger estándar
│   └── theme.py                    # Paleta de colores y constantes de UI
├── knowledge_base/                 # Documentos Markdown que conforman el RAG
│   ├── 01_sca_brewing_water_standards.md
│   ├── 02_sca_cva_cupping_protocol.md
│   ├── 03_wcr_sensory_lexicon.md
│   ├── 04_espresso_fundamentos.md
│   ├── 05_origenes_cafe.md
│   ├── 07_metodos_pourover.md
│   ├── 08_metodos_inmersion.md
│   ├── 09_ciencia_extraccion.md
│   ├── 10_james_hoffmann_tecnicas.md
│   └── 11_barista_hustle_scott_rao.md
├── scripts/
│   └── ingest.py                   # Ingesta de documentos a Supabase (correr 1 vez)
├── supabase/
│   └── migrations/
│       ├── 001_auth_rls.sql        # RLS policies para tabla recipes
│       └── 002_recipes.sql         # Schema de tabla recipes
├── tests/
│   ├── test_document_manager.py
│   ├── test_recipe_manager.py
│   └── test_consultant_agent.py
├── .env.example
├── .streamlit/
│   └── config.toml                 # Tema claro con paleta café
└── requirements.txt
```

### Stack tecnológico

| Capa | Tecnología | Detalle |
|---|---|---|
| Frontend | Streamlit | UI web + mobile |
| LLM | Groq — Llama 3.3 70B | Generación de respuestas (gratuito) |
| Embeddings | Google Gemini Embedding 001 | Vectorización de documentos (gratuito) |
| Vector DB | Supabase + pgvector | Búsqueda semántica |
| Base de datos | Supabase (PostgreSQL) | Recetas y calibraciones |
| Auth | Supabase Auth | Login de baristas |
| Deploy | Streamlit Cloud | Hosting gratuito |

### Flujo del RAG

```
Usuario escribe pregunta
        ↓
consultant_agent detecta intent
(recipe / troubleshoot / origin / sensory / general)
        ↓
        ├── recipe_manager busca recetas propias aprobadas (SQL)
        └── document_manager busca chunks relevantes (vector search)
                ↓
        Se construye contexto combinado
                ↓
        Groq genera respuesta con el contexto
                ↓
        Respuesta + fuentes se muestran en el chat
```

### Base de datos — tablas principales

**`documents`** — chunks del knowledge base con embeddings
```sql
id          bigserial primary key
content     text
metadata    jsonb        -- { source: "04_espresso_fundamentos.md", chunk_index: 0 }
embedding   vector(768)  -- gemini-embedding-001 con output_dimensionality=768
```

**`recipes`** — recetas propias del café
```sql
id, cafe_name, name, method, coffee_bean
dose_g, water_g, ratio, water_temp_c, brew_time_seconds, yield_g
grind_notes, flavor_notes, tips
created_by, approved, approved_by, created_at
```

**`calibrations`** — notas de calibración diaria
```sql
id, recorded_at, shift_moment, room_temp_c, humidity_pct
coffee_name, roaster_name, roast_date, days_since_roast
varietal, origin, altitude_masl, process
grinder_name, grinder_setting, hopper_level, machine_name, group_temp_c
dose_g, yield_g, brew_time_seconds, ratio, tds
extraction_balance, approved, acidity, sweetness, bitterness
flavor_notes, adjustment_vs_prev, free_notes, created_by
```

---

## Setup desde cero

### 1. Clonar y crear entorno

```bash
git clone https://github.com/luc45hn/barista-rag
cd barista-rag
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Crear proyecto en Supabase

1. Crear nuevo proyecto en [supabase.com](https://supabase.com)
2. En **Project Settings → API** copiar:
   - Project URL → `SUPABASE_URL`
   - Publishable key → `SUPABASE_KEY`
   - Secret key → `SUPABASE_SERVICE_KEY`

### 3. Configurar variables de entorno

```bash
cp .env.example .env
```

Completar `.env`:
```
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=tu-publishable-key
SUPABASE_SERVICE_KEY=tu-service-role-key
GOOGLE_API_KEY=tu-google-ai-studio-key
GROQ_API_KEY=tu-groq-key
```

**Google API Key:** [aistudio.google.com](https://aistudio.google.com) → Get API key → Create API key

**Groq API Key:** [console.groq.com](https://console.groq.com) → API Keys → Create key

### 4. Ejecutar migrations en Supabase

En el **SQL Editor** de Supabase, ejecutar en orden:

```sql
-- Habilitar extensión de vectores
create extension if not exists vector;

-- Tabla de documentos con embeddings
create table documents (
  id         bigserial primary key,
  content    text not null,
  metadata   jsonb,
  embedding  vector(768)
);
create index on documents using hnsw (embedding vector_cosine_ops);
alter table documents enable row level security;
create policy "Authenticated users can read documents"
  on documents for select using (true);

-- Función de búsqueda vectorial
create or replace function match_documents(
  query_embedding vector(768),
  match_count     int default 4
)
returns table(id bigint, content text, metadata jsonb, similarity float)
language sql stable security definer as $$
  select id, content, metadata,
    1 - (embedding <=> query_embedding) as similarity
  from documents
  order by embedding <=> query_embedding
  limit match_count;
$$;
```

Luego ejecutar el contenido de `supabase/migrations/002_recipes.sql` y `supabase/migrations/001_auth_rls.sql`.

Para la tabla de calibraciones:

```sql
create table calibrations (
  id uuid primary key default gen_random_uuid(),
  recorded_at timestamptz not null default now(),
  shift_moment text, room_temp_c numeric, humidity_pct numeric,
  coffee_name text, roaster_name text, roast_date date, days_since_roast integer,
  varietal text, origin text, altitude_masl integer, process text,
  grinder_name text, grinder_setting text, hopper_level text,
  machine_name text, group_temp_c numeric, pressure_bar numeric,
  dose_g numeric, yield_g numeric, brew_time_seconds integer, ratio text, tds numeric,
  approved boolean default false, extraction_balance text,
  acidity integer, sweetness integer, bitterness integer,
  flavor_notes text, adjustment_vs_prev text, free_notes text,
  created_by text not null
);
alter table calibrations enable row level security;
create policy "read calibrations" on calibrations for select using (true);
create policy "insert calibrations" on calibrations for insert with check (true);
```

### 5. Crear usuarios en Supabase

En **Authentication → Users → Add user → Create new user** crear los usuarios de las baristas con email y contraseña.

### 6. Ingestar documentos

```bash
python scripts/ingest.py
```

Esto lee los 11 archivos Markdown de `knowledge_base/`, los divide en chunks, genera embeddings con Gemini y los sube a Supabase. Tarda ~3 minutos. Se puede re-ejecutar para actualizar la base de conocimiento.

### 7. Correr la app localmente

```bash
streamlit run app.py
```

---

## Deploy en Streamlit Cloud

1. Ir a [share.streamlit.io](https://share.streamlit.io)
2. Conectar el repo de GitHub
3. Main file: `app.py`
4. En **Advanced settings → Secrets** agregar todas las variables del `.env`:

```toml
SUPABASE_URL = "https://..."
SUPABASE_KEY = "..."
SUPABASE_SERVICE_KEY = "..."
GOOGLE_API_KEY = "..."
GROQ_API_KEY = "..."
```

---

## Base de conocimiento

Los documentos en `knowledge_base/` cubren:

| Archivo | Contenido |
|---|---|
| `01_sca_brewing_water_standards.md` | Golden Cup Standard, parámetros de agua SCA/SCAE, cupping, métodos |
| `02_sca_cva_cupping_protocol.md` | Sistema CVA 2024, protocolo de cata, glosario sensorial |
| `03_wcr_sensory_lexicon.md` | 110 atributos sensoriales del café con descripción y referencias |
| `04_espresso_fundamentos.md` | Parámetros de espresso, dialing in, defectos, leche, mantenimiento |
| `05_origenes_cafe.md` | Perfiles de sabor por origen, procesos, guía de selección |
| `07_metodos_pourover.md` | V60 (3 recetas), Chemex, Kalita Wave con troubleshooting |
| `08_metodos_inmersion.md` | AeroPress (4 recetas), French Press, Clever Dripper, Cold Brew |
| `09_ciencia_extraccion.md` | TDS, extracción, tabla de molienda, Brewing Control Chart |
| `10_james_hoffmann_tecnicas.md` | Ultimate V60, Ultimate AeroPress, Shakerato, Espresso Tonic |
| `11_barista_hustle_scott_rao.md` | Método 80:20, extracción diferencial, espresso de alta extracción |

### Agregar documentos al knowledge base

1. Agregar archivo `.md` a la carpeta `knowledge_base/`
2. Re-ejecutar `python scripts/ingest.py`
3. El script limpia y re-ingesta todos los documentos automáticamente

---

## Uso de la app

### Chat
El uso principal. Las baristas pueden preguntar en lenguaje natural:
- *"¿cómo corrijo un espresso ácido?"*
- *"¿cuál es el ratio para el V60?"*
- *"¿qué diferencia hay entre un latte y un flat white?"*
- *"¿a qué sabe un café de Kenia?"*

El agente detecta el intent, busca contexto relevante en los documentos y en las recetas propias del café, y genera una respuesta citando las fuentes.

### Recetas propias
Las baristas pueden cargar las recetas específicas de su café (con los gramos exactos de su máquina, el café que tienen en carta, etc.). Las recetas quedan pendientes de aprobación hasta que una barista senior las valide. Una vez aprobadas, el agente las prioriza sobre el conocimiento genérico cuando responde preguntas relacionadas.

### Calibraciones
Registro diario de la calibración del molino y la máquina. Ningún campo es obligatorio — se captura lo que se pueda en el momento. El historial permite ver cómo evolucionan los parámetros a lo largo del tiempo.

---

## Límites de uso (free tier)

| Servicio | Límite gratuito |
|---|---|
| Groq (Llama 3.3 70B) | ~1.700 requests/día |
| Google Gemini Embedding | 1.500 requests/día |
| Supabase | 500 MB base de datos, 2 GB bandwidth |
| Streamlit Cloud | 1 app, siempre activa |

Para uso de 2–3 baristas en un turno normal, estos límites son más que suficientes.