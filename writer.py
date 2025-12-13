import sys, getopt

def get_args(argv):
    image_file = None  # path to iso, e.g. debian.iso (TODO: always use this, dont make it an option)
    disk_file = None   # path to disk, e.g. /dev/sda

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
            disk_file = arg

    if not image_file or not disk_file:
        print("Error: both -i/--iso and -o/--disk are required")
        print("writer.py -i <path_to_iso> -o <path_to_disk>")
        sys.exit(2)

    return image_file, disk_file


def main():
    src, dst = get_args(sys.argv[1:])
    print(src, dst)
    pass

if __name__ == "__main__":
    main()
