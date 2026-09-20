import os
import json
import asyncio
import subprocess
from dataclasses import dataclass
from urllib.error import URLError, HTTPError
from urllib.request import Request, urlopen

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


@dataclass(frozen=True)
class GitCommitInfo:
    message: str
    author_name: str


@dataclass(frozen=True)
class GitRepoScan:
    commit: GitCommitInfo | None
    commit_hash: str
    count: int
    files: int
    insertions: int
    deletions: int


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
            GDT_Timestamp('repo_pr_ready'),
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

    def _pull_requests_due(self) -> bool:
        if self.get_provider() != GDT_GitProvider.GITHUB:
            return False
        # The regular Git poll is intentionally frequent so commits appear
        # quickly.  GitHub's unauthenticated REST quota is not.  Reuse the
        # readiness timestamp as the last successful PR scan and keep this
        # API request to an hourly cadence.
        if (last_checked := self.gdo_val('repo_pr_ready')) and \
                Time.get_time(last_checked) > Application.TIME - Time.ONE_HOUR:
            return False
        return True

    def _fetch_pull_requests(self) -> list:
        """Perform only the blocking forge request; safe to run in a worker."""
        base = self.get_web_url().replace('https://github.com/', '', 1)
        request = Request(f'https://api.github.com/repos/{base}/pulls?state=open&per_page=100',
                          headers={'Accept': 'application/vnd.github+json', 'User-Agent': 'PyGDO-Git'})
        with urlopen(request, timeout=10) as response:
            pulls = json.load(response)
        if not isinstance(pulls, list):
            raise json.JSONDecodeError('expected pull request list', '', 0)
        return pulls

    def _store_pull_requests(self, pulls: list) -> list:
        """Persist PR state on the Dog thread after a worker fetch completed."""
        from gdo.git.GDO_GitPullRequest import GDO_GitPullRequest
        baseline = not self.gdo_val('repo_pr_ready')
        created = []
        for pull in pulls:
            values = {'gpr_repo': self.get_id(), 'gpr_number': pull['number'],
                      'gpr_title': pull['title'], 'gpr_url': pull['html_url'],
                      'gpr_author': pull['user']['login'], 'gpr_state': pull['state'],
                      'gpr_updated': pull['updated_at'].replace('T', ' ').replace('Z', '')}
            known = GDO_GitPullRequest.table().get_by_vals({'gpr_repo': self.get_id(), 'gpr_number': pull['number']})
            if known:
                known.save_vals(values)
            else:
                pull = GDO_GitPullRequest.blank(values).insert()
                if not baseline:
                    created.append(pull)
        self.save_val('repo_pr_ready', Time.get_date())
        return created

    def _pull_request_error(self, error: Exception) -> list:
        # A forge API outage must not stop ordinary Git polling. A rate limit
        # is also an outage for this optional watcher; defer retrying it.
        Logger.warning(f"Cannot check pull requests for {self.render_name()}: {error}")
        self.save_val('repo_pr_ready', Time.get_date())
        return []

    def check_pull_requests(self) -> list:
        """Synchronous compatibility helper used by CLI/tests."""
        if not self._pull_requests_due():
            return []
        try:
            pulls = self._fetch_pull_requests()
        except (HTTPError, URLError, OSError, json.JSONDecodeError) as error:
            return self._pull_request_error(error)
        return self._store_pull_requests(pulls)

    async def check_pull_requests_async(self) -> list:
        """Non-blocking PR polling for the Dog event loop."""
        if not self._pull_requests_due():
            return []
        try:
            pulls = await asyncio.to_thread(self._fetch_pull_requests)
        except (HTTPError, URLError, OSError, json.JSONDecodeError) as error:
            return self._pull_request_error(error)
        return self._store_pull_requests(pulls)

    ##########
    # Render #
    ##########
    def render_name(self):
        return f"{self.get_id()}-{self.get_repo_name()}"


    #########
    # Check #
    #########
    async def check_repo(self) -> GDT_RepoUpdate:
        try:
            if not self.get_repo():
                raise Exception(f"Invalid Repo! {self.render_name()}")

            Logger.debug(f"Checking repo {self.render_name()}")
            old_hash = self.gdo_val('repo_commit')
            scan = await asyncio.to_thread(self._pull_and_scan, self.get_path(), old_hash)
        except Exception:
            # A broken or inaccessible checkout must not monopolize the
            # single-repository polling turn. The next oldest repo can then
            # be checked on the following timer tick.
            self.save_val('repo_checked', Time.get_date())
            raise
        self.save_vals({
            'repo_changed': Time.get_date() if scan.commit else self.gdo_val('repo_changed'),
            'repo_commit': scan.commit_hash,
            'repo_commits': self.gdo_value('repo_commits') + scan.count,
            'repo_checked': Time.get_date(),
        })
        if not scan.commit:
            return None
        return GDT_RepoUpdate().commit(scan.commit).added(scan.count).stats(
            scan.files, scan.insertions, scan.deletions)

    @staticmethod
    def _pull_and_scan(path: str, last_hash: str) -> 'GitRepoScan':
        """Perform blocking GitPython work outside the connector event loop."""
        GDO_GitRepo.ensure_safe_directory(path)
        repo = git.Repo(path)
        repo.remotes.origin.pull()
        count = insertions = deletions = 0
        changed_files = set()
        latest = None
        commit_hash = last_hash
        for commit in repo.iter_commits():
            if str(commit.hexsha) == last_hash:
                break
            count += 1
            stats = commit.stats
            changed_files.update(stats.files.keys())
            insertions += stats.total.get('insertions', 0)
            deletions += stats.total.get('deletions', 0)
            if latest is None:
                latest = GitCommitInfo(commit.message, commit.author.name)
                commit_hash = str(commit.hexsha)
        return GitRepoScan(latest, commit_hash, count, len(changed_files), insertions, deletions)

    @staticmethod
    def ensure_safe_directory(path: str) -> None:
        """Trust one application-managed checkout for the Dog user only."""
        path = os.path.abspath(path)
        result = subprocess.run(
            ['git', 'config', '--global', '--get-all', 'safe.directory'],
            capture_output=True, check=True, text=True)
        if path not in result.stdout.splitlines():
            subprocess.run(
                ['git', 'config', '--global', '--add', 'safe.directory', path],
                check=True)
