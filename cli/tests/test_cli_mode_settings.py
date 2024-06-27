import unittest
from unittest.mock import patch, mock_open, MagicMock
import os

from cli.onionshare_cli.mode_settings import ModeSettings, global_branch_coverage, overall_branch_coverage

class CommonMock:
    def __init__(self, platform):
        self.platform = platform
    
    def build_password(self, length):
        return "mocked_password"
    
    def build_persistent_dir(self):
        return "/mocked/persistent/dir"
    
    def log(self, *args):
        pass

class TestModeSettings(unittest.TestCase):
    def setUp(self):
        for key in global_branch_coverage:
            global_branch_coverage[key] = False

    def tearDown(self):
        ModeSettings.print_global_coverage()

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='{"persistent": {"enabled": true}}')
    @patch('json.load')
    def test_load_existing_file(self, mock_json_load, mock_open, mock_path_exists):
        """Test loading settings from an existing file."""
        mock_path_exists.return_value = True
        mock_json_load.return_value = {"persistent": {"enabled": True}}

        common = CommonMock(platform='Linux')
        mode_settings = ModeSettings(common, filename="test.json")

        mode_settings.load()

        self.assertTrue(mode_settings.get("persistent", "enabled"))
        self.assertEqual(mock_open.call_count, 2)
        mock_open.assert_any_call("test.json", "r")
        self.assertTrue(global_branch_coverage["load_1"])
        self.assertTrue(global_branch_coverage["load_2"])
        self.assertFalse(global_branch_coverage["load_3"])
        self.assertFalse(global_branch_coverage["load_4"])

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_load_nonexistent_file(self, mock_open, mock_path_exists):
        """Test behavior when the settings file does not exist."""
        mock_path_exists.return_value = False

        common = CommonMock(platform='Linux')
        mode_settings = ModeSettings(common, filename="test.json")

        mode_settings.load()

        self.assertTrue(mode_settings.just_created)
        mock_open.assert_not_called()
        self.assertFalse(global_branch_coverage["load_1"])
        self.assertFalse(global_branch_coverage["load_2"])
        self.assertFalse(global_branch_coverage["load_3"])
        self.assertTrue(global_branch_coverage["load_4"])

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='invalid json')
    def test_load_invalid_json(self, mock_open, mock_path_exists):
        """Test behavior when the settings file contains invalid JSON."""
        mock_path_exists.return_value = True

        common = CommonMock(platform='Linux')
        mode_settings = ModeSettings(common, filename="test.json")

        mode_settings.load()

        self.assertTrue(mode_settings.just_created)
        self.assertEqual(mock_open.call_count, 2)
        mock_open.assert_any_call("test.json", "r")
        self.assertTrue(global_branch_coverage["load_1"])
        self.assertTrue(global_branch_coverage["load_2"])
        self.assertTrue(global_branch_coverage["load_3"])
        self.assertTrue(global_branch_coverage["load_4"])

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load', side_effect=Exception("JSON error"))
    def test_load_json_exception(self, mock_json_load, mock_open, mock_path_exists):
        """Test loading settings when an exception occurs."""
        mock_path_exists.return_value = True

        common = CommonMock(platform='Linux')
        mode_settings = ModeSettings(common, filename="test.json")

        mode_settings.load()

        self.assertTrue(mode_settings.just_created)
        self.assertEqual(mock_open.call_count, 2)
        mock_open.assert_any_call("test.json", "r")
        self.assertTrue(global_branch_coverage["load_1"])
        self.assertTrue(global_branch_coverage["load_2"])
        self.assertTrue(global_branch_coverage["load_3"])
        self.assertTrue(global_branch_coverage["load_4"])

    @patch('platform.system')
    @patch('os.path.expanduser')
    def test_build_default_receive_data_dir_windows(self, mock_expanduser, mock_platform_system):
        """Test building the default receive data directory path on Windows."""
        mock_platform_system.return_value = 'Windows'
        mock_expanduser.return_value = 'C:\\Users\\testuser\\OnionShare'

        common = CommonMock(platform='Windows')
        mode_settings = ModeSettings(common)

        expected_path = 'C:\\Users\\testuser\\OnionShare'
        actual_path = mode_settings.build_default_receive_data_dir()

        self.assertEqual(expected_path, actual_path)
        self.assertTrue(global_branch_coverage["build_default_receive_data_dir_2"])

    @patch('platform.system')
    @patch('os.path.expanduser')
    def test_build_default_receive_data_dir_other(self, mock_expanduser, mock_platform_system):
        """Test building the default receive data directory path on other OSes."""
        mock_platform_system.return_value = 'Linux'
        mock_expanduser.return_value = '/home/testuser/OnionShare'

        common = CommonMock(platform='Linux')
        mode_settings = ModeSettings(common)

        expected_path = '/home/testuser/OnionShare'
        actual_path = mode_settings.build_default_receive_data_dir()

        self.assertEqual(expected_path, actual_path)
        self.assertTrue(global_branch_coverage["build_default_receive_data_dir_3"])

    @patch('platform.system')
    @patch('pwd.getpwuid')
    @patch('os.getuid')
    def test_build_default_receive_data_dir_darwin(self, mock_getuid, mock_getpwuid, mock_platform_system):
        """Test building the default receive data directory path on macOS."""
        mock_platform_system.return_value = 'Darwin'
        mock_getuid.return_value = 1000
        mock_getpwuid.return_value.pw_dir = '/Users/testuser'

        common = CommonMock(platform='Darwin')
        mode_settings = ModeSettings(common)

        expected_path = os.path.join('/Users/testuser', 'OnionShare')
        actual_path = mode_settings.build_default_receive_data_dir()

        self.assertEqual(expected_path, actual_path)
        self.assertTrue(global_branch_coverage["build_default_receive_data_dir_1"])

class CustomTextTestRunner(unittest.TextTestRunner):
    def run(self, test):
        result = super().run(test)
        ModeSettings.print_overall_coverage()
        return result

if __name__ == '__main__':
    unittest.main(testRunner=CustomTextTestRunner())
