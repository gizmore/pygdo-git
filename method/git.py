from gdo.base.GDT import GDT
from gdo.base.Method import Method


class git(Method):
    """Show the compact chat reference for the Git module."""

    @classmethod
    def gdo_trigger(cls) -> str:
        return 'git'

    def gdo_execute(self) -> GDT:
        return self.reply('msg_git_help')
