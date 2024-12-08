from gdo.base.GDO import GDO
from gdo.base.GDT import GDT
from gdo.core.GDT_AutoInc import GDT_AutoInc
from gdo.core.GDT_Creator import GDT_Creator
from gdo.core.GDT_Name import GDT_Name
from gdo.core.GDT_String import GDT_String
from gdo.core.GDT_UInt import GDT_UInt
from gdo.date.GDT_Created import GDT_Created
from gdo.net.GDT_Url import GDT_Url


class GDO_GitRepo(GDO):

    def gdo_columns(self) -> list[GDT]:
        return [
            GDT_AutoInc('repo_id'),
            GDT_Name('repo_name'),
            GDT_Url('repo_url').reachable(True).schemes(['ssh', 'http', 'https']).not_null(),
            GDT_String('repo_commit'),
            GDT_UInt('repo_commits'),
            GDT_Created('repo_created'),
            GDT_Creator('repo_creator'),
        ]
