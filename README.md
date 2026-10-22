# AudioSleuth — Digital Audio Forensics Toolkit

[![Academic Project](https://img.shields.io/badge/Academic-PICT%20%7C%20SPPU-blue.svg)](https://pict.edu)
[![Course](https://img.shields.io/badge/Course-CSDF%20Lab-indigo.svg)](#)
[![Python](https://img.shields.io/badge/Python-3.13-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61DAFB.svg?logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178C6.svg?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Vite](https://img.shields.io/badge/Vite-8.x-646CFF.svg?logo=vite&logoColor=white)](https://vitejs.dev/)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-v4-38B2AC.svg?logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)

---

## 1. Project Overview

**AudioSleuth** is a local-first digital audio forensic analysis workstation engineered to assist investigators and digital forensics students in examining digital audio recordings, verifying cryptographic evidence integrity, visualizing acoustic properties, detecting explainable signal anomalies, and compiling structured forensic reports.

- **Institution:** Pune Institute of Computer Technology (PICT)
- **Affiliation:** Savitribai Phule Pune University (SPPU)
- **Laboratory:** Cyber Security and Digital Forensics (CSDF) Lab
- **Current Milestone:** Phase 6B (Cross-Recording Forensic Comparison) — Complete

---

## 2. Core Forensic Principles

1. **Evidence Immutability:** Original uploaded audio bytes are preserved byte-for-byte in isolated storage. Signal processing is strictly performed on decoded working copies or in-memory arrays.
2. **Cryptographic Integrity Verification:** SHA-256 digests are computed immediately upon intake from original bytes. Re-verification recalculates the stored file digest to detect accidental alteration or disk tampering.
3. **Scientific Explainability:** Signal anomaly detectors (RMS energy, amplitude discontinuities, STFT spectral flux) expose actual mathematical metrics and configurable thresholds. The system explicitly avoids unsubstantiated claims of authenticity or "AI deepfake" verdicts without empirical evidence.
4. **Local-First & Privacy Preserving:** No external cloud dependencies, paid APIs, or external telemetry. Operates entirely offline on the investigator's local workstation.

---

## 3. Project Structure

```
CSDF/
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI routes and v1 API aggregator
│   │   │   ├── routes/health.py
│   │   │   └── v1/router.py
│   │   ├── core/             # Configuration, structured logging, errors
│   │   │   ├── config.py
│   │   │   ├── logging.py
│   │   │   └── errors.py
│   │   ├── schemas/          # Pydantic request/response models
│   │   │   ├── common.py
│   │   │   └── health.py
│   │   ├── services/         # Orchestration & business logic (Phase 2 & 5)
│   │   ├── analysis/         # Signal processing & anomaly detection (Phase 4)
│   │   ├── evidence/         # Evidence intake & SHA-256 hashing (Phase 2)
│   │   ├── models/           # SQLite database models (Phase 5)
│   │   ├── repositories/     # Database persistence (Phase 5)
│   │   ├── reports/          # ReportLab PDF generator (Phase 6)
│   │   ├── audit/            # Structured audit trail (Phase 5)
│   │   └── main.py           # Application factory & middlewares
│   ├── tests/                # Automated pytest suite
│   │   ├── conftest.py
│   │   └── test_health.py
│   ├── data/                 # Local evidence vault and SQLite DB
│   │   └── evidence/
│   ├── requirements.txt      # Python dependencies
│   ├── .env.example          # Backend environment variables template
│   └── pytest.ini            # Pytest configuration
├── frontend/
│   ├── src/
│   │   ├── api/              # Axios HTTP client & health API
│   │   ├── components/       # Layout (Sidebar, Header) & common UI
│   │   ├── pages/            # Dashboard, Cases, New Case, Diagnostics
│   │   ├── types/            # TypeScript data contracts
│   │   ├── App.tsx           # React Router definition
│   │   ├── main.tsx          # React DOM entry
│   │   └── index.css         # Tailwind CSS styling
│   ├── package.json          # Node dependencies & npm scripts
│   ├── vite.config.ts        # Vite configuration with API proxy
│   └── .env.example          # Frontend environment variables template
├── .gitignore                # Workspace gitignore rules
├── README.md                 # Project documentation & setup instructions
└── AGENTS.md                 # Primary project specification
```

---

## 4. Setup & Running in Windows PowerShell

### Prerequisites
- **Python 3.11+** (Tested on Python 3.13.2)
- **Node.js 18+** (Tested on Node v26.8.2 / npm 11.19.1)
- **PowerShell 7+** or Windows PowerShell 5.1

---

### Step 1: Backend Setup & Execution

Open a PowerShell terminal in the repository root (`c:\college\BE\LP4\CSDF`):

```powershell
# 1. Create Python virtual environment (if not already created)
python -m venv backend\.venv

# 2. Activate virtual environment
.\backend\.venv\Scripts\Activate.ps1

# 3. Install backend dependencies
python -m pip install -r backend\requirements.txt

# 4. Copy environment configuration
Copy-Item backend\.env.example backend\.env -Force

# 5. Launch FastAPI backend with live reload
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

The backend is now accessible at:
- **API Root:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Health Check:** [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)
- **Interactive OpenAPI Docs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

### Step 2: Frontend Setup & Execution

Open a second PowerShell terminal in the repository root:

```powershell
# 1. Navigate to frontend directory
cd frontend

# 2. Install Node dependencies
npm install

# 3. Copy environment configuration
Copy-Item .env.example .env -Force

# 4. Launch Vite development server
npm run dev
```

The frontend workstation is now accessible at:
- **Web UI:** [http://localhost:5173/](http://localhost:5173/)

---

### Step 3: Run Automated Tests

To run the backend test suite:

```powershell
# In repository root with active virtual environment:
.\backend\.venv\Scripts\python.exe -m pytest backend\tests
```

To run the frontend type-check and production build test:

```powershell
# In frontend directory:
npm run build
```

---

## 5. Development Roadmap & Phase Status

| Phase | Description | Status |
| :--- | :--- | :---: |
| **Phase 0** | Repository Inspection and Architecture Planning | **Complete** |
| **Phase 1** | Foundation (FastAPI + React 19 + Tailwind v4 + Health Subsystems + Tests) | **Complete** |
| **Phase 2** | Evidence Acquisition (Streaming Upload, Validation, Safe Storage, SHA-256 Hashing, Integrity Verification) | **Complete** |
| **Phase 3** | Audio Metadata and Visualizations (Non-destructive decode, Waveform, STFT Spectrogram, FFT Spectrum, Embedded Tags) | **Complete** |
| **Phase 4** | Forensic Signal Analysis (Silence, Discontinuities, Spectral Flux) | **Complete** |
| **Phase 5** | Case Management & SQLite Persistence & Audit Logging | **Complete** |
| **Phase 6A** | Forensic PDF Report Generation (ReportLab, In-Memory Charts, ISO/IEC 27037 Compliance) | **Complete** |
| **Phase 6B** | Cross-Recording Forensic Comparison (Metadata, Dynamics, STFT Spectrum, Timeline) | **Complete** |
| **Phase 7** | Comprehensive Testing, Malformed Input Tests, and Hardening | Planned |
| **Phase 8** | Integration, Demonstration, and Defense Preparation | Planned |

---

## 6. Phase 3 API Endpoints & Capabilities

### Endpoints
- `GET /api/v1/evidence/{evidence_id}/metadata`: Extracts encoded container properties, decoded acoustic signal parameters, and embedded metadata tags (ID3, RIFF INFO, Vorbis comments).
- `GET /api/v1/evidence/{evidence_id}/waveform`: Generates downsampled deterministic min/max envelope data preserving transient amplitude spikes over a configurable point budget.
- `GET /api/v1/evidence/{evidence_id}/spectrogram`: Computes STFT magnitude heatmap in decibels over time and frequency with Hann windowing and safe finite log-clamping.
- `GET /api/v1/evidence/{evidence_id}/spectrum`: Computes calibrated FFT power spectrum, Nyquist ceiling, and isolates the dominant harmonic peak.
- `GET /api/v1/evidence/{evidence_id}/audio`: Streams audio for in-browser playback with HTTP Range request support (`206 Partial Content`) for instant scrubbing.

### Audio-Processing Methodology
1. **Evidence Hygiene & Pre-Check Integrity:** Before any decoding occurs, AudioSleuth recalculates the stored file's SHA-256 digest on disk and verifies it against the registered digest. If a mismatch is detected, decoding is aborted immediately and an `INTEGRITY_MISMATCH` alert is raised.
2. **Non-Destructive In-Memory Decoding:** The original audio evidence in the evidence vault is never altered, normalized, or rewritten. Audio is read using `soundfile` directly into temporary NumPy float32 arrays and cleaned up automatically.
3. **Deterministic Waveform Envelopes:** Rather than decimating samples arbitrarily, audio is partitioned into contiguous time windows. The true minimum and maximum sample values per window are retained, guaranteeing that brief transient discontinuities or spikes are never lost.
4. **Time-Frequency STFT Spectrogram:** Uses `scipy.signal.stft` with a Hann window. Magnitudes are converted to logarithmic decibels ($20 \log_{10} |STFT|$). Clamped safely against digital silence (`np.maximum(mag, 1e-6)`) with an 80 dB dynamic range floor, guaranteeing zero NaNs or infinities.
5. **Calibrated FFT Power Spectrum:** Computes one-sided real FFT (`np.fft.rfft`) with Hann window. Frequencies are calibrated in Hertz up to the Nyquist limit ($f_s / 2$). Dominant peak frequency detection isolates the primary tone within documented ±5 Hz accuracy.

### Enforced Resource Limits
- `MAX_UPLOAD_SIZE_BYTES`: 100 MB
- `MAX_DECODED_DURATION_SECONDS`: 1,800 seconds (30 minutes)
- `MAX_DECODED_SAMPLES`: 100,000,000 samples
- `WAVEFORM_POINT_BUDGET`: 100 to 10,000 display points (default 1,000)
- `SPECTROGRAM_MAX_TIME_FRAMES`: 4,000 frames
- `SPECTROGRAM_MAX_FREQ_BINS`: 2,048 bins
- `SPECTRUM_MAX_BINS`: 4,096 bins

### Supported Formats & Decoder Caveats
- **WAV:** Full support for uncompressed PCM (8/16/24/32-bit) and IEEE float formats.
- **FLAC:** Lossless compressed audio decoded with bit depth and sample accuracy.
- **MP3:** MPEG-1/2 Audio Layer III decoded via libsndfile. Bit depth is reported as `null` for lossy/variable-rate formats to avoid fabricating unverified data.

> [!WARNING]
> **Forensic Evidentiary Disclaimer:** Metadata properties and signal visualizations alone do NOT establish whether an audio recording is authentic, fake, or tampered with. Normal speech dynamics, background noise, and lossy compression artifacts routinely generate transient peaks and spectral boundaries. Signal visualizations serve as investigative aids requiring contextual interpretation and multi-factor verification.

---

## 7. Phase 4 Explainable Forensic Signal Analysis

Phase 4 implements explainable, mathematically grounded audio signal processing detectors to assist investigators in localizing suspicious signal anomalies. AudioSleuth strictly adheres to scientific explainability: every flagged interval reports its mathematical formulation, exact measured values, configurable decision thresholds, localized timestamps, and evidentiary disclaimers.

### 7.1 Primary Analysis Endpoint

- **Endpoint:** `POST /api/v1/evidence/{evidence_id}/analyze`
- **Method:** `POST`
- **Description:** Runs selected explainable signal anomaly detectors on verified, non-destructively decoded evidence audio.
- **Pre-Check Requirement:** Recalculates physical evidence SHA-256 before decoding. Rejects tampered evidence with `400 Bad Request` (`INTEGRITY_MISMATCH`).

#### Request Schema (`AnalysisRequest`)

All fields are optional; omitting them activates default parameters:

```json
{
  "enable_silence": true,
  "enable_transitions": true,
  "enable_spectral_flux": true,
  "silence_params": {
    "window_duration_seconds": 0.05,
    "hop_duration_seconds": 0.025,
    "rms_threshold": 0.01,
    "min_silence_duration_seconds": 0.25
  },
  "transition_params": {
    "threshold": 0.35,
    "min_separation_seconds": 0.05,
    "context_window_seconds": 0.05
  },
  "spectral_params": {
    "n_fft": 1024,
    "hop_length": 256,
    "threshold": 0.40,
    "min_separation_seconds": 0.1,
    "context_window_seconds": 0.1
  }
}
```

#### Enforced Parameter Bounds & Defaults

| Detector | Parameter | Type | Default | Enforced Bounds | Description |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **Silence** | `window_duration_seconds` | `float` | `0.05` (50ms) | `[0.01, 1.0]` | Sliding RMS window duration |
| | `hop_duration_seconds` | `float` | `0.025` (25ms) | `[0.005, 0.5]` | Window hop step |
| | `rms_threshold` | `float` | `0.01` (~-40 dB) | `[0.00001, 0.5]` | Linear RMS energy cutoff |
| | `min_silence_duration_seconds` | `float` | `0.25` (250ms) | `[0.05, 10.0]` | Minimum duration to report as an interval |
| **Discontinuity** | `threshold` | `float` | `0.35` | `[0.05, 1.5]` | Adjacent-sample step delta threshold ($\lvert \Delta x \rvert$) |
| | `min_separation_seconds` | `float` | `0.05` (50ms) | `[0.01, 2.0]` | Temporal suppression cluster radius |
| | `context_window_seconds` | `float` | `0.05` (50ms) | `[0.01, 0.5]` | Context review window around event |
| **Spectral Flux** | `n_fft` | `int` | `1024` | `[128, 4096]` | STFT window size in samples |
| | `hop_length` | `int` | `256` | `[32, 2048]` | STFT frame hop step in samples |
| | `threshold` | `float` | `0.40` | `[0.05, 1.5]` | Normalized spectral flux peak threshold |
| | `min_separation_seconds` | `float` | `0.10` (100ms) | `[0.02, 2.0]` | Temporal suppression cluster radius |
| | `context_window_seconds` | `float` | `0.10` (100ms) | `[0.02, 0.5]` | Context review window around event |

#### Response Schema (`AnalysisResponse`)

```json
{
  "analysis_id": "ANL-20261022180000-a1b2c3",
  "evidence_id": "EVD-20261022170000-d4e5f6",
  "source_sha256": "7a356839cf9e578f72dfd38a063bb942b10a26aa2cd6174bb0df55227d82585c",
  "created_at": "2026-10-22T18:00:00.123456+00:00",
  "execution_status": "completed",
  "summary": {
    "total_findings": 3,
    "by_category": {
      "silence": 1,
      "transition": 1,
      "spectral": 1
    },
    "by_priority": {
      "high": 1,
      "medium": 1,
      "low": 1
    },
    "execution_time_ms": 32.45
  },
  "findings": [
    {
      "id": "FIND-20261022180000-88f1a2",
      "evidence_id": "EVD-20261022170000-d4e5f6",
      "source_sha256": "7a356839cf9e578f72dfd38a063bb942b10a26aa2cd6174bb0df55227d82585c",
      "detector_name": "silence_interval_detector",
      "algorithm_version": "1.0.0",
      "category": "silence",
      "priority": "medium",
      "start_time": 0.5000,
      "end_time": 1.1000,
      "duration_seconds": 0.6000,
      "event_time": 0.5000,
      "metric_name": "rms_energy",
      "measured_value": 0.000000,
      "applied_threshold": 0.0100,
      "units": "linear_rms",
      "parameters": {
        "window_duration_seconds": 0.05,
        "hop_duration_seconds": 0.025,
        "rms_threshold": 0.01,
        "min_silence_duration_seconds": 0.25
      },
      "explanation": "True digital silence detected (0.60s, min RMS: 0.000000). Exact zero-amplitude intervals rarely occur naturally in acoustic microphone recordings and may indicate digital muting, cutting, or padding.",
      "suggested_action": "Inspect interval in waveform view to determine whether ambient background noise drops to absolute zero or transitions abruptly at boundary timestamps.",
      "disclaimer": "Finding represents an explainable acoustic signal indicator for manual forensic review, not definitive proof of tampering, synthesis, or editing."
    }
  ],
  "parameters_applied": {
    "silence": "default",
    "transitions": "default",
    "spectral_flux": "default"
  }
}
```

---

### 7.2 Detection Methodologies & Scientific Formulations

#### A. Silence & Low-Energy Interval Detection (`silence.py`)
- **Mathematical Metric:** Short-Time Root Mean Square (RMS) energy:
  $$\text{RMS} = \sqrt{\frac{1}{N} \sum_{i=1}^N x_i^2}$$
  calculated over sliding frames of length `window_duration_seconds` advancing by `hop_duration_seconds`. Multichannel recordings average squared amplitudes across channels prior to frame extraction.
- **Interval Aggregation:** Contiguous frames below `rms_threshold` are joined into intervals. Intervals shorter than `min_silence_duration_seconds` are discarded.
- **Priority Classification:**
  - **Medium Priority:** True digital zero ($\text{min RMS} < 10^{-6}$ for $\ge 1.0\text{s}$) or prolonged silence ($\ge 3.0\text{s}$). True zero rarely occurs in physical microphone recordings due to ambient acoustic noise floors and thermal preamp hiss.
  - **Low Priority:** Natural speech pauses or ambient acoustic dropouts ($< 3.0\text{s}$).

#### B. Abrupt Amplitude Discontinuity Detection (`transitions.py`)
- **Mathematical Metric:** Instantaneous adjacent-sample absolute difference:
  $$\Delta x[n] = \lvert x[n] - x[n-1] \rvert$$
  For multichannel audio, the maximum difference across channels is evaluated: $\max_c \lvert x_c[n] - x_c[n-1] \rvert$.
- **Temporal Suppression & Peak Selection:** Candidate indices exceeding `threshold` within `min_separation_seconds` are clustered. Only the maximum spike per cluster is retained, preventing multiple duplicate findings from ringing or single onset transients.
- **Priority Classification:**
  - **High Priority ($\ge 0.70$):** Severe instantaneous step jump, characteristic of hard splice points, buffer discontinuities, or clipped waveforms.
  - **Medium Priority ($\ge 0.45$):** Moderate step exceeding typical speech formant gradients; warrants splice/onset review.
  - **Low Priority ($< 0.45$):** Mild step consistent with plosive consonants (/p/, /t/, /k/) or sharp percussive attacks.

#### C. STFT Spectral Flux Anomaly Detection (`spectral.py`)
- **Mathematical Metric:** Euclidean distance between consecutive L2-normalized STFT magnitude vectors:
  $$SF(t) = \sqrt{\sum_k \left(X_{\text{norm}}(t, k) - X_{\text{norm}}(t-1, k)\right)^2}$$
  where $X_{\text{norm}}(t, k) = \frac{X(t, k)}{\lVert X(t) \rVert_2 + \epsilon}$.
- **Volume Invariance:** Normalizing magnitude vectors ensures spectral flux measures redistributions of frequency energy rather than overall loudness changes.
- **Temporal Suppression:** Clusters candidate peaks within `min_separation_seconds` to report discrete acoustic transition points.
- **Priority Classification:**
  - **High Priority ($\ge 0.85$):** Drastic reallocation of frequency energy between adjacent frames; characteristic of spliced recordings or acoustic scene changes.
  - **Medium Priority ($\ge 0.60$):** Moderate spectral change exceeding smooth phoneme transitions.
  - **Low Priority ($< 0.60$):** Natural acoustic onsets, consonant attacks, or musical chord changes.

---

### 7.3 Cryptographic Integrity Pre-Check Behavior

Every analysis request performs mandatory pre-analysis SHA-256 verification via `verify_and_load_audio`:
1. The stored evidence file on disk is read and its SHA-256 digest is computed using `hashlib.sha256`.
2. The digest is compared to the intake record's `sha256_hash` using constant-time `hmac.compare_digest`.
3. **If digests match:** Non-destructive in-memory decoding proceeds into a temporary NumPy float32 working representation. Original files are never modified.
4. **If digests mismatch:** Decoding and analysis are immediately refused. An HTTP `400 Bad Request` with error code `INTEGRITY_MISMATCH` is returned:
   ```json
   {
     "error": {
       "code": "INTEGRITY_MISMATCH",
       "message": "CRITICAL INTEGRITY FAILURE: Stored evidence bytes have been altered or corrupted on disk. Audio inspection refused to preserve forensic chain-of-custody.",
       "details": {
         "evidence_id": "EVD-...",
         "expected_sha256": "...",
         "calculated_sha256": "..."
       }
     }
   }
   ```

---

### 7.4 Forensic Interpretation Limitations

> [!CAUTION]
> **Forensic Evidentiary Disclaimer:**  
> 1. **Indicators, Not Proof:** Flagged intervals are mathematical acoustic anomalies highlighting regions for human examiner inspection. They do NOT constitute legal or definitive proof of tampering, digital synthesis, audio editing, or malicious intent.
> 2. **Natural False Positives:** Natural human speech acoustics routinely produce signal patterns that cross thresholds: plosive consonants create sharp amplitude steps, vocal pauses create silence intervals, and abrupt speaker phonations generate spectral flux peaks.
> 3. **Environmental & Codec Factors:** Lossy compression (e.g., MP3/AAC quantization boundaries), microphone handling noise, room reverberation, and automatic gain control (AGC) frequently trigger anomaly indicators.
> 4. **No Automated Authenticity Verdicts:** AudioSleuth intentionally avoids unverified claims of "AI deepfake detection" or binary "authentic vs. fake" verdicts. Findings serve strictly to guide the forensic investigator's manual timeline review.

---

## 8. Phase 5 Case Management, SQLite Persistence & Structured Audit Logging

Phase 5 establishes a robust, durable SQLite relational foundation for forensic investigation cases, strict custodial evidence association, and immutable-style structured audit logging.

### 8.1 Case Management API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/cases` | Creates a new forensic case with a unique ID (`CASE-...`), title, investigator, and notes. Emits `case_created`. |
| `GET` | `/api/v1/cases` | Lists cases with optional `?status=active|closed` filtering, pagination, and dynamic evidence counts. |
| `GET` | `/api/v1/cases/{case_id}` | Retrieves case details, current status, metadata, and evidence count. Returns 404 (`CASE_NOT_FOUND`) if invalid. |
| `PATCH` | `/api/v1/cases/{case_id}` | Updates editable case metadata (`title`, `investigator_name`, `description`). Emits `case_updated`. |
| `POST` | `/api/v1/cases/{case_id}/status` | Executes explicit case status transition (`active` ↔ `closed`) with mandatory audit reason. Emits `case_closed` or `case_reopened`. |
| `GET` | `/api/v1/cases/{case_id}/evidence` | Lists all evidence items strictly bound to the case. Returns 404 if case does not exist. |
| `GET` | `/api/v1/cases/{case_id}/audit` | Retrieves chronological audit events scoped to a specific case. |
| `GET` | `/api/v1/audit` | Global audit log query endpoint with action/case/evidence filters and pagination. |
| `GET` | `/api/v1/audit/{event_id}` | Retrieves a single audit event record by its unique ID (`EVT-...`). |

### 8.2 Custodial Integrity & Case Lifecycle Enforcement

1. **Strict Evidence Association:** Evidence cannot be orphaned. Uploading evidence requires a valid `case_id`. Nonexistent cases return HTTP 404 (`CASE_NOT_FOUND`).
2. **Case Finality Lock (`CASE_CLOSED`):** When a case is transitioned to `closed`, all further evidence intake attempts for that case are rejected with HTTP 400 (`CASE_CLOSED`). An examiner must explicitly reopen the case with a documented reason before additional recordings can be acquired.
3. **Non-Destructive Schema Evolution:** Database migrations use `PRAGMA table_info` introspection to conditionally add new columns (`description`, `status`) and indexes (`idx_cases_status`, `idx_audit_case_id`, `idx_audit_evidence_id`, `idx_audit_timestamp`, `idx_audit_action`) without data loss or dropping tables.

### 8.3 Structured Audit Logging Architecture

All significant forensic actions are permanently recorded into the `audit_events` SQLite table via `AuditService`:

- **Event Identifier:** Unique, human-readable prefix `EVT-<uuid4_hex[:12]>`.
- **Timestamp:** ISO 8601 UTC timestamp of execution.
- **Action Types:**
  - `case_created`: Case initialization with title, examiner, and notes.
  - `case_updated`: Metadata modifications with diff details.
  - `case_closed`: Case closure with documented reason.
  - `case_reopened`: Case reopening with documented reason.
  - `evidence_uploaded`: Evidence file intake, format, size, and SHA-256 hash.
  - `integrity_verified`: Hash recalculation outcome (`match`, `mismatch`, `unverifiable`).
  - `metadata_inspected`: Audio container and signal property extraction.
  - `signal_analyzed`: Signal anomaly detector execution, parameters, and findings counts.
- **Forensic Sanitization:** Audit logging strictly sanitizes input details. Binary byte streams, decrypted audio buffers, credentials, and raw memory representations are stripped to prevent database bloating and data leakage.

### 8.4 Legal & Forensic Chain-of-Custody Disclosure

> [!NOTE]
> **ISO/IEC 27037 Disclosure:**  
> The structured audit log provides application-level accountability and chronological tracking for academic demonstrations and investigative review. Standard SQLite persistence does NOT provide cryptographically anchored, hardware-secured, or WORM (Write Once, Read Many) tamper-proof guarantees. In certified forensic casework, database records must be supplemented with external physical chain-of-custody documentation and write-blocked media archives.

---

## 9. Phase 6A Forensic PDF Report Generation

Phase 6A provides automated, evidence-based PDF examination report generation for AudioSleuth. Reports are compiled entirely in memory using ReportLab without writing unmanaged files into the evidence vault or modifying original evidence bytes. Every report reflects actual persisted case metadata, pre-checked cryptographic integrity results, extracted audio properties, explainable signal anomaly findings, and durable audit logs.

### 9.1 Report Generation Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/evidence/{evidence_id}/report` | Generates and streams PDF report for the evidence item using default query options. |
| `POST` | `/api/v1/evidence/{evidence_id}/report` | Generates and streams PDF report with a customized JSON request payload. |
| `GET` | `/api/v1/cases/{case_id}/evidence/{evidence_id}/report` | Generates PDF report with strict validation of the case-to-evidence relationship. |

### 9.2 Request Options & Parameters

The report generation service accepts configurable options via query parameters (`GET`) or JSON body (`POST`):

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `include_visualizations` | `bool` | `true` | When `true`, embeds rendered waveform envelopes and STFT spectrogram charts. |
| `include_audit` | `bool` | `true` | When `true`, embeds chronological audit events associated with the evidence. |
| `run_analysis` | `bool` | `true` | When `true`, automatically executes signal anomaly detectors if not previously run. |
| `case_id` | `string` | `null` | Optional case identifier. If provided, verifies that the evidence belongs to this case. |
| `notes` | `string` | `null` | Optional examiner notes appended to the report. |

#### HTTP Response Headers
- `Content-Type`: `application/pdf`
- `Content-Disposition`: `attachment; filename="AudioSleuth_Forensic_Report_{evidence_id}.pdf"`

### 9.3 Cryptographic Integrity Pre-Check Policy

Before generating any report that describes evidence as verified:
1. **Physical Hash Re-Calculation:** AudioSleuth recalculates the SHA-256 digest directly from the stored evidence bytes on disk.
2. **Mandatory Abort on Tampering:** If the calculated digest does not match the registered intake digest, report generation is immediately aborted with HTTP 400 (`INTEGRITY_MISMATCH`). The system refuses to silently issue a clean report for tampered evidence.
3. **Custodial Validation:** If an explicit `case_id` is supplied and does not match the evidence's registered case association, the request is rejected with HTTP 400 (`CASE_EVIDENCE_MISMATCH`).

### 9.4 Report Structure & Contents

Generated PDF reports follow a standard forensic structure formatted with running headers and dynamic two-pass page numbering ("Page X of Y"):

1. **Title Banner & Metadata Header:** Document title, unique report identifier (`REP-...`), generation timestamp (UTC), and software version.
2. **Section 1 — Forensic Case Record:** Case identifier, case title, assigned investigator, case status (`active`/`closed`), and case description.
3. **Section 2 — Evidence Identification & Custody:** Evidence identifier, original filename, media format, physical file size, registered intake SHA-256 digest, and pre-generation integrity check result (`MATCH`).
4. **Section 3 — Audio Signal Parameters & Container Tags:** Decoded sample rate, channel count, duration, sample format, bit depth (or lossy indicator), and embedded metadata tags (ID3, RIFF INFO, Vorbis comments).
5. **Section 4 — Acoustic Signal Visualizations (Optional):** In-memory high-resolution waveform amplitude envelope and STFT time-frequency spectrogram charts rendered directly via Pillow and ReportLab without temporary disk files.
6. **Section 5 — Explainable Signal Anomaly Findings:** Detailed findings table including finding ID, detection category, priority level, start/end timestamps, measured values, applied thresholds, explainable descriptions, and recommended manual review actions.
7. **Section 6 — Chronological Chain of Custody Audit Log (Optional):** Durable audit trail records listing event IDs, timestamps, actions (`case_created`, `evidence_uploaded`, `integrity_verified`, `signal_analyzed`), and execution outcomes.
8. **Section 7 — Methodology, Limitations & Examiner Sign-Off:** Explicit ISO/IEC 27037 forensic disclaimers and an examiner signature block.

### 9.5 Audit Trail Integration

Every successful report generation triggers a durable audit event:
- **Action:** `report_generated`
- **Details:** Includes `report_id`, evidence ID, case ID, options flags, findings count, and generation timestamp.

### 9.6 Forensic Evidentiary Limitations

> [!CAUTION]
> **Forensic Report Interpretation Notice:**  
> 1. **Algorithmic Indicators Only:** Anomaly detections (silence intervals, amplitude discontinuities, spectral flux spikes) are screening indicators designed to assist human examiners. They do NOT establish definitive proof of malicious tampering, audio splicing, or digital synthesis.
> 2. **Human Examination Required:** All flagged timestamps must be manually audited and correlated with recording context, background acoustics, and speaker dynamics.
> 3. **Unsigned Document Notice:** Unless digitally signed with an external public key infrastructure (PKI) certificate, the generated PDF represents an investigative report and does not constitute a legally certified or tamper-proof instrument on its own.

---

## 10. Phase 6B Cross-Recording Forensic Comparison

Phase 6B provides deterministic, explainable cross-recording forensic comparison capabilities. An investigator can compare any two registered evidence recordings—whether acquired under the same case or across different investigations—to evaluate container metadata, signal dynamics, STFT spectral characteristics, and Phase 4 anomaly temporal distributions.

### 10.1 Comparison Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/evidence` | Lists all registered evidence items across cases (optional `?case_id=...` filter) for comparison picker selection. |
| `POST` | `/api/v1/evidence/compare` | Executes a cross-recording forensic comparison between two evidence recordings and returns detailed metrics. |
| `GET` | `/api/v1/comparisons/{comparison_id}` | Retrieves a previously executed and persisted comparison result by its unique identifier (`COMP-...`). |
| `POST` | `/api/v1/evidence/compare/report` | Executes a comparison and streams a downloadable multi-page PDF comparison examination report. |
| `GET` | `/api/v1/comparisons/{comparison_id}/report` | Generates and streams a downloadable PDF comparison report for a historical comparison record. |

### 10.2 Comparison Dimensions & Metrics

Cross-recording analysis is partitioned into four explainable dimensions:

#### 1. Evidence Custody & Recording Metadata
- **File & Media Properties:** Filenames, detected container formats (`WAV`, `MP3`, `FLAC`), and physical file sizes.
- **Duration Delta:** Measures $|t_A - t_B|$ in seconds. Marked as duration-aligned if difference $\le 0.05$ seconds.
- **Sampling Frequency & Channels:** Exact match checks for sampling rate (Hz) and channel count. If rates differ, comparison is safely bounded up to the minimum shared Nyquist ceiling ($f_{\max} = \min(f_{s,A}/2, f_{s,B}/2)$).
- **Cryptographic Byte Identity:** Full constant-time comparison of intake SHA-256 digests. If hashes match identically, recordings are confirmed to be byte-for-byte identical duplicates.

#### 2. Signal-Level Energy & Macro Dynamics
- **Peak Amplitude:** Measures maximum absolute sample value ($\max |s|$).
- **RMS Energy & Ratio:** Measures root-mean-square energy ($\sqrt{\frac{1}{N}\sum s_i^2}$) and relative energy ratio in decibels ($20 \log_{10} \frac{\text{RMS}_A}{\text{RMS}_B}$).
- **Crest Factor:** Ratio of peak amplitude to RMS energy ($\frac{\text{peak}}{\text{RMS}}$), quantifying dynamic peakiness.
- **Zero Crossing Rate (ZCR):** Rate of signal sign reversals per second, sensitive to dominant frequency and noise floor.
- **Envelope Pearson Correlation ($r$):** Computes Pearson linear correlation coefficient $r \in [-1.0, 1.0]$ between normalized macro-amplitude envelopes (default 500 envelope points).

#### 3. STFT Spectral Characteristics
- **Spectral Centroid (Hz):** Center of gravity of frequency spectrum: $C = \frac{\sum_k f_k P(k)}{\sum_k P(k)}$.
- **Spectral Roll-Off (Hz):** Frequency below which 85% of total spectral power resides.
- **Spectral Flatness:** Wiener entropy ratio of geometric mean to arithmetic mean of power spectrum, indicating tonal vs noise-like distribution.
- **Spectral Cosine Similarity ($S_{\text{spec}}$):** Evaluates inner product between L2-normalized mean STFT power spectrum profiles interpolated onto a shared frequency grid up to the lower Nyquist ceiling:
  $$S_{\text{spec}} = \frac{\mathbf{P}_A \cdot \mathbf{P}_B}{\|\mathbf{P}_A\|_2 \|\mathbf{P}_B\|_2} \in [0.0, 1.0]$$
- **Spectral Euclidean Distance:** Normalized L2 distance between unit-length spectral profiles.

#### 4. Anomaly Timeline Distribution
- **Phase 4 Integration:** Reuses silence, amplitude transition, and STFT spectral flux anomaly detectors on both recordings.
- **Findings Counts:** Compares total and per-category anomaly occurrences.
- **Anomaly Density:** Quantifies flagged anomaly events per minute of audio.
- **10-Bin Normalized Timeline Distribution:** Bins detected anomalies into ten deciles ($0-10\%, 10-20\%, \dots, 90-100\%$) along each recording's normalized duration, exposing relative temporal clustering.

### 10.3 Transparent Scoring Formula

AudioSleuth strictly avoids black-box machine learning scores. The composite similarity index is calculated transparently from documented, normalized components:

$$\text{Similarity Score} = 0.50 \cdot S_{\text{spec}} + 0.30 \cdot \max(0, r_{\text{envelope}}) + 0.20 \cdot \max\left(0, 1 - \frac{|\Delta t|}{\max(t_A, t_B)}\right)$$

- **$S_{\text{spec}}$:** STFT Spectral Cosine Similarity $\in [0, 1]$
- **$r_{\text{envelope}}$:** Amplitude envelope Pearson correlation $\in [-1, 1]$
- **$|\Delta t| / \max(t_A, t_B)$:** Fractional duration disparity $\in [0, 1]$

#### Acoustic Similarity Classification Labels
- **Byte-Identical Duplicate:** SHA-256 hashes match identically.
- **Very High Acoustic Similarity:** Score $\ge 0.92$, spectral similarity $\ge 0.95$, and duration delta $\le 0.05$s (typical of container conversion or identical audio re-encoded).
- **Moderate Similarity:** Score $\ge 0.70$ (shares general acoustic or spectral bandwidth, but exhibits temporal or dynamic variations).
- **Divergent Acoustic Profiles:** Score $< 0.70$ (distinct frequency content or recording duration).

### 10.4 Mandatory Integrity Pre-Check & Audit Trail

1. **Storage Integrity Re-Calculation:** Prior to decoding either recording for comparison, physical disk SHA-256 hashes are recalculated. If either file fails verification, the request is aborted with HTTP 400 (`INTEGRITY_MISMATCH`).
2. **Durable Audit Event:** Executing a comparison writes an `evidence_compared` audit event into the SQLite audit trail, recording comparison ID, both evidence IDs, registered hashes, spectral similarity, envelope correlation, and similarity score.
3. **Evidence Immutability:** Original files in the evidence vault remain strictly read-only. No temporary audio files are written to disk.

### 10.5 Forensic Evidentiary Limitations

> [!CAUTION]
> **Forensic Cross-Recording Comparison Limitations:**  
> 1. **Different Hashes $\neq$ Different Audio:** Audio files with different SHA-256 digests can contain identical acoustic content due to re-encoding, tag editing, or container format differences.
> 2. **Identical Hashes $\neq$ Proof of Authenticity:** A matching SHA-256 hash confirms byte-level physical identity between the compared files; it does not verify who recorded the audio or whether tampering occurred prior to intake.
> 3. **Spectral Similarity $\neq$ Source Attribution:** High spectral or envelope similarity does NOT establish that two recordings were captured by the same microphone, in the same room, or produced by the same speaker.
> 4. **Investigative Screening Tool:** Comparative metrics are intended to guide the human examiner's manual timeline inspection, not to serve as automated legal proof of authenticity or manipulation.




