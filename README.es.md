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
├── static/
│   ├── icon-192.png                # Ícono PWA (192x192)
│   ├── icon-512.png                # Ícono PWA (512x512)
│   └── manifest.json               # Manifiesto PWA
├── supabase/
│   └── migrations/                 # Migrations SQL
├── tests/                          # 56 tests cubriendo todos los módulos
├── .github/
│   └── workflows/
│       ├── tests.yml               # Corre tests en cada push a master
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
| Base de datos | Supabase (PostgreSQL) | Cafeterías, recetas, calibraciones, mensajes y logs |
| Auth | Supabase Auth | Login de baristas con scope por cafetería |
| Sesión | streamlit-local-storage | Sesión persistente entre cierres del browser |
| Deploy | Streamlit Cloud | Hosting gratuito |
| CI | GitHub Actions | Tests automáticos + keep alive |

## Modelo multi-cafetería

Cada usuario pertenece a una cafetería (`cafe_id` en los metadatos del usuario en Supabase Auth):

- **Recetas:** las recetas públicas solo las ven los usuarios de la misma cafetería
- **Calibraciones:** visibles solo dentro de la misma cafetería
- **RAG:** las recetas relacionadas en el chat se filtran por cafetería

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

**`documents`** — chunks del knowledge base con embeddings
```sql
id bigserial primary key, content text, metadata jsonb, embedding vector(768)
```

**`recipes`** — recetas con modelo de visibilidad por cafetería
```sql
id, cafe_name, name, method, coffee_bean
dose_g, water_g, ratio, water_temp_c, brew_time_seconds, yield_g
grind_notes, flavor_notes, tips
created_by, cafe_id, is_public, made_public_by, use_in_rag, created_at
```

Estados de una receta:
- `is_public = false` → privada, solo visible para el creador
- `is_public = true` → pública, visible para todos los usuarios de la misma cafetería
- `use_in_rag = true` → aparece como receta relacionada en respuestas del chat

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

### 4. Ejecutar migrations en Supabase

En el **SQL Editor** de Supabase, ejecutar este script completo:

```sql
create extension if not exists vector;

create table cafes (
  id uuid primary key default gen_random_uuid(),
  name text not null, city text,
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

create or replace function match_documents(query_embedding vector(768), match_count int default 4)
returns table(id bigint, content text, metadata jsonb, similarity float)
language sql stable security definer as $$
  select id, content, metadata, 1 - (embedding <=> query_embedding) as similarity
  from documents order by embedding <=> query_embedding limit match_count;
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

### 5. Crear cafeterías

```sql
insert into cafes (name, city) values ('Nombre del café', 'Ciudad') returning id, name;
```

### 6. Crear usuarios en Supabase

En **Authentication → Users → Add user → Create new user**.

### 7. Asignar usuarios a cafeterías

```sql
update auth.users
set raw_user_meta_data = jsonb_set(coalesce(raw_user_meta_data, '{}'), '{cafe_id}', '"uuid-de-la-cafeteria"')
where email = 'barista@ejemplo.com';
```

### 8. Ingestar documentos

```bash
python scripts/ingest.py
```

### 9. Correr la app localmente

```bash
streamlit run app.py
```

---

## Deploy en Streamlit Cloud

1. Ir a [share.streamlit.io](https://share.streamlit.io)
2. Conectar el repo de GitHub — main file: `app.py`
3. En **Advanced settings → Secrets** agregar todas las variables del `.env`

### Secrets para GitHub Actions

En **GitHub → Settings → Secrets and variables → Actions**, agregar los mismos 5 secrets. Esto habilita los tests automáticos en cada push.

---

## PWA — Instalación en el celular

Las baristas pueden instalar la app en su pantalla de inicio:

- **Android:** menú del browser → "Agregar a pantalla de inicio"
- **iPhone:** botón compartir → "Añadir a pantalla de inicio"

Una vez instalada, la app se abre sin barra del navegador como una app nativa. La sesión persiste entre cierres gracias a `streamlit-local-storage`.

---

## Base de conocimiento

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

---

## Tests

```bash
pytest tests/ -v
```

56 tests cubriendo config, document manager, recipe manager, agente y app utils.

---

## CI/CD

- **tests.yml** — corre `pytest tests/ -v` en cada push a `master`
- **keep_alive.yml** — hace ping a la app cada 6 horas para evitar que duerma. También se puede ejecutar manualmente desde GitHub Actions.

---

## Límites de uso (free tier)

| Servicio | Límite gratuito |
|---|---|
| Groq (Llama 3.3 70B) | ~1.700 requests/día |
| Google Gemini Embedding | 1.500 requests/día |
| Supabase | 500 MB base de datos, 2 GB bandwidth |
| Streamlit Cloud | 1 app, duerme después de ~12h inactividad (mantenida activa por GitHub Actions) |
| GitHub Actions | 2.000 minutos/mes |
