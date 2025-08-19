from utils import *
import fcntl

class FileMutex:
    def __init__(self, path=LOCK_FILE):
        self.path = path
        self.lockfile = None

    def reserve(self):
        """Try to acquire the lock. Returns True if successful, False otherwise."""
        if self.lockfile is not None:
            return True  # already locked in this process

        self.lockfile = open(self.path, "w")
        try:
            fcntl.flock(self.lockfile, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except BlockingIOError:
            self.lockfile.close()
            self.lockfile = None
            return False

    def release(self):
        """Release the lock if held."""
        if self.lockfile is not None:
            fcntl.flock(self.lockfile, fcntl.LOCK_UN)
            self.lockfile.close()
            self.lockfile = None
            return True
        return False