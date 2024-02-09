import logging
import os
import sys

import yaml
from app import log
from app.solution.borg import Borg
from app.solution.btrfs import Btrfs
from app.solution.restic import Restic

logger = logging.getLogger(__name__)


def check_if_linux() -> None:
    """
    ### Checks if executing system platform is Linux.\n
    This application has only support for Linux (sorry Win/Mac users).\n
    #### Exits application if system platform is not Linux.
    """

    logger.debug("Checking if Linux platform...")

    if sys.platform != "linux":
        logger.critical(
            "Application can only be run on Linux platform. Exiting...")
        sys.exit(1)

    logger.debug("Linux confirmed.")


def check_help_request() -> None:
    """
    ### Checks if application is executed with no argument(s), "--help" or "-h" flag.\n
    Prints help message, if requested by flag(s)/missing argument(s).\n
    #### Exits application if help message was printed.
    """

    logger.debug("Checking for help message request...")

    if ("--help" in sys.argv) or ("-h" in sys.argv) or (len(sys.argv) < 2):
        print(
            f"""\nUsage:\n\t{sys.argv[0]} --config <CONFIG_PATH> [--help|-h] [--libvirt] [--snap] \
[--retention] [--sync]\n""",
        )
        sys.exit(0)

    logger.debug("No help message requested.")


def check_if_superuser() -> None:
    """
    ### Checks if application is executed as superuser.\n
    This application needs superuser permissions to execute a lot of the backup functionality.\n
    #### Exits application if executing user is not superuser.
    """

    logger.debug("Checking superuser permissions...")

    if os.geteuid() != 0:
        logger.critical("Application not run as superuser. Exiting...")
        sys.exit(1)

    logger.debug("Permissions OK.")


def get_config() -> dict:
    """
    ### Returns config file settings.\n
    Returns settings if file exists and is free of syntax error(s).\n
    #### Exits application if file is missing or due to syntax error(s).
    """

    logger.debug("Locating config file...")

    # Get config path.
    for index, arg in enumerate(sys.argv):
        if arg == "--config":
            try:
                config_path = sys.argv[index + 1]
                break
            except IndexError:
                logger.critical(
                    "Could not find config path after '--config' flag. Exiting..."
                )
                sys.exit(1)

    # Open and syntax check config file.
    try:
        with open(config_path, "r", encoding="utf-8") as file:
            logger.debug("Config located.")
            logger.debug("Checking config syntax...")
            config = yaml.safe_load(file)
            logger.debug("Syntax OK.")
            return config

    except OSError:
        logger.critical(
            "Could not open config file '%s'. Exiting...", config_path)
        sys.exit(1)

    except yaml.scanner.ScannerError:
        logger.critical(
            "Syntax error(s) in config file '%s'. Exiting...", config_path)
        sys.exit(1)


def get_backup_object(config: dict) -> Btrfs | Borg | Restic:
    """
    ### Returns child object from parent "Backup" class.\n
    Child can be a "Btrfs", "Borg" or "Restic" class object.\n
    Child object gets determined by "source:<TYPE>" setting in config file.\n
    #### Exits application if "source:<TYPE>" setting does not resolve any child object.
    """

    logger.debug("Checking 'source:<TYPE>' setting...")

    if "source" not in config:
        logger.critical(
            "Can not find 'source' setting in config file. Exiting...")
        sys.exit(1)

    if "btrfs" in config["source"]:
        logger.debug("Setting 'source:btrfs' OK.")
        return Btrfs(config)

    elif "borg" in config["source"]:
        logger.debug("Setting 'source:borg' OK.")
        return Borg(config)

    elif "restic" in config["source"]:
        logger.debug("Setting 'source:restic' OK.")
        return Restic(config)

    logger.critical(
        "Setting '<TYPE>' in 'source' section of config file is not a valid source type. Exiting...")
    sys.exit(1)


def lock():
    """
    ### Locks current application execution.\n
    Hinders other executions of this application from interfering with snapshot creation and/or
    retention policy execution etc...\n
    #### Exits application if lock file already exists.
    """

    try:
        logger.debug("Locking application execution...")
        with open("/tmp/btree_up.lock", "x", encoding="utf-8") as file:
            file.write(f"LOCKED PID: {os.getpid()}")

    except OSError:
        logger.critical(
            "Application execution is already locked at '/tmp/btree_up.lock'. Exiting...")
        sys.exit(1)

    logger.debug("Execution successfully locked.")


def unlock():
    """
    ### Unlocks current application execution.\n
    Removes current execution lock file.\n
    """

    try:
        logger.debug("Unlocking application execution...")
        os.remove("/tmp/btree_up.lock")

    except OSError:
        logger.critical(
            "Could not remove execution lock at '/tmp/btree_up.lock'. Exiting...")
        sys.exit(1)

    logger.debug("Execution successfully unlocked.")
