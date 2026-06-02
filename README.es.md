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
├── scripts/
│   └── ingest.py                   # Ingesta de documentos a Supabase (correr 1 vez)
├── supabase/
│   └── migrations/                 # Migrations SQL
├── tests/                          # 41 tests cubriendo todos los módulos core
├── .env.example
├── .streamlit/
│   └── config.toml                 # Tema claro con paleta café
└── requirements.txt
```

## Stack tecnológico

| Capa | Tecnología | Detalle |
|---|---|---|
| Frontend | Streamlit | UI web + mobile-first |
| LLM | Groq — Llama 3.3 70B | Generación de respuestas (gratuito) |
| Embeddings | Google Gemini Embedding 001 | Vectorización de documentos (gratuito) |
| Vector DB | Supabase + pgvector | Búsqueda semántica |
| Base de datos | Supabase (PostgreSQL) | Cafeterías, recetas, calibraciones y logs |
| Auth | Supabase Auth | Login de baristas con scope por cafetería |
| Deploy | Streamlit Cloud | Hosting gratuito |

## Modelo multi-cafetería

Cada usuario pertenece a una cafetería (`cafe_id` guardado en los metadatos del usuario en Supabase Auth). Los datos están aislados por cafetería:

- **Recetas:** las recetas públicas solo las ven los usuarios de la misma cafetería
- **Calibraciones:** visibles solo dentro de la misma cafetería
- **RAG:** las recetas relacionadas que aparecen en el chat se filtran por la cafetería del usuario

## Flujo del RAG

```
Usuario escribe pregunta
        ↓
consultant_agent detecta intent
(recipe / troubleshoot / origin / sensory / general)
        ↓
document_manager busca chunks relevantes (vector search)
        ↓
Groq genera respuesta con el contexto técnico
        ↓
recipe_manager busca recetas RAG públicas filtradas por cafe_id
        ↓
Respuesta + fuentes + recetas relacionadas (expanders) se muestran en el chat
        ↓
Query se registra en query_logs
```

## Base de datos — tablas principales

**`cafes`** — cafeterías registradas en la plataforma
```sql
id          uuid primary key
name        text
city        text
created_at  timestamptz
```

**`documents`** — chunks del knowledge base con embeddings
```sql
id          bigserial primary key
content     text
metadata    jsonb        -- { source: "04_espresso_fundamentos.md", chunk_index: 0 }
embedding   vector(768)  -- gemini-embedding-001 con output_dimensionality=768
```

**`recipes`** — recetas del café con modelo de visibilidad por cafetería
```sql
id, cafe_name, name, method, coffee_bean
dose_g, water_g, ratio, water_temp_c, brew_time_seconds, yield_g
grind_notes, flavor_notes, tips
created_by, cafe_id, is_public, made_public_by, use_in_rag, created_at
```

Estados de una receta:
- `is_public = false` → privada, solo visible para el creador
- `is_public = true` → pública, visible para todos los usuarios de la misma cafetería
- `use_in_rag = true` → aparece como receta relacionada en respuestas del chat (requiere `is_public = true`)

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

**`query_logs`** — registro de consultas por usuario
```sql
id, created_at, user_email, query, intents, chunks_found, had_own_recipes
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

En el **SQL Editor** de Supabase, ejecutar este script completo:

```sql
create extension if not exists vector;

create table cafes (
  id          uuid primary key default gen_random_uuid(),
  name        text not null,
  city        text,
  created_at  timestamptz not null default now()
);
alter table cafes enable row level security;
create policy "read cafes" on cafes for select using (true);

create table documents (
  id         bigserial primary key,
  content    text not null,
  metadata   jsonb,
  embedding  vector(768)
);
create index on documents using hnsw (embedding vector_cosine_ops);
alter table documents enable row level security;
create policy "read documents" on documents for select using (true);

create or replace function match_documents(
  query_embedding vector(768),
  match_count int default 4
)
returns table(id bigint, content text, metadata jsonb, similarity float)
language sql stable security definer as $$
  select id, content, metadata,
    1 - (embedding <=> query_embedding) as similarity
  from documents
  order by embedding <=> query_embedding
  limit match_count;
$$;

create or replace function get_my_cafe_id()
returns uuid language sql stable security definer as $$
  select (raw_user_meta_data->>'cafe_id')::uuid
  from auth.users where id = auth.uid();
$$;

create table recipes (
  id                  uuid primary key default gen_random_uuid(),
  cafe_name           text not null,
  name                text not null,
  method              text not null,
  coffee_bean         text,
  dose_g              numeric,
  water_g             numeric,
  ratio               text,
  water_temp_c        numeric,
  brew_time_seconds   integer,
  yield_g             numeric,
  grind_notes         text,
  flavor_notes        text,
  tips                text,
  created_by          text not null,
  cafe_id             uuid references cafes(id),
  is_public           boolean not null default false,
  made_public_by      text,
  use_in_rag          boolean not null default false,
  created_at          timestamptz not null default now()
);
alter table recipes enable row level security;
create policy "Users can read recipes in their cafe"
  on recipes for select
  using (cafe_id = get_my_cafe_id() or created_by = auth.email());
create policy "Users can insert recipes" on recipes for insert with check (true);
create policy "Users can update own recipes" on recipes for update using (created_by = auth.email());

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
  created_by text not null,
  cafe_id uuid references cafes(id)
);
alter table calibrations enable row level security;
create policy "Users can read calibrations in their cafe"
  on calibrations for select
  using (cafe_id = get_my_cafe_id() or created_by = auth.email());
create policy "insert calibrations" on calibrations for insert with check (true);

create table query_logs (
  id          uuid primary key default gen_random_uuid(),
  created_at  timestamptz not null default now(),
  user_email  text not null,
  query       text not null,
  intents     text[],
  chunks_found integer,
  had_own_recipes boolean default false
);
alter table query_logs enable row level security;
create policy "insert query_logs" on query_logs for insert with check (true);
create policy "read query_logs" on query_logs for select using (true);
```

### 5. Crear cafeterías

```sql
insert into cafes (name, city) values ('Nombre del café', 'Ciudad') returning id, name;
```

Guardá los UUIDs devueltos — los necesitás para asignar a los usuarios.

### 6. Crear usuarios en Supabase

En **Authentication → Users → Add user → Create new user** crear los usuarios con email y contraseña.

### 7. Asignar usuarios a cafeterías

En el **SQL Editor**, asignar el `cafe_id` a cada usuario:

```sql
update auth.users
set raw_user_meta_data = jsonb_set(
  coalesce(raw_user_meta_data, '{}'),
  '{cafe_id}',
  '"uuid-de-la-cafeteria"'
)
where email = 'barista@ejemplo.com';
```

### 8. Ingestar documentos

```bash
python scripts/ingest.py
```

Lee los 11 archivos Markdown de `knowledge_base/`, los divide en chunks, genera embeddings y los sube a Supabase. Tarda ~3 minutos. Se puede re-ejecutar para actualizar la base de conocimiento.

### 9. Correr la app localmente

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

---

## Tests

```bash
pytest tests/ -v
```

41 tests cubriendo config, document manager, recipe manager y el agente.

---

## Límites de uso (free tier)

| Servicio | Límite gratuito |
|---|---|
| Groq (Llama 3.3 70B) | ~1.700 requests/día |
| Google Gemini Embedding | 1.500 requests/día |
| Supabase | 500 MB base de datos, 2 GB bandwidth |
| Streamlit Cloud | 1 app, siempre activa |

Para uso de 2–3 baristas en un turno normal, estos límites son más que suficientes.
