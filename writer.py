import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from devices import DeviceVerifyError, verify_device


GRUB_CFG = """set timeout=10

search --file /venlelu.tag --set=root
set iso_dir=/iso

for iso_path in ${iso_dir}/*.iso ${iso_dir}/*.ISO; do
    if [ -e "$iso_path" ]; then
        menuentry "$iso_path" "$iso_path" {
            set isofile=$2
            export isofile
            loopback loop $2
            set root=loop
            configfile (loop)/boot/grub/grub.cfg
        }
    fi
done

menuentry "Reboot" { reboot }
menuentry "Power off" { halt }
"""


def run(cmd):
    subprocess.run(cmd, check=True)


def main():
    parser = argparse.ArgumentParser(
        description=""
    )
    parser.add_argument(
        "--device", required=True, help="target block device, e.g. /dev/sda"
    )
    parser.add_argument("--iso-dir", help="directory of .iso files to copy")
    parser.add_argument("--yes", action="store_true", help="skip confirmation")
    args = parser.parse_args()

    if os.geteuid() != 0:
        print("Must be run as root", file=sys.stderr)
        sys.exit(2)

    try:
        device_root = verify_device(args.device)
    except DeviceVerifyError as e:
        sys.exit(f"Error: {e}")

    if not args.yes:
        if (
            input(f"Wipe /dev/{device_root}? (yes/no): ").lower()
            != "yes"
        ):
            return

    device = f"/dev/{device_root}"
    iso_src = Path(args.iso_dir) if args.iso_dir else None
    if iso_src and not iso_src.is_dir():
        sys.exit(f"Error: {iso_src} is not a directory")

    # Partition and format
    # Very useful docs: https://www.rodsbooks.com/gdisk/sgdisk-walkthrough.html
    run(["sgdisk", "--zap-all", device])
    # 512 MB EFI partition (fat32)
    run(["sgdisk", "-n", "1:1MiB:+512MiB", "-t", "1:EF00", device])
    # Rest for isos (ext4)
    run(["sgdisk", "-n", "2:0:0", "-t", "2:8300", device])
    run(["mkfs.vfat", "-F", "32", "-n", "VENLEFI", f"{device}1"])
    run(["mkfs.ext4", "-F", "-L", "VENLELU", f"{device}2"])

    # Mount and install grub
    with tempfile.TemporaryDirectory() as tmp:
        efi_mount = Path(tmp) / "efi"
        data_mount = Path(tmp) / "data"
        efi_mount.mkdir()
        data_mount.mkdir()

        try:
            run(["mount", f"{device}1", str(efi_mount)])
            run(["mount", f"{device}2", str(data_mount)])

            run(
                [
                    "grub-install",
                    "--target=x86_64-efi",
                    "--removable",
                    f"--efi-directory={efi_mount}",
                    f"--boot-directory={data_mount}/boot",
                    "--no-nvram", # fix uefi issues with nvram
                    device,
                ]
            )

            # Write config and setup diss
            grub_cfg = data_mount / "boot/grub/grub.cfg"
            grub_cfg.parent.mkdir(parents=True, exist_ok=True)
            grub_cfg.write_text(GRUB_CFG)
            # Creates a tag so easily found by grub
            (data_mount / "venlelu.tag").write_text("venlelu")

            iso_dir = data_mount / "iso"
            iso_dir.mkdir()

            if iso_src:
                for iso in sorted(iso_src.glob("*.iso")) + sorted(
                    iso_src.glob("*.ISO")
                ):
                    print(f"Copying {iso.name}")
                    shutil.copy2(iso, iso_dir / iso.name)
        finally:
            subprocess.run(["umount", str(data_mount)], capture_output=True)
            subprocess.run(["umount", str(efi_mount)], capture_output=True)

    print("Done")


if __name__ == "__main__":
    main()
