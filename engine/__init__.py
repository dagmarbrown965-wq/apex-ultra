"""APEX engine package (Phase 42).

Isolated signal-producer layer. Writes canonical signal_contract v1.0 JSONL to
engine/output/. Communicates with the frozen shadow pipeline ONLY through that
file on disk. This package imports nothing from any broker or execution module.
"""
