import ipaddress
import logging
import re
import subprocess
import sys
from pathlib import Path

import validators

logger = logging.getLogger(__name__)


class Backup:
    """
    ### Parent class for shared methods and attributes in different backup solutions.
    """

    def __init__(self, config: dict):
        """
        ### Initializes parent 'Backup' class.\n
        Validates and checks all relevant settings in config file.\n
        #### Exits application if setting is invalid or missing.
        """

        self.config = config
        self.target_remote_user = ""
        self.target_remote_address = ""
        self.target_remote_port = int()

        # Check optional 'target:remote:*' settings.
        if "target" in self.config:
            if "remote" in self.config["target"]:
                self.__ck_t_rem_usr()
                self.__ck_t_rem_addr()
                self.__ck_t_rem_port()
                self.__ck_t_rem_con()

    def __ck_t_rem_usr(self) -> None:
        """
        ### Checks username format.\n
        Checks if 'target:remote:user' setting in config file has a valid username format only
        containing characters, numbers, '.', '_' and '-'.\n
        #### Exits application if username format is invalid.
        """

        logger.debug("Checking setting 'target:remote:user'...")

        # Check if 'target:remote:user' setting exists.
        try:
            self.target_remote_user = self.config["target"]["remote"]["user"]

        except KeyError:
            logger.critical(
                "Can not find 'user' setting in 'target:remote' section of config file. Exiting..."
            )
            sys.exit(1)

        # Check 'target:remote:user' format.
        usr_re = "^[a-zA-Z0-9._-]+$"

        if not re.match(usr_re, self.target_remote_user):
            logger.critical(
                """Setting 'user' in 'target:remote' section of config file is not a valid username.
                Exiting..."""
            )
            sys.exit(1)

        logger.debug("Setting 'target:remote:user' OK.")

    def __ck_t_rem_addr(self) -> None:
        """
        ### Checks address format.\n
        Checks if 'target:remote:address' setting in config file has a valid IP or domain format.\n
        #### Exits application if address format is invalid.
        """

        logger.debug("Checking setting 'target:remote:address'...")

        # Check if 'target:remote:address' setting exists.
        try:
            self.target_remote_address = self.config["target"]["remote"]["address"]

        except KeyError:
            logger.critical(
                """Can not find 'address' setting in 'target:remote' section of config file.
                Exiting..."""
            )
            sys.exit(1)

        # Check 'target:remote:address' format.
        try:
            ipaddress.ip_address(self.target_remote_address)

        except ValueError:
            if not validators.domain(self.target_remote_address):
                logger.critical(
                    """Setting 'address' in 'target:remote' section of config file is not a valid IP
                    or domain. Exiting..."""
                )
                sys.exit(1)

        logger.debug("Setting 'target:remote:address' OK.")

    def __ck_t_rem_port(self) -> None:
        """
        ### Checks port format.\n
        Checks if 'target:remote:port' setting in config file is a valid port number between 1 -
        65,535.\n
        #### Exits application if port format is invalid.
        """

        logger.debug("Checking setting 'target:remote:port'...")

        # Check if 'target:remote:port' setting exists.
        try:
            self.target_remote_port = self.config["target"]["remote"]["port"]

        except KeyError:
            logger.critical(
                "Can not find 'port' setting in 'target:remote' section of config file. Exiting..."
            )
            sys.exit(1)

        # Check if 'target:remote:port' is an integer.
        if not isinstance(self.target_remote_port, int):
            logger.critical(
                """Setting 'port' in 'target:remote' section of config file is not an integer.
                Exiting..."""
            )
            sys.exit(1)

        # Check if 'target:remote:port' integer is between 1 and 65,535.
        if not (self.target_remote_port >= 1 and self.target_remote_port <= 65535):
            logger.critical(
                """Setting 'port' in 'target:remote' section of config file is not inside a
                valid port range of 1-65,535 (port: '%s'). Exiting...""",
                self.target_remote_port,
            )
            sys.exit(1)

        logger.debug("Setting 'target:remote:port' OK.")

    def __ck_t_rem_con(self) -> None:
        """
        ### Checks SSH connection to remote target.\n
        Checks if remote SSH connection is possible without password input (using pubkey auth).\n
        #### Exits application if SSH connection failed.
        """

        logger.debug("Checking SSH remote target connection...")

        # Try connecting to remote target.
        proc = subprocess.run(
            [
                "ssh",
                "-o",
                "ConnectTimeout=3",
                "-p",
                str(self.target_remote_port),
                self.target_remote_user + "@" + self.target_remote_address,
                "echo $USER",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        # Evaluate connection attempt.
        if proc.returncode:
            logger.critical(
                "Failed SSH connection to remote target '%s@%s' on port '%s'. Exiting...\n%s",
                self.target_remote_user,
                self.target_remote_address,
                self.target_remote_port,
                proc.stderr.strip(),
            )
            sys.exit(1)

        logger.debug("SSH connection OK.")

    def ck_t_rem_path(self, path: str) -> None:
        """
        ### Checks path existence on remote target.\n
        Checks if passed path is a valid path to a remote directory (indicated by remote target
        settings in config section 'target:remote:*').\n
        #### Exits application if remote target path is invalid.
        """

        logger.debug("Checking if path '%s' exists on remote target...", path)

        # Check if remote settings are set.
        if not (
            self.target_remote_address
            and self.target_remote_user
            and self.target_remote_port
        ):
            logger.critical(
                """Trying to validate remote target path '%s' without any remote target
                settings. Exiting...""",
                path,
            )
            sys.exit(1)

        # Try connection to remote target and check path existence.
        proc = subprocess.run(
            [
                "ssh",
                "-o",
                "ConnectTimeout=3",
                "-p",
                str(self.target_remote_port),
                self.target_remote_user + "@" + self.target_remote_address,
                "test",
                "-d",
                path,
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        # Evaluate connection result.
        if proc.returncode:
            logger.critical(
                "Remote target path '%s' does not exist. Exiting...\n%s",
                path,
                proc.stderr.strip(),
            )
            sys.exit(1)

        logger.debug("Path '%s' OK.", path)

    def ck_path(self, path: str) -> None:
        """
        ### Checks local path existence.\n
        #### Exits application if path is invalid.
        """

        logger.debug("Checking if path '%s' exists locally.", path)

        # Check if local path exists.
        if not Path(path).is_dir():
            logger.critical(
                "Path '%s' is not a valid local path. Exiting...", path)
            sys.exit(1)

        logger.debug("Path '%s' OK.", path)

    def get_t_rem_dir_names(self, path: str) -> list[str] | list:
        """
        ### Get list of all directory names in target remote path.\n
        #### Returns empty list if no directory was found.
        """

        logger.debug(
            "Getting directory names of target remote path via SSH connection..."
        )

        # Try connecting to remote target and get directory names.
        proc = subprocess.run(
            [
                "ssh",
                "-o",
                "ConnectTimeout=3",
                "-p",
                str(self.target_remote_port),
                self.target_remote_user + "@" + self.target_remote_address,
                "cd " + path.rstrip("/") +
                '; for dir in */; do echo "$dir"; done',
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        # Evaluate connection results.
        if proc.returncode:
            logger.critical(
                "Failed to get list of directory names from target remote path. Exiting...\n%s",
                proc.stderr.strip(),
            )
            sys.exit(1)

        ret_val = (proc.stdout).replace("/", "").split("\n")[:-1]

        logger.debug("Target remote directory names OK.")

        return ret_val

    def get_dir_names(self, path: str) -> list[str] | list:
        """
        ### Get list of all directory names in local path.\n
        #### Returns empty list if no directory was found.
        """

        logger.debug("Getting directory names from local path ...")

        dir_paths = list(Path(path).iterdir())
        dir_names = []

        # Convert all directory paths to directory names.
        for dir_path in dir_paths:
            dir_name_re = "[^/]+$"
            dir_name = re.search(dir_name_re, str(dir_path)).group()
            dir_names.append(dir_name)

        logger.debug("Local directory names OK.")

        return dir_names

    def renew_virtual_machine_config(self) -> None:
        """
        N/A
        """

        pass

    def create_snapshot(self) -> None:
        pass

    def run_retention_policy(self) -> None:
        pass

    def sync_to_target(self) -> None:
        pass
