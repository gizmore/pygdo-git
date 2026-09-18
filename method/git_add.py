import os

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
from gdo.git.GDT_GitProvider import GDT_GitProvider
from gdo.core.GDT_String import GDT_String


class git_add(Method):

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
        if os.path.exists(path):
            raise ValueError('The checkout path already exists.')
        repo = GDO_GitRepo.blank({
            'repo_name': name,
            'repo_url': url,
            'repo_provider': GDO_GitRepo.detect_provider(url) if provider == GDT_GitProvider.GENERIC else provider,
            'repo_checked': Time.get_date(),
        }).insert()
        try:
            Files.create_dir(path)
            checkout = await asgiref.sync.SyncToAsync(git.Repo.clone_from)(url, path)
            # Baseline the clone: only commits received after git.add should
            # be announced by the polling timer.
            repo.save_vals({
                'repo_ready': Time.get_date(),
                'repo_commit': str(checkout.head.commit.hexsha),
                'repo_commits': sum(1 for _ in checkout.iter_commits()),
            })
            return self.reply('msg_cloned_repo', (repo.render_name(), html(url), path))
        except Exception as ex:
            Logger.exception(ex)
            Files.delete_dir(path)
            repo.delete()
            raise ex

    @staticmethod
    def is_git_url(url: str) -> bool:
        import re
        return (
            url.startswith(('https://', 'http://', 'ssh://', 'git://')) or
            bool(re.fullmatch(r'[A-Za-z0-9_.-]+@[A-Za-z0-9_.-]+:[^\s]+', url))
        ) and not url.startswith('ext::')
