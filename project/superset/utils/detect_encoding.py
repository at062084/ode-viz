#!/usr/bin/env python3
"""
Detect CSV file encoding

Usage:
    python detect_encoding.py <csv_file_path>
"""

import sys
import chardet

def detect_file_encoding(file_path):
    """Detect the encoding of a file."""
    with open(file_path, 'rb') as f:
        # Read first 100KB for detection
        raw_data = f.read(100000)
        result = chardet.detect(raw_data)
        return result

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python detect_encoding.py <csv_file_path>")
        print("\nExample:")
        print("  python detect_encoding.py /tmp/AL_Ausbildung_RGS.csv")
        sys.exit(1)

    file_path = sys.argv[1]

    try:
        result = detect_file_encoding(file_path)
        print(f"\n📄 File: {file_path}")
        print(f"🔍 Detected encoding: {result['encoding']}")
        print(f"✅ Confidence: {result['confidence'] * 100:.1f}%")

        if result['encoding'].lower() in ['utf-8', 'ascii']:
            print("\n✅ This is a standard encoding, should work fine!")
        else:
            print(f"\n⚠️  This is a non-UTF8 encoding ({result['encoding']})")
            print("   The create_sample_dashboard.py script will auto-detect it.")

    except FileNotFoundError:
        print(f"❌ Error: File not found: {file_path}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error detecting encoding: {e}")
        sys.exit(1)
