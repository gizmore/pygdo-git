import os

import git
from git import Repo, InvalidGitRepositoryError, NoSuchPathError

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
from gdo.git.GDT_GitProvider import GDT_GitProvider
from gdo.core.GDT_String import GDT_String


class GDO_GitRepo(GDO):

    def gdo_columns(self) -> list[GDT]:
        return [
            GDT_AutoInc('repo_id'),
            GDT_Name('repo_name').unique().not_null(),
            # A Git remote is not necessarily a web URL: git@host:owner/repo.git
            # and ssh:// URLs are normal, supported repository locations.
            GDT_String('repo_url').not_null().maxlen(1024),
            GDT_GitProvider('repo_provider'),
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
        path = Application.files_path(f"git_repo/{self.get_repo_name()}/")
        if os.path.isdir(path):
            return path
        # Keep repositories created by the pre-shortname layout usable during
        # an upgrade; new checkouts always use the cleaner shortname path.
        legacy = Application.files_path(f"git_repo/{self.get_id()}_{self.get_repo_name()}/")
        return legacy if os.path.isdir(legacy) else path

    def get_repo(self) -> Repo:
        try:
            return git.Repo(self.get_path())
        except (InvalidGitRepositoryError, NoSuchPathError):
            return None

    def get_url(self) -> str:
        return self.gdo_val('repo_url')

    def get_provider(self) -> str:
        return self.gdo_val('repo_provider') or GDT_GitProvider.GENERIC

    @staticmethod
    def detect_provider(url: str) -> str:
        host = url.lower()
        if 'github.com' in host:
            return GDT_GitProvider.GITHUB
        if 'gitlab' in host:
            return GDT_GitProvider.GITLAB
        if 'gitea' in host or 'forgejo' in host or 'codeberg.org' in host:
            return GDT_GitProvider.GITEA
        if 'bitbucket.org' in host:
            return GDT_GitProvider.BITBUCKET
        return GDT_GitProvider.GENERIC

    def get_commit_count(self) -> int:
        return self.gdo_value('repo_commits')

    def get_commit_hash(self) -> str:
        return self.gdo_val('repo_commit')

    def get_web_url(self) -> str:
        url = self.get_url().removesuffix('.git')
        if url.startswith(('https://', 'http://')):
            return url
        # Common SSH Git syntax maps cleanly to a browser URL for GitHub,
        # Gitea, GitLab and most self-hosted forges. Bare Git remotes simply
        # have no browseable commit URL, which is fine.
        import re
        match = re.match(r'^(?:ssh://)?(?:[^@/]+@)?([^/:]+)[:/]([^\s]+)$', url)
        if match:
            return f"https://{match.group(1)}/{match.group(2)}"
        return ''

    def get_commit_url(self, commit: str | None = None) -> str:
        commit = commit or self.get_commit_hash()
        if not (base := self.get_web_url()):
            return ''
        if self.get_provider() == GDT_GitProvider.GITLAB:
            return f'{base}/-/commit/{commit}'
        if self.get_provider() == GDT_GitProvider.BITBUCKET:
            return f'{base}/commits/{commit}'
        return f'{base}/commit/{commit}'

    def get_compare_url(self, old: str, new: str) -> str:
        """Return a forge diff link, or an empty string for plain Git remotes."""
        if not (base := self.get_web_url()):
            return ''
        provider = self.get_provider()
        if provider == GDT_GitProvider.GITLAB:
            return f'{base}/-/compare?from={old}&to={new}'
        if provider == GDT_GitProvider.BITBUCKET:
            return f'{base}/branches/compare/{old}..{new}'
        if provider in (GDT_GitProvider.GITHUB, GDT_GitProvider.GITEA):
            return f'{base}/compare/{old}...{new}'
        return ''

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
