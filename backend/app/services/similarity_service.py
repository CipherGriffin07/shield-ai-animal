"""
Image similarity engine for Lost & Found matching.

Computes a perceptual "average hash" (aHash) for each uploaded photo:
the image is shrunk to 8x8 greyscale, and each pixel is compared to
the mean brightness to produce a 64-bit fingerprint. Two images that
look visually similar produce fingerprints with a small Hamming
distance, which is converted into a 0-1 similarity score.

This is a real, working, dependency-light similarity measure (no
external API key required) that runs immediately on upload. It can be
swapped for / augmented with a Gemini Vision embedding comparison
later for stronger fuzzy matching - see app/services/gemini_service.py.
"""
from __future__ import annotations

from PIL import Image

HASH_SIZE = 8  # 8x8 -> 64-bit fingerprint


def compute_image_signature(file_path: str) -> str:
    with Image.open(file_path) as img:
        img = img.convert("L").resize((HASH_SIZE, HASH_SIZE), Image.LANCZOS)
        pixels = list(img.getdata())

    average = sum(pixels) / len(pixels)
    bits = "".join("1" if p >= average else "0" for p in pixels)
    return f"{int(bits, 2):016x}"


def similarity_score(signature_a: str | None, signature_b: str | None) -> float:
    if not signature_a or not signature_b:
        return 0.0
    try:
        a, b = int(signature_a, 16), int(signature_b, 16)
    except ValueError:
        return 0.0
    hamming_distance = bin(a ^ b).count("1")
    return round(1 - (hamming_distance / (HASH_SIZE * HASH_SIZE)), 4)
