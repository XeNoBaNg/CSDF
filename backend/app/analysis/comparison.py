"""Explainable forensic audio comparison algorithms.

Implements deterministic, mathematically grounded cross-recording comparison:
1. Signal-level statistics (peak amplitude, RMS energy, crest factor, zero crossing rate).
2. STFT spectral summaries (spectral centroid, roll-off, flatness, and normalized spectral cosine similarity).
3. Amplitude envelope correlation.
4. Anomaly timeline distribution comparison across normalized time bins.

Contains zero machine learning, black-box classifiers, or unsubstantiated source attribution.
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from scipy import signal


def compute_signal_statistics(
    samples: np.ndarray,
    sample_rate: int,
) -> Dict[str, float]:
    """Computes basic signal energy and dynamic statistics for a mono or multichannel audio array.

    Multichannel signals are downmixed to mono via channel-averaging.
    """
    if samples.size == 0 or sample_rate <= 0:
        return {
            "peak_amplitude": 0.0,
            "rms_energy": 0.0,
            "crest_factor": 0.0,
            "zero_crossing_rate": 0.0,
        }

    # Downmix to 1D mono for unified statistic evaluation
    if samples.ndim > 1:
        if samples.shape[0] < samples.shape[1] and samples.shape[0] <= 8:
            samples = samples.T
        mono = np.mean(samples, axis=-1)
    else:
        mono = samples

    mono = np.nan_to_num(mono, nan=0.0, posinf=1.0, neginf=-1.0)
    total_samples = len(mono)

    # 1. Peak amplitude (|s|_max)
    peak = float(np.max(np.abs(mono)))

    # 2. RMS energy (sqrt(mean(s^2)))
    rms = float(np.sqrt(np.mean(mono**2)))

    # 3. Crest factor (peak / RMS) - measure of dynamic peakiness
    crest_factor = float(peak / (rms + 1e-8)) if rms > 1e-8 else 1.0

    # 4. Zero Crossing Rate (fraction of sign changes per second)
    if total_samples > 1:
        zero_crossings = np.sum(np.diff(np.signbit(mono)) != 0)
        zcr = float((zero_crossings * sample_rate) / (total_samples - 1))
    else:
        zcr = 0.0

    return {
        "peak_amplitude": round(peak, 5),
        "rms_energy": round(rms, 5),
        "crest_factor": round(crest_factor, 3),
        "zero_crossing_rate": round(zcr, 2),
    }


def compute_spectral_profile(
    samples: np.ndarray,
    sample_rate: int,
    n_fft: int = 1024,
    hop_length: int = 512,
    max_freq_hz: Optional[float] = None,
) -> Dict[str, Any]:
    """Computes calibrated STFT spectral summaries:
    - Mean spectral centroid (Hz)
    - Mean spectral roll-off 85% (Hz)
    - Mean spectral flatness (Wiener entropy)
    - Average power spectral density profile across frequency bins
    """
    if samples.size == 0 or sample_rate <= 0:
        return {
            "spectral_centroid_hz": 0.0,
            "spectral_rolloff_hz": 0.0,
            "spectral_flatness": 0.0,
            "freqs": [],
            "mean_psd": [],
        }

    # Downmix to mono
    if samples.ndim > 1:
        if samples.shape[0] < samples.shape[1] and samples.shape[0] <= 8:
            samples = samples.T
        mono = np.mean(samples, axis=-1)
    else:
        mono = samples

    mono = np.nan_to_num(mono, nan=0.0, posinf=1.0, neginf=-1.0)
    total_samples = len(mono)

    effective_n_fft = min(n_fft, max(64, total_samples))
    if total_samples < effective_n_fft:
        mono = np.pad(mono, (0, effective_n_fft - total_samples), mode="constant")

    freqs, _, zxx = signal.stft(
        mono,
        fs=sample_rate,
        window="hann",
        nperseg=effective_n_fft,
        noverlap=max(0, effective_n_fft - hop_length),
        boundary=None,
        padded=True,
    )

    mag = np.abs(zxx)  # (freq_bins, time_frames)
    power = mag**2
    mean_psd = np.mean(power, axis=1)  # (freq_bins,)

    # Restrict to max_freq_hz if provided
    if max_freq_hz is not None and max_freq_hz > 0:
        valid_idx = freqs <= max_freq_hz
        if np.any(valid_idx):
            freqs = freqs[valid_idx]
            mean_psd = mean_psd[valid_idx]
            power = power[valid_idx, :]

    total_power = np.sum(mean_psd)
    eps = 1e-12

    # 1. Spectral Centroid: sum(f * P(f)) / sum(P(f))
    if total_power > eps:
        centroid = float(np.sum(freqs * mean_psd) / total_power)
    else:
        centroid = 0.0

    # 2. Spectral Roll-Off: 85% energy threshold
    if total_power > eps:
        cumulative_power = np.cumsum(mean_psd)
        rolloff_idx = np.searchsorted(cumulative_power, 0.85 * total_power)
        rolloff_idx = min(rolloff_idx, len(freqs) - 1)
        rolloff = float(freqs[rolloff_idx])
    else:
        rolloff = 0.0

    # 3. Spectral Flatness (Wiener entropy): geometric mean / arithmetic mean
    # Avoid zero division and log(0) with safe eps
    safe_psd = np.maximum(mean_psd, eps)
    geom_mean = np.exp(np.mean(np.log(safe_psd)))
    arith_mean = np.mean(safe_psd)
    flatness = float(geom_mean / (arith_mean + eps)) if arith_mean > eps else 0.0
    flatness = float(np.clip(flatness, 0.0, 1.0))

    return {
        "spectral_centroid_hz": round(centroid, 1),
        "spectral_rolloff_hz": round(rolloff, 1),
        "spectral_flatness": round(flatness, 4),
        "freqs": freqs,
        "mean_psd": mean_psd,
    }


def compare_spectral_distributions(
    profile_a: Dict[str, Any],
    profile_b: Dict[str, Any],
    num_eval_bins: int = 128,
) -> Dict[str, float]:
    """Compares two spectral profiles by interpolating their mean power spectra onto a
    common frequency grid up to the minimum shared Nyquist ceiling.

    Returns:
        - cosine_similarity: Cosine similarity between normalized spectral envelopes in [0, 1].
        - euclidean_distance: L2 distance between normalized spectral envelopes.
        - centroid_diff_hz: Absolute difference in spectral centroid.
        - rolloff_diff_hz: Absolute difference in spectral roll-off.
        - flatness_diff: Absolute difference in spectral flatness.
    """
    freqs_a = profile_a.get("freqs", np.array([]))
    psd_a = profile_a.get("mean_psd", np.array([]))
    freqs_b = profile_b.get("freqs", np.array([]))
    psd_b = profile_b.get("mean_psd", np.array([]))

    centroid_a = profile_a.get("spectral_centroid_hz", 0.0)
    centroid_b = profile_b.get("spectral_centroid_hz", 0.0)
    rolloff_a = profile_a.get("spectral_rolloff_hz", 0.0)
    rolloff_b = profile_b.get("spectral_rolloff_hz", 0.0)
    flatness_a = profile_a.get("spectral_flatness", 0.0)
    flatness_b = profile_b.get("spectral_flatness", 0.0)

    centroid_diff = abs(centroid_a - centroid_b)
    rolloff_diff = abs(rolloff_a - rolloff_b)
    flatness_diff = abs(flatness_a - flatness_b)

    if len(freqs_a) == 0 or len(freqs_b) == 0:
        return {
            "cosine_similarity": 0.0,
            "euclidean_distance": 1.0,
            "centroid_diff_hz": round(centroid_diff, 1),
            "rolloff_diff_hz": round(rolloff_diff, 1),
            "flatness_diff": round(flatness_diff, 4),
        }

    # Highest shared frequency
    max_shared_freq = min(float(freqs_a[-1]), float(freqs_b[-1]))
    if max_shared_freq <= 0:
        return {
            "cosine_similarity": 0.0,
            "euclidean_distance": 1.0,
            "centroid_diff_hz": round(centroid_diff, 1),
            "rolloff_diff_hz": round(rolloff_diff, 1),
            "flatness_diff": round(flatness_diff, 4),
        }

    # Common evaluation grid
    common_freqs = np.linspace(0, max_shared_freq, num_eval_bins)
    interp_psd_a = np.interp(common_freqs, freqs_a, psd_a)
    interp_psd_b = np.interp(common_freqs, freqs_b, psd_b)

    # Normalize each to unit L2 norm
    eps = 1e-12
    norm_a = np.linalg.norm(interp_psd_a)
    norm_b = np.linalg.norm(interp_psd_b)

    if norm_a > eps and norm_b > eps:
        vec_a = interp_psd_a / norm_a
        vec_b = interp_psd_b / norm_b
        cosine_sim = float(np.dot(vec_a, vec_b))
        cosine_sim = float(np.clip(cosine_sim, 0.0, 1.0))
        euclidean_dist = float(np.linalg.norm(vec_a - vec_b))
    else:
        cosine_sim = 1.0 if (norm_a <= eps and norm_b <= eps) else 0.0
        euclidean_dist = 0.0 if (norm_a <= eps and norm_b <= eps) else 1.0

    return {
        "cosine_similarity": round(cosine_sim, 4),
        "euclidean_distance": round(euclidean_dist, 4),
        "centroid_diff_hz": round(centroid_diff, 1),
        "rolloff_diff_hz": round(rolloff_diff, 1),
        "flatness_diff": round(flatness_diff, 4),
    }


def compute_envelope_correlation(
    samples_a: np.ndarray,
    samples_b: np.ndarray,
    num_points: int = 500,
) -> float:
    """Downsamples both signals to an amplitude envelope of `num_points` and computes
    their Pearson correlation coefficient r in [-1.0, 1.0].

    This provides a linear correlation metric of macro-level dynamic variations.
    """
    if samples_a.size == 0 or samples_b.size == 0:
        return 0.0

    def _extract_envelope(arr: np.ndarray, target_len: int) -> np.ndarray:
        if arr.ndim > 1:
            arr = np.mean(arr, axis=-1)
        arr = np.abs(arr)
        n = len(arr)
        if n == 0:
            return np.zeros(target_len)
        if n <= target_len:
            return np.interp(np.linspace(0, n - 1, target_len), np.arange(n), arr)
        # Partition into contiguous windows and take RMS envelope
        splits = np.array_split(arr, target_len)
        return np.array([float(np.sqrt(np.mean(w**2))) if len(w) > 0 else 0.0 for w in splits])

    env_a = _extract_envelope(samples_a, num_points)
    env_b = _extract_envelope(samples_b, num_points)

    std_a = np.std(env_a)
    std_b = np.std(env_b)

    if std_a > 1e-8 and std_b > 1e-8:
        corr = float(np.corrcoef(env_a, env_b)[0, 1])
        return round(float(np.clip(corr, -1.0, 1.0)), 4)
    # If both are flat (e.g. constant silence or constant DC), check if means match
    if std_a <= 1e-8 and std_b <= 1e-8:
        return 1.0 if abs(np.mean(env_a) - np.mean(env_b)) < 1e-6 else 0.0
    return 0.0


def compare_anomaly_timelines(
    findings_a: List[Any],
    duration_a: float,
    findings_b: List[Any],
    duration_b: float,
    num_bins: int = 10,
) -> Dict[str, Any]:
    """Compares the category counts and temporal distributions of Phase 4 signal anomaly findings.

    Maps timestamps into `num_bins` normalized relative time segments (0-10%, 10-20%, ...).
    """
    counts_a: Dict[str, int] = {"silence": 0, "transition": 0, "spectral": 0, "total": len(findings_a)}
    counts_b: Dict[str, int] = {"silence": 0, "transition": 0, "spectral": 0, "total": len(findings_b)}

    bins_a = [0] * num_bins
    bins_b = [0] * num_bins

    def _process_findings(findings: List[Any], duration: float, counts_dict: Dict[str, int], bins: List[int]) -> None:
        for f in findings:
            cat = getattr(f, "category", "")
            if hasattr(cat, "value"):
                cat_val = str(cat.value).lower()
            else:
                cat_val = str(cat).lower()

            if "silence" in cat_val:
                counts_dict["silence"] += 1
            elif "transition" in cat_val:
                counts_dict["transition"] += 1
            elif "spectral" in cat_val:
                counts_dict["spectral"] += 1

            start_t = getattr(f, "start_time", 0.0)
            if duration > 0:
                rel_pos = np.clip(start_t / duration, 0.0, 0.9999)
                bin_idx = int(rel_pos * num_bins)
                bins[bin_idx] += 1

    _process_findings(findings_a, duration_a, counts_a, bins_a)
    _process_findings(findings_b, duration_b, counts_b, bins_b)

    density_a = round((counts_a["total"] / (duration_a / 60.0)), 2) if duration_a > 0 else 0.0
    density_b = round((counts_b["total"] / (duration_b / 60.0)), 2) if duration_b > 0 else 0.0

    return {
        "counts_a": counts_a,
        "counts_b": counts_b,
        "density_per_minute_a": density_a,
        "density_per_minute_b": density_b,
        "binned_distribution_a": bins_a,
        "binned_distribution_b": bins_b,
        "distribution_bins": num_bins,
    }
