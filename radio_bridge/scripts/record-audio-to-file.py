#!/usr/bin/env python

"""
Record audio from the input into a .wav file.
"""

import sys
import argparse

from radio_bridge.rx import RX


def main(path: str, duration: int) -> None:
    rx = RX(file_path=path, time=duration)
    rx.record_audio()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Record audio to a .wav file")
    parser.add_argument(
        "--path",
        type=str,
        help="Path where the recording will be saved",
        default="recording.wav",
    )
    parser.add_argument(
        "--duration",
        type=int,
        help="How long to record (in seconds)",
        default=30,
    )
    args = parser.parse_args(sys.argv[1:])

    main(args.path, args.duration)
