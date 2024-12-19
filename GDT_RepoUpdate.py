from git import Commit

from gdo.base.GDT import GDT


class GDT_RepoUpdate(GDT):

    _commit: Commit
    _added: int

    def commit(self, commit: Commit):
        self._commit = commit
        return self

    def added(self, added: int):
        self._added = added
        return self
