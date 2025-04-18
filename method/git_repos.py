from gdo.base.GDO import GDO
from gdo.base.GDT import GDT
from gdo.base.Query import Query
from gdo.core.GDT_Bool import GDT_Bool
from gdo.git.GDO_GitRepo import GDO_GitRepo
from gdo.table.MethodQueryTable import MethodQueryTable


class git_repos(MethodQueryTable):

    @classmethod
    def gdo_trigger(cls) -> str:
        return 'git.repos'

    def gdo_parameters(self) -> list[GDT]:
        return [
            GDT_Bool('watched').initial('0'),
        ]

    def gdo_table(self) -> GDO:
        return GDO_GitRepo.table()

    def gdo_table_query(self) -> Query:
        query = super().gdo_table_query()
        if self.param_value('watched'):
            query.where('1')
        return query
