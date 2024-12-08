from gdo.base.Application import Application
from gdo.base.GDO_Module import GDO_Module
from gdo.date.Time import Time
from gdo.git.GDO_GitAbo import GDO_GitAbo
from gdo.git.GDO_GitRepo import GDO_GitRepo


class module_git(GDO_Module):

    def gdo_classes(self):
        return [
            GDO_GitRepo,
            GDO_GitAbo,
        ]

    def gdo_subscribe_events(self):
        Application.EVENTS.add_timer(Time.ONE_MINUTE, self.git_timer, Application.EVENTS.FOREVER)

    def git_timer(self):
        pass