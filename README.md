# PromptAdsCraft AI — Intelligent Marketing Content Studio

> **Craft smarter prompts. Create better ads.**

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://promptadscraft-302005.streamlit.app)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-78%20passed-brightgreen.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

PromptAdsCraft AI is a complete, production-ready marketing studio designed for digital marketers, founders, agency teams, and content creators. It transforms a product brief into an end-to-end, multi-format advertising campaign package using structured prompt synthesis, platform-adapted creative angles, and transparent heuristic quality audits.

🌐 **Live Application:** [https://promptadscraft-302005.streamlit.app](https://promptadscraft-302005.streamlit.app)

---

## ⚡ Core Creative Engine

PromptAdsCraft AI is powered by a custom **Multi-Variable Prompt Synthesis Engine** written in pure Python:

$$\text{Copy} = f(\text{Business/Brand}, \text{Product}, \text{Target Audience}, \text{USPs}, \text{Tone}, \text{Platform}, \text{Duration}, \text{Context})$$

### Why This Engine?
- **💰 Zero Cost & No API Keys Required:** Runs out of the box with zero third-party dependencies, rate limits, or monthly API subscription fees.
- **⚡ Sub-Second Instant Generation:** Generates comprehensive UGC scripts, hooks, CTAs, and quality audits in under 1 second without network latency.
- **🚀 100% Reliable Deployment:** Seamlessly runs on Streamlit Community Cloud with zero configuration.
- **🛡️ Deterministic & Compliant:** Strictly enforces verified user inputs and guards against unverified health claims, fake urgency, and fabricated testimonials.

---

## 🎯 Key Capabilities

- **📋 Strategic Campaign Briefs:** Synthesizes product features and customer insights into a clear creative direction while actively flagging unverified claims.
- **🎣 Distinct Advertising Hooks (3–10 Variations):** Produces psychologically varied opening hooks (Curiosity/Open Loop, Pain Point, Bold Statement, Demonstration-Led, Contrast, Empathy, Simplicity).
- **🎬 Scene-by-Scene UGC Video Scripts:** Complete with timestamps, camera visual directions, spoken creator dialogue, on-screen text overlays, shot types, and transitions tailored for 15s, 30s, or 60s formats.
- **📣 Objective-Aligned Calls to Action (CTAs):** Categorized by funnel stage (Engagement, Website Visit, Product Discovery, Purchase Intent) with recommended primary CTA matching campaign goals.
- **📱 Social Captions & Niche Hashtags:** Punchy concise and extended captions paired with targeted, non-spammy discoverability hashtags.
- **🔄 Cross-Platform Adaptations:** Adapts format, pacing, structure, and best-practice guidelines specifically for **Instagram Reels**, **YouTube Shorts**, and **Paid Social Ads**.
- **💡 6 Alternative Creative Angles:** Generates distinct marketing angles (Problem & Solution, Product Demo, Educational Breakdown, Lifestyle Integration, Feature & Benefit, and Authentic Creator Monologue).
- **✏️ In-Line Studio Editor & Section Regeneration:** Refine any copy directly and regenerate individual sections on demand without re-running the entire campaign.
- **🎨 Visual Creative Gallery:** Studio-grade visual showcase filterable by asset category.
- **🔍 Content Quality & Compliance Audit:** Transparent 7-factor heuristic scoring (Audience Relevance, Message Clarity, Hook Distinctiveness, CTA Relevance, Platform Suitability, Claim Verification, and Testimonial Language Safety).
- **📥 Multi-Format Export:** One-click downloads as formatted **Markdown (.md)**, **Plain Text (.txt)**, or structured **JSON (.json)**.
- **💾 Local Campaign History:** Auto-saves campaigns locally with search, status filtering, and full library export/management.
- **🔬 Interactive Prompt Inspector:** Inspect system roles, context injection blocks, output schemas, and sanitized prompt previews.

---

## 🏗️ Architecture & Data Flow

```
                      [ User Input / Product Brief ]
                                    │
                                    ▼
                         [ src/validators.py ]
                         (Pydantic v2 Validation)
                                    │
                                    ▼
                       [ src/synthesis_engine.py ]
               (Multi-Variable Pure Python Synthesis Engine)
                 Brief ➔ Hooks ➔ UGC Script ➔ CTAs ➔
                 Captions ➔ Platform Adaptation ➔ Angles
                                    │
                                    ▼
                        [ src/quality_checker.py ]
                     (7-Factor Heuristic Compliance Audit)
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

## 🛠️ Technology Stack

- **Frontend & Web UI:** [Streamlit](https://streamlit.io/)
- **Core Synthesis Engine:** Pure Python (Zero external API dependencies)
- **Data Validation & Typing:** [Pydantic v2](https://docs.pydantic.dev/)
- **Automated Testing:** [pytest](https://docs.pytest.org/) (78 automated tests)
- **Local Persistence:** JSON storage (`campaigns.json`)
- **Deployment Platform:** Streamlit Community Cloud

---

## 🚀 Installation & Local Setup

Follow these steps to run the application locally on your machine.

### Prerequisites
- Python 3.10, 3.11, or 3.12 installed ([Download Python](https://www.python.org/downloads/))
- Git installed on your system ([Download Git](https://git-scm.com/))

### 1. Clone the Repository
```bash
git clone https://github.com/sangeetha302005/PromptAdsCraft.git
cd PromptAdsCraft
```

### 2. Create a Virtual Environment
- **macOS / Linux:**
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```
- **Windows (PowerShell):**
  ```powershell
  python -m venv venv
  .\venv\Scripts\Activate.ps1
  ```
  *(If script execution is restricted in PowerShell, run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`)*
- **Windows (Command Prompt):**
  ```cmd
  python -m venv venv
  venv\Scripts\activate.bat
  ```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Application
```bash
streamlit run app.py
```
Your web browser will automatically open to `http://localhost:8501`.

> 💡 **No API keys or configuration needed!** PromptAdsCraft AI runs out of the box with 100% of features immediately active.

---

## 🧪 Running the Test Suite

The codebase includes comprehensive unit and integration tests covering data validation, variable substitution, heuristic audits, persistence, and output synthesis.

To run the automated tests:
```bash
pytest tests/ -v
```

All **78 tests** execute locally in under 1 second without consuming any network bandwidth or external API calls.

---

## 📂 Project Structure

```
PromptAdsCraft/
├── app.py                      # Main Streamlit web application & routing
├── config.py                   # Centralized configuration & defaults
├── requirements.txt            # Python dependencies
├── .env.example                # Example environment configuration (optional)
├── .gitignore                  # Git exclusions
├── README.md                   # Project documentation
├── prompts/                    # Modular prompt templates
│   ├── campaign_brief.txt      # Brief generator template
│   ├── hooks.txt               # Ad hooks template
│   ├── ugc_script.txt          # Scene-by-scene UGC script template
│   ├── cta.txt                 # Categorized CTA template
│   ├── captions.txt            # Captions and hashtags template
│   ├── platform_adaptation.txt # Multi-platform adaptation template
│   └── quality_review.txt      # Quality review audit template
├── src/                        # Core application modules
│   ├── __init__.py
│   ├── synthesis_engine.py     # Pure-Python Multi-Variable Prompt Synthesis Engine
│   ├── content_generator.py    # Campaign generation pipeline orchestrator
│   ├── prompt_builder.py       # SafeDict variable substitution & prompt previews
│   ├── validators.py           # Pydantic input validation models
│   ├── quality_checker.py      # Heuristic compliance and quality audit engine
│   ├── storage.py              # Local JSON campaign history manager
│   ├── exporters.py            # Markdown, plain text, and JSON exporters
│   └── ai_service.py           # Neural AI provider wrapper
├── examples/                   # Reference campaign briefs
│   ├── skincare_campaign.json  # E-commerce moisturizer campaign
│   ├── local_cafe_campaign.json# Local coffee shop autumn promotion
│   └── saas_campaign.json      # SaaS productivity app campaign
└── tests/                      # Automated test suite
    ├── test_validators.py      # Form data validation tests
    ├── test_prompt_builder.py  # Template substitution tests
    ├── test_quality_checker.py # Compliance & heuristic audit tests
    ├── test_storage.py         # Persistence & history tests
    ├── test_exporters.py       # File serialization tests
    └── test_ai_service_and_generator.py # Synthesis & pipeline tests
```

---

## 🛡️ Responsible Marketing Principles

PromptAdsCraft AI adheres to modern consumer protection and advertising transparency standards:
- **No Fabricated Customer Reviews:** UGC scripts are explicitly designated as creative performance directions for creators, never as real customer testimonials.
- **Deceptive Urgency & Scarcity Shield:** The quality engine flags artificial pressure phrases (e.g., *"only 2 left"*, *"expires in 5 minutes"*) unless verified by the business.
- **Transparent Heuristic Quality:** Scores evaluate structure, clarity, and safety — they are never presented as guaranteed predictions of advertising reach or conversion rates.
- **Human-in-the-Loop:** Permanent reminders advise brands to review and legally verify claims before publishing.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
