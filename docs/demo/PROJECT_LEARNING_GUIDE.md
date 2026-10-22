# AudioSleuth — Comprehensive Technical & Forensic Learning Guide

**Project:** AudioSleuth — Digital Audio Forensics Toolkit  
**Academic Subject:** Cyber Security and Digital Forensics (CSDF) Lab  
**Institution:** Pune Institute of Computer Technology (PICT), SPPU  
**Author / Examiner:** PICT CSDF Final Year Computer Engineering Project Team  
**Scope:** Complete System Architecture, Signal Mathematics, Forensic Workflows & Implementation Reference  

---

## 1. The Forensic Problem AudioSleuth Solves

In modern digital forensics, audio recordings—such as voice memos, emergency calls, witness interviews, wiretaps, and courtroom exhibits—are increasingly submitted as digital evidence. However, digital audio is inherently vulnerable:
- **Trivial Manipulation:** Audio editing tools (Audacity, DAW software) allow anyone to cut words, insert phrases, mute segments, or rearrange sentences without leaving obvious audible seams.
- **Unscientific Claims:** Laypersons often rely on unverified claims of "AI deepfake" or "authentic" without empirical signal-level justification.
- **Custodial Spoilage:** Inexperienced investigators often open original evidence recordings in media players or editors that silently modify file timestamps, rewrite ID3 container tags, or re-encode samples.

### The Purpose of AudioSleuth
AudioSleuth is a **local-first digital audio forensics workstation**. It provides:
1. **Strict Custodial Evidence Handling:** Uploaded evidence is cryptographically hashed with SHA-256 at intake and locked in byte-for-byte read-only storage.
2. **Non-Destructive In-Memory Signal Inspection:** Original files are never modified. Decoding takes place directly into temporary memory buffers.
3. **Scientifically Grounded Anomaly Detection:** Rather than relying on black-box neural networks, AudioSleuth exposes explainable signal processing algorithms (RMS energy, adjacent-sample discontinuities, STFT spectral flux) with transparent mathematical thresholds.
4. **Permanent Audit Logging & Case Binding:** Every action (case creation, upload, hash check, analysis, comparison, report download) is recorded in a durable SQLite audit trail.
5. **Court-Ready Forensic Documentation:** Automated ReportLab engines generate structured PDF examination reports complying with ISO/IEC 27037 principles.

---

## 2. Target Users & Investigative Workflow

### Target Users
- **Digital Forensic Examiners:** Law enforcement or private cybersecurity investigators examining suspect recordings.
- **CSDF Students & Academic Researchers:** Learning acoustic signal processing, cryptographic hash verification, and forensic chain-of-custody protocols.
- **Internal Corporate Incident Responders:** Auditing recorded helpdesk calls, compliance logs, or meeting disclosures.

### The Standard Forensic Workflow

```
[1. Evidence Acquisition]
  │  Drag-and-drop audio recording into an active forensic case.
  ▼
[2. Cryptographic Registration]
  │  Compute intake SHA-256 digest; store original bytes in isolated vault.
  ▼
[3. Pre-Analysis Integrity Re-Check]
  │  Recalculate physical disk hash; verify against registered intake hash.
  ▼
[4. Non-Destructive Decoding & Inspection]
  │  Extract container metadata, render waveform envelopes, spectrogram, spectrum.
  ▼
[5. Explainable Signal Anomaly Screening]
  │  Execute RMS silence detection, amplitude discontinuity analysis, and STFT flux.
  ▼
[6. Cross-Recording Forensic Comparison (Optional)]
  │  Compare against reference recording (metadata, dynamics, spectral profile, score).
  ▼
[7. Automated PDF Report Generation]
  │  Compile court-ready examination document with custody logs and disclaimers.
```

---

## 3. Cryptographic Evidence Integrity & SHA-256

### What SHA-256 Does
SHA-256 (Secure Hash Algorithm 256-bit) is a cryptographic one-way hash function developed by the NSA and standardized by NIST (FIPS 180-4). It processes an arbitrary stream of input bytes and computes a deterministic, fixed-length 64-character hexadecimal digest (256 bits).

Key mathematical properties:
1. **Pre-image Resistance (One-Way):** Given a digest $H$, it is computationally infeasible to reconstruct the original audio bytes $M$ such that $\text{SHA-256}(M) = H$.
2. **Second Pre-image Resistance:** Given an audio file $M_1$, it is infeasible to find another file $M_2 \neq M_1$ such that $\text{SHA-256}(M_1) = \text{SHA-256}(M_2)$.
3. **Collision Resistance:** It is infeasible to find any two distinct files that yield the same hash.
4. **Avalanche Effect:** Flipping even a single bit in a 100 MB audio recording changes approximately 50% of the output hash characters completely unpredictably.

### Intake Hashing vs. Integrity Re-Verification
- **At Ingestion:** AudioSleuth streams the uploaded raw bytes through Python’s `hashlib.sha256()`. The resulting digest is stored in the database alongside the file size and timestamp.
- **At Re-Verification:** Whenever an examiner views the file, runs analysis, or compiles a report, AudioSleuth re-reads the physical file from disk, recalculates the SHA-256 digest, and uses constant-time `hmac.compare_digest()` to compare against the intake hash.
- **If digests match:** Confirms the stored file has suffered zero byte modifications, accidental corruption, or disk tampering.
- **If digests mismatch:** AudioSleuth halts immediately and raises an `INTEGRITY_MISMATCH` alert, refusing to process tampered evidence.

### What SHA-256 Does NOT Prove
> [!IMPORTANT]
> **Forensic Distinction: Storage Integrity $\neq$ Pre-Acquisition Authenticity**  
> A matching hash proves that the file in the evidence vault is **byte-for-byte identical** to the file uploaded during intake. It does **not** prove:
> - Who created or recorded the audio.
> - Whether the audio was edited, spliced, or synthesized **before** the investigator received it.
> - What microphone was used or where the recording took place.

---

## 4. Case Management, Evidence Association & Audit Trails

### Relational Hierarchy (Custodial Structure)
To avoid orphaned evidence or lost chain-of-custody records, AudioSleuth enforces a strict relational structure in SQLite:

```
[Forensic Case] (CASE-YYYYMMDD-xxxxxx)
  │  ├── Title, Assigned Investigator, Notes/Description, Status (active/closed)
  │
  ├──► [Evidence Items] (EVD-YYYYMMDD-xxxxxx)
  │      ├── Original Filename, Stored Filename, File Size, SHA-256 Hash, Format
  │
  ├──► [Audit Trail] (EVT-YYYYMMDD-xxxxxx)
  │      ├── Timestamp (UTC), Action, Outcome, Evidence ID, Detailed Parameters
  │
  └──► [Cross-Recording Comparisons] (COMP-YYYYMMDD-xxxxxx)
         ├── Evidence A & B, Case A & B, Metrics Summary, Similarity Score
```

### Case Status Lifecycle & The Closed-Case Lock
A forensic case has two primary states:
1. `active`: Evidence can be ingested, analyzed, compared, and reported on.
2. `closed`: Represents formal case finality.
   - **Enforced Security Rule:** Once a case is closed, all subsequent evidence upload attempts are rejected with `HTTP 400 Bad Request` (`CASE_CLOSED`).
   - To add new evidence, an investigator must explicitly reopen the case with a documented reason, which emits a durable `case_reopened` audit event.

### Structured Audit Trail
The `audit_events` table permanently logs forensic actions:
- `case_created`, `case_updated`, `case_closed`, `case_reopened`
- `evidence_uploaded`, `integrity_verified`, `metadata_inspected`
- `signal_analyzed`, `evidence_compared`, `report_generated`

**Sanitization Policy:** To preserve database performance and avoid evidentiary leakage, audit records store metadata, IDs, thresholds, and counts—never raw audio buffers, decoded sample arrays, or memory addresses.

---

## 5. Audio Formats: WAV vs. FLAC vs. MP3

| Characteristic | WAV (Waveform Audio File Format) | FLAC (Free Lossless Audio Codec) | MP3 (MPEG-1/2 Audio Layer III) |
| :--- | :--- | :--- | :--- |
| **Compression** | Uncompressed (Raw PCM) | Lossless Compressed | Lossy Psychoacoustic Compressed |
| **Data Preservation** | Exact physical acoustic samples stored directly as integers or IEEE floats. | Mathematically compresses data (like ZIP for audio) with zero loss of sample values. | Discards acoustic frequencies deemed inaudible to human ears via psychoacoustic masking. |
| **File Size** | Very large (~10 MB per minute of 44.1 kHz 16-bit stereo). | Moderate (~50-60% of WAV size). | Small (~10% of WAV size, e.g., 128-320 kbps). |
| **Bit Depth** | Definite (8, 16, 24, 32-bit). | Definite (16, 24-bit). | **None / Variable** (Decoded as floating-point sub-band values). |
| **Forensic Utility** | **Gold Standard:** Preserves every transient edge, micro-spike, and ambient noise floor without codec artifacts. | Excellent: Full sample-level reconstruction without quantization loss. | Requires Caution: Codec quantization frames (576 or 1152 samples) introduce artificial high-frequency cuts and transient smearing. |

---

## 6. Acoustic & Signal Processing Fundamentals

### 1. Sample Rate ($f_s$) and the Nyquist-Shannon Theorem
Audio is an analog continuous wave. To store it digitally, it must be sampled at discrete intervals:
- **Sample Rate ($f_s$):** Number of samples captured per second (e.g., 44,100 Hz for CD quality, 48,000 Hz for broadcast).
- **Nyquist-Shannon Sampling Theorem:** To accurately reconstruct an analog frequency $f_{\max}$ without aliasing distortion, the sample rate must be strictly greater than twice the highest frequency:
  $$f_s > 2 \cdot f_{\max} \implies f_{\text{Nyquist}} = \frac{f_s}{2}$$
  For $f_s = 44,100\text{ Hz}$, the Nyquist ceiling is $22,050\text{ Hz}$ (covering the full range of human hearing, 20 Hz to 20,000 Hz).

### 2. Channels & Duration
- **Channels:** Single microphone = Mono (1 channel); Left + Right microphones = Stereo (2 channels).
- **Total Samples:** For a 30.0s stereo recording at 44.1 kHz:
  $$N_{\text{total}} = 30.0 \cdot 44,100 \cdot 2 = 2,646,000 \text{ channel samples (1,323,000 sample frames)}$$

### 3. Amplitude & Root Mean Square (RMS) Energy
- **Sample Amplitude ($x[n]$):** Normalized to $[-1.0, 1.0]$. Peak amplitude is $\max |x[n]|$.
- **RMS Energy:** Quantifies the perceived power / loudness over a window of $N$ samples:
  $$\text{RMS} = \sqrt{\frac{1}{N} \sum_{i=1}^N x[i]^2}$$
  Unlike peak amplitude (which only measures an instantaneous transient), RMS measures continuous acoustic energy.

### 4. Fast Fourier Transform (FFT) vs. Short-Time Fourier Transform (STFT)
- **Time Domain vs. Frequency Domain:** A standard waveform shows amplitude over time ($x(t)$), but reveals nothing about which musical notes or vocal formants are present.
- **FFT (Fast Fourier Transform):** Converts a time-domain signal into its frequency components ($X(f)$), showing which frequencies have the most power. However, standard FFT loses temporal information (you know a 1,000 Hz tone occurred, but not *when*).
- **STFT (Short-Time Fourier Transform):** Solves this by sliding a small window (e.g., Hann window of 1,024 samples) across the audio and computing the FFT for each frame. This produces a **Time-Frequency Spectrogram** ($X(t, f)$), showing how frequency energy evolves across time.

---

## 7. Mathematical Formulations of Phase 4 Anomaly Detectors

AudioSleuth avoids unexplainable machine learning and implements three transparent, deterministic detectors:

### Detector A: Silence & Low-Energy Interval Detection (`silence.py`)
- **Forensic Objective:** Identify suspicious acoustic dropouts, digital muting, or cut segments where microphone background noise drops unnaturally.
- **Algorithm:**
  1. Partitions audio into sliding frames of length $W$ (default: 50 ms / 0.05s) advancing by hop size $H$ (default: 25 ms / 0.025s).
  2. For stereo audio, squares amplitudes across channels before averaging:
     $$\text{RMS}_m = \sqrt{\frac{1}{W \cdot C} \sum_{c=1}^C \sum_{i=1}^W x_c[m \cdot H + i]^2}$$
  3. Identifies contiguous sequences of frames where $\text{RMS}_m < \text{Threshold}$ (default: 0.01 / ~-40 dB).
  4. Discards intervals shorter than `min_silence_duration_seconds` (default: 0.25s).
- **Priority Classification:**
  - **Medium Priority:** True digital zero ($\text{min RMS} < 10^{-6}$ for $\ge 1.0\text{s}$) or prolonged silence ($\ge 3.0\text{s}$). Natural acoustic environments always possess ambient noise floors (room tone, thermal mic hiss); exact digital zero indicates synthetic muting or padding.
  - **Low Priority:** Natural speech pauses or ambient acoustic dropouts ($< 3.0\text{s}$).

---

### Detector B: Abrupt Amplitude Discontinuity Detection (`transitions.py`)
- **Forensic Objective:** Detect splice points, edited waveform cuts, buffer dropouts, or clicks caused by joining non-phase-aligned audio clips.
- **Algorithm:**
  1. Computes instantaneous adjacent-sample absolute differences across all channels:
     $$\Delta x[n] = \max_{c} \lvert x_c[n] - x_c[n-1] \rvert$$
  2. Flags sample indices where $\Delta x[n] \ge \text{Threshold}$ (default: 0.35 in normalized range $[0.0, 1.0]$).
  3. **Temporal Suppression (Clustering):** A single physical transient or ringing wave can cross the threshold multiple times within milliseconds. The detector clusters candidate spikes within `min_separation_seconds` (default: 50 ms) and retains only the single largest peak per cluster.
- **Priority Classification:**
  - **High Priority ($\ge 0.70$):** Severe step jump, characteristic of hard edit splices or severe buffer loss.
  - **Medium Priority ($\ge 0.45$):** Moderate step exceeding typical speech formant gradients.
  - **Low Priority ($< 0.45$):** Mild step consistent with plosive consonants (/p/, /b/, /t/) or percussive attacks.

---

### Detector C: STFT Spectral Flux Anomaly Detection (`spectral.py`)
- **Forensic Objective:** Detect sudden acoustic scene changes, room acoustic transitions, or spliced background noise profiles.
- **Algorithm:**
  1. Computes STFT magnitude spectrum matrix $X(t, k)$ with Hann windowing (default $N_{\text{fft}} = 1024$, hop $= 256$).
  2. **Volume Invariance (L2 Normalization):** To ensure the detector measures changes in *frequency distribution* rather than simple volume changes, each frame's magnitude vector is normalized to unit length:
     $$X_{\text{norm}}(t, k) = \frac{X(t, k)}{\sqrt{\sum_j X(t, j)^2} + \epsilon}$$
  3. **Euclidean Spectral Distance:** Computes the distance between consecutive normalized frames:
     $$SF(t) = \sqrt{\sum_k \left(X_{\text{norm}}(t, k) - X_{\text{norm}}(t-1, k)\right)^2}$$
  4. Flags frames where $SF(t) \ge \text{Threshold}$ (default: 0.40) and applies temporal suppression clustering (default: 100 ms).
- **Priority Classification:**
  - **High Priority ($\ge 0.85$):** Drastic reallocation of frequency spectrum energy; characteristic of spliced recordings or background scene changes.
  - **Medium Priority ($\ge 0.60$):** Moderate spectral change exceeding smooth vocal transitions.
  - **Low Priority ($< 0.60$):** Natural acoustic onsets, consonant attacks, or musical chord changes.

---

## 8. Cross-Recording Comparison Metrics & Scoring Formula

When comparing two evidence recordings ($A$ and $B$), AudioSleuth evaluates four dimensions:

### 1. Envelope Pearson Linear Correlation ($r_{\text{envelope}}$)
Extracts downsampled macro-amplitude envelopes $\mathbf{e}_A$ and $\mathbf{e}_B$ (500 points) and calculates Pearson's correlation coefficient:
$$r = \frac{\sum_{i} (e_{A,i} - \bar{e}_A)(e_{B,i} - \bar{e}_B)}{\sqrt{\sum_{i} (e_{A,i} - \bar{e}_A)^2} \sqrt{\sum_{i} (e_{B,i} - \bar{e}_B)^2}} \in [-1.0, 1.0]$$
Measures whether dynamic loudness swells and pauses align in time.

### 2. Spectral Cosine Similarity ($S_{\text{spec}}$)
Computes mean STFT power spectrum profiles $\mathbf{P}_A$ and $\mathbf{P}_B$, interpolates them onto a shared frequency grid up to the lower Nyquist ceiling ($\min(f_{s,A}/2, f_{s,B}/2)$), and calculates the normalized cosine angle:
$$S_{\text{spec}} = \frac{\mathbf{P}_A \cdot \mathbf{P}_B}{\|\mathbf{P}_A\|_2 \|\mathbf{P}_B\|_2} \in [0.0, 1.0]$$
Measures overall harmonic balance and frequency distribution alignment regardless of volume.

### 3. Transparent Composite Similarity Formula
AudioSleuth does **not** use a black-box neural network. The similarity index is computed from documented, weighted components:

$$\text{Similarity Score} = 0.50 \cdot S_{\text{spec}} + 0.30 \cdot \max(0, r_{\text{envelope}}) + 0.20 \cdot \max\left(0, 1 - \frac{|\Delta t|}{\max(t_A, t_B)}\right)$$

- **Weight Rationale:**
  - $50\%$ on Spectral Profile ($S_{\text{spec}}$): Frequency characteristics represent the acoustic signature of voice and environment.
  - $30\%$ on Dynamics Correlation ($r_{\text{envelope}}$): Loudness envelopes track timing and cadence.
  - $20\%$ on Duration Alignment ($|\Delta t|$): Accounts for length disparities.

#### Classification Labels
- **Byte-Identical Duplicate:** SHA-256 hashes match identically (Score: 1.0000).
- **Very High Acoustic Similarity:** Score $\ge 0.92$, $S_{\text{spec}} \ge 0.95$, and $\Delta t \le 0.05$s (typical of container re-encoding).
- **Moderate Similarity:** Score $\ge 0.70$ (shares general acoustic or vocal profile, but differs in timing or dynamics).
- **Divergent Acoustic Profiles:** Score $< 0.70$ (distinct audio contents).

---

## 9. Architectural Breakdown & Module Interactions

```
  React 19 Frontend (Vite + Tailwind v4)
       │
       ▼ (Axios HTTP / REST API)
  FastAPI Backend (Port 8000)
       │
       ├──► api/routes/          # Endpoint definitions & request routing
       │      ├── cases.py       # Case CRUD, status lock, evidence upload
       │      ├── evidence.py    # Evidence listing, inspection, verify-integrity
       │      ├── comparison.py  # Cross-recording comparison & comparison PDF
       │      ├── reports.py     # Individual evidence PDF report compilation
       │      ├── audit.py       # Global audit query endpoints
       │      └── health.py      # Subsystem health diagnostics
       │
       ├──► services/            # Business logic orchestration
       │      ├── case_service.py
       │      ├── evidence_service.py
       │      ├── comparison_service.py
       │      ├── report_service.py
       │      └── audit_service.py
       │
       ├──► analysis/            # Pure signal processing (independent of HTTP)
       │      ├── silence.py     # RMS windowed silence detection
       │      ├── transitions.py # Sample-delta discontinuity detector
       │      ├── spectral.py    # STFT spectral flux anomaly detector
       │      └── metadata.py    # Container properties & embedded tags
       │
       ├──► repositories/        # SQLite persistence layer
       │      ├── database.py    # SQLite connection engine & schema migrations
       │      ├── case_repository.py
       │      ├── evidence_repository.py
       │      ├── comparison_repository.py
       │      └── audit_repository.py
       │
       └──► reports/             # PDF compilation engines
              ├── pdf_generator.py            # Evidence examination report
              ├── comparison_pdf_generator.py # Cross-comparison examination report
              └── chart_generator.py          # In-memory Pillow/ReportLab chart renderer
```

---

## 10. PDF Report Generation with ReportLab

### In-Memory Compilation (Zero Disk Pollution)
Forensic workstations must avoid creating temporary, unmanaged files on disk that could confuse evidence auditing. AudioSleuth generates all PDF reports entirely in RAM:
1. Chart generation (`chart_generator.py`) renders waveform envelopes and spectrogram heatmaps into `io.BytesIO` streams using Pillow (`PIL.Image`).
2. `SimpleDocTemplate` and `NumberedCanvas` compile running headers, footers, tables, and embedded images.
3. The resulting document is streamed directly as an HTTP response (`application/pdf`) with `Content-Disposition: attachment`.
4. The generation event, options, and findings count are immediately logged into the `audit_events` SQLite table.

---

## 11. Scientific & Legal Limitations (ISO/IEC 27037)

During an academic viva or courtroom defense, an investigator must speak with precision. AudioSleuth explicitly documents the following limitations:

1. **Screening Tool, Not a Final Legal Verdict:** Flagged anomaly intervals are mathematical screening indicators. Natural human speech acoustics routinely produce signal patterns that cross thresholds: plosive consonants (/p/, /k/) cause amplitude steps, vocal pauses trigger silence intervals, and abrupt speaker phonations cause spectral flux spikes.
2. **Environmental & Codec Factors:** Lossy compression (MP3 sub-band quantization), room reverberation, microphone handling, and automatic gain control (AGC) frequently trigger anomaly indicators.
3. **No Automated "Deepfake" Claims:** AudioSleuth intentionally avoids unverified claims of "AI deepfake detection" or binary "authentic vs. fake" verdicts without evaluated, validated machine learning models.
4. **Unsigned Document Notice:** Unless digitally signed with an external PKI certificate, generated PDF reports represent investigative assistance documents rather than legally certified instruments.

---

## 12. Key Files Reference

| File Path | Role and Key Responsibilities |
| :--- | :--- |
| `backend/app/main.py` | FastAPI application factory, CORS setup, logging middleware, error handlers. |
| `backend/app/core/config.py` | Runtime configuration (upload limits, audio bounds, database URL, CORS). |
| `backend/app/evidence/storage.py` | Safe file storage, filename sanitization, SHA-256 intake calculation. |
| `backend/app/evidence/integrity.py` | Disk hash re-calculation and constant-time integrity verification. |
| `backend/app/analysis/silence.py` | Sliding RMS energy calculation and low-energy interval detection. |
| `backend/app/analysis/transitions.py` | Adjacent-sample step delta discontinuity detector and temporal clustering. |
| `backend/app/analysis/spectral.py` | STFT Normalized Spectral Flux anomaly detector. |
| `backend/app/services/comparison_service.py` | 4-dimension cross-recording comparison engine and composite score calculation. |
| `backend/app/reports/pdf_generator.py` | Two-pass ReportLab PDF generator for individual evidence examinations. |
| `backend/app/reports/comparison_pdf_generator.py` | ReportLab PDF generator for cross-recording comparison examinations. |
| `backend/app/repositories/database.py` | SQLite connection factory, WAL mode, schema initialization, safe migrations. |
| `frontend/src/pages/AudioInspectionPage.tsx` | Interactive inspection workspace with audio player, Plotly charts, and findings table. |
| `frontend/src/pages/CrossComparisonPage.tsx` | Side-by-side comparative examination UI with metric cards and anomaly distributions. |
| `frontend/src/pages/NewInvestigationPage.tsx` | Case creation, drag-and-drop evidence upload, intake hash display. |
| `frontend/src/pages/CaseHistoryPage.tsx` | Case history list, status toggle (`active`/`closed`), modal case editing, audit viewer. |
