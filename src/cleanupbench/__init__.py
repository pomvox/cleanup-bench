"""Cleanup Bench: a public benchmark for dictation cleanup.

See docs/spec.md for the contract this package implements.
"""

__version__ = "0.1.0"

#: The dataset version this package scores against. Items are frozen per
#: version (docs/spec.md section 7.4). Bumped by a release commit only.
BENCH_VERSION = "1.0.0-dev"
