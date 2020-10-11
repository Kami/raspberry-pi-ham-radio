#!/usr/bin/env python

import sys
import argparse

from radio_bridge.dtmf  import DTMFDecoder

"""
Decode DTMF sequence in the provided .wav file.
"""

def main(path: str, implementation: str) -> None:
    dtmf = DTMFDecoder(file_path=path, implementation=implementation)
    result = dtmf.decode()

    print("Decoded char / sequence: %s" % (result))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Decode DTMF sequence in a provided .wav file"
    )
    parser.add_argument(
        "--path",
        type=str,
        help="Path where the recording is stored",
        required=True
    )
    parser.add_argument(
        "--implementation",
        type=str,
        help="Which decode implementation to use",
        default="fft_1"
    )

    args = parser.parse_args(sys.argv[1:])

    main(args.path, args.implementation)
