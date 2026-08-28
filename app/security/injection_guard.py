import re

# Common patterns used in prompt injection attempts
INJECTION_PATTERNS = [
    r"ignore (all )?(previous|prior|above) instructions",
    r"disregard (all )?(previous|prior|above)",
    r"system prompt",
    r"you are now",
    r"act as (a|an)",
    r"new instructions?:",
    r"forget (everything|all)",
    r"reveal (your|the) (prompt|instructions)",
    r"do anything now",
    r"jailbreak",
    r"override (your|the) (rules|instructions|guidelines)",
]

COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]

def scan_for_injection(text: str) -> dict:
    """
    Scans a chunk of text for suspicious instruction-like patterns.
    Returns a dict with a boolean flag and which patterns matched (for logging).
    """
    matches = [p.pattern for p in COMPILED_PATTERNS if p.search(text)]
    return {
        "flagged": len(matches) > 0,
        "matched_patterns": matches,
    }

def filter_safe_chunks(chunks_with_scores: list) -> list:
    """
    Takes a list of (point, score) tuples, removes any whose text is flagged
    as a likely injection attempt, and logs what was filtered.
    """
    safe = []
    for point, score in chunks_with_scores:
        result = scan_for_injection(point.payload["text"])
        if result["flagged"]:
            print(f"⚠️ Injection pattern detected in chunk from {point.payload['source']}: {result['matched_patterns']}")
            continue
        safe.append((point, score))
    return safe