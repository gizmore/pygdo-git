import os
import unittest

from gdo.base.Application import Application
from gdo.base.ModuleLoader import ModuleLoader
from gdo.base.Util import module_enabled
from gdotest.TestUtil import reinstall_module, GDOTestCase


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




if __name__ == '__main__':
    unittest.main()
