import sys, getopt, os
from pathlib import Path

class DeviceVerifyError(Exception):
    pass

def is_readonly(root_block_name: str) -> bool:
    # /sys/block/<disk>/ro, 0 - not read only, 1 read only
    # https://www.kernel.org/doc/Documentation/ABI/stable/sysfs-block
    return (Path("/sys/block") / root_block_name / "ro").read_text().strip() == "1"

def is_block_name(name: str) -> bool:
    return (Path("/sys/class/block") / name).exists()

def is_partition(name: str) -> bool:
    return (Path("/sys/class/block") / name / "partition").exists()

def verify_device(block_device: str) -> str:
    """
    Checks if device is valid root block device
    Returns root name of the provided device
    """
    # TODO: check sys/block/<device>/removable
    
    if not block_device.startswith("/dev/"):
        raise DeviceVerifyError(f"not a /dev path: {block_device}")

    name = os.path.basename(block_device)
    if not is_block_name(name):
        raise DeviceVerifyError(f"not a block device: {block_device}")

    if is_partition(name):
        raise DeviceVerifyError("refusing to write to partition. give root block device!")

    root = name

    try:
        if is_readonly(root):
            raise DeviceVerifyError(f"/dev/{root} is read-only (sysfs ro=1)")
    except PermissionError as e:
        raise DeviceVerifyError("permission denied reading sysfs; run as root?") from e
    except OSError as e:
        raise DeviceVerifyError(f"failed reading /sys/block/{root}/ro") from e

    return root

def check_image():
    pass

def get_args(argv) -> tuple[str, str]:
    image_file = None  # path to iso, e.g. debian.iso (TODO: always use this, DONT make it an option)
    block_device = None   # path to disk, e.g. /dev/sda

    try:
        opts, _ = getopt.getopt(argv, "hi:o:", ["ifile=", "ofile="])
    except getopt.GetoptError:
        print("writer.py -i <path_to_iso> -o <path_to_disk>")
        sys.exit(2)

    for opt, arg in opts:
        if opt == "-h":
            print("writer.py -i <path_to_iso> -o <path_to_disk>")
            sys.exit(0)
        elif opt in ("-i", "--iso"):
            image_file = arg
        elif opt in ("-o", "--disk"):
            block_device = arg

    if not image_file or not block_device:
        print("Error: both -i/--iso and -o/--disk are required")
        print("writer.py -i <path_to_iso> -o <path_to_disk>")
        sys.exit(2)

    return image_file, block_device


def main():
    src, dst = get_args(sys.argv[1:])
    root = ""
    try:
        root = verify_device(dst)
    except DeviceVerifyError as e:
        print(e, file=sys.stderr)

    print(root)
    pass

if __name__ == "__main__":
    main()
