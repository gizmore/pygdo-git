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
from gdo.net.GDT_Url import GDT_Url


class git_add(Method):

    def gdo_trigger(self) -> str:
        return 'git.add'

    def gdo_parameters(self) -> list[GDT]:
        return [
            GDT_Name('name').not_null(),
            GDT_Url('url').not_null().reachable().external().schemes(['http', 'https']),
        ]

    async def gdo_execute(self) -> GDT:
        url = self.param_val('url')
        name = self.param_val('name')
        repo = GDO_GitRepo.blank({
            'repo_name': name,
            'repo_url': url,
            'repo_checked': Time.get_date(),
        }).insert()
        path = Application.files_path(f"git_repo/{repo.get_id()}_{name}/")
        try:
            Files.create_dir(path)
            await asgiref.sync.SyncToAsync(git.Repo.clone_from)(url, path)
            repo.save_val('repo_ready', Time.get_date())
            return self.reply('msg_cloned_repo', (repo.render_name(), html(url), path))
        except Exception as ex:
            Logger.exception(ex)
            Files.delete_dir(path)
            repo.delete()
            raise ex
