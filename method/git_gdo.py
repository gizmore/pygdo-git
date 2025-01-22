from gdo.admin.GDT_Module import GDT_Module
from gdo.base.GDO_Module import GDO_Module
from gdo.base.GDT import GDT
from gdo.base.Method import Method
from gdo.base.ModuleLoader import ModuleLoader
from gdo.base.Trans import t
from gdo.base.Util import Arrays
from gdo.install.Installer import Installer


class git_gdo(Method):

    def gdo_trigger(self) -> str:
        return 'git.gdo'

    def gdo_parameters(self) -> list[GDT]:
        return [
            GDT_Module('module').positional(),
        ]

    def get_module(self) -> GDO_Module:
        return self.param_value('module')

    def gdo_execute(self) -> GDT:
        if module := self.get_module():
            return self.git_module_repos(module)
        else:
            return self.git_modules_overview()

    def git_module_repos(self, module: GDO_Module) -> GDT:
        info = Installer.get_repo_info(module)
        return self.reply('msg_git_module', (module.render_name(), f" {t('or') }".join(info[0])))

    def git_modules_overview(self) -> GDT:
        out = []
        for module in ModuleLoader.instance()._cache.values():
            out.append(module.render_name())
        return self.reply('msg_git_modules', (Arrays.human_join(out),))
