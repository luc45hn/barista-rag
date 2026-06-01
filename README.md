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
├── supabase/
│   └── migrations/                 # SQL migrations
├── tests/                          # 38 tests covering all core modules
├── .env.example
├── .streamlit/
│   └── config.toml                 # Light theme with coffee palette
└── requirements.txt
```

## Tech Stack

| Layer | Technology | Detail |
|---|---|---|
| Frontend | Streamlit | Web + mobile-first UI |
| LLM | Groq — Llama 3.3 70B | Response generation (free) |
| Embeddings | Google Gemini Embedding 001 | Document vectorization (free) |
| Vector DB | Supabase + pgvector | Semantic search |
| Database | Supabase (PostgreSQL) | Recipes, calibrations and query logs |
| Auth | Supabase Auth | Barista login |
| Deploy | Streamlit Cloud | Free hosting |

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
recipe_manager searches public recipes marked as RAG
↓
Response + sources + related recipes (expanders) shown in chat
↓
Query logged in query_logs
```

## Database Schema

**`documents`** — knowledge base chunks with embeddings
```sql
id bigserial primary key
content text
metadata jsonb        -- { source: "04_espresso_fundamentos.md", chunk_index: 0 }
embedding vector(768) -- gemini-embedding-001 with output_dimensionality=768
```

**`recipes`** — café recipes with visibility model
```sql
id, cafe_name, name, method, coffee_bean
dose_g, water_g, ratio, water_temp_c, brew_time_seconds, yield_g
grind_notes, flavor_notes, tips
created_by, is_public, made_public_by, use_in_rag, created_at
```

Recipe states:
- `is_public = false` → private, only visible to the creator
- `is_public = true` → public, visible to all users
- `use_in_rag = true` → appears as a related recipe in chat responses (requires `is_public = true`)

**`calibrations`** — daily calibration notes (all fields optional)

**`query_logs`** — query log per user

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

**Google API Key:** [aistudio.google.com](https://aistudio.google.com) → Get API key → Create API key

**Groq API Key:** [console.groq.com](https://console.groq.com) → API Keys → Create key

### 4. Run Supabase migrations

In the Supabase **SQL Editor**, run the full migration script from `README.es.md` (Setup section, step 4).

### 5. Create users in Supabase

In **Authentication → Users → Add user → Create new user** create barista accounts with email and password.

### 6. Ingest documents

```bash
python scripts/ingest.py
```

Reads all Markdown files from `knowledge_base/`, splits them into chunks, generates embeddings with Gemini and uploads to Supabase. Takes ~3 minutes. Can be re-run to update the knowledge base.

### 7. Run locally

```bash
streamlit run app.py
```

---

## Deploy on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Connect the GitHub repo
3. Main file: `app.py`
4. In **Advanced settings → Secrets** add all variables from `.env`:

```toml
SUPABASE_URL = "https://..."
SUPABASE_KEY = "..."
SUPABASE_SERVICE_KEY = "..."
GOOGLE_API_KEY = "..."
GROQ_API_KEY = "..."
```

---

## Knowledge Base

| File | Content |
|---|---|
| `01_sca_brewing_water_standards.md` | Golden Cup Standard, SCA/SCAE water parameters, cupping, brewing methods |
| `02_sca_cva_cupping_protocol.md` | CVA 2024 system, cupping protocol, sensory glossary |
| `03_wcr_sensory_lexicon.md` | 110 coffee sensory attributes with descriptions and references |
| `04_espresso_fundamentos.md` | Espresso parameters, dialing in, defects, milk steaming, maintenance |
| `05_origenes_cafe.md` | Flavor profiles by origin, processes, selection guide |
| `07_metodos_pourover.md` | V60 (3 recipes), Chemex, Kalita Wave with troubleshooting |
| `08_metodos_inmersion.md` | AeroPress (4 recipes), French Press, Clever Dripper, Cold Brew |
| `09_ciencia_extraccion.md` | TDS, extraction, grind size chart, Brewing Control Chart |
| `10_james_hoffmann_tecnicas.md` | Ultimate V60, Ultimate AeroPress, Shakerato, Espresso Tonic |
| `11_barista_hustle_scott_rao.md` | 80:20 method, differential extraction, high-extraction espresso |

---

## Tests

```bash
pytest tests/ -v
```

38 tests covering config, document manager, recipe manager and the agent.

---

## Free Tier Limits

| Service | Free limit |
|---|---|
| Groq (Llama 3.3 70B) | ~1,700 requests/day |
| Google Gemini Embedding | 1,500 requests/day |
| Supabase | 500 MB database, 2 GB bandwidth |
| Streamlit Cloud | 1 app, always on |

For 2–3 baristas during a normal shift, these limits are more than sufficient.
