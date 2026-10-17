# PromptAdsCraft AI — Intelligent Marketing Content Generator

> **Tagline:** Craft smarter prompts. Create better ads.

PromptAdsCraft AI is a complete, production-ready, AI-powered web application designed for small businesses, digital marketers, agency teams, and content creators. It transforms a product brief into an end-to-end, multi-format advertising campaign package using structured prompt engineering, responsible marketing guardrails, and automated heuristic quality checks.

---

## Table of Contents
1. [Real-World Problem](#real-world-problem)
2. [Main Objectives & Features](#main-objectives--features)
3. [Architecture and Data Flow](#architecture-and-data-flow)
4. [Technology Stack](#technology-stack)
5. [Folder Structure](#folder-structure)
6. [Installation & Setup (Windows)](#installation--setup-windows)
7. [Running the Application](#running-the-application)
8. [Demo Mode vs. Live AI Mode](#demo-mode-vs-live-ai-mode)
9. [Prompt Engineering System & Inspector](#prompt-engineering-system--inspector)
10. [Running the Automated Tests](#running-the-automated-tests)
11. [Example Scenarios](#example-scenarios)
12. [Responsible Marketing & Limitations](#responsible-marketing--limitations)
13. [Future Enhancements](#future-enhancements)

---

## 1. Real-World Problem

Digital marketers and entrepreneurs often struggle to consistently produce scroll-stopping advertising creative. High-performing digital campaigns require:
- Multiple diverse opening hooks to combat ad fatigue.
- Relatable User-Generated Content (UGC) scripts tailored to short-form video algorithms.
- Objective-aligned Calls to Action (CTAs).
- Platform-adapted creative variations (Instagram Reels vs. YouTube Shorts vs. Paid Social Ads).
- Persuasive copy that remains truthful, compliant with regulatory bodies (FTC, ASA), and free from hallucinated guarantees or fake customer testimonials.

Generic AI prompts usually yield repetitive, overly generic, or unverified claims. **PromptAdsCraft AI** solves this by establishing modular prompt templates, strict user-supplied fact injection, and a transparent heuristic quality review system.

---

## 2. Main Objectives & Features

- **Campaign Brief Generation:** Distills user-supplied features and audience insights into a clear creative direction and flags unverified claims.
- **Distinct Advertising Hooks (3–10 variations):** Generates genuinely varied hooks across 8+ psychological angles (Curiosity/Open Loop, Pain Point, Bold Statement, Demonstration-Led, Contrast, etc.).
- **Scene-by-Scene UGC Video Scripts:** Complete with timestamps, visual directions, spoken dialogue, on-screen text overlays, shot types, and seamless transitions.
- **Categorized Calls to Action (CTAs):** Divided into Engagement, Website Visit, Product Discovery, and Purchase Intent, with a recommended primary CTA based on marketing objective.
- **Feed Captions & Relevant Hashtags:** Concise and extended captions paired with non-spammy niche hashtags.
- **Platform Adaptation:** Tailors creative format, pacing, copy, and best-practice guidance specifically for **Instagram Reels**, **YouTube Shorts**, and **Paid Social Ads**.
- **Alternative Creative Angles:** Provides 6 divergent conceptual approaches (Problem & Solution, Product Demo, Educational, Lifestyle, Feature & Benefit, Honest Review).
- **In-Line Editing & Section Regeneration:** Edit any output field directly and regenerate individual sections (Hooks, Script, CTAs, Captions) on demand without re-running the entire campaign.
- **Creative Gallery:** Filterable visual showcase inspired by modern creative studios across Hooks, Scripts, CTAs & Captions, and Platform Creatives.
- **Heuristic Quality Review:** 7-factor transparent heuristic score (Audience Relevance, Message Clarity, Hook Distinctiveness, CTA Relevance, Platform Suitability, Claim Verification, and Testimonial Language Safety) with actionable warnings.
- **Multi-Format Export & History:** Download in-memory formatted **Markdown (.md)**, **Plain Text (.txt)**, or **JSON (.json)**, and manage campaigns in the local library with search and status filtering.
- **Interactive Prompt Inspector:** View system roles, task designs, schemas, and a sanitized preview of assembled user prompts with substituted variables.
- **Settings & Safe Connection Test:** Configure API key in session, test connection with lightweight `models.list()` without token charge, and switch models dynamically.

---

## 3. Architecture and Data Flow

```
                      [ User Input / Form Brief ]
                                   │
                                   ▼
                       [ src/validators.py ]
                        (Pydantic Validation)
                                   │
                    ┌──────────────┴──────────────┐
                    ▼                             ▼
        [ API Key Configured? ]        [ No Key Configured ]
                    │                             │
                    ▼                             ▼
         [ Live AI Service ]               [ Demo Mode ]
          (OpenAI API SDK)         (Deterministic Realistic Data)
                    │                             │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                     [ src/prompt_builder.py ]
                     (SafeDict Template Injection)
                                   │
                                   ▼
                    [ src/content_generator.py ]
               (Brief ➔ Hooks ➔ Script ➔ CTAs ➔
                Captions ➔ Platforms ➔ Angles)
                                   │
                                   ▼
                    [ src/quality_checker.py ]
                  (Heuristic Multi-Factor Audit)
                                   │
                                   ▼
                       [ Streamlit UI (app.py) ]
                                   │
                    ┌──────────────┴──────────────┐
                    ▼                             ▼
        [ Markdown / JSON Export ]     [ Local Storage JSON ]
          (src/exporters.py)             (src/storage.py)
```

---

## 4. Technology Stack

- **Language:** Python 3.10+
- **Frontend / Web Framework:** Streamlit
- **AI Integration:** OpenAI Python SDK (`openai>=1.3.0`)
- **Validation:** Pydantic v2
- **Testing:** pytest & pytest-mock
- **Configuration:** python-dotenv & Streamlit secrets
- **Persistence:** Local JSON (`campaigns.json`)

---

## 5. Folder Structure

```
PromptAdsCraft/
├── app.py                      # Main Streamlit web application & routing
├── config.py                   # Centralized configuration & environment loader
├── requirements.txt            # Python dependencies
├── .env.example                # Example environment variable file
├── .gitignore                  # Git exclusions (credentials, cache, storage)
├── README.md                   # Comprehensive project documentation
├── prompts/                    # Reusable modular prompt templates
│   ├── campaign_brief.txt      # Brief generator template
│   ├── hooks.txt               # Ad hooks template
│   ├── ugc_script.txt          # Scene-by-scene UGC script template
│   ├── cta.txt                 # Categorized CTA template
│   ├── captions.txt            # Captions and hashtags template
│   ├── platform_adaptation.txt # Multi-platform adaptation template
│   └── quality_review.txt      # Independent quality review template
├── src/                        # Core application modules
│   ├── __init__.py
│   ├── ai_service.py           # OpenAI API client, error handling & JSON parser
│   ├── prompt_builder.py       # SafeDict variable substitution & prompt previews
│   ├── validators.py           # Pydantic form data validation schemas
│   ├── content_generator.py    # Generation orchestrator & Demo Mode provider
│   ├── quality_checker.py      # Heuristic compliance and quality rules
│   ├── storage.py              # Local JSON campaign history manager
│   └── exporters.py            # Markdown and JSON export generators
├── examples/                   # Illustrative scenario briefs
│   ├── skincare_campaign.json  # Skincare moisturizer example
│   ├── local_cafe_campaign.json# Seasonal cafe coffee example
│   └── saas_campaign.json      # SaaS productivity app example
└── tests/                      # Automated test suite
    ├── __init__.py
    ├── test_validators.py      # Input validation & edge cases
    ├── test_prompt_builder.py  # Variable substitution & template integrity
    ├── test_quality_checker.py # Heuristic rules & regex safety tests
    ├── test_exporters.py       # Markdown & JSON serialization tests
    ├── test_storage.py         # Persistence, recovery, and corruption handling
    └── test_ai_service_and_generator.py # Mocked AI calls & Demo Mode logic
```

---

## 6. Installation & Setup (Windows)

### Prerequisites
- Python 3.10, 3.11, or 3.12 installed on your system.
- PowerShell or Windows Command Prompt.

### Step 1: Open PowerShell in Project Directory
```powershell
cd "C:\Users\Sangeetha Suresh\Downloads\PromptAdsCraft"
```

### Step 2: Create a Virtual Environment
```powershell
python -m venv venv
```

### Step 3: Activate the Virtual Environment
```powershell
.\venv\Scripts\Activate.ps1
```
*(If script execution is disabled on your system, run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`)*

### Step 4: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 5: Configure Environment Variables
Copy `.env.example` to `.env`:
```powershell
Copy-Item .env.example .env
```
Open `.env` in any text editor and optionally set your OpenAI API key:
```env
OPENAI_API_KEY=sk-...your-actual-key...
OPENAI_MODEL=gpt-4o-mini
MAX_TOKENS=2000
REQUEST_TIMEOUT=30
```
> **Note:** If no `OPENAI_API_KEY` is provided, PromptAdsCraft AI will automatically run in **Demo Mode**.

---

## 7. Running the Application

Launch the Streamlit app with:
```powershell
streamlit run app.py
```
Your default browser will automatically open to `http://localhost:8501`.

---

## 8. Demo Mode vs. Live AI Mode

| Feature | Demo Mode (No API Key) | Live AI Mode (Valid OpenAI Key) |
|---|---|---|
| **Indicator** | ⚠️ Yellow banner: "Demo Mode Active" | ✅ Green badge: "AI Connected" |
| **Output Type** | Realistic, deterministic sample content | Dynamic, customized generative content |
| **Labeling** | Every item is clearly labeled `[DEMO]` | Authentic generated copy based on user inputs |
| **Cost** | 100% Free, offline capable | Standard OpenAI API token pricing |
| **Full Workflow** | Full generation, UI, audit, exports & history | Full generation, UI, audit, exports & history |

---

## 9. Prompt Engineering System & Inspector

Every generation step uses a versioned template in `prompts/`. Prompts are engineered according to industry best practices:
1. **System Persona:** Gives the model a specific role (e.g., senior direct-response copywriter or compliance auditor).
2. **Strict Context Isolation:** Only user-provided inputs are injected; the model is explicitly forbidden from inventing clinical or statistical claims.
3. **Structured JSON Output:** Responses are constrained to clean JSON schemas for reliable parsing.
4. **Sanitized Preview:** The in-app **Prompt Inspector** lets users examine assembled prompts without exposing internal system guidelines or API secrets.

---

## 10. Running the Automated Tests

The project includes unit and integration tests covering form validation, template substitution, heuristic audits, persistence, mocked AI responses, and Demo Mode.

Run tests using pytest:
```powershell
pytest -v
```

To run with coverage (if `coverage` is installed):
```powershell
pytest --cov=src tests/
```

All tests mock API interactions so **no paid OpenAI credits or real API keys are consumed during testing**.

---

## 11. Example Scenarios

Three pre-configured JSON files in `examples/` demonstrate how different businesses can use the tool:
- **`examples/skincare_campaign.json`**: Everyday moisturizer focusing on routine demonstration while strictly avoiding clinical or medical claims.
- **`examples/local_cafe_campaign.json`**: Seasonal Autumn Spice Latte focusing on warm atmosphere, barista visuals, and local awareness.
- **`examples/saas_campaign.json`**: FocusFlow productivity tool focusing on feature demonstration and free app downloads without fake user statistics.

---

## 12. Responsible Marketing & Limitations

PromptAdsCraft AI is built with responsible marketing principles:
- **No Fabricated Testimonials:** UGC scripts are explicitly marked as creative performance concepts, not genuine customer testimonials.
- **No False Scarcity:** Urgency claims like "only 3 left" or "expires in 10 minutes" are flagged unless verified by the user.
- **Heuristic Quality Checks:** The quality scores are transparent heuristic estimates of message clarity and compliance, **never guaranteed predictions of ad conversions or viral reach**.
- **Human in the Loop:** A permanent disclaimer reminds users to review and legally verify claims before publishing.

---

## 13. Future Enhancements

- Multilingual creative generation (Spanish, French, German, Japanese).
- Direct integration with Meta Ads Manager and TikTok Ads API for automated drafting.
- Audio voiceover generation (ElevenLabs or OpenAI TTS) directly linked to script timestamps.
- Video storyboard thumbnail generation using image generation models.
