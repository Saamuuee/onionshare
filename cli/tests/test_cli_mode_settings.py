import unittest
from unittest.mock import patch, mock_open, MagicMock
import os
import json

from onionshare_cli.mode_settings import ModeSettings

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
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='{"persistent": {"enabled": true}}')
    @patch('json.load')
    def test_load_existing_file(self, mock_json_load, mock_open, mock_path_exists):
        mock_path_exists.return_value = True
        mock_json_load.return_value = {"persistent": {"enabled": True}}
        
        common = CommonMock(platform='Linux')
        mode_settings = ModeSettings(common, filename="test.json")
        
        mode_settings.load()
        
        self.assertTrue(mode_settings.get("persistent", "enabled"))
        self.assertEqual(mock_open.call_count, 2)
        mock_open.assert_any_call("test.json", "r")

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_load_nonexistent_file(self, mock_open, mock_path_exists):
        mock_path_exists.return_value = False
        
        common = CommonMock(platform='Linux')
        mode_settings = ModeSettings(common, filename="test.json")
        
        mode_settings.load()
        
        self.assertTrue(mode_settings.just_created)
        mock_open.assert_not_called()

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='invalid json')
    def test_load_invalid_json(self, mock_open, mock_path_exists):
        mock_path_exists.return_value = True
        
        common = CommonMock(platform='Linux')
        mode_settings = ModeSettings(common, filename="test.json")
        
        mode_settings.load()
        
        self.assertTrue(mode_settings.just_created)
        self.assertEqual(mock_open.call_count, 2)
        mock_open.assert_any_call("test.json", "r")

    @patch('platform.system')
    @patch('pwd.getpwuid')
    @patch('os.getuid')
    def test_build_default_receive_data_dir_darwin(self, mock_getuid, mock_getpwuid, mock_platform_system):
        mock_platform_system.return_value = 'Darwin'
        mock_getuid.return_value = 1000
        mock_getpwuid.return_value.pw_dir = '/Users/testuser'
        
        common = CommonMock(platform='Darwin')
        mode_settings = ModeSettings(common)
        
        expected_path = os.path.join('/Users/testuser', 'OnionShare')
        actual_path = mode_settings.build_default_receive_data_dir()
        
        self.assertEqual(expected_path, actual_path)
    
    @patch('platform.system')
    @patch('os.path.expanduser')
    def test_build_default_receive_data_dir_windows(self, mock_expanduser, mock_platform_system):
        mock_platform_system.return_value = 'Windows'
        mock_expanduser.return_value = 'C:\\Users\\testuser\\OnionShare'
        
        common = CommonMock(platform='Windows')
        mode_settings = ModeSettings(common)
        
        expected_path = 'C:\\Users\\testuser\\OnionShare'
        actual_path = mode_settings.build_default_receive_data_dir()
        
        self.assertEqual(expected_path, actual_path)
    
    @patch('platform.system')
    @patch('os.path.expanduser')
    def test_build_default_receive_data_dir_other(self, mock_expanduser, mock_platform_system):
        mock_platform_system.return_value = 'Linux'
        mock_expanduser.return_value = '/home/testuser/OnionShare'
        
        common = CommonMock(platform='Linux')
        mode_settings = ModeSettings(common)
        
        expected_path = '/home/testuser/OnionShare'
        actual_path = mode_settings.build_default_receive_data_dir()
        
        self.assertEqual(expected_path, actual_path)

    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dumps')
    def test_save_settings(self, mock_json_dumps, mock_open):
        common = CommonMock(platform='Linux')
        mode_settings = ModeSettings(common, filename="test.json")
        
        mode_settings.set("persistent", "enabled", True)
        mode_settings.save()
        
        self.assertEqual(mock_open.call_count, 1)
        mock_open.assert_called_once_with("test.json", "w")
        self.assertEqual(mock_json_dumps.call_count, 1)
        mock_json_dumps.assert_called_once_with(mode_settings._settings, indent=2)
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dumps')
    def test_save_settings_disabled(self, mock_json_dumps, mock_open):
        common = CommonMock(platform='Linux')
        mode_settings = ModeSettings(common, filename="test.json")
        
        mode_settings.set("persistent", "enabled", False)
        mode_settings.save()
        
        mock_open.assert_not_called()
        mock_json_dumps.assert_not_called()

    def test_fill_in_defaults_add_missing_keys(self):
        common = CommonMock(platform='Linux')
        mode_settings = ModeSettings(common)
        
        mode_settings._settings = {
            "onion": {"private_key": "key"},
            "general": {"title": "Test Title"}
        }
        
        mode_settings.fill_in_defaults()
        
        expected_settings = {
            "onion": {
                "private_key": "key",
                "client_auth_priv_key": None,
                "client_auth_pub_key": None,
            },
            "persistent": {"mode": None, "enabled": False},
            "general": {
                "title": "Test Title",
                "public": False,
                "autostart_timer": False,
                "autostop_timer": False,
                "service_id": None,
            },
            "share": {"autostop_sharing": True, "filenames": []},
            "receive": {
                "data_dir": mode_settings.build_default_receive_data_dir(),
                "webhook_url": None,
                "disable_text": False,
                "disable_files": False,
            },
            "website": {"disable_csp": False, "custom_csp": None, "filenames": []},
            "chat": {},
        }
        
        self.assertDictEqual(mode_settings._settings, expected_settings)
    
    def test_fill_in_defaults_no_overwrite_existing_keys(self):
        common = CommonMock(platform='Linux')
        mode_settings = ModeSettings(common)
        
        mode_settings._settings = {
            "onion": {
                "private_key": "key",
                "client_auth_priv_key": "auth_key"
            },
            "general": {"title": "Test Title", "public": True}
        }
        
        mode_settings.fill_in_defaults()
        
        self.assertEqual(mode_settings._settings["onion"]["private_key"], "key")
        self.assertEqual(mode_settings._settings["onion"]["client_auth_priv_key"], "auth_key")
        self.assertEqual(mode_settings._settings["general"]["title"], "Test Title")
        self.assertEqual(mode_settings._settings["general"]["public"], True)
        self.assertEqual(mode_settings._settings["general"]["autostart_timer"], False)
        self.assertEqual(mode_settings._settings["general"]["autostop_timer"], False)

if __name__ == '__main__':
    unittest.main()