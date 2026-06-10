# ☕ Barista IA

Asistente inteligente para baristas en entrenamiento. Combina un RAG con conocimiento técnico de café de fuentes especializadas (SCA, James Hoffmann, WCR, Barista Hustle, Scott Rao) con recetas, calibraciones y documentos propios del café.

---

## Arquitectura

```
barista-rag/
├── app.py                          # UI Streamlit — chat, recetas, calibraciones, documentos
├── core/
│   ├── consultant_agent.py         # Agente RAG — detección de intent, búsqueda híbrida, generación
│   ├── document_manager.py         # Búsqueda vectorial + búsqueda híbrida por intent
│   ├── document_ingestor.py        # Subida, ingesta y aprobación de documentos de usuarios
│   ├── recipe_manager.py           # CRUD de recetas
│   ├── config.py                   # Variables de entorno y configuración
│   ├── logger.py                   # Logger estándar
│   └── theme.py                    # Paleta de colores y constantes de UI
├── knowledge_base/
│   ├── 01-11_...                   # SCA, WCR, Hoffmann, Scott Rao, orígenes, métodos
│   └── 12_equipamiento_maquinas_espresso.md  # Guía de máquinas, calderas y variables ajustables
├── scripts/
│   └── ingest.py                   # Ingesta de documentos base (preserva documentos de usuarios)
├── static/                         # Íconos PWA y manifest
├── tests/                          # 56 tests
├── .github/workflows/              # tests.yml + keep_alive.yml (Playwright)
└── requirements.txt
```

## Stack tecnológico

| Capa | Tecnología | Detalle |
|---|---|---|
| Frontend | Streamlit | UI web + mobile-first, instalable como PWA |
| LLM | Gemini 2.5 Flash → Groq fallback | API key por cafetería, fallback automático |
| Embeddings | Google Gemini Embedding 001 | Key separada (`GOOGLE_EMBEDDING_KEY`) para cuota independiente |
| Vector DB | Supabase + pgvector | Búsqueda vectorial + búsqueda híbrida por intent |
| Base de datos | Supabase (PostgreSQL) | Cafeterías, recetas, calibraciones, mensajes, documentos, logs |
| Storage | Supabase Storage | Archivos PDF y Markdown subidos por usuarios |
| Auth | Supabase Auth | Login de baristas con scope por cafetería |
| Sesión | streamlit-local-storage | Sesión persistente entre cierres del browser |
| Deploy | Streamlit Cloud | Hosting gratuito |
| CI | GitHub Actions | Tests automáticos + keep alive con Playwright cada 2h |

## Modelo multi-cafetería

Cada usuario pertenece a una cafetería (`cafe_id` en los metadatos de Supabase Auth). Cada cafetería puede tener su propia Gemini API key (`gemini_api_key` en tabla `cafes`):

- **Recetas, calibraciones, documentos, mensajes** — visibles solo dentro de la misma cafetería
- **RAG** — chunks del knowledge base + documentos aprobados filtrados por cafetería
- **LLM** — usa la key de Gemini de la cafetería si existe, fallback automático a Groq

## Flujo del RAG

```
Usuario escribe pregunta
        ↓
consultant_agent detecta intent
(recipe / troubleshoot / origin / sensory / general)
        ↓
document_manager: búsqueda vectorial (top 4 chunks)
+ búsqueda híbrida: si intent=origin → fuerza 1 chunk del documento de orígenes
        ↓
Gemini 2.5 Flash genera respuesta (fallback a Groq en 429/503)
        ↓
recipe_manager: busca recetas RAG públicas de la cafetería
        ↓
Respuesta + fuentes + expanders de recetas relacionadas
        ↓
Mensajes guardados en Supabase → historial persistente
        ↓
Query registrada en query_logs
```

## Base de datos — tablas principales

**`cafes`**
```sql
id uuid, name text, city text, gemini_api_key text, created_at timestamptz
```

**`documents`** — knowledge base global + documentos de usuarios
```sql
id bigserial, content text
metadata jsonb  -- { source, cafe_id?, user_document_id?, approved?, chunk_index }
embedding vector(768)
```

**`user_documents`**
```sql
id uuid, cafe_id uuid, uploaded_by text, filename text, storage_path text
approved boolean, approved_by text, created_at timestamptz
```

**`recipes`**
```sql
id, cafe_name, name, method, coffee_bean, dose_g, water_g, ratio
water_temp_c, brew_time_seconds, yield_g, grind_notes, flavor_notes, tips
created_by, cafe_id, is_public, made_public_by, use_in_rag, created_at
```

**`calibrations`** — todos los campos opcionales
```sql
id, recorded_at, shift_moment, room_temp_c, humidity_pct
coffee_name, roaster_name, roast_date, days_since_roast, varietal, origin
altitude_masl, process, grinder_name, grinder_setting, hopper_level
machine_name, group_temp_c, dose_g, yield_g, brew_time_seconds, ratio, tds
extraction_balance, acidity, sweetness, bitterness, flavor_notes
adjustment_vs_prev, free_notes, created_by, cafe_id
```

**`messages`**
```sql
id uuid, user_email text, cafe_id uuid
role text, content text, sources text[], related_recipes jsonb, created_at timestamptz
```

**`query_logs`**
```sql
id, created_at, user_email, query, intents, chunks_found, had_own_recipes
```

---

## Setup desde cero

### 1. Clonar y crear entorno

```bash
git clone https://github.com/luc45hn/barista-rag
cd barista-rag
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Crear proyecto en Supabase

Copiar Project URL, Publishable key y Secret key desde **Project Settings → API**.

### 3. Configurar variables de entorno

```bash
cp .env.example .env
```

```
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=tu-publishable-key
SUPABASE_SERVICE_KEY=tu-service-role-key
GOOGLE_API_KEY=tu-gemini-flash-key          # LLM (por cafetería, o fallback)
GOOGLE_EMBEDDING_KEY=tu-embedding-key       # Solo embeddings (cuota separada)
GROQ_API_KEY=tu-groq-key                    # LLM fallback (siempre gratuito)
```

> **Nota:** `GOOGLE_API_KEY` y `GOOGLE_EMBEDDING_KEY` pueden ser la misma key o diferentes. Usar keys separadas duplica el cupo gratuito de embeddings.

### 4. Crear bucket de Storage

En Supabase **Storage**, crear un bucket privado llamado `user-documents`.

### 5. Ejecutar migrations en Supabase

En el **SQL Editor**, ejecutar este script completo:

```sql
create extension if not exists vector;

create table cafes (
  id uuid primary key default gen_random_uuid(),
  name text not null, city text,
  gemini_api_key text,
  created_at timestamptz not null default now()
);
alter table cafes enable row level security;
create policy "read cafes" on cafes for select using (true);

create table documents (
  id bigserial primary key, content text not null,
  metadata jsonb, embedding vector(768)
);
create index on documents using hnsw (embedding vector_cosine_ops);
alter table documents enable row level security;
create policy "read documents" on documents for select using (true);

create or replace function match_documents(
  query_embedding vector(768),
  match_count int default 4,
  filter_cafe_id uuid default null
)
returns table(id bigint, content text, metadata jsonb, similarity float)
language sql stable security definer as $$
  select id, content, metadata,
    1 - (embedding <=> query_embedding) as similarity
  from documents
  where
    (metadata->>'cafe_id') is null
    or (
      (filter_cafe_id is null or (metadata->>'cafe_id') = filter_cafe_id::text)
      and (metadata->>'approved' = 'true' or metadata->>'approved' is null)
    )
  order by embedding <=> query_embedding
  limit match_count;
$$;

create or replace function get_my_cafe_id()
returns uuid language sql stable security definer as $$
  select (raw_user_meta_data->>'cafe_id')::uuid from auth.users where id = auth.uid();
$$;

create table recipes (
  id uuid primary key default gen_random_uuid(),
  cafe_name text not null, name text not null, method text not null,
  coffee_bean text, dose_g numeric, water_g numeric, ratio text,
  water_temp_c numeric, brew_time_seconds integer, yield_g numeric,
  grind_notes text, flavor_notes text, tips text,
  created_by text not null, cafe_id uuid references cafes(id),
  is_public boolean not null default false, made_public_by text,
  use_in_rag boolean not null default false,
  created_at timestamptz not null default now()
);
alter table recipes enable row level security;
create policy "Users can read recipes in their cafe" on recipes for select
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
  created_by text not null, cafe_id uuid references cafes(id)
);
alter table calibrations enable row level security;
create policy "Users can read calibrations in their cafe" on calibrations for select
  using (cafe_id = get_my_cafe_id() or created_by = auth.email());
create policy "insert calibrations" on calibrations for insert with check (true);

create table user_documents (
  id uuid primary key default gen_random_uuid(),
  cafe_id uuid not null references cafes(id),
  uploaded_by text not null, filename text not null, storage_path text not null,
  approved boolean not null default false, approved_by text,
  created_at timestamptz not null default now()
);
alter table user_documents enable row level security;
create policy "Users can read documents in their cafe"
  on user_documents for select using (cafe_id = get_my_cafe_id());
create policy "Users can insert documents" on user_documents for insert with check (true);
create policy "Users can update documents in their cafe"
  on user_documents for update using (cafe_id = get_my_cafe_id());

create table messages (
  id uuid primary key default gen_random_uuid(),
  user_email text not null, cafe_id uuid references cafes(id),
  role text not null, content text not null,
  sources text[], related_recipes jsonb,
  created_at timestamptz not null default now()
);
alter table messages enable row level security;
create policy "Users can read own messages" on messages for select using (user_email = auth.email());
create policy "Users can insert own messages" on messages for insert with check (user_email = auth.email());

create table query_logs (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  user_email text not null, query text not null,
  intents text[], chunks_found integer, had_own_recipes boolean default false
);
alter table query_logs enable row level security;
create policy "insert query_logs" on query_logs for insert with check (true);
create policy "read query_logs" on query_logs for select using (true);
```

### 6. Crear cafeterías y asignar usuarios

```sql
insert into cafes (name, city) values ('Nombre', 'Ciudad') returning id;

update auth.users
set raw_user_meta_data = jsonb_set(coalesce(raw_user_meta_data, '{}'), '{cafe_id}', '"uuid"')
where email = 'barista@ejemplo.com';
```

### 7. Asignar Gemini API key por cafetería (opcional)

```sql
update cafes set gemini_api_key = 'tu-key' where id = 'cafe-uuid';
```

Sin key, la cafetería usa Groq/Llama automáticamente.

### 8. Ingestar documentos base

```bash
python scripts/ingest.py
```

Seguro re-ejecutar — preserva chunks de documentos de usuarios.

### 9. Correr la app localmente

```bash
streamlit run app.py
```

---

## Deploy en Streamlit Cloud

1. Conectar repo en [share.streamlit.io](https://share.streamlit.io) → main file: `app.py`
2. Agregar los 6 secrets en **Advanced settings → Secrets**
3. Agregar los mismos secrets en **GitHub → Settings → Secrets → Actions**

---

## PWA — Instalación en el celular

- **Android:** menú del browser → "Agregar a pantalla de inicio"
- **iPhone:** botón compartir → "Añadir a pantalla de inicio"

La sesión persiste entre cierres gracias a `streamlit-local-storage`.

---

## Base de conocimiento

| Archivo | Contenido |
|---|---|
| `01_sca_brewing_water_standards.md` | Golden Cup, parámetros de agua SCA |
| `02_sca_cva_cupping_protocol.md` | CVA 2024, protocolo de cata |
| `03_wcr_sensory_lexicon.md` | 110 atributos sensoriales |
| `04_espresso_fundamentos.md` | Parámetros de espresso, dialing in, defectos |
| `05_origenes_cafe.md` | Perfiles de sabor por origen y proceso |
| `07_metodos_pourover.md` | V60, Chemex, Kalita Wave |
| `08_metodos_inmersion.md` | AeroPress, French Press, Cold Brew |
| `09_ciencia_extraccion.md` | TDS, extracción, tabla de molienda |
| `10_james_hoffmann_tecnicas.md` | Ultimate V60, AeroPress, Shakerato |
| `11_barista_hustle_scott_rao.md` | Método 80:20, espresso de alta extracción |
| `12_equipamiento_maquinas_espresso.md` | Máquinas (Simonelli, La Marzocco, Victoria Arduino, Rancilio), tipos de caldera, variables ajustables por máquina |

---

## Tests

```bash
pytest tests/ -v  # 56 tests
```

---

## CI/CD

- **tests.yml** — corre en cada push a `master`
- **keep_alive.yml** — script Playwright cada 2h, clickea el botón de "wake up" si la app está dormida

---

## Límites de uso (free tier)

| Servicio | Límite gratuito |
|---|---|
| Groq (Llama 3.3 70B) | ~1.700 req/día |
| Gemini 2.5 Flash | 20 req/día (por key) |
| Gemini Embedding 001 | 1.500 req/día (por key) |
| Supabase | 500 MB DB, 1 GB storage, 2 GB bandwidth |
| Streamlit Cloud | 1 app, ~12h inactividad (mantenida activa por GitHub Actions) |
| GitHub Actions | 2.000 min/mes |
