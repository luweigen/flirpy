import glob
import logging
import os
import platform
import shutil
import subprocess
import sys

try:
    from importlib.resources import files as _resource_files
except ImportError:
    import pkg_resources
    _resource_files = None

logger = logging.getLogger(__name__)


class Exiftool:
    def __init__(self, path=None):

        if path is None:
            if sys.platform.startswith("win32"):
                if _resource_files is not None:
                    self.path = str(_resource_files("flirpy").joinpath("bin/exiftool.exe"))
                else:
                    self.path = pkg_resources.resource_filename(
                        "flirpy", "bin/exiftool.exe"
                    )
            # Fix problems on ARM Linux platforms (e.g. Raspberry Pi).
            # Exclude macOS (darwin) which also reports arm64 on Apple Silicon.
            elif (platform.uname()[4].startswith("arm")
                  and not sys.platform.startswith("darwin")):
                if os.path.isfile("/usr/bin/exiftool"):
                    self.path = "/usr/bin/exiftool"
                else:
                    logger.warning("Exiftool not installed, try: apt install exiftool")
            else:
                # macOS / Linux x86_64: try bundled binary, fall back to system
                if _resource_files is not None:
                    self.path = str(_resource_files("flirpy").joinpath("bin/exiftool"))
                else:
                    self.path = pkg_resources.resource_filename("flirpy", "bin/exiftool")

                if not os.path.isfile(self.path):
                    system_exiftool = shutil.which("exiftool")
                    if system_exiftool:
                        self.path = system_exiftool
                    else:
                        logger.warning("Exiftool not found")

        else:
            self.path = path
            self._check_path()

    def _check_path(self):
        try:
            subprocess.check_output([self.path])
            logger.info("Exiftool path verified at {}".format(self.path))
            return True
        except FileNotFoundError:
            logger.error("Couldn't find Exiftool at {}".format(self.path))
            return False

        return False

    def copy_meta(self, folder, filemask="%f.fff", output_folder="./", ext="tiff"):

        cwd = folder

        cmd = [self.path]
        cmd.append("-r")
        cmd.append("-overwrite_original")
        cmd.append("-tagsfromfile")
        cmd.append(filemask)
        cmd.append("-ext")
        cmd.append(ext)
        cmd.append(output_folder)

        logger.debug(" ".join(cmd))

        res = subprocess.call(
            cmd, cwd=cwd, stderr=subprocess.PIPE, stdout=subprocess.PIPE
        )
        return res

    def write_meta(self, filemask):

        # Do some mangling here to avoid busting the command line limit.
        # First, we run the command in the right working directory
        cwd = os.path.dirname(filemask)

        cmd = [self.path]
        cmd.append("-ext")
        cmd.append("fff")
        cmd.append(".")
        cmd.append("-w!")
        cmd.append(".txt")

        logger.debug(" ".join(cmd))

        res = subprocess.call(
            cmd, cwd=cwd, stderr=subprocess.PIPE, stdout=subprocess.PIPE
        )

        return res

    def meta_from_file(self, filename):
        meta = {}

        with open(filename, "r") as f:
            for line in f:
                res = line.split(":")

                key = res[0].strip()
                value = "".join(res[1:])

                meta[key] = value

        return meta
