import asgiref.sync
import git

from gdo.base.Application import Application
from gdo.base.GDT import GDT
from gdo.base.Method import Method
from gdo.base.Util import Files, html
from gdo.core.GDT_Name import GDT_Name
from gdo.git.GDO_GitRepo import GDO_GitRepo
from gdo.net.GDT_Url import GDT_Url


class git_add(Method):

    def gdo_trigger(self) -> str:
        return 'git.add'

    def gdo_parameters(self) -> [GDT]:
        return [
            GDT_Name('name').not_null(),
            GDT_Url('url').not_null().reachable().schemes(['http', 'https', 'ssh']),
        ]

    async def gdo_execute(self):
        url = self.param_val('url')
        name = self.param_val('name')
        GDO_GitRepo.blank({
            'repo_name': name,
            'repo_url': url,
        }).insert()
        path = Application.files_path(f"git_repo/{name}")
        Files.create_dir(path)
        await asgiref.sync.SyncToAsync(git.Repo.clone_from)(url, path)
        return self.reply('msg_cloned_repo', [html(url), html(path)])
