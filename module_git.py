from gdo.base.Application import Application
from gdo.base.GDO_Module import GDO_Module
from gdo.base.GDT import GDT
from gdo.base.GDO import GDO
from gdo.date.GDT_Duration import GDT_Duration
from gdo.date.Time import Time
from gdo.git.GDO_GitAbo import GDO_GitAbo
from gdo.git.GDO_GitRepo import GDO_GitRepo
from gdo.git.GDO_GitPullRequest import GDO_GitPullRequest


class module_git(GDO_Module):

    ##########
    # Config #
    ##########

    def gdo_module_config(self) -> list[GDT]:
        return [
            GDT_Duration('git_check_sleep').not_null().min(30).max(Time.ONE_WEEK).initial('1m'),
        ]

    def cfg_sleep(self) -> float:
        return self.get_config_value('git_check_sleep')

    ##########
    # Module #
    ##########
    def gdo_classes(self) -> list[type[GDO]]:
        return [
            GDO_GitRepo,
            GDO_GitAbo,
            GDO_GitPullRequest,
        ]

    ##########
    # Events #
    ##########

    def gdo_subscribe_events(self):
        Application.EVENTS.add_timer(self.cfg_sleep(), self.git_timer)

    async def git_timer(self):
        sleep = self.cfg_sleep()
        try:
            cut = Time.get_date(Application.TIME - sleep)
            if repo := GDO_GitRepo.table().select().where(f"repo_ready IS NOT NULL AND repo_checked < '{cut}'").order('repo_checked').first().exec().fetch_object():
                if update := await repo.check_repo():
                    await GDO_GitAbo.table().announce(repo, update)
                for pull in repo.check_pull_requests():
                    await GDO_GitAbo.table().announce_pull_request(repo, pull)

        finally:
            Application.EVENTS.add_timer(sleep, self.git_timer)
