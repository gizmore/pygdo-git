from gdo.base.GDO import GDO
from gdo.base.GDT import GDT
from gdo.base.Render import Render
from gdo.base.Trans import Trans, tiso
from gdo.core.GDO_Channel import GDO_Channel
from gdo.core.GDO_User import GDO_User
from gdo.core.GDT_AutoInc import GDT_AutoInc
from gdo.core.GDT_Channel import GDT_Channel
from gdo.core.GDT_Creator import GDT_Creator
from gdo.core.GDT_Object import GDT_Object
from gdo.core.GDT_Unique import GDT_Unique
from gdo.core.GDT_User import GDT_User
from gdo.date.GDT_Created import GDT_Created
from gdo.git.GDO_GitRepo import GDO_GitRepo
from gdo.git.GDT_RepoUpdate import GDT_RepoUpdate


class GDO_GitAbo(GDO):

    def gdo_columns(self) -> list[GDT]:
        return [
            GDT_AutoInc('gra_id'),
            GDT_Object('gra_repo').table(GDO_GitRepo.table()).not_null().cascade_delete(),
            GDT_User('gra_user'),
            GDT_Channel('gra_channel'),
            GDT_Created('gra_created'),
            GDT_Creator('gra_creator'),
            GDT_Unique('unique_user').unique_columns('gra_user', 'gra_repo'),
            GDT_Unique('unique_chan').unique_columns('gra_channel', 'gra_repo'),
        ]

    def get_user(self) -> GDO_User:
        return self.gdo_value('gra_user')

    def get_channel(self) -> GDO_Channel:
        return self.gdo_value('gra_channel')

    async def get_user_abo(self, repo: GDO_GitRepo, user: GDO_User) -> 'GDO_GitAbo':
        return await self.table().get_by_vals({'gra_user': user.get_id(), 'gra_repo': repo.get_id()})

    async def get_channel_abo(self, repo: GDO_GitRepo, channel: GDO_Channel) -> 'GDO_GitAbo':
        return await self.table().get_by_vals({'gra_channel': channel.get_id(), 'gra_repo': repo.get_id()})

    async def get_repo_abo(self, repo: GDO_GitRepo, user: GDO_User, channel: GDO_Channel):
        return await self.get_channel_abo(repo, channel) if channel else await self.get_user_abo(repo, user)

    def has_subscribed(self, repo: GDO_GitRepo, user: GDO_User, channel: GDO_Channel) -> bool:
        return True if self.get_repo_abo(repo, user, channel) else False

    def get_repo_abos(self, repo: GDO_GitRepo) -> list['GDO_GitAbo']:
        return self.table().select().where(f'gra_repo={repo.get_id()}').exec().fetch_all()

    async def announce(self, repo: GDO_GitRepo, update: GDT_RepoUpdate):
        commit = update._commit
        for abo in self.get_repo_abos(repo):
            if chan := abo.get_channel():
                await chan.send(tiso(chan.get_lang_iso(), 'msg_git_update', [update._added, repo.get_commit_url(), Render.bold(commit.message.strip(), chan.get_server().get_connector().get_render_mode()), commit.author.name]))
            elif user := abo.get_user():
                await user.send('msg_git_update', [update._added, repo.get_commit_url(), Render.bold(commit.message.strip(), user.get_server().get_connector().get_render_mode()), commit.author.name])
            else:
                raise Exception("git abbo announce in not possible state.")
