import os
import subprocess

import asgiref.sync
import git

from gdo.base.Application import Application
from gdo.base.GDT import GDT
from gdo.base.Logger import Logger
from gdo.base.Method import Method
from gdo.base.Util import Files, html
from gdo.core.GDT_Name import GDT_Name
from gdo.date.Time import Time
from gdo.git.GDO_GitRepo import GDO_GitRepo
from gdo.git.GDO_GitAbo import GDO_GitAbo
from gdo.git.GDT_GitProvider import GDT_GitProvider
from gdo.core.GDT_String import GDT_String


class git_add(Method):

    def gdo_method_hidden(self) -> bool:
        return True

    @classmethod
    def gdo_trigger(cls) -> str:
        return 'git.add'

    def gdo_parameters(self) -> list[GDT]:
        return [
            GDT_Name('name').not_null().positional(),
            GDT_String('url').not_null().maxlen(1024).positional(),
            GDT_GitProvider('provider').positional(),
        ]

    async def gdo_execute(self) -> GDT:
        url = self.param_val('url')
        name = self.param_val('name')
        provider = self.param_val('provider')
        if not self.is_git_url(url):
            raise ValueError('Unsupported Git URL. Use https://, ssh://, git:// or git@host:path.')
        if GDO_GitRepo.table().get_by_vals({'repo_name': name}):
            raise ValueError('A repository with that shortname already exists.')
        path = Application.files_path(f"git_repo/{name}/")
        self.ensure_safe_directory(path)
        # A module reinstall can remove the database row while deliberately
        # preserving files.  Let the owner register that already-existing,
        # matching checkout again instead of requiring manual file removal.
        checkout = None
        if os.path.exists(path):
            try:
                checkout = git.Repo(path)
                origin = checkout.remotes.origin.url
                if self.normalize_url(origin) != self.normalize_url(url):
                    raise ValueError('The existing checkout has a different origin URL.')
            except (git.InvalidGitRepositoryError, AttributeError) as ex:
                raise ValueError('The checkout path already exists but is not a Git repository.') from ex
        reused_checkout = checkout is not None
        repo = GDO_GitRepo.blank({
            'repo_name': name,
            'repo_url': url,
            'repo_provider': GDO_GitRepo.detect_provider(url) if provider == GDT_GitProvider.GENERIC else provider,
            'repo_checked': Time.get_date(),
        }).insert()
        try:
            if not reused_checkout:
                Files.create_dir(path)
                checkout = await asgiref.sync.SyncToAsync(git.Repo.clone_from)(url, path)
            # Baseline the clone: only commits received after git.add should
            # be announced by the polling timer.
            repo.save_vals({
                'repo_ready': Time.get_date(),
                'repo_commit': str(checkout.head.commit.hexsha),
                'repo_commits': sum(1 for _ in checkout.iter_commits()),
            })
            self.subscribe_current_target(repo)
            return self.reply('msg_cloned_repo', (repo.render_name(), html(url), path))
        except Exception as ex:
            Logger.exception(ex)
            # Do not delete a valid checkout that was merely being
            # re-registered after a module/database reinstall.
            if not reused_checkout:
                Files.delete_dir(path)
            repo.delete()
            raise ex

    def subscribe_current_target(self, repo: GDO_GitRepo) -> None:
        """Subscribe the invoking user or channel exactly once after git.add."""
        user = self._env_user
        channel = self._env_channel
        if GDO_GitAbo.table().get_repo_abo(repo, user, channel):
            return
        GDO_GitAbo.blank({
            'gra_repo': repo.get_id(),
            'gra_user': user.get_id() if not channel else None,
            'gra_channel': channel.get_id() if channel else None,
            'gra_creator': user.get_id(),
        }).insert()

    @staticmethod
    def ensure_safe_directory(path: str) -> None:
        """Trust an application-managed checkout for the Dog's Git user."""
        path = os.path.abspath(path)
        result = subprocess.run(
            ['git', 'config', '--global', '--get-all', 'safe.directory'],
            capture_output=True, check=True, text=True)
        if path not in result.stdout.splitlines():
            subprocess.run(
                ['git', 'config', '--global', '--add', 'safe.directory', path],
                check=True)

    @staticmethod
    def is_git_url(url: str) -> bool:
        import re
        return (
            url.startswith(('https://', 'http://', 'ssh://', 'git://')) or
            bool(re.fullmatch(r'[A-Za-z0-9_.-]+@[A-Za-z0-9_.-]+:[^\s]+', url))
        ) and not url.startswith('ext::')

    @staticmethod
    def normalize_url(url: str) -> str:
        return url.removesuffix('/').removesuffix('.git').lower()
