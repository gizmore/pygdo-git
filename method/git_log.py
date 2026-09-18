from gdo.base.GDT import GDT
from gdo.base.Method import Method
from gdo.core.GDT_Object import GDT_Object
from gdo.core.GDT_UInt import GDT_UInt
from gdo.git.GDO_GitRepo import GDO_GitRepo


class git_log(Method):
    """Show the local Git history; works as a web page and in chat."""

    def gdo_method_hidden(self) -> bool:
        return True

    @classmethod
    def gdo_trigger(cls) -> str:
        return 'git.log'

    def gdo_parameters(self) -> list[GDT]:
        return [
            GDT_Object('repo').table(GDO_GitRepo.table()).not_null().positional(),
            GDT_UInt('limit').initial('10').min(1).max(50),
        ]

    def gdo_execute(self) -> GDT:
        repo = self.param_value('repo')
        local = repo.get_repo()
        if not local:
            return self.reply('msg_git_not_ready', (repo.render_name(),))
        link_base = repo.get_commit_url().rsplit('/commit/', 1)[0] if repo.get_commit_url() else ''
        lines = []
        for commit in list(local.iter_commits())[:self.param_value('limit')]:
            sha = str(commit.hexsha)
            link = f'{link_base}/commit/{sha}' if link_base else sha[:10]
            lines.append(f'{sha[:10]} {commit.author.name}: {commit.message.strip()} {link}')
        return self.reply('msg_git_log', (repo.render_name(), '\n'.join(lines) or '-'))
