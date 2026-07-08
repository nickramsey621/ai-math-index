#!/usr/bin/env python3
"""Daily driver: incremental harvest -> ingest -> classify -> build.

Harvests the last 14 days of datestamps (revisions are deduped by ingest),
so occasional missed runs self-heal.
"""
import os, subprocess, sys, tempfile
from datetime import date, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))

def run(script, *args):
    subprocess.run([sys.executable, os.path.join(HERE, script), *args], check=True)

def main():
    frm = (date.today() - timedelta(days=14)).isoformat()
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as tf:
        raw = tf.name
    try:
        run("harvest.py", raw, frm)
        run("ingest.py", raw)
        run("classify.py")
        run("build.py")
    finally:
        os.unlink(raw)

main()
