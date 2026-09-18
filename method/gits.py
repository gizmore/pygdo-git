from gdo.base.GDT import GDT
from gdo.base.Method import Method
from gdo.git.GDO_GitRepo import GDO_GitRepo


class gits(Method):
    """List all watched Git repositories in text connectors."""

    @classmethod
    def gdo_trigger(cls) -> str:
        return 'gits'

    def gdo_execute(self) -> GDT:
        repos = GDO_GitRepo.table().select().order('repo_name').exec().fetch_all()
        listing = ', '.join(repo.render_name() for repo in repos) or '-'
        return self.reply('msg_git_repos', (listing,))
