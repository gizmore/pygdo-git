from gdo.base.GDO import GDO
from gdo.base.GDT import GDT
from gdo.core.GDT_AutoInc import GDT_AutoInc
from gdo.core.GDT_Char import GDT_Char
from gdo.core.GDT_Object import GDT_Object
from gdo.core.GDT_String import GDT_String
from gdo.core.GDT_UInt import GDT_UInt
from gdo.core.GDT_Unique import GDT_Unique
from gdo.date.GDT_Timestamp import GDT_Timestamp
from gdo.git.GDO_GitRepo import GDO_GitRepo
from gdo.net.GDT_Url import GDT_Url


class GDO_GitPullRequest(GDO):
    def gdo_columns(self) -> list[GDT]:
        return [
            GDT_AutoInc('gpr_id'),
            GDT_Object('gpr_repo').table(GDO_GitRepo.table()).not_null().cascade_delete(),
            GDT_UInt('gpr_number').not_null(),
            # Forge titles are free text, not a local object identifier.
            GDT_String('gpr_title').not_null().maxlen(255),
            GDT_Url('gpr_url').not_null().maxlen(1024),
            GDT_String('gpr_author').not_null().maxlen(128),
            GDT_Char('gpr_state').not_null().maxlen(16).initial('open'),
            GDT_Timestamp('gpr_updated'),
            GDT_Unique('unique_repo_number').unique_columns('gpr_repo', 'gpr_number'),
        ]
