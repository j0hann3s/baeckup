#!/usr/bin/env python3

import sys

from app import function as fn


def main() -> None:
    """
    # Entry point.
    """

    fn.check_if_linux()
    fn.check_help_request()
    fn.check_if_superuser()

    config = fn.get_config()
    backup = fn.get_backup_object(config)

    fn.lock()

    if "--libvirt" in sys.argv:
        backup.renew_virtual_machine_config()

    if "--snap" in sys.argv:
        backup.create_snapshot()

    if "--retention" in sys.argv:
        backup.run_retention_policy()

    if "--sync" in sys.argv:
        backup.sync_to_target()

    fn.unlock()


if __name__ == "__main__":
    main()
