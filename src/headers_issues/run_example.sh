#!/bin/bash

# This script demonstrates how our header analysis pipeline works 
# on a small sample of 15 domains from the Common Crawl dataset.

echo "=========================================================="
echo " Running Security Header Analyzer "
echo "=========================================================="

INPUT_JSONL="example_000000.jsonl"
OUTPUT_CSV="example_results.csv"
ANALYZER_SCRIPT="./header_analyzer.py"

if [ ! -f "$INPUT_JSONL" ]; then
    echo "Error: $INPUT_JSONL not found!"
    exit 1
fi

echo "[*] Step 1: Running the analyzer on the sample data..."
python3 "$ANALYZER_SCRIPT" --input "$INPUT_JSONL" --output "$OUTPUT_CSV"

echo ""
echo "[*] Step 2: Output CSV generated at $OUTPUT_CSV"
echo "[*] Analysis Results Preview:"
echo "----------------------------------------------------------"
head -n 5 "$OUTPUT_CSV"
echo "----------------------------------------------------------"
echo ""
echo "Done! You can inspect $OUTPUT_CSV for the full list of detected security issues."
