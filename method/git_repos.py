from gdo.base.GDO import GDO
from gdo.git.GDO_GitRepo import GDO_GitRepo
from gdo.table.MethodQueryTable import MethodQueryTable


class git_repos(MethodQueryTable):

    def gdo_trigger(self) -> str:
        return 'git.repos'

    def gdo_table(self) -> GDO:
        return GDO_GitRepo.table()
