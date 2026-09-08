# Fact Knowledge Layer

A document intelligence system that extracts meaningful numerical and semantic facts from PDF documents, links each fact back to its source evidence, normalizes different representations, and identifies relationships between facts across the documents.

Built as part of the **Superjoin VIT 2026 Engineering Intern Hiring Assignment**.

---

## 🚀 Overview

Organizations often store important information across multiple reports and documents. The same business metric may appear in different formats, units, time periods, or levels of precision.

For example:

* One document may report revenue as **₹8,142 Cr**
* Another may report the same value as **₹81,415.38 million**

A simple text search would treat these as different values. This project extracts the underlying facts, normalizes their representations, and compares them to determine whether they:

* **CORROBORATE** — support the same fact
* **CONTRADICT** — contain materially different values for the same context
* **RECONCILE** — differ because of rounding, reporting precision, or contextual differences
* **UNCERTAIN** — cannot be compared reliably

Every extracted fact retains its source document, page number, and evidence text.

---

## ✨ Key Features

### 1. Multi-PDF Processing

The application accepts multiple PDF documents and processes them together.

The system is not dependent on a fixed number of documents and can be used with additional PDFs.

### 2. Fact Extraction

The system identifies meaningful numerical facts such as:

* Revenue
* Profit and loss
* EBITDA
* Margins
* Growth
* Shipment volumes
* Tonnage
* Customers
* Market share
* PIN codes
* Facilities
* Employees
* Countries
* Other numerical business metrics

Each fact contains structured information including:

```text
Subject
Predicate
Value
Unit
Time Context
Scope
Source Evidence
Confidence
```

### 3. Evidence Traceability

Every extracted fact is linked to:

* Source document
* Page number
* Original evidence text

This makes the system auditable instead of producing unsupported conclusions.

### 4. Value Normalization

Different numerical representations are converted into comparable forms.

Examples:

```text
₹8,142 Cr
₹81,415.38 million
```

can be normalized to the same underlying INR scale.

Similarly:

```text
374 thousand tonnes
373,854 tonnes
```

can be compared quantitatively.

### 5. Cross-Document Reasoning

Facts from different documents are compared and classified into relationships:

```text
CORROBORATES
CONTRADICTS
RECONCILES
UNCERTAIN
```

The system also provides a reason and confidence score for each relationship.

### 6. Source-Aware UI

The Streamlit interface provides:

* Document upload
* Document statistics
* Extracted facts
* Normalized values
* Evidence snippets
* Confidence scores
* Cross-document relationships
* Relationship reasoning

---

# 🏗️ Architecture

```text
                  ┌─────────────────────┐
                  │     PDF Documents   │
                  └──────────┬──────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │   PDF Extraction    │
                  │      PyMuPDF        │
                  └──────────┬──────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │  Relevant Page      │
                  │     Filtering       │
                  └──────────┬──────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │    Fact Extraction │
                  │  Local / LLM-ready │
                  └──────────┬──────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │     Normalization   │
                  │ Units + Predicates  │
                  └──────────┬──────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │ Fact Matching       │
                  │ Subject + Metric    │
                  │ + Time Context      │
                  └──────────┬──────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │    Relationship     │
                  │     Reasoning       │
                  └──────────┬──────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │    Streamlit UI     │
                  └─────────────────────┘
```

---

# 📂 Project Structure

```text
fact-knowledge-layer/
│
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── pdf_extractor.py
│   ├── fact_extractor.py
│   ├── normalizer.py
│   ├── matcher.py
│   ├── reasoning.py
│   └── pipeline.py
│
├── ui/
│   └── streamlit_app.py
│
├── data/
│   └── .gitkeep
│
├── tests/
│   └── test_normalizer.py
│
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
└── run.py
```

---

# 🧩 Component Responsibilities

## `pdf_extractor.py`

Responsible for extracting page-level text from PDFs using PyMuPDF.

Page-level extraction is important because the system needs to preserve the location of evidence.

---

## `fact_extractor.py`

Responsible for converting document text into structured facts.

The extractor produces facts containing numerical values, units, time information, scope, evidence, and confidence.

The implementation is designed so that an LLM-based extraction layer can be used when available, while a local extraction path can be used during development.

---

## `normalizer.py`

Responsible for converting different representations into a common form.

Examples include:

```text
million → 1,000,000
crore → 10,000,000
lakh → 100,000
thousand → 1,000
```

It also normalizes metric names such as different expressions of service revenue or shipment volume.

---

## `matcher.py`

Finds potentially comparable facts across documents.

The current matching stage considers:

* Subject
* Predicate
* Time context

Only candidate facts that appear comparable are sent to the reasoning layer.

---

## `reasoning.py`

Compares normalized values and determines the relationship between candidate facts.

The current relationship categories are:

```text
CORROBORATES
CONTRADICTS
RECONCILES
UNCERTAIN
```

A confidence score and explanation are generated for every relationship.

---

## `pipeline.py`

Coordinates the complete processing workflow:

```text
PDF
 ↓
Page extraction
 ↓
Relevant page filtering
 ↓
Fact extraction
 ↓
Normalization
 ↓
Candidate matching
 ↓
Relationship reasoning
```

---

## `streamlit_app.py`

Provides the user-facing interface.

Users can upload multiple PDFs and inspect:

* Overview statistics
* Extracted facts
* Evidence
* Relationships
* Source documents

---

# 🔍 Example Reasoning Cases

## Case 1 — Corroboration

Two documents may report the same FY24 revenue using different units.

Example:

```text
Document A:
₹8,142 Cr

Document B:
₹81,415.38 million
```

After unit normalization, the values are effectively equivalent.

Result:

```text
CORROBORATES
```

---

## Case 2 — Contradiction

If two documents describe the same metric, period, and scope but report materially different values:

```text
Document A:
Revenue = X

Document B:
Revenue = Y
```

where the normalized difference is substantial, the system can classify the relationship as:

```text
CONTRADICTS
```

---

## Case 3 — Apparent Contradiction

Two values can look different without actually being contradictory.

For example:

```text
373,854 tonnes
374 thousand tonnes
```

The second representation corresponds to approximately:

```text
374,000 tonnes
```

The difference is very small and can reasonably be explained by rounding.

Result:

```text
RECONCILES
```

---

## Case 4 — Extraction / Reasoning Uncertainty

PDFs frequently contain complex tables where relationships between row labels, columns, values, and units can be lost during plain-text extraction.

Instead of inventing a fact or forcing a relationship, the system can assign lower confidence or classify a comparison as:

```text
UNCERTAIN
```

This makes uncertainty visible to the user instead of hiding an extraction failure.

---

# 🛠️ Tech Stack

### Language

* Python

### PDF Processing

* PyMuPDF

### Data Validation

* Pydantic

### AI / LLM

* Google Gemini
* Google GenAI SDK

### UI

* Streamlit

### Data / Processing

* Python standard library
* Regular expressions

### Testing

* Pytest

---

# ⚙️ Setup

## 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd fact-knowledge-layer
```

## 2. Create a virtual environment

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

## 4. Configure environment variables

Create a `.env` file based on `.env.example`.

Example:

```env
GOOGLE_API_KEY=your_api_key_here
```

**Never commit `.env` or API keys to GitHub.**

---

# ▶️ Running the Application

Start the Streamlit application:

```bash
streamlit run ui/streamlit_app.py
```

The application will open in the browser.

Upload one or more PDF documents and click:

```text
Analyze Documents
```

The system will process the documents and display the extracted knowledge layer.

---

# 🧪 Running Tests

Run:

```bash
pytest
```

The current tests cover normalization behavior.

---

# 📊 Design Decisions & Trade-offs

## Why page-level extraction?

Evidence traceability is a core requirement of the system.

Processing PDFs page-by-page allows every fact to retain a specific source page instead of only referencing an entire document.

### Trade-off

Page-level processing is simpler and more traceable, but complex tables may require specialized table extraction in future versions.

---

## Why normalize values?

Documents frequently use different units and representations.

Without normalization:

```text
₹8,142 Cr
```

and

```text
₹81,415.38 million
```

could incorrectly appear to be unrelated values.

Normalization allows the reasoning layer to compare the underlying quantities.

---

## Why separate extraction, normalization, matching, and reasoning?

Each stage has a distinct responsibility.

```text
Extraction
    ↓
Normalization
    ↓
Matching
    ↓
Reasoning
```

This separation makes the system easier to test, debug, and extend.

---

## Why confidence scores?

Document extraction and cross-document reasoning are not always deterministic.

A confidence score allows uncertain results to be surfaced rather than presented as unquestionable facts.

---

# ⚠️ Current Limitations

### 1. Complex PDF Tables

Plain text extraction can lose table structure.

A value may become separated from its corresponding row or column.

### 2. Semantic Matching

The current matcher relies primarily on normalized subject, predicate, and time context.

Highly different wording for the same concept may not always be matched.

### 3. Time Context

Different representations of the same reporting period, such as:

```text
FY24
FY2024
Financial Year 2024
```

may require additional temporal normalization.

### 4. Scope Detection

A metric may refer to different business segments, geographies, or operational scopes.

More sophisticated scope extraction would improve reasoning accuracy.

### 5. LLM Rate Limits

LLM-based extraction can be affected by API rate limits and quota availability.

The system therefore maintains a local extraction path for development and testing.

---

# 🚀 Future Improvements

Possible next steps include:

* Semantic embeddings for fact matching
* Vector search for large document collections
* Better table extraction
* More robust temporal normalization
* Explicit scope and geography extraction
* Human review workflow for low-confidence facts
* FastAPI backend
* Persistent database storage
* Incremental document ingestion
* Duplicate fact detection
* Fact history/version tracking
* Knowledge graph visualization
* Support for significantly larger document collections

---

# 🎥 Demo

**Demo video:**
`https://fact-knowledge-layer-bnf54joyj5quqtzblckotq.streamlit.app/`

The demonstration will show:

1. Uploading multiple PDFs
2. Extracting structured facts
3. Inspecting source evidence
4. Comparing facts across documents
5. Viewing corroboration, contradiction, and reconciliation results
6. Handling uncertain extraction/reasoning

---

# 📌 Assignment Coverage

| Requirement                           | Implementation |
| ------------------------------------- | -------------- |
| Multiple PDFs                         | ✅              |
| Numerical / semantic fact extraction  | ✅              |
| Source evidence for every fact        | ✅              |
| Value normalization                   | ✅              |
| Cross-document comparison             | ✅              |
| Corroboration detection               | ✅              |
| Contradiction detection               | ✅              |
| Contextual reconciliation             | ✅              |
| Uncertainty handling                  | ✅              |
| Simple UI                             | ✅              |
| Additional PDF support                | ✅              |
| No hard-coded document-specific facts | ✅              |
| Confidence scores                     | ✅              |
| AI-assisted extraction path           | ✅              |

---

# 👩‍💻 Author

**Prerna**

B.Tech Computer Science Engineering

Vellore Institute of Technology
