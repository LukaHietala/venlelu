"""
Uses sysfs ABI to handle device verification, so fully Linux-specific
https://www.kernel.org/doc/Documentation/ABI/stable/sysfs-block
"""

import os
import re
from pathlib import Path


class DeviceVerifyError(Exception):
    pass


def _is_readonly(root_block_name: str) -> bool:
    # /sys/block/<disk>/ro, 0 - not read only, 1 read only
    ro_path = Path("/sys/class/block") / root_block_name / "ro"
    try:
        return ro_path.read_text().strip() == "1"
    except PermissionError as e:
        raise DeviceVerifyError("permission denied reading sysfs; run as root?") from e
    except FileNotFoundError as e:
        raise DeviceVerifyError(f"missing sysfs attribute: {ro_path}") from e


def _is_block_name(name: str) -> bool:
    return (Path("/sys/class/block") / name).exists()


def _is_partition(name: str) -> bool:
    return (Path("/sys/class/block") / name / "partition").exists()


def _is_removable(name: str) -> bool:
    # /sys/block/<disk>/removable, 0 - non-removable, 1 - removable
    removable_path = Path("/sys/class/block") / name / "removable"
    try:
        return removable_path.read_text().strip() == "1"
    except PermissionError as e:
        raise DeviceVerifyError("permission denied reading sysfs; run as root?") from e
    except FileNotFoundError as e:
        raise DeviceVerifyError(f"missing sysfs attribute: {removable_path}") from e


def _suggest_root_name(name: str) -> str:
    # nvme0n1p1 -> nvme0n1, sda1 -> sda
    return re.sub(r"p?\d+$", "", name)


def verify_device(block_device: str) -> str:
    """
    Checks if device is valid root block device
    Returns root name of the provided device
    """
    if not block_device.startswith("/dev/"):
        raise DeviceVerifyError(f"not a /dev path: {block_device}")

    name = os.path.basename(block_device)
    if not _is_block_name(name):
        raise DeviceVerifyError(f"not a block device: {block_device}")

    if _is_partition(name):
        root_guess = _suggest_root_name(name)
        hint = f" (did you mean /dev/{root_guess}?)" if root_guess else ""
        raise DeviceVerifyError(f"refusing to write to partition {block_device}{hint}")

    if not _is_removable(name):
        confirm = input(
            f"/dev/{name} is not a removable device (likely internal). Want to risk it? (yes/no): "
        )
        if confirm.lower() != "yes":
            raise DeviceVerifyError(
                f"refusing to write to non-removable device (/dev/{name})"
            )

    if _is_readonly(name):
        raise DeviceVerifyError(f"/dev/{name} is read-only (sysfs ro=1)")
    return name
