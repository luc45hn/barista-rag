# ☕ Barista IA

Intelligent assistant for baristas in training. Combines a RAG (Retrieval-Augmented Generation) with technical coffee knowledge from specialized sources (SCA, James Hoffmann, WCR, Barista Hustle, Scott Rao) with the café's own recipes and calibration notes.

> 📖 [Versión en español](README.es.md)

---

## Architecture

```
barista-rag/
├── app.py                          # Streamlit UI — chat, recipes, calibrations
├── core/
│   ├── consultant_agent.py         # RAG agent — intent detection + generation
│   ├── document_manager.py         # Vector search in Supabase (pgvector)
│   ├── recipe_manager.py           # Recipe CRUD in Supabase
│   ├── config.py                   # Environment variables and configuration
│   ├── logger.py                   # Standard logger
│   └── theme.py                    # Color palette and UI constants
├── knowledge_base/                 # Markdown documents that form the RAG
├── scripts/
│   └── ingest.py                   # Document ingestion to Supabase (run once)
├── static/
│   ├── icon-192.png                # PWA icon (192x192)
│   ├── icon-512.png                # PWA icon (512x512)
│   └── manifest.json               # PWA manifest
├── supabase/
│   └── migrations/                 # SQL migrations
├── tests/                          # 56 tests covering all core modules and app utils
├── .github/
│   └── workflows/
│       ├── tests.yml               # Run tests on every push to master
│       └── keep_alive.yml          # Ping app every 6 hours to prevent sleep
├── .env.example
├── .streamlit/
│   └── config.toml                 # Light theme with coffee palette
└── requirements.txt
```

## Tech Stack

| Layer | Technology | Detail |
|---|---|---|
| Frontend | Streamlit | Web + mobile-first UI, installable as PWA |
| LLM | Groq — Llama 3.3 70B | Response generation (free) |
| Embeddings | Google Gemini Embedding 001 | Document vectorization (free) |
| Vector DB | Supabase + pgvector | Semantic search |
| Database | Supabase (PostgreSQL) | Cafes, recipes, calibrations, messages and query logs |
| Auth | Supabase Auth | Barista login with cafe scoping |
| Session | streamlit-local-storage | Persistent session across browser closes |
| Deploy | Streamlit Cloud | Free hosting |
| CI | GitHub Actions | Automated tests + keep alive |

## Multi-cafe Model

Each user belongs to a café (`cafe_id` stored in Supabase Auth user metadata). Data is scoped by café:

- **Recipes:** public recipes are visible only to users of the same café
- **Calibrations:** visible only within the same café
- **RAG:** related recipes shown in chat are filtered by the user's café

## RAG Flow

```
User writes question
        ↓
consultant_agent detects intent
(recipe / troubleshoot / origin / sensory / general)
        ↓
document_manager searches relevant chunks (vector search)
        ↓
Groq generates response with technical context
        ↓
recipe_manager searches public RAG recipes filtered by cafe_id
        ↓
Response + sources + related recipes (expanders) shown in chat
        ↓
Messages saved to Supabase for persistence across sessions
        ↓
Query logged in query_logs
```

## Database Schema

**`cafes`** — registered cafés
```sql
id uuid primary key, name text, city text, created_at timestamptz
```

**`documents`** — knowledge base chunks with embeddings
```sql
id bigserial primary key, content text, metadata jsonb, embedding vector(768)
```

**`recipes`** — café recipes with visibility model
```sql
id, cafe_name, name, method, coffee_bean
dose_g, water_g, ratio, water_temp_c, brew_time_seconds, yield_g
grind_notes, flavor_notes, tips
created_by, cafe_id, is_public, made_public_by, use_in_rag, created_at
```

Recipe states:
- `is_public = false` → private, only visible to the creator
- `is_public = true` → public, visible to all users of the same café
- `use_in_rag = true` → appears as a related recipe in chat responses

**`calibrations`** — daily calibration notes (all fields optional)
```sql
id, recorded_at, shift_moment, room_temp_c, humidity_pct
coffee_name, roaster_name, roast_date, days_since_roast
varietal, origin, altitude_masl, process
grinder_name, grinder_setting, hopper_level, machine_name, group_temp_c
dose_g, yield_g, brew_time_seconds, ratio, tds
extraction_balance, approved, acidity, sweetness, bitterness
flavor_notes, adjustment_vs_prev, free_notes, created_by, cafe_id
```

**`messages`** — persistent chat history per user
```sql
id uuid primary key, user_email text, cafe_id uuid
role text, content text, sources text[], related_recipes jsonb
created_at timestamptz
```

**`query_logs`** — query log per user
```sql
id, created_at, user_email, query, intents, chunks_found, had_own_recipes
```

---

## Setup

### 1. Clone and create environment

```bash
git clone https://github.com/luc45hn/barista-rag
cd barista-rag
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Create Supabase project

1. Create a new project at [supabase.com](https://supabase.com)
2. In **Project Settings → API** copy:
   - Project URL → `SUPABASE_URL`
   - Publishable key → `SUPABASE_KEY`
   - Secret key → `SUPABASE_SERVICE_KEY`

### 3. Configure environment variables

```bash
cp .env.example .env
```

Fill in `.env`:
```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-publishable-key
SUPABASE_SERVICE_KEY=your-service-role-key
GOOGLE_API_KEY=your-google-ai-studio-key
GROQ_API_KEY=your-groq-key
```

### 4. Run Supabase migrations

In the Supabase **SQL Editor**, run this full script:

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

### 5. Create cafés

```sql
insert into cafes (name, city) values ('Café Name', 'City') returning id, name;
```

### 6. Create users in Supabase

In **Authentication → Users → Add user → Create new user**.

### 7. Assign users to cafés

```sql
update auth.users
set raw_user_meta_data = jsonb_set(coalesce(raw_user_meta_data, '{}'), '{cafe_id}', '"your-cafe-uuid"')
where email = 'barista@example.com';
```

### 8. Ingest documents

```bash
python scripts/ingest.py
```

### 9. Run locally

```bash
streamlit run app.py
```

---

## Deploy on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Connect the GitHub repo — main file: `app.py`
3. In **Advanced settings → Secrets** add all variables from `.env`

### GitHub Actions secrets

In **GitHub → Settings → Secrets and variables → Actions**, add the same 5 variables. This enables automated tests on every push.

---

## PWA — Install on mobile

Users can install the app on their home screen:

- **Android:** browser menu → "Add to home screen"
- **iPhone:** share button → "Add to Home Screen"

Once installed, the app opens without browser bars, just like a native app. Sessions persist across closes thanks to `streamlit-local-storage`.

---

## Knowledge Base

| File | Content |
|---|---|
| `01_sca_brewing_water_standards.md` | Golden Cup Standard, SCA/SCAE water parameters |
| `02_sca_cva_cupping_protocol.md` | CVA 2024 system, cupping protocol |
| `03_wcr_sensory_lexicon.md` | 110 coffee sensory attributes |
| `04_espresso_fundamentos.md` | Espresso parameters, dialing in, defects, milk |
| `05_origenes_cafe.md` | Flavor profiles by origin, processes |
| `07_metodos_pourover.md` | V60 (3 recipes), Chemex, Kalita Wave |
| `08_metodos_inmersion.md` | AeroPress (4 recipes), French Press, Cold Brew |
| `09_ciencia_extraccion.md` | TDS, extraction, grind size chart |
| `10_james_hoffmann_tecnicas.md` | Ultimate V60, Ultimate AeroPress, Shakerato |
| `11_barista_hustle_scott_rao.md` | 80:20 method, high-extraction espresso |

---

## Tests

```bash
pytest tests/ -v
```

56 tests covering config, document manager, recipe manager, consultant agent and app utils.

---

## CI/CD

- **tests.yml** — runs `pytest tests/ -v` on every push to `master`
- **keep_alive.yml** — pings the app every 6 hours to prevent Streamlit Cloud sleep. Can also be triggered manually from GitHub Actions.

---

## Free Tier Limits

| Service | Free limit |
|---|---|
| Groq (Llama 3.3 70B) | ~1,700 requests/day |
| Google Gemini Embedding | 1,500 requests/day |
| Supabase | 500 MB database, 2 GB bandwidth |
| Streamlit Cloud | 1 app, sleeps after ~12h inactivity (kept alive by GitHub Actions) |
| GitHub Actions | 2,000 minutes/month |
