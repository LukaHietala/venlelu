"""
Uses sysfs ABI to handle device verification, so fully Linux-specific
https://www.kernel.org/doc/Documentation/ABI/stable/sysfs-block
"""

import os
from pathlib import Path

class DeviceVerifyError(Exception):
    pass

def is_readonly(root_block_name: str) -> bool:
    # /sys/block/<disk>/ro, 0 - not read only, 1 read only
    return (Path("/sys/block") / root_block_name / "ro").read_text().strip() == "1"

def is_block_name(name: str) -> bool:
    return (Path("/sys/class/block") / name).exists()

def is_partition(name: str) -> bool:
    return (Path("/sys/class/block") / name / "partition").exists()

def is_removable(name: str) -> bool:
    # /sys/block/<disk>/removable, 0 - non-removable, 1 - removable
    return (Path("/sys/block") / name / "removable").read_text().strip() == "1"

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

    if not is_removable(name):
        confirm = input(f"/dev/{name} is not removable device (likely not a USB or external device). Want to risk it? (yes/no): ")
        if confirm.lower() != "yes":
            raise DeviceVerifyError("refusing to write to removable device")

    try:
        if is_readonly(name):
            raise DeviceVerifyError(f"/dev/{name} is read-only (sysfs ro=1)")
    except PermissionError as e:
        raise DeviceVerifyError("permission denied reading sysfs; run as root?") from e
    except OSError as e:
        raise DeviceVerifyError(f"failed reading /sys/block/{name}/ro") from e
    return name
