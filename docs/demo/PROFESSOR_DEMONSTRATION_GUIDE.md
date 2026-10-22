# AudioSleuth — Live Professor Demonstration & Viva Defense Guide

**Project:** AudioSleuth — Digital Audio Forensics Toolkit  
**Academic Subject:** Cyber Security and Digital Forensics (CSDF) Lab  
**Institution:** Pune Institute of Computer Technology (PICT), SPPU  
**Author / Presenter:** Final Year Computer Engineering Student  
**Target Duration:** 8 to 10 Minutes  
**Demonstration Scope:** Live End-to-End Walkthrough, Forensic Verification, and Professor Viva Defense  

---

## 1. Demonstration Setup & Pre-Flight Checklist

Before calling the professor to your workstation, verify these three conditions:

1. **Backend Server Running:**
   - Terminal 1: `python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload`
   - Health Check: Open [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health) and confirm `"status": "healthy"`.
2. **Frontend Running:**
   - Terminal 2: `npm run dev` in `frontend/`
   - Open browser at [http://localhost:5173/](http://localhost:5173/).
3. **Downloads Test Files Ready:**
   - `C:\Users\abhin\Downloads\sample-audio-30s-16bit-44khz.wav` (5.29 MB)
   - `C:\Users\abhin\Downloads\sample-500kb.mp3` (500 KB)

---

## 2. Minute-by-Minute Demonstration Timeline (8–10 Minutes)

| Time | Phase | Target Screen / UI | Key Message / Action |
| :---: | :--- | :--- | :--- |
| **0:00 – 1:00** | Introduction & Motivation | Dashboard (`/`) | Problem of digital audio tampering, unverified "deepfake" claims, and need for local-first forensic workstations. |
| **1:00 – 2:15** | Case Ingestion & SHA-256 Hashing | New Investigation (`/cases/new`) | Create case, upload WAV and MP3, show instant cryptographic intake digest calculation. |
| **2:15 – 3:30** | Evidence Integrity & Non-Destructive Storage | New Investigation & Cases (`/cases`) | Show safe `.bin` vault storage, verify SHA-256 integrity, demonstrate the closed-case upload lock. |
| **3:30 – 5:00** | Non-Destructive Signal Inspection | Audio Inspection (`/evidence/:id`) | Show interactive player (HTTP 206), min/max envelope waveform, STFT spectrogram (dB), FFT spectrum with dominant tone. |
| **5:00 – 6:30** | Explainable Anomaly Detection | Findings Section | Show RMS silence detection, amplitude discontinuity detector, STFT spectral flux anomalies. Test seek-to-timestamp. |
| **6:30 – 7:45** | Cross-Recording Comparison | Cross-Comparison (`/compare`) | Compare WAV vs MP3, explain transparent formula (Score: 60.3%), envelope correlation, spectral cosine similarity. |
| **7:45 – 8:45** | Court-Ready PDF Reports & Audit Trail | PDF Viewer & Audit Trail Modal | Open generated PDF report with charts, show durable chronological audit log in SQLite. |
| **8:45 – 9:30** | Conclusion & Defense Transition | System Status (`/status`) | Summarize ISO/IEC 27037 compliance, test suite results (79 passed tests), transition to viva questions. |

---

## 3. Step-by-Step Spoken Script & Screen Actions

### Step 1: Introduction & Problem Statement (0:00 – 1:00)
**Action:** Open browser at `http://localhost:5173/` (Dashboard).

**Spoken Script:**
> *"Respected Professor, good morning. Today I am presenting my CSDF mini-project: **AudioSleuth — Digital Audio Forensics Toolkit**.*  
> *In digital forensics, audio recordings like voice calls, witness statements, and sting operations are often submitted as digital evidence. However, audio is notoriously easy to edit using tools like Audacity, where words can be deleted or spliced in seconds.*  
> *Existing solutions either make unscientific claims about 'AI deepfakes' without explainability, or require uploading confidential recordings to external cloud services. AudioSleuth solves this as a **100% local-first, explainable forensic toolkit** designed according to ISO/IEC 27037 standards for digital evidence handling.*  
> *It combines evidence custody, cryptographic SHA-256 integrity verification, explainable signal processing anomaly detection, cross-recording comparisons, and automated PDF reporting."*

---

### Step 2: Case Creation & Cryptographic Intake (1:00 – 2:15)
**Action:** Click **"New Investigation"** on the sidebar.
- Case Title: `Homicide Inquiry Audio Audit`
- Investigator: `PICT CSDF Examiner`
- Notes: `Forensic examination of intercepted voice recordings.`
- Click **"Initialize Forensic Case"**.

**Spoken Script:**
> *"In digital forensics, evidence cannot exist in isolation without chain of custody. Here, we first establish a formal investigation case.*  
> *Once the case is created, we ingest our first piece of digital evidence: a 30-second 44.1 kHz WAV recording from our Downloads folder.*  
> *(Drag and drop `sample-audio-30s-16bit-44khz.wav`)*  
> *Notice what happens immediately upon intake: AudioSleuth streams the raw uploaded bytes through a SHA-256 hashing engine, computing this 64-character hexadecimal digest ending in `...038928e9`.*  
> *The original file in our Downloads folder is completely untouched. In the backend evidence vault, the evidence is renamed to a safe identifier with a `.bin` extension to prevent accidental execution or path traversal."*

---

### Step 3: Integrity Verification & Closed-Case Security (2:15 – 3:30)
**Action:** Also ingest `sample-500kb.mp3`. Click **"Verify Storage Integrity"**.
Then go to **"Cases"**, click the lock icon to close the case, and explain the upload lock.

**Spoken Script:**
> *"Now we verify the evidence. When I click 'Verify Storage Integrity', AudioSleuth re-reads the physical file from disk and recalculates its SHA-256 digest in real time.*  
> *Because both hashes match, the system confirms storage integrity. However, as an investigator, we must note: **a matching hash confirms byte-level storage consistency; it does not prove the recording was authentic before acquisition**.*  
> *Next, notice our case workflow protection: if an examiner marks a case as 'Closed', the database locks the case. Any subsequent attempt to upload evidence is rejected by the API with HTTP 400 `CASE_CLOSED`. This guarantees case finality until an examiner explicitly reopens it with a documented reason."*

---

### Step 4: Non-Destructive Audio Inspection & Signal Visualizations (3:30 – 5:00)
**Action:** Reopen the case and click **"Inspect"** on the WAV evidence item. The `/evidence/:id` workspace opens.
- Click **Play** for 2-3 seconds, scrub the seeker bar.
- Point to the Waveform, Spectrogram, and Power Spectrum.

**Spoken Script:**
> *"Now we enter the Audio Inspection Workspace. Audio is decoded non-destructively in RAM using temporary NumPy float32 arrays; the original file is never altered.*  
> *We have three acoustic signal representations:*  
> 1. *First is the **Downsampled Min/Max Envelope Waveform**. Rather than discarding samples arbitrarily, we divide the 1.32 million samples into 1,000 bins and preserve the absolute minimum and maximum values in every bin. This ensures brief transient spikes or clicks are never lost.*  
> 2. *Second is the **Time-Frequency Spectrogram** computed via Short-Time Fourier Transform (STFT) with a Hann window. It shows acoustic frequency power in decibels across time.*  
> 3. *Third is the **Calibrated FFT Power Spectrum**. Here we see frequencies up to the 22,050 Hz Nyquist ceiling, and the system automatically isolates the dominant fundamental frequency: exactly 196 Hz, which corresponds to the G3 bass note of this acoustic recording."*

---

### Step 5: Explainable Signal Anomaly Detection (5:00 – 6:30)
**Action:** Scroll down to **"Explainable Signal Anomaly Detection"**. Click **"Run Forensic Analysis"**.
- Show the 52 findings summary.
- Filter by category and priority.
- Click **"Jump to Time"** on finding #1 to navigate the audio player to 0.50s.

**Spoken Script:**
> *"Instead of an unverified black-box neural network, AudioSleuth runs three explainable signal-processing detectors based on standard mathematical principles:*  
> 1. ***RMS Silence Detector:** Calculates sliding window Root Mean Square energy. If energy drops below 0.01 (~-40 dB) for more than 250 milliseconds, it flags a potential muting or cutting interval. In this recording, natural audio continues throughout, so zero false-positive silence intervals were reported.*  
> 2. ***Amplitude Discontinuity Detector:** Evaluates instantaneous adjacent-sample absolute differences ($|\Delta x[n]|$). Splice edits cause sharp vertical jumps exceeding 0.35. We also apply temporal suppression clustering so a single transient isn't reported five times.*  
> 3. ***STFT Spectral Flux Detector:** Measures the Euclidean distance between consecutive L2-normalized frequency magnitude vectors. It isolates moments where frequency energy is abruptly reallocated. In this recording, 52 natural harmonic transitions were flagged.*  
> *When I click 'Jump to Time', the audio player instantly seeks to that exact millisecond so the examiner can audition the transition."*

---

### Step 6: Cross-Recording Comparison (6:30 – 7:45)
**Action:** Navigate to **"Cross-Comparison"** (`/compare`).
- Select Recording A: `sample-audio-30s-16bit-44khz.wav`
- Select Recording B: `sample-500kb.mp3`
- Click **"Execute Forensic Comparison"**.

**Spoken Script:**
> *"In forensic casework, an investigator often needs to compare an unknown recording against an authentic reference copy.*  
> *Here we compare our WAV file against the MP3 file across four dimensions:*  
> 1. ***Metadata & Container:** Both share an identical 30.00-second duration and 44.1 kHz sample rate, but their hashes differ because one is uncompressed PCM and the other is lossy MP3.*  
> 2. ***Dynamics:** We compare RMS energy ratio (6.95 dB delta), Crest Factor, Zero Crossing Rate, and Pearson Envelope Correlation ($r = 0.5398$).*  
> 3. ***Spectral Profile:** We compute the STFT Spectral Cosine Similarity ($S_{\text{spec}} = 0.4826$) mapped up to the lower Nyquist ceiling.*  
> 4. ***Transparent Scoring Formula:** AudioSleuth computes a transparent similarity score: $50\%$ on spectral cosine similarity, $30\%$ on envelope correlation, and $20\%$ on duration alignment. The resulting score is **60.32%**, classified as **`Divergent Acoustic Profiles`**.*  
> *This comparison is permanently saved in SQLite and can be retrieved at any time."*

---

### Step 7: Court-Ready PDF Reports & Audit Trail (7:45 – 8:45)
**Action:** Click **"Download Comparison PDF Report"** (or open the previously downloaded PDF).
Then go to **Cases**, open the **Audit Trail Modal**.

**Spoken Script:**
> *"To present findings in court, AudioSleuth compiles automated, evidence-based PDF examination reports using ReportLab.*  
> *Notice that charts, metadata, findings tables, and ISO/IEC 27037 forensic disclaimers are compiled entirely in memory—zero unmanaged temporary files are created on disk.*  
> *Finally, here is our **Durable Audit Log**. Every single action—case creation, evidence upload, hash check, signal analysis, comparison, and report export—is recorded in SQLite with UTC timestamps and examiner identifiers. This provides complete application-level accountability."*

---

### Step 8: Conclusion (8:45 – 9:30)
**Action:** Navigate to **"System Status"** (`/status`).

**Spoken Script:**
> *"To conclude, AudioSleuth is fully operational across all planned milestones from Phase 1 to Phase 6B.*  
> *Our backend test suite has **79 out of 79 automated tests passing**, and the frontend builds cleanly with zero TypeScript errors.*  
> *Most importantly, AudioSleuth adheres to the fundamental principle of digital forensics: **it produces reproducible, mathematically explainable measurements, preserves evidence integrity, and distinguishes objective observations from subjective conclusions**.*  
> *Thank you, Professor. I am now ready for your questions."*

---

## 4. Likely Professor Viva Questions & Answers

### Fundamental Questions

#### Q1: "What is the purpose of computing SHA-256 at intake, and does a matching hash prove the audio is genuine?"
**Answer:**  
> *"SHA-256 computes a 256-bit cryptographic digest from the file's raw bytes. Its purpose is **evidence integrity verification**—proving that the file stored in our custody has not suffered bit rot, accidental editing, or disk tampering since the moment it was acquired.*  
> *However, **a matching hash does not prove the recording is genuine or authentic**. A file that was manipulated or synthesized prior to acquisition will still have a valid, matching SHA-256 hash. Hashing proves storage integrity, not pre-acquisition authenticity."*

#### Q2: "What is the difference between FFT and STFT?"
**Answer:**  
> *"Standard FFT (Fast Fourier Transform) takes an entire audio signal and converts it into the frequency domain. It tells us what frequencies exist across the whole recording, but discards time information—we don't know when a frequency occurred.*  
> *STFT (Short-Time Fourier Transform) slides a small window (such as a 1,024-sample Hann window) across the audio in steps (hop length) and computes the FFT for each frame. This gives us a 2D matrix of frequency power over time, which allows us to render the time-frequency spectrogram and track when acoustic events occurred."*

#### Q3: "What is Root Mean Square (RMS) energy, and why is it better than peak amplitude for detecting silence?"
**Answer:**  
> *"Peak amplitude only measures the single highest sample point in a window. A loud pop or click lasting 1 sample could make peak amplitude 1.0 even if the rest of the window is complete silence.*  
> *RMS energy is the square root of the mean of squared sample values ($\sqrt{\frac{1}{N}\sum x_i^2}$). It measures continuous acoustic energy over the entire frame, which directly corresponds to perceived loudness and prevents single transient spikes from obscuring silence."*

#### Q4: "Why does the MP3 file have `bit_depth: null` while WAV has `bit_depth: 16`?"
**Answer:**  
> *"WAV files store uncompressed PCM samples with an explicit quantization bit depth (e.g., 16-bit signed integer or 24-bit).*  
> *MP3 is a lossy psychoacoustic format. It uses sub-band filtering and MDCT (Modified Discrete Cosine Transform) with floating-point quantization factors. It does not store samples in fixed-bit integers. Fabricating a bit depth like '16-bit' for an MP3 would be forensically inaccurate. AudioSleuth strictly adheres to truth-in-evidence by reporting lossy formats as null/Lossy."*

#### Q5: "What is Zero Crossing Rate (ZCR) and why was it higher in the MP3 file?"
**Answer:**  
> *"Zero Crossing Rate measures how many times the audio waveform changes sign (crosses zero amplitude) per second. It correlates with high-frequency acoustic content and noise.*  
> *In our comparison, the MP3 had a ZCR of 1,557 crossings/s compared to 686 crossings/s for the WAV because the MP3 sample contained high-frequency percussion and harmonic treble energy around 1,046 Hz, whereas the WAV audio was dominated by low-frequency bass formants around 196 Hz."*

---

### Advanced / Challenging Viva Questions

#### Q6: "Why did you implement explainable signal anomaly detectors instead of training a deep learning AI model for deepfake detection?"
**Answer:**  
> *"In a legal and forensic context, **explainability and reproducibility are paramount under evidentiary standards like Daubert and ISO/IEC 27037**. Deep learning models are notoriously prone to dataset overfitting: a neural network trained on one synthetic voice generator will completely fail on another, or produce high confidence false positives on noisy microphone recordings without explaining why.*  
> *By using RMS energy, sample-delta discontinuities, and STFT spectral flux, every single finding AudioSleuth produces is backed by a verifiable mathematical equation, a localized timestamp, and a configurable threshold that an independent expert witness can reproduce in any standard laboratory."*

#### Q7: "Can someone tamper with your SQLite database or audit log?"
**Answer:**  
> *"In our local development architecture, SQLite provides relational persistence and structured audit logging for application-level accountability. However, as documented in our ISO/IEC 27037 disclosure, **a standard SQLite file on disk is not a cryptographically anchored WORM (Write Once, Read Many) drive or blockchain**.*  
> *In a certified forensic laboratory, AudioSleuth's SQLite database must be coupled with physical write-blocked evidence drives, signed audit log exports, and external cryptographic timestamps. For future production hardening, we have planned HMAC-chained audit log hashing."*

#### Q8: "How does your cross-recording comparison handle audio files that have different sample rates?"
**Answer:**  
> *"If Recording A is sampled at 44,100 Hz (Nyquist: 22,050 Hz) and Recording B is sampled at 16,000 Hz (Nyquist: 8,000 Hz), comparing them naively would cause severe frequency bin misalignment.*  
> *AudioSleuth solves this by identifying the **minimum shared Nyquist ceiling** ($\min(f_{s,A}/2, f_{s,B}/2) = 8,000\text{ Hz}$) and interpolating both recordings' mean STFT power spectrum profiles onto a shared 512-point frequency grid up to that ceiling. This allows mathematically sound spectral cosine similarity without creating artificial out-of-band artifacts."*

#### Q9: "What causes false positives in your Spectral Flux detector?"
**Answer:**  
> *"Spectral flux measures the Euclidean distance between consecutive L2-normalized STFT magnitude vectors. Any rapid redistribution of frequency energy causes a peak.*  
> *In natural human speech, plosive consonants like /p/, /t/, and /k/, sharp vocal inflections, or background door closes cause sudden spectral redistribution, triggering low or medium priority flux findings.*  
> *That is why AudioSleuth explicitly classifies findings by priority and includes an evidentiary disclaimer: **findings are screening indicators for manual examiner review, never automated proof of tampering**."*

#### Q10: "How did you ensure that long audio recordings do not exhaust server memory?"
**Answer:**  
> *"AudioSleuth enforces strict resource ceilings in `backend/app/core/config.py`:*  
> - *Maximum upload size is bounded at 100 MB (`MAX_UPLOAD_SIZE_MB`).*  
> - *Maximum decoded duration is restricted to 1,800 seconds (30 minutes).*  
> - *Waveform rendering uses a configurable point budget (default 1,000 points, max 10,000), using min/max chunking rather than sending raw millions of samples to the browser.*  
> - *Spectrogram time frames and frequency bins are capped at 1,000 frames and 512 bins, preventing browser DOM freezing and excessive GPU texture memory consumption."*

---

## 5. Technical Highlights to Emphasize to the Professor

1. **Non-Destructive In-Memory Architecture:** Original files in `backend/data/evidence/` are never overwritten; audio processing runs on temporary NumPy float32 arrays.
2. **Zero-Pollution PDF Generation:** Waveforms and spectrograms are rendered directly into RAM buffers (`io.BytesIO`) using Pillow and ReportLab without cluttering disk storage.
3. **HTTP Range Audio Scrubbing (HTTP 206):** In-browser audio streaming supports byte-range requests, allowing immediate scrubbing across long files without waiting for full download.
4. **Comprehensive Test Suite:** 79 automated backend pytest tests and clean TypeScript compilation (`tsc -b`).
