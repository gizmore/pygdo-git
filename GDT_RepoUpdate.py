from git import Commit

from gdo.base.GDT import GDT


class GDT_RepoUpdate(GDT):

    _commit: Commit
    _added: int
    _files: int
    _insertions: int
    _deletions: int

    def commit(self, commit: Commit):
        self._commit = commit
        return self

    def added(self, added: int):
        self._added = added
        return self

    def stats(self, files: int, insertions: int, deletions: int):
        self._files = files
        self._insertions = insertions
        self._deletions = deletions
        return self
