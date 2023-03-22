import subprocess

from settings.config import RES2DINV_EXE


def invert_batch_file(BATCH_FILE: str) -> None:
    subprocess.call([RES2DINV_EXE, BATCH_FILE])