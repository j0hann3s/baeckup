import logging
import os
import sys

import yaml

from app import backup

logger = logging.getLogger(__name__)


def check_if_linux() -> None:
    """
    ### Checks if executing system platform is Linux.\n
    This application has only support for Linux, sorry Win/Mac users.\n
    #### Exits application if system platform is not Linux.
    """

    logger.debug("Checking Linux platform...")

    if sys.platform != "linux":
        logger.critical("Application can only be run on Linux platform. Exiting...")
        sys.exit(1)

    logger.debug("Linux confirmed.")


def check_help_request() -> None:
    """
    ### Checks if application is executed with no arguments, '--help' or '-h' flag.\n
    Prints help message, if requested by flags/missing arguments.\n
    #### Exits application if help message got printed.
    """

    logger.debug("Checking help args...")

    if ("--help" in sys.argv) or ("-h" in sys.argv) or (len(sys.argv) < 2):
        print(
            f"""\nUsage:\n\t{sys.argv[0]} --config <CONFIG_PATH> [--help|-h] [--libvirt] [--snap] \
[--retention] [--sync]\n""",
        )
        sys.exit(0)

    logger.debug("No help args.")


def check_if_superuser() -> None:
    """
    ### Checks if application is executed as superuser.\n
    This application needs root rights to execute a lot of the backup functionality.\n
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
    Returns settings if file exists and is free of syntax error.\n
    #### Exits application if file is missing or due to syntax error.
    """

    config_path = ""

    logger.debug("Checking config file...")

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

    # If no config file was found.
    if not config_path:
        logger.critical(
            """Could not find config file. Run again with '--help' argument to see usage info.
            Exiting..."""
        )
        sys.exit(1)

    try:
        # Open and syntax check config.
        with open(config_path, "r", encoding="utf-8") as file:
            logger.debug("Config OK.")
            logger.debug("Checking config syntax...")
            config = yaml.safe_load(file)
            logger.debug("Syntax OK.")
            return config

    except OSError:
        logger.critical("Could not open config file '%s'. Exiting...", config_path)
        sys.exit(1)

    except yaml.scanner.ScannerError:
        logger.critical("Syntax error in config file '%s'. Exiting...", config_path)
        sys.exit(1)


def get_backup_object(config: dict) -> backup.Btrfs | backup.Borg | backup.Restic:
    """
    ### Returns inheriting <TYPE> object from parent 'Backup' class.\n
    <TYPE> can be 'Btrfs', 'Borg' or 'Restic' class object.\n
    <TYPE> object gets determined by 'source:<TYPE>' setting in config file.\n
    #### Exits application if 'source:<TYPE>' setting does not resolve child object.
    """

    if "source" not in config:
        logger.critical("Can not find 'source' setting in config file. Exiting...")
        sys.exit(1)

    logger.debug("Checking 'source:<TYPE>' setting...")

    if "btrfs" in config["source"]:
        logger.debug("Setting 'source:btrfs' OK.")
        return backup.Btrfs(config)

    if "borg" in config["source"]:
        logger.debug("Setting 'source:borg' OK.")
        return backup.Borg(config)

    if "restic" in config["source"]:
        logger.debug("Setting 'source:restic' OK.")
        return backup.Restic(config)

    logger.critical(
        """Setting '<TYPE>' in 'source' section of config file is not a valid
        source type. Exiting...""",
    )
    sys.exit(1)


def lock():
    """
    ### Locks current application execution.\n
    Hinders other executions of this application from interfering with snapshot creation and
    retention policy execution and more.\n
    #### Exits application if lock file already exists.
    """

    try:
        logger.debug("Locking application execution...")
        with open(".träsor.lock", "x", encoding="utf-8") as file:
            file.write("LOCKED")

    except OSError:
        logger.critical(
            "Application execution is locked at '%s'. Exiting...",
            os.getcwd() + "/.träsor.lock",
        )
        sys.exit(1)

    logger.debug("Execution locked.")


def unlock():
    """
    ### Unlocks current application execution.\n
    Removes current execution lock file.\n
    """

    try:
        logger.debug("Unlocking application execution...")
        os.remove(f"{os.getcwd()}/.träsor.lock")

    except OSError:
        logger.critical(
            "Could not remove execution lock '%s'. Exiting...",
            os.getcwd() + "/.träsor.lock",
        )
        sys.exit(1)

    logger.debug("Execution unlocked.")
