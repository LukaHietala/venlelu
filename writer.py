import sys, getopt

from devices import DeviceVerifyError, verify_device

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
