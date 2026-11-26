import unittest
from unittest.mock import MagicMock, mock_open, patch

from gdo.base.Application import Application
from gdo.git.module_git import module_git


class GitTimerProcessTest(unittest.IsolatedAsyncioTestCase):
    def test_guard_requires_own_dog_pid(self):
        with patch.object(Application, 'IS_DOG', True), \
             patch.object(Application, 'IS_HTTP', False), \
             patch.object(Application, 'IS_REPL', False, create=True), \
             patch('gdo.core.method.launch.launch.lock_path', return_value='/test/dog.pid'), \
             patch('gdo.git.module_git.os.getpid', return_value=123), \
             patch('builtins.open', mock_open(read_data='123')):
            self.assertTrue(module_git.is_running_dog_process())
        with patch.object(Application, 'IS_DOG', True), \
             patch.object(Application, 'IS_HTTP', False), \
             patch.object(Application, 'IS_REPL', False, create=True), \
             patch('gdo.core.method.launch.launch.lock_path', return_value='/test/dog.pid'), \
             patch('gdo.git.module_git.os.getpid', return_value=123), \
             patch('builtins.open', mock_open(read_data='456')):
            self.assertFalse(module_git.is_running_dog_process())
        with patch.object(Application, 'IS_DOG', True), \
             patch.object(Application, 'IS_HTTP', True):
            self.assertFalse(module_git.is_running_dog_process())
        with patch.object(Application, 'IS_DOG', True), \
             patch.object(Application, 'IS_REPL', True, create=True):
            self.assertFalse(module_git.is_running_dog_process())
        with patch.object(Application, 'IS_DOG', False):
            self.assertFalse(module_git.is_running_dog_process())

    async def test_timer_skips_check_outside_dog_but_reschedules(self):
        module = module_git()
        events = MagicMock()
        with patch.object(module, 'cfg_sleep', return_value=60), \
             patch.object(module, 'is_running_dog_process', return_value=False), \
             patch.object(Application, 'EVENTS', events, create=True), \
             patch('gdo.git.module_git.GDO_GitRepo.table') as table:
            await module.git_timer()
        table.assert_not_called()
        events.add_timer.assert_called_once_with(60, module.git_timer)
