import os
import tempfile
import unittest
from unittest.mock import patch

from gdo.git.GDO_GitRepo import GDO_GitRepo


class RestoreCheckoutTest(unittest.TestCase):
    def test_missing_checkout_clones_saved_url(self):
        with tempfile.TemporaryDirectory() as temp:
            path = os.path.join(temp, 'repos', 'zen')
            with patch.object(GDO_GitRepo, 'ensure_safe_directory'), \
                    patch('gdo.git.GDO_GitRepo.git.Repo.clone_from') as clone:
                GDO_GitRepo.restore_missing_checkout(path, 'https://example.org/zen.git')
            self.assertTrue(os.path.isdir(path))
            clone.assert_called_once_with('https://example.org/zen.git', path)

    def test_existing_directory_is_never_replaced(self):
        with tempfile.TemporaryDirectory() as temp:
            with patch('gdo.git.GDO_GitRepo.git.Repo.clone_from') as clone:
                with self.assertRaisesRegex(ValueError, 'already exists'):
                    GDO_GitRepo.restore_missing_checkout(temp, 'https://example.org/zen.git')
            clone.assert_not_called()

    def test_unsupported_url_does_not_create_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            path = os.path.join(temp, 'zen')
            with self.assertRaisesRegex(ValueError, 'unsupported'):
                GDO_GitRepo.restore_missing_checkout(path, 'ext::dangerous')
            self.assertFalse(os.path.exists(path))
