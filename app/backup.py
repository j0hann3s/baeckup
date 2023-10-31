import datetime
import ipaddress
import logging
import re
import subprocess
import sys
from pathlib import Path

import validators

import app.function as fn

logger = logging.getLogger(__name__)


class Backup:
    """
    ### Parent class for shared methods and attributes in different backup solutions.
    """

    def __init__(self, config: dict):
        """
        ### Initializes parent 'Backup' class.\n
        Validates and checks all relevant settings in config file.\n
        #### Exits application if settings are invalid or missing.
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
            logger.critical("Path '%s' is not a valid local path. Exiting...", path)
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
                "cd " + path.rstrip("/") + '; for dir in */; do echo "$dir"; done',
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

    # Add Libvirt methods here...

    def renew_virtual_machine_config(self) -> None:
        """
        N/A
        """

        pass


class Btrfs(Backup):
    """
    ### Child class for btrfs backup methods and attributes.
    """

    def __init__(self, config: dict):
        """
        ### Initializes btrfs child class.\n
        Validates and checks all present source/target settings for btrfs in config file.\n
        #### Exits application if settings are invalid or missing.
        """

        super().__init__(config)

        self.source_btrfs_snapshot_path = ""
        self.target_btrfs_snapshot_path = ""
        self.source_btrfs_subvolume_paths = set()
        self.source_btrfs_retention_policies = {}

        self.__ck_s_btrfs_snap_path()

        # Check optional 'target:btrfs:*' settings.
        if "target" in self.config:
            self.__ck_t_btrfs_snap_path()

        # Check optional 'source:btrfs:subvolume_paths' settings.
        if "subvolume_paths" in self.config["source"]["btrfs"]:
            self.__ck_s_btrfs_subvol_paths()
            self.__ck_dup_subvol_names()

        # Check optional 'source:btrfs:retention_policies' settings.
        if "retention_policies" in self.config["source"]["btrfs"]:
            self.__ck_s_btrfs_ret_policies()

    def __ck_s_btrfs_snap_path(self) -> None:
        """
        ### Checks btrfs snapshot path in source.\n
        #### Exits application if snapshot path in source is invalid.
        """

        logger.debug("Checking setting 'source:btrfs:snapshot_path'...")

        # Check if 'source:btrfs:snapshot_path' setting exists.
        try:
            self.source_btrfs_snapshot_path = (
                self.config["source"]["btrfs"]["snapshot_path"]
            ).rstrip("/")

        except KeyError:
            logger.critical(
                """Can not find 'snapshot_path' setting in 'source:btrfs' section of config file.
                Exiting..."""
            )
            sys.exit(1)

        # Check source path.
        super().ck_path(self.source_btrfs_snapshot_path)

        logger.debug("Setting 'source:btrfs:snapshot_path' OK.")

    def __ck_t_btrfs_snap_path(self) -> None:
        """
        ### Checks btrfs snapshot path in target.\n
        #### Exits application if snapshot path in target is invalid.
        """

        logger.debug("Checking setting 'target:btrfs:snapshot_path'...")

        # Check if 'target:btrfs' setting exists.
        if "btrfs" not in self.config["target"]:
            logger.critical(
                "Can not find 'btrfs' setting in 'target' section of config file. Exiting..."
            )
            sys.exit(1)

        # Check if 'target:btrfs:snapshot_path' setting exists.
        try:
            self.target_btrfs_snapshot_path = (
                self.config["target"]["btrfs"]["snapshot_path"]
            ).rstrip("/")

        except KeyError:
            logger.critical(
                """Can not find 'snapshot_path' setting in 'target:btrfs' section of config file.
                Exiting..."""
            )
            sys.exit(1)

        # Check remote target path, if applicable.
        if "remote" in self.config["target"]:
            super().ck_t_rem_path(self.target_btrfs_snapshot_path)

        # Check local target path.
        else:
            super().ck_path(self.target_btrfs_snapshot_path)

        logger.debug("Setting 'target:btrfs:snapshot_path' OK.")

    def __ck_s_btrfs_subvol_paths(self) -> None:
        """
        ### Checks btrfs subvolume paths.\n
        #### Exits application if subvolume is not valid.
        """

        logger.debug("Checking setting 'source:btrfs:subvolume_paths'...")

        self.source_btrfs_subvolume_paths = self.config["source"]["btrfs"][
            "subvolume_paths"
        ]

        # Check if every subvolume is valid in btrfs.
        for subvol in self.source_btrfs_subvolume_paths:
            proc = subprocess.run(
                ["btrfs", "subvolume", "show", subvol],
                capture_output=True,
                text=True,
                check=False,
            )

            if proc.returncode:
                logger.critical(
                    "The btrfs subvolume '%s' is not valid. Exiting...\n%s",
                    subvol,
                    proc.stderr.strip(),
                )
                sys.exit(1)

        logger.debug("Setting 'source:btrfs:subvolume_paths' OK.")

    def __ck_dup_subvol_names(self) -> None:
        """
        ### Checks btrfs subvolume for duplicate names.\n
        Checks right-most directory name of subvolume path against all other paths.\n
        #### Exits application if duplicate names are found.
        """

        logger.debug("Checking for duplicate subvolume names with different paths...")

        # Check for duplicate subvolume names.
        for subvol_a_path in self.source_btrfs_subvolume_paths:
            subvol_a_path = subvol_a_path.rstrip("/")
            for subvol_b_path in self.source_btrfs_subvolume_paths:
                subvol_b_path = subvol_b_path.rstrip("/")
                dir_name_re = "([^/]+$)"
                subvol_a_name = re.search(dir_name_re, subvol_a_path).group()
                subvol_b_name = re.search(dir_name_re, subvol_b_path).group()

                # Check for duplicate subvolume names with different subvolume paths.
                if subvol_a_path != subvol_b_path and subvol_a_name == subvol_b_name:
                    logger.critical(
                        """Duplicate subvolume name detected. Subvolume path '%s' and '%s' produce
                        the same subvolume name '%s'. The name has to be unique in the set of
                        subvolumes. Exiting...""",
                        subvol_a_path,
                        subvol_b_path,
                        subvol_a_name,
                    )
                    sys.exit(1)

        logger.debug("Duplicate subvolume name test OK.")

    def __ck_s_btrfs_ret_policies(self) -> None:
        """
        ### Checks btrfs snapshot retention policies.\n
        Checks that policies are lists only containing integers.\n
        #### Exits application if values are not lists only containing integers.
        """

        logger.debug("Checking setting 'source:btrfs:retention_policies'...")

        # Check if 'source:btrfs:retention_policies' setting exists.
        try:
            self.source_btrfs_retention_policies = self.config["source"]["btrfs"][
                "retention_policies"
            ]

        except KeyError:
            logger.critical(
                """Can not find 'retention_policies' setting in 'source:btrfs' section of config
                file. Exiting..."""
            )
            sys.exit(1)

        # Loop through all policies and check their format.
        for policy_name in self.source_btrfs_retention_policies:
            if not isinstance(self.source_btrfs_retention_policies[policy_name], list):
                logger.critical(
                    "Retention policy '%s' with value '%s' is not a list. Exiting...",
                    policy_name,
                    self.source_btrfs_retention_policies[policy_name],
                )
                sys.exit(1)

            for policy_lst in self.source_btrfs_retention_policies[policy_name]:
                if not isinstance(policy_lst, int):
                    logger.critical(
                        "List of retention policy '%s' contains non-int value '%s'. Exiting...",
                        policy_name,
                        policy_lst,
                    )
                    sys.exit(1)

        logger.debug("Setting 'source:btrfs:retention_policies' OK.")

    def __inc_sync_to_t(self, s_snaps: list[str], t_snaps: list[str]) -> None:
        """
        ### Sync passed btrfs snapshots from source to local target, incrementally.\n
        Empty passed lists have no effect.\n
        #### Executes full snapshot send if no common snapshot exist.
        """

        latest_common_snap = ""

        # Loop over all source snapshot.
        for s_snap in s_snaps:
            # Indicate common snapshot.
            if s_snap in t_snaps:
                latest_common_snap = s_snap

            # Sync missing snapshot from source to target if common snapshot exists.
            elif s_snap not in t_snaps and latest_common_snap != "":
                proc = subprocess.Popen(
                    [
                        "btrfs",
                        "send",
                        "-v",
                        "-p",
                        self.source_btrfs_snapshot_path + "/" + latest_common_snap,
                        self.source_btrfs_snapshot_path + "/" + s_snap,
                    ],
                    stdout=subprocess.PIPE,
                )

                proc = subprocess.Popen(
                    ["btrfs", "receive", self.target_btrfs_snapshot_path],
                    stdin=proc.stdout,
                )

                proc.communicate()

        # If source and target have no common snapshots; full send.
        if not latest_common_snap:
            logger.info("No common snapshot found.")
            self.__full_sync_to_t(s_snaps)
            self.__inc_sync_to_t(s_snaps, t_snaps)

    def __inc_sync_to_rem_t(self, s_snaps: list[str], t_snaps: list[str]) -> None:
        """
        ### Sync passed btrfs snapshots from source to remote target, incrementally.\n
        Empty passed lists have no effect.\n
        #### Executes full snapshot send if no common snapshot exist.
        """

        latest_common_snap = ""

        # Loop over all source snapshot.
        for s_snap in s_snaps:
            # Indicate common snapshot.
            if s_snap in t_snaps:
                latest_common_snap = s_snap

            # Sync missing snapshot from source to target if common snapshot exists.
            elif s_snap not in t_snaps and latest_common_snap != "":
                proc = subprocess.Popen(
                    [
                        "btrfs",
                        "send",
                        "-v",
                        "-p",
                        self.source_btrfs_snapshot_path + "/" + latest_common_snap,
                        self.source_btrfs_snapshot_path + "/" + s_snap,
                    ],
                    stdout=subprocess.PIPE,
                )

                proc = subprocess.Popen(
                    [
                        "ssh",
                        "-o",
                        "ConnectTimeout=3",
                        "-p",
                        str(self.target_remote_port),
                        f"{self.target_remote_user}@{self.target_remote_address}",
                        f"btrfs receive {self.target_btrfs_snapshot_path}",
                    ],
                    stdin=proc.stdout,
                )

                proc.communicate()

        # If source and target have no common snapshots; full send.
        if not latest_common_snap:
            logger.info("No common snapshot found.")
            self.__full_sync_to_rem_t(s_snaps)
            self.__inc_sync_to_rem_t(s_snaps, t_snaps)

    def __full_sync_to_t(self, s_snaps: list[str]) -> None:
        """
        ### Sync passed btrfs snapshots from source to local target, full send.\n
        Empty passed lists have no effect.\n
        """

        logger.info("Starting full snapshot send...")

        # Sync oldest snapshot from source to target.
        proc = subprocess.Popen(
            [
                "btrfs",
                "send",
                "-v",
                f"{self.source_btrfs_snapshot_path}/{s_snaps[0]}",
            ],
            stdout=subprocess.PIPE,
        )

        proc = subprocess.Popen(
            ["btrfs", "receive", self.target_btrfs_snapshot_path],
            stdin=proc.stdout,
        )

        proc.communicate()

        logger.info("Full snapshot send finished.")

    def __full_sync_to_rem_t(self, s_snaps: list[str]) -> None:
        """
        ### Sync passed btrfs snapshots from source to remote target, full send.\n
        Empty passed lists have no effect.\n
        """

        logger.info("Starting full snapshot send...")

        # Sync oldest snapshot from source to target.
        proc = subprocess.Popen(
            [
                "btrfs",
                "send",
                "-v",
                f"{self.source_btrfs_snapshot_path}/{s_snaps[0]}",
            ],
            stdout=subprocess.PIPE,
        )

        proc = subprocess.Popen(
            [
                "ssh",
                "-o",
                "ConnectTimeout=3",
                "-p",
                str(self.target_remote_port),
                f"{self.target_remote_user}@{self.target_remote_address}",
                f"btrfs receive {self.target_btrfs_snapshot_path}",
            ],
            stdin=proc.stdout,
        )

        proc.communicate()

        logger.info("Full snapshot send finished.")

    def __del_old_t_snaps(self, s_snaps: list[str], t_snaps: list[str]) -> None:
        """
        ### Delete old and obsolete snapshot from local target if non-existent on source.
        """

        for t_snap in t_snaps:
            if t_snap not in s_snaps:
                proc = subprocess.run(
                    [
                        "btrfs",
                        "subvolume",
                        "delete",
                        f"{self.target_btrfs_snapshot_path}/{t_snap}",
                    ],
                    capture_output=True,
                    text=True,
                    check=False,
                )

                if proc.returncode:
                    logger.error(
                        "Failed to delete local target btrfs snapshot '%s'.\n%s",
                        self.target_btrfs_snapshot_path + "/" + t_snap,
                        proc.stderr.strip(),
                    )

    def __del_old_rem_t_snaps(self, s_snaps: list[str], t_snaps: list[str]) -> None:
        """
        ### Delete old and obsolete snapshot from remote target if non-existent on source.
        """

        for t_snap in t_snaps:
            if t_snap not in s_snaps:
                proc = subprocess.run(
                    [
                        "ssh",
                        "-o",
                        "ConnectTimeout=3",
                        "-p",
                        str(self.target_remote_port),
                        f"{self.target_remote_user}@{self.target_remote_address}",
                        f"btrfs subvolume delete {self.target_btrfs_snapshot_path}/{t_snap}",
                    ],
                    capture_output=True,
                    text=True,
                    check=False,
                )

                if proc.returncode:
                    logger.error(
                        "Failed to delete remote target btrfs snapshot '%s'.\n%s",
                        self.target_btrfs_snapshot_path + "/" + t_snap,
                        proc.stderr.strip(),
                    )

    ######################

    def __calc_eligible_snaps(self, policy_lst: list[int]) -> list[str] | list:
        """
        ### Calculates all eligible snapshot(s) according to policy time frame.\n
        Snapshot name(s) have to match beginning pattern 'YYYY_MM_DD_HH_MM' from which time
        difference is calculated.\n
        #### Returns list with all eligible snapshot(s), or empty list if no snapshot(s) are found.
        """

        current_time = datetime.datetime.now()
        snap_names = fn.get_dir_names(self.source_snapshot_path)
        eligible_snaps = []

        for snap in snap_names:
            snap_time_re = "^[0-9]{4}_[0-9]{2}_[0-9]{2}_[0-9]{2}_[0-9]{2}"
            snap_time = re.search(snap_time_re, snap).group()
            snap_time = datetime.datetime.strptime(snap_time, "%Y_%m_%d_%H_%M")

            if (
                (current_time - snap_time).days >= policy_lst[0]
                and (current_time - snap_time).days <= policy_lst[1]
                and (current_time - snap_time).seconds >= policy_lst[2]
                and (current_time - snap_time).seconds <= policy_lst[3]
            ):
                eligible_snaps.append(snap)

        return eligible_snaps

    def __rm_excess_snaps(
        self, policy_lst: list[int], eligible_snaps: list[str] | list
    ) -> None:
        """
        ### Removes excess snapshot(s).\n
        Removes all excess snapshot(s), except for amount that should be kept according to
        passed policy.
        """

        eligible_snaps.sort()

        for snap in eligible_snaps[policy_lst[4] :]:
            proc = subprocess.run(
                [
                    "btrfs",
                    "subvolume",
                    "delete",
                    f"{self.source_snapshot_path}/{snap}",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            if proc.returncode:
                logger.error(
                    "The btrfs snapshot '%s' could not be deleted.\n%s",
                    snap,
                    proc.stderr.strip(),
                )

    def create_snapshot(self) -> None:
        """
        ### Creates snapshot, if 'snapshot_path' and 'subvolume_paths' have been set.\n
        #### Exits application if snapshot creation failed.
        """

        current_time = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M")

        # Check if 'source:btrfs:subvolume_paths' setting exists.
        if "subvolume_paths" not in self.config["source"]["btrfs"]:
            logger.critical(
                """Can not find 'subvolume_paths' setting in 'source:btrfs' section of config file.
                Exiting..."""
            )
            sys.exit(1)

        if self.source_btrfs_snapshot_path and self.source_btrfs_subvolume_paths:
            logger.info("Creating snapshot...")

            for subvol_path in self.source_btrfs_subvolume_paths:
                subvol_path = subvol_path.rstrip("/")
                subvol_name_re = "[^/]+$"
                subvol_name = re.search(subvol_name_re, subvol_path).group()
                snap_name = f"{current_time}_{subvol_name}"
                proc = subprocess.run(
                    [
                        "btrfs",
                        "subvolume",
                        "snapshot",
                        "-r",
                        subvol_path,
                        f"{self.source_btrfs_snapshot_path}/{snap_name}",
                    ],
                    capture_output=True,
                    text=True,
                    check=False,
                )

                if proc.returncode:
                    logger.critical(
                        "Failed to create new btrfs snapshot '%s'.\n%s\nExiting...",
                        snap_name,
                        proc.stderr.strip(),
                    )
                    sys.exit(1)

            logger.info("Finished snapshot creation.")

    def run_retention_policies(self) -> None:
        """
        ### Removes snapshot(s) according to set policies.\n
        Removes snapshot(s) indicated by respective policies time frame and keeps specified number
        of snapshot(s).\n
        #### Only runs if retention policies are set.
        """

        logger.info("Executing retention policies...")

        # Check if 'source:btrfs:retention_policies' setting exists.
        if not self.source_btrfs_retention_policies:
            logger.critical(
                """Can not find 'retention_policies' setting in 'source:btrfs' section of config 
                file. Exiting..."""
            )
            sys.exit(1)

        for policy in self.source_btrfs_retention_policies.values():
            eligible_snaps = self.__calc_eligible_snaps(policy)
            self.__rm_excess_snaps(policy, eligible_snaps)

        logger.debug("Retention policy execution OK.")

    ######################

    def sync_to_target(self) -> None:
        """
        ### Sync btrfs snapshot to target.\n
        Sync source snapshot to target and delete obsolete snapshot from target which are not
        present in source.\n
        #### Exits application if sync could not be executed successfully.
        """

        logger.info("Syncing snapshot to target...")

        # Check if 'target' setting exists.
        if "target" not in self.config:
            logger.critical("Can not find 'target' section in config file. Exiting...")
            sys.exit(1)

        # Check if 'target:btrfs' setting exists.
        if "btrfs" not in self.config["target"]:
            logger.critical(
                "Can not find 'btrfs' setting in 'target' section of config file. Exiting..."
            )
            sys.exit(1)

        # Get source snapshot list.
        s_snap_names = super().get_dir_names(self.source_btrfs_snapshot_path)

        # Get target snapshot list.
        if "remote" in self.config["target"]:
            t_snap_names = super().get_t_rem_dir_names(self.target_btrfs_snapshot_path)
        else:
            t_snap_names = super().get_dir_names(self.target_btrfs_snapshot_path)

        # Sync missing snapshot from source to target.
        if "remote" in self.config["target"]:
            self.__inc_sync_to_rem_t(s_snap_names, t_snap_names)
        else:
            self.__inc_sync_to_t(s_snap_names, t_snap_names)

        logger.debug("Snapshot sync OK.")

        logger.info("Deleting old snapshot on target...")

        # Delete old snapshots on target.
        if "remote" in self.config["target"]:
            self.__del_old_rem_t_snaps(s_snap_names, t_snap_names)
        else:
            self.__del_old_t_snaps(s_snap_names, t_snap_names)

        logger.debug("Old snapshot deletion OK")


class Borg(Backup):
    """
    ### Class for borg methods and attributes.
    """


class Restic(Backup):
    """
    ### Class for restic methods and attributes.
    """
