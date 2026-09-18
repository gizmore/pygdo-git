from gdo.base.GDT import GDT
from gdo.base.Method import Method
from gdo.core.GDT_Bool import GDT_Bool
from gdo.core.GDT_Object import GDT_Object
from gdo.git.GDO_GitAbo import GDO_GitAbo
from gdo.git.GDO_GitRepo import GDO_GitRepo


class git_watch(Method):

    @classmethod
    def gdo_trigger(cls) -> str:
        return 'git.abbo'

    def gdo_parameters(self) -> list[GDT]:
        return [
            GDT_Object('repo').table(GDO_GitRepo.table()).not_null().positional(),
            GDT_Bool('enabled').initial('1').positional(),
        ]

    def get_repo(self) -> GDO_GitRepo:
        return self.param_value('repo')

    def gdo_execute(self) -> GDT:
        if repo := self.get_repo():
            abo = GDO_GitAbo.table().get_repo_abo(repo, self._env_user, self._env_channel)
            if self.param_value('enabled'):
                if not abo:
                    GDO_GitAbo.blank({
                        'gra_repo': repo.get_id(),
                        'gra_user': self._env_user.get_id() if not self._env_channel else None,
                        'gra_channel': self._env_channel.get_id() if self._env_channel else None,
                        'gra_creator': self._env_user.get_id(),
                    }).insert()
                return self.reply('msg_git_subscribed', (repo.render_name(),))
            if abo:
                abo.delete()
            return self.reply('msg_git_unsubscribed', (repo.render_name(),))
        return self.reply('msg_git_watches')
