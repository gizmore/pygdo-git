from gdo.base.GDO import GDO
from gdo.base.GDT import GDT
from gdo.core.GDT_AutoInc import GDT_AutoInc
from gdo.core.GDT_Channel import GDT_Channel
from gdo.core.GDT_Creator import GDT_Creator
from gdo.core.GDT_Object import GDT_Object
from gdo.core.GDT_User import GDT_User
from gdo.date.GDT_Created import GDT_Created
from gdo.git.GDO_GitRepo import GDO_GitRepo


class GDO_GitAbo(GDO):

    def gdo_columns(self) -> list[GDT]:
        return [
            GDT_AutoInc('gra_id'),
            GDT_Object('gra_repo').table(GDO_GitRepo.table()).not_null(),
            GDT_User('gra_user'),
            GDT_Channel('gra_channel'),
            GDT_Created('gra_created'),
            GDT_Creator('gra_creator'),
        ]
