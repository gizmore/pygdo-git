from gdo.base.GDT import GDT
from gdo.base.Method import Method
from gdo.core.GDT_Object import GDT_Object
from gdo.git.GDO_GitAbo import GDO_GitAbo
from gdo.git.GDO_GitRepo import GDO_GitRepo


class git_watch(Method):

    def gdo_parameters(self) -> [GDT]:
        return [
            GDT_Object('repo').table(GDO_GitRepo.table()).not_null(),
        ]

    def get_repo(self) -> GDO_GitRepo:
        return self.param_value('repo')

    def gdo_execute(self):
        repo = self.get_repo()
        if repo.has_subscribed(self._env_user, self._env_channel):
            return self.err('err_already_subscribed')
        GDO_GitAbo.blank({
            'gra_repo': repo.get_id(),
            'gra_user': self._env_user.get_id() if not self._env_channel else None,
            'gra_channel': self._env_channel.get_id() if self._env_channel else None,
        }).insert()
        return self.reply('msg_subscribed', [repo.render_name()])
