"""High-performance forensic audio chart generator for ReportLab PDF reports.

Renders deterministic waveform amplitude envelopes and STFT magnitude spectrogram
heatmaps directly in memory via NumPy and Pillow, ensuring zero disk overhead
and zero external display server dependencies.
"""

import io
import math
from typing import Tuple
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import scipy.signal


def _create_forensic_colormap() -> np.ndarray:
    """Builds a 256-entry RGB colormap optimized for forensic acoustic analysis.

    Transitions from deep dark blue/navy (silence floor, -80 dB) through teal,
    emerald, amber, and vibrant crimson (peak energy, 0 dB).
    """
    palette = np.zeros((256, 3), dtype=np.uint8)
    # Control anchors: (index, R, G, B)
    anchors = [
        (0, 15, 23, 42),       # -80 dB: Slate/Navy
        (48, 30, 58, 138),     # -65 dB: Deep Blue
        (96, 13, 148, 136),    # -50 dB: Teal
        (150, 34, 197, 94),    # -33 dB: Emerald Green
        (205, 234, 179, 8),    # -16 dB: Vibrant Amber
        (255, 239, 68, 68),    #   0 dB: Intense Crimson
    ]

    for i in range(len(anchors) - 1):
        idx_start, r_s, g_s, b_s = anchors[i]
        idx_end, r_e, g_e, b_e = anchors[i + 1]
        steps = idx_end - idx_start
        for step in range(steps):
            frac = step / float(steps)
            r = int(r_s + frac * (r_e - r_s))
            g = int(g_s + frac * (g_e - g_s))
            b = int(b_s + frac * (b_e - b_s))
            palette[idx_start + step] = [r, g, b]

    palette[255] = [239, 68, 68]
    return palette


_FORENSIC_PALETTE = _create_forensic_colormap()


def render_waveform_image(
    samples: np.ndarray,
    sample_rate: int,
    width: int = 1200,
    height: int = 280,
) -> bytes:
    """Renders a peak-preserving waveform envelope chart into a PNG byte stream.

    Args:
        samples: 1D or 2D floating-point audio array in [-1.0, 1.0].
        sample_rate: Audio sampling rate in Hertz.
        width: Image width in pixels.
        height: Image height in pixels.

    Returns:
        Raw bytes of the rendered PNG image.
    """
    # Mono downmix if multichannel
    if samples.ndim > 1:
        signal = np.mean(samples, axis=0)
    else:
        signal = samples

    total_samples = len(signal)
    duration_sec = total_samples / float(sample_rate) if sample_rate > 0 else 0.0

    # Layout geometry
    left_m = 70
    right_m = 30
    top_m = 40
    bottom_m = 40
    gw = max(10, width - left_m - right_m)
    gh = max(10, height - top_m - bottom_m)
    mid_y = top_m + gh // 2

    # Canvas setup
    bg_color = (15, 23, 42)      # Slate 900
    grid_color = (30, 41, 59)    # Slate 800
    zero_line_color = (51, 65, 85) # Slate 700
    wave_color = (6, 182, 212)   # Cyan 500
    text_color = (148, 163, 184) # Slate 400
    title_color = (241, 245, 249)# Slate 100

    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()

    # Draw header text
    header_text = f"Forensic Waveform Envelope (Min/Max Tracking) | Duration: {duration_sec:.3f}s | Rate: {sample_rate:,} Hz"
    draw.text((left_m, 14), header_text, fill=title_color, font=font)

    # Draw background graph box & gridlines
    draw.rectangle([left_m, top_m, left_m + gw, top_m + gh], outline=(51, 65, 85), width=1)

    # Guidelines at +1.0, +0.5, 0.0, -0.5, -1.0
    for level, label in [
        (1.0, "+1.0"),
        (0.5, "+0.5"),
        (0.0, " 0.0"),
        (-0.5, "-0.5"),
        (-1.0, "-1.0"),
    ]:
        y_pos = int(mid_y - level * (gh / 2.0))
        y_pos = max(top_m, min(top_m + gh, y_pos))
        line_col = zero_line_color if level == 0.0 else grid_color
        draw.line([(left_m, y_pos), (left_m + gw, y_pos)], fill=line_col, width=1)
        draw.text((left_m - 40, y_pos - 5), label, fill=text_color, font=font)

    # Envelope rendering: chunk samples across available pixel columns
    if total_samples > 0 and gw > 0:
        chunk_size = total_samples / float(gw)
        for col in range(gw):
            idx_start = int(col * chunk_size)
            idx_end = int((col + 1) * chunk_size)
            idx_end = max(idx_start + 1, min(total_samples, idx_end))
            slice_data = signal[idx_start:idx_end]

            if len(slice_data) > 0:
                v_min = float(np.min(slice_data))
                v_max = float(np.max(slice_data))
            else:
                v_min = 0.0
                v_max = 0.0

            y_top = int(mid_y - v_max * (gh / 2.0))
            y_bot = int(mid_y - v_min * (gh / 2.0))

            # Clamp within bounding box
            y_top = max(top_m, min(top_m + gh, y_top))
            y_bot = max(top_m, min(top_m + gh, y_bot))
            if y_top >= y_bot:
                y_bot = y_top + 1

            px_x = left_m + col
            draw.line([(px_x, y_top), (px_x, y_bot)], fill=wave_color, width=1)

    # Draw bottom time axis marks (5 points)
    num_ticks = 5
    for t_idx in range(num_ticks):
        frac = t_idx / float(num_ticks - 1)
        tick_x = int(left_m + frac * gw)
        t_sec = frac * duration_sec
        draw.line([(tick_x, top_m + gh), (tick_x, top_m + gh + 5)], fill=zero_line_color, width=1)
        lbl = f"{t_sec:.2f}s"
        draw.text((tick_x - 12, top_m + gh + 8), lbl, fill=text_color, font=font)

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def render_spectrogram_image(
    samples: np.ndarray,
    sample_rate: int,
    width: int = 1200,
    height: int = 360,
    n_fft: int = 1024,
    hop_length: int = 256,
) -> bytes:
    """Renders a calibrated STFT magnitude spectrogram into a PNG byte stream.

    Args:
        samples: 1D or 2D floating-point audio array.
        sample_rate: Sampling frequency in Hertz.
        width: Canvas width in pixels.
        height: Canvas height in pixels.
        n_fft: Window length for STFT.
        hop_length: Hop stride between successive STFT frames.

    Returns:
        Raw bytes of the rendered PNG image.
    """
    if samples.ndim > 1:
        signal = np.mean(samples, axis=0)
    else:
        signal = samples

    total_samples = len(signal)
    duration_sec = total_samples / float(sample_rate) if sample_rate > 0 else 0.0
    nyquist_hz = sample_rate // 2

    # Compute STFT safely
    effective_nperseg = min(n_fft, max(64, total_samples)) if total_samples > 0 else 64
    effective_noverlap = min(effective_nperseg - 1, effective_nperseg - hop_length)
    if effective_noverlap < 0:
        effective_noverlap = effective_nperseg // 2

    try:
        _, _, zxx = scipy.signal.stft(
            signal,
            fs=sample_rate,
            nperseg=effective_nperseg,
            noverlap=effective_noverlap,
            window="hann",
        )
        mag = np.abs(zxx)
        # Convert to calibrated decibels clamped to [-80, 0] dB
        db = 20.0 * np.log10(np.maximum(mag, 1e-6))
        db = np.clip(db, -80.0, 0.0)
    except Exception:
        # Fallback empty matrix if signal too short
        db = np.full((128, 250), -80.0, dtype=np.float32)

    # Map decibels to [0, 255] and apply palette
    normalized = np.clip((db + 80.0) / 80.0 * 255.0, 0.0, 255.0).astype(np.uint8)
    rgb_spectrogram = _FORENSIC_PALETTE[normalized]
    # Flip vertically so 0 Hz is at bottom
    rgb_spectrogram = rgb_spectrogram[::-1, :, :]

    raw_spec_img = Image.fromarray(rgb_spectrogram, mode="RGB")

    # Geometry layout
    left_m = 75
    right_m = 90
    top_m = 40
    bottom_m = 40
    spec_w = max(10, width - left_m - right_m)
    spec_h = max(10, height - top_m - bottom_m)

    # Resize spectrogram array to target display rectangle
    resized_spec = raw_spec_img.resize((spec_w, spec_h), resample=Image.Resampling.BILINEAR)

    # Canvas setup
    bg_color = (15, 23, 42)
    border_color = (51, 65, 85)
    text_color = (148, 163, 184)
    title_color = (241, 245, 249)

    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()

    # Paste spectrogram into frame
    img.paste(resized_spec, (left_m, top_m))
    draw.rectangle([left_m, top_m, left_m + spec_w, top_m + spec_h], outline=border_color, width=1)

    # Title header
    header_text = f"STFT Time-Frequency Spectrogram (Decibels) | Hann {effective_nperseg} | Nyquist: {nyquist_hz:,} Hz"
    draw.text((left_m, 14), header_text, fill=title_color, font=font)

    # Y-axis frequency tick marks (5 points)
    freq_ticks = [
        (1.0, f"{nyquist_hz:,} Hz"),
        (0.75, f"{int(nyquist_hz * 0.75):,} Hz"),
        (0.5, f"{int(nyquist_hz * 0.5):,} Hz"),
        (0.25, f"{int(nyquist_hz * 0.25):,} Hz"),
        (0.0, "0 Hz"),
    ]
    for frac, label in freq_ticks:
        y_pos = int(top_m + (1.0 - frac) * spec_h)
        y_pos = max(top_m, min(top_m + spec_h, y_pos))
        draw.line([(left_m - 4, y_pos), (left_m, y_pos)], fill=border_color, width=1)
        draw.text((left_m - 68, y_pos - 5), label, fill=text_color, font=font)

    # X-axis time marks (5 points)
    num_ticks = 5
    for t_idx in range(num_ticks):
        frac = t_idx / float(num_ticks - 1)
        tick_x = int(left_m + frac * spec_w)
        t_sec = frac * duration_sec
        draw.line([(tick_x, top_m + spec_h), (tick_x, top_m + spec_h + 5)], fill=border_color, width=1)
        lbl = f"{t_sec:.2f}s"
        draw.text((tick_x - 12, top_m + spec_h + 8), lbl, fill=text_color, font=font)

    # Draw colorbar scale on the right
    cb_x0 = left_m + spec_w + 20
    cb_x1 = cb_x0 + 16
    cb_y0 = top_m
    cb_y1 = top_m + spec_h

    # Vertical gradient from 0 dB (top) to -80 dB (bottom)
    for y_offset in range(spec_h):
        frac_db = 1.0 - (y_offset / float(spec_h))
        color_idx = int(np.clip(frac_db * 255.0, 0, 255))
        c_r, c_g, c_b = _FORENSIC_PALETTE[color_idx]
        draw.line([(cb_x0, cb_y0 + y_offset), (cb_x1, cb_y0 + y_offset)], fill=(int(c_r), int(c_g), int(c_b)), width=1)

    draw.rectangle([cb_x0, cb_y0, cb_x1, cb_y1], outline=border_color, width=1)

    # Colorbar labels
    db_labels = [
        (0.0, " 0 dB"),
        (0.25, "-20 dB"),
        (0.5, "-40 dB"),
        (0.75, "-60 dB"),
        (1.0, "-80 dB"),
    ]
    for frac_y, db_str in db_labels:
        y_pos = int(cb_y0 + frac_y * spec_h)
        draw.line([(cb_x1, y_pos), (cb_x1 + 4, y_pos)], fill=border_color, width=1)
        draw.text((cb_x1 + 6, y_pos - 5), db_str, fill=text_color, font=font)

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()
