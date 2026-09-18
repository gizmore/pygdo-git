from gdo.base.Trans import t
from gdo.core.GDT_Enum import GDT_Enum


class GDT_GitProvider(GDT_Enum):
    """Known forge URL layouts; generic remotes remain fully supported."""

    GENERIC = 'generic'
    GITHUB = 'github'
    GITLAB = 'gitlab'
    GITEA = 'gitea'  # Includes Forgejo and Codeberg.
    BITBUCKET = 'bitbucket'

    def __init__(self, name: str = 'repo_provider'):
        super().__init__(name)
        self.not_null().initial(self.GENERIC).icon('select')

    def gdo_choices(self) -> dict:
        return {
            self.GENERIC: t('git_provider_generic'),
            self.GITHUB: 'GitHub',
            self.GITLAB: 'GitLab',
            self.GITEA: 'Gitea / Forgejo / Codeberg',
            self.BITBUCKET: 'Bitbucket',
        }
