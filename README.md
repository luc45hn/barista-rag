# ☕ Barista IA

Intelligent assistant for baristas in training. Combines a RAG (Retrieval-Augmented Generation) with technical coffee knowledge from specialized sources (SCA, James Hoffmann, WCR, Barista Hustle, Scott Rao) with the café's own recipes, calibration notes and custom documents.

> 📖 [Versión en español](README.es.md)

---

## Architecture

```
barista-rag/
├── app.py                          # Streamlit UI — chat, recipes, calibrations, documents
├── core/
│   ├── consultant_agent.py         # RAG agent — intent detection, hybrid search, generation
│   ├── document_manager.py         # Vector search + hybrid search by intent
│   ├── document_ingestor.py        # User document upload, ingestion and approval
│   ├── recipe_manager.py           # Recipe CRUD in Supabase
│   ├── config.py                   # Environment variables and configuration
│   ├── logger.py                   # Standard logger
│   └── theme.py                    # Color palette and UI constants
├── knowledge_base/                 # Markdown documents that form the base RAG
│   ├── 01-11_...                   # SCA, WCR, Hoffmann, Scott Rao, origins, methods
│   └── 12_equipamiento_maquinas_espresso.md  # Equipment guide: machines, boilers, variables
├── scripts/
│   └── ingest.py                   # Base document ingestion (run once, preserves user docs)
├── static/                         # PWA icons and manifest
├── tests/                          # 56 tests
├── .github/workflows/              # tests.yml + keep_alive.yml (Playwright)
└── requirements.txt
```

## Tech Stack

| Layer | Technology | Detail |
|---|---|---|
| Frontend | Streamlit | Web + mobile-first UI, installable as PWA |
| LLM | Gemini 2.5 Flash → Groq fallback | Per-café API key, automatic fallback on quota/error |
| Embeddings | Google Gemini Embedding 001 | Separate key (`GOOGLE_EMBEDDING_KEY`) to avoid quota conflicts |
| Vector DB | Supabase + pgvector | Semantic search + hybrid search by intent |
| Database | Supabase (PostgreSQL) | Cafes, recipes, calibrations, messages, documents, logs |
| Storage | Supabase Storage | User-uploaded PDF and Markdown files |
| Auth | Supabase Auth | Barista login with cafe scoping |
| Session | streamlit-local-storage | Persistent session across browser closes |
| Deploy | Streamlit Cloud | Free hosting |
| CI | GitHub Actions | Automated tests + Playwright keep alive every 2h |

## Multi-cafe Model

Each user belongs to a café (`cafe_id` in Supabase Auth metadata). Each café can have its own Gemini API key (`gemini_api_key` in `cafes` table) for the LLM. Data is scoped by café:

- **Recipes, calibrations, documents, messages** — visible only within the same café
- **RAG** — knowledge base chunks + approved user documents filtered by café
- **LLM** — uses café's Gemini key if available, falls back to Groq automatically

## RAG Flow

```
User writes question
        ↓
consultant_agent detects intent
(recipe / troubleshoot / origin / sensory / general)
        ↓
document_manager: vector search (top 4 chunks)
+ hybrid search: if intent=origin → force 1 chunk from origins doc
        ↓
Gemini 2.5 Flash generates response (falls back to Groq on 429/503)
        ↓
recipe_manager: search public RAG recipes by café
        ↓
Response + sources + related recipe expanders shown in chat
        ↓
Messages saved to Supabase → persistent chat history
        ↓
Query logged in query_logs
```

## Database Schema

**`cafes`**
```sql
id uuid, name text, city text, gemini_api_key text, created_at timestamptz
```

**`documents`** — global knowledge base + user-uploaded chunks
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

**`calibrations`** — all fields optional
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

## Setup

### 1. Clone and create environment

```bash
git clone https://github.com/luc45hn/barista-rag
cd barista-rag
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Create Supabase project

Copy Project URL, Publishable key and Secret key from **Project Settings → API**.

### 3. Configure environment variables

```bash
cp .env.example .env
```

```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-publishable-key
SUPABASE_SERVICE_KEY=your-service-role-key
GOOGLE_API_KEY=your-gemini-flash-key        # LLM (per-café, or fallback)
GOOGLE_EMBEDDING_KEY=your-embedding-key     # Embeddings only (separate quota)
GROQ_API_KEY=your-groq-key                  # Fallback LLM (always free)
```

> **Note:** `GOOGLE_API_KEY` and `GOOGLE_EMBEDDING_KEY` can be the same key or different keys. Using separate keys doubles the free embedding quota.

### 4. Create Storage bucket

In Supabase **Storage**, create a private bucket named `user-documents`.

### 5. Run Supabase migrations

Full SQL script in `README.es.md` (Setup section, step 5). Key additions vs basic setup:

```sql
-- Add gemini_api_key to cafes
alter table cafes add column if not exists gemini_api_key text;

-- match_documents with cafe filtering and approved check
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
```

### 6. Create cafés and assign users

```sql
insert into cafes (name, city) values ('Café Name', 'City') returning id;

update auth.users
set raw_user_meta_data = jsonb_set(coalesce(raw_user_meta_data, '{}'), '{cafe_id}', '"uuid"')
where email = 'barista@example.com';
```

### 7. Set Gemini API key per café (optional)

```sql
update cafes set gemini_api_key = 'your-key' where id = 'cafe-uuid';
```

Without a key, the café uses Groq/Llama automatically.

### 8. Ingest base documents

```bash
python scripts/ingest.py
```

Safe to re-run — preserves user-uploaded document chunks.

### 9. Run locally

```bash
streamlit run app.py
```

---

## Deploy on Streamlit Cloud

1. Connect repo at [share.streamlit.io](https://share.streamlit.io) → main file: `app.py`
2. Add all 6 secrets in **Advanced settings → Secrets**
3. Add same secrets in **GitHub → Settings → Secrets → Actions**

---

## PWA

- **Android:** browser menu → "Add to home screen"
- **iPhone:** share → "Add to Home Screen"

Session persists across closes via `streamlit-local-storage`.

---

## Knowledge Base

| File | Content |
|---|---|
| `01_sca_brewing_water_standards.md` | Golden Cup, SCA water parameters |
| `02_sca_cva_cupping_protocol.md` | CVA 2024, cupping protocol |
| `03_wcr_sensory_lexicon.md` | 110 sensory attributes |
| `04_espresso_fundamentos.md` | Espresso parameters, dialing in, defects |
| `05_origenes_cafe.md` | Flavor profiles by origin and process |
| `07_metodos_pourover.md` | V60, Chemex, Kalita Wave |
| `08_metodos_inmersion.md` | AeroPress, French Press, Cold Brew |
| `09_ciencia_extraccion.md` | TDS, extraction, grind chart |
| `10_james_hoffmann_tecnicas.md` | Ultimate V60, AeroPress, Shakerato |
| `11_barista_hustle_scott_rao.md` | 80:20 method, high-extraction espresso |
| `12_equipamiento_maquinas_espresso.md` | Machines (Simonelli, La Marzocco, Victoria Arduino, Rancilio), boiler types, adjustable variables per machine |

---

## Tests

```bash
pytest tests/ -v  # 56 tests
```

---

## CI/CD

- **tests.yml** — runs on every push to `master`
- **keep_alive.yml** — Playwright script every 2h, clicks "wake up" button if app is sleeping

---

## Free Tier Limits

| Service | Free limit |
|---|---|
| Groq (Llama 3.3 70B) | ~1,700 req/day |
| Gemini 2.5 Flash | 20 req/day (per key) |
| Gemini Embedding 001 | 1,500 req/day (per key) |
| Supabase | 500 MB DB, 1 GB storage, 2 GB bandwidth |
| Streamlit Cloud | 1 app, ~12h sleep (kept alive by GitHub Actions) |
| GitHub Actions | 2,000 min/month |
