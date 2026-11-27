"""Bounded per-assembly caching, versioned by the imported CSV fingerprint."""
import hashlib
import json

from django.core.cache import cache


def cached_exons(assembly, revision, namespace, identity, load):
    # No metadata means no trustworthy version.
    if assembly not in ('hg19', 'hg38') or not revision:
        return load()
    digest = hashlib.sha256(json.dumps(identity, sort_keys=True, default=str).encode()).hexdigest()
    key = f'exons:v2:{assembly}:{revision}:{namespace}:{digest}'
    missing = object()
    value = cache.get(key, missing)
    if value is missing:
        value = load()
        cache.set(key, value, timeout=300)
    return value
