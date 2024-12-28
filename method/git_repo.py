from gdo.base.GDO import GDO
from gdo.base.GDT import GDT
from gdo.base.Method import Method
from gdo.base.Query import Query
from gdo.core.GDT_Bool import GDT_Bool
from gdo.core.GDT_Object import GDT_Object
from gdo.git.GDO_GitRepo import GDO_GitRepo
from gdo.table.MethodQueryTable import MethodQueryTable


class git_repo(Method):

    def gdo_trigger(self) -> str:
        return 'git.repo'

    def gdo_parameters(self) -> list[GDT]:
        return [
            GDT_Object('repo').table(GDO_GitRepo.table()).not_null(),
        ]

    def get_repo(self) -> GDO_GitRepo:
        return self.param_value('repo')

    def gdo_execute(self) -> GDT:
        repo = self.get_repo()
        return self.reply('msg_git_repo', [repo.get_commit_count(), repo.render_name(), repo.get_commit_url()])
