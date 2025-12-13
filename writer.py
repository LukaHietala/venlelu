import argparse
import sys
from pathlib import Path

from devices import DeviceVerifyError, verify_device


def check_image(path: str) -> str:
    iso_path = Path(path)
    if not iso_path.exists():
        raise FileNotFoundError(f"iso not found: {iso_path}")
    if not iso_path.is_file():
        raise FileNotFoundError(f"not a regular file: {iso_path}")
    return str(iso_path)


def get_args(argv) -> tuple[str, str]:
    parser = argparse.ArgumentParser(description="Raw write ISO image to block device")
    parser.add_argument("-i", "--input", required=True, help="path to ISO image")
    parser.add_argument(
        "-o", "--output", required=True, help="target block device, e.g. /dev/sda"
    )
    args = parser.parse_args(argv)
    return args.input, args.output


def main():
    src, dst = get_args(sys.argv[1:])
    try:
        src = check_image(src)
    except FileNotFoundError as e:
        print(e, file=sys.stderr)
        sys.exit(2)

    try:
        root = verify_device(dst)
    except DeviceVerifyError as e:
        print(e, file=sys.stderr)
        sys.exit(2)

    print(root)
    print(src)


if __name__ == "__main__":
    main()
