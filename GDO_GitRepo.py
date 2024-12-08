from gdo.base.GDO import GDO
from gdo.base.GDT import GDT
from gdo.core.GDO_Channel import GDO_Channel
from gdo.core.GDO_User import GDO_User
from gdo.core.GDT_AutoInc import GDT_AutoInc
from gdo.core.GDT_Char import GDT_Char
from gdo.core.GDT_Creator import GDT_Creator
from gdo.core.GDT_Name import GDT_Name
from gdo.core.GDT_UInt import GDT_UInt
from gdo.date.GDT_Created import GDT_Created
from gdo.date.GDT_Timestamp import GDT_Timestamp
from gdo.net.GDT_Url import GDT_Url


class GDO_GitRepo(GDO):

    def gdo_columns(self) -> list[GDT]:
        return [
            GDT_AutoInc('repo_id'),
            GDT_Name('repo_name').not_null(),
            GDT_Url('repo_url').reachable(True).schemes(['ssh', 'http', 'https']).not_null(),
            GDT_Char('repo_commit').maxlen(40),
            GDT_UInt('repo_commits'),
            GDT_Timestamp('repo_checked'),
            GDT_Created('repo_created'),
            GDT_Creator('repo_creator'),
        ]

    def has_subscribed(self, user: GDO_User, channel: GDO_Channel) -> bool:
        if channel:
            return GDO_GitRepo.table().get_by_vals({}) is not None
        else:
            return GDO_GitRepo.table().get_by_vals({}) is not None
