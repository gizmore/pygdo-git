import os
import unittest
from unittest.mock import MagicMock, patch

from gdo.base.Application import Application
from gdo.base.ModuleLoader import ModuleLoader
from gdo.base.Util import module_enabled
from gdotest.TestUtil import reinstall_module, GDOTestCase
from gdo.git.GDO_GitRepo import GDO_GitRepo
from gdo.git.GDT_GitProvider import GDT_GitProvider


class GitTest(GDOTestCase):

    def setUp(self):
        super().setUp()
        Application.init(os.path.dirname(__file__ + "/../../../../"))
        loader = ModuleLoader.instance()
        loader.load_modules_db(True)
        loader.init_modules(True, True)
        loader.init_cli()

    def test_00_install(self):
        reinstall_module('git')
        reinstall_module('git')
        self.assertTrue(module_enabled('git'), 'Install git does not work')

    def test_01_install2(self):
        pass

    def test_02_pull_request_baseline_and_new_pr(self):
        repo = GDO_GitRepo.blank({
            'repo_name': 'pull-test',
            'repo_url': 'https://github.com/example/pull-test.git',
            'repo_provider': GDT_GitProvider.GITHUB,
        }).insert()

        def api_response(pulls):
            response = MagicMock()
            response.read.return_value = __import__('json').dumps(pulls).encode()
            request = MagicMock()
            request.__enter__.return_value = response
            return request

        first = [{
            'number': 1, 'title': 'Existing PR',
            'html_url': 'https://github.com/example/pull-test/pull/1',
            'user': {'login': 'existing'}, 'state': 'open',
            'updated_at': '2026-09-18T00:00:00Z',
        }]
        second = first + [{
            'number': 2, 'title': 'New PR',
            'html_url': 'https://github.com/example/pull-test/pull/2',
            'user': {'login': 'new'}, 'state': 'open',
            'updated_at': '2026-09-18T00:01:00Z',
        }]
        with patch('gdo.git.GDO_GitRepo.urlopen', side_effect=[api_response(first), api_response(second)]):
            self.assertEqual([], repo.check_pull_requests())
            created = repo.check_pull_requests()
        self.assertEqual(1, len(created))
        self.assertEqual(2, created[0].gdo_val('gpr_number'))




if __name__ == '__main__':
    unittest.main()
