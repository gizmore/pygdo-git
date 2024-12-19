import git
from git import Repo, InvalidGitRepositoryError

from gdo.base.Application import Application
from gdo.base.GDO import GDO
from gdo.base.GDT import GDT
from gdo.base.Logger import Logger
from gdo.core.GDO_Channel import GDO_Channel
from gdo.core.GDO_User import GDO_User
from gdo.core.GDT_AutoInc import GDT_AutoInc
from gdo.core.GDT_Char import GDT_Char
from gdo.core.GDT_Creator import GDT_Creator
from gdo.core.GDT_Name import GDT_Name
from gdo.core.GDT_UInt import GDT_UInt
from gdo.date.GDT_Created import GDT_Created
from gdo.date.GDT_Timestamp import GDT_Timestamp
from gdo.date.Time import Time
from gdo.git.GDT_RepoUpdate import GDT_RepoUpdate
from gdo.net.GDT_Url import GDT_Url


class GDO_GitRepo(GDO):

    def gdo_columns(self) -> list[GDT]:
        return [
            GDT_AutoInc('repo_id'),
            GDT_Name('repo_name').unique().not_null(),
            GDT_Url('repo_url').reachable(True).external().schemes(['http', 'https']).not_null(),
            GDT_Char('repo_commit').maxlen(40),
            GDT_UInt('repo_commits').not_null().initial('0'),
            GDT_Timestamp('repo_ready'),
            GDT_Timestamp('repo_checked'),
            GDT_Timestamp('repo_changed'),
            GDT_Created('repo_created'),
            GDT_Creator('repo_creator'),
        ]

    def get_repo_name(self) -> str:
        return self.gdo_val('repo_name')

    def get_path(self) -> str:
        return Application.files_path(f"git_repo/{self.get_id()}_{self.get_repo_name()}/")

    def get_repo(self) -> Repo:
        try:
            return git.Repo(self.get_path())
        except InvalidGitRepositoryError:
            return None

    def get_url(self) -> str:
        return self.gdo_val('repo_url')

    def get_commit_count(self) -> int:
        return self.gdo_value('repo_commits')

    def get_commit_hash(self) -> str:
        return self.gdo_val('repo_commit')

    def get_commit_url(self):
        return f"{self.get_url()}/commit/{self.get_commit_hash()}"

    def has_subscribed(self, user: GDO_User, channel: GDO_Channel) -> bool:
        from gdo.git.GDO_GitAbo import GDO_GitAbo
        return GDO_GitAbo.table().has_subscribed(self, user, channel)

    ##########
    # Render #
    ##########
    def render_name(self):
        return f"{self.get_id()}-{self.get_repo_name()}"


    #########
    # Check #
    #########
    async def check_repo(self) -> GDT_RepoUpdate:
        if repo := self.get_repo():
            Logger.debug(f"Checking repo {self.render_name()}")
            changed = False
            o = repo.remotes.origin
            o.pull()
            new_count = 0
            old_count = self.gdo_value('repo_commits')
            last_hash = self.gdo_val('repo_commit')
            last_commit = None
            new_hash = last_hash
            repo_changed = self.gdo_val('repo_changed')
            for commit in repo.iter_commits():
                if str(commit.hexsha) == last_hash:
                    break
                new_count += 1
                if not changed:
                    last_commit = commit
                    changed = True
                    new_hash = str(commit.hexsha)
                    repo_changed = Time.get_date()
            self.save_vals({
                'repo_changed': repo_changed,
                'repo_commit': new_hash,
                'repo_commits': old_count + new_count,
                'repo_checked': Time.get_date(),
            })
            if not changed:
                return None
            return GDT_RepoUpdate().commit(last_commit).added(new_count)
        else:
            self.save_vals({
                'repo_checked': Time.get_date(),
            })
            raise Exception(f"Invalid Repo! {self.render_name()}")
