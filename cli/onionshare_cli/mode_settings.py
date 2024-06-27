# -*- coding: utf-8 -*-
"""
OnionShare | https://onionshare.org/

Copyright (C) 2014-2022 Micah Lee, et al. <micah@micahflee.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import os
import json
import platform

if platform.system() == "Darwin":
    import pwd

global_branch_coverage = {
    "load_1": False,  # if branch for os.path.exists(self.filename)
    "load_1_else": False,  # else branch for os.path.exists(self.filename)
    "load_2": False,  # try branch
    "load_2_else": False,  # else branch for try
    "load_3": False,  # except branch
    "load_4": False,  # if loading settings didn't work
    "build_default_receive_data_dir_1": False,  # Darwin branch
    "build_default_receive_data_dir_1_else": False,  # else branch for Darwin
    "build_default_receive_data_dir_2": False,  # Windows branch
    "build_default_receive_data_dir_2_else": False,  # else branch for Windows
    "build_default_receive_data_dir_3": False,  # Other OSes branch
}

overall_branch_coverage = {key: False for key in global_branch_coverage}

class ModeSettings:
    """
    This stores the settings for a single instance of an OnionShare mode. In CLI there
    is only one ModeSettings, and in the GUI there is a separate ModeSettings for each tab
    """

    def __init__(self, common, filename=None, id=None):
        self.common = common

        self.default_settings = {
            "onion": {
                "private_key": None,
                "client_auth_priv_key": None,
                "client_auth_pub_key": None,
            },
            "persistent": {"mode": None, "enabled": False},
            "general": {
                "title": None,
                "public": False,
                "autostart_timer": False,
                "autostop_timer": False,
                "service_id": None,
            },
            "share": {"autostop_sharing": True, "filenames": []},
            "receive": {
                "data_dir": self.build_default_receive_data_dir(),
                "webhook_url": None,
                "disable_text": False,
                "disable_files": False,
            },
            "website": {"disable_csp": False, "custom_csp": None, "filenames": []},
            "chat": {},
        }
        self._settings = {}

        self.just_created = False
        if id:
            self.id = id
        else:
            self.id = self.common.build_password(3)

        self.load(filename)

    def fill_in_defaults(self):
        """
        If there are any missing settings from self._settings, replace them with
        their default values.
        """
        for key in self.default_settings:
            if key in self._settings:
                for inner_key in self.default_settings[key]:
                    if inner_key not in self._settings[key]:
                        self._settings[key][inner_key] = self.default_settings[key][inner_key]
            else:
                self._settings[key] = self.default_settings[key]

    def get(self, group, key):
        return self._settings[group][key]

    def set(self, group, key, val):
        self._settings[group][key] = val
        self.common.log("ModeSettings", "set", f"updating {self.id}: {group}.{key} = {val}")
        self.save()

    def build_default_receive_data_dir(self):
        """
        Returns the path of the default Downloads directory for receive mode.
        """
        if self.common.platform == "Darwin":
            global_branch_coverage["build_default_receive_data_dir_1"] = True
            overall_branch_coverage["build_default_receive_data_dir_1"] = True
            real_homedir = pwd.getpwuid(os.getuid()).pw_dir
            return os.path.join(real_homedir, "OnionShare")
        else:
            global_branch_coverage["build_default_receive_data_dir_1_else"] = True
            overall_branch_coverage["build_default_receive_data_dir_1_else"] = True
            if self.common.platform == "Windows":
                global_branch_coverage["build_default_receive_data_dir_2"] = True
                overall_branch_coverage["build_default_receive_data_dir_2"] = True
                return os.path.expanduser("~\\OnionShare")
            else:
                global_branch_coverage["build_default_receive_data_dir_2_else"] = True
                overall_branch_coverage["build_default_receive_data_dir_2_else"] = True
                global_branch_coverage["build_default_receive_data_dir_3"] = True
                overall_branch_coverage["build_default_receive_data_dir_3"] = True
                return os.path.expanduser("~/OnionShare")

    def load(self, filename=None):
        # Load persistent settings from disk. If the file doesn't exist, create it
        if filename:
            self.filename = filename
        else:
            self.filename = os.path.join(self.common.build_persistent_dir(), f"{self.id}.json")

        if os.path.exists(self.filename):
            global_branch_coverage["load_1"] = True
            overall_branch_coverage["load_1"] = True
            try:
                global_branch_coverage["load_2"] = True
                overall_branch_coverage["load_2"] = True
                with open(self.filename, "r") as f:
                    self._settings = json.load(f)
                    self.fill_in_defaults()
                    self.common.log("ModeSettings", "load", f"loaded {self.filename}")
                    return
            except Exception:
                global_branch_coverage["load_3"] = True
                overall_branch_coverage["load_3"] = True
        else:
            global_branch_coverage["load_1_else"] = True
            overall_branch_coverage["load_1_else"] = True

        # If loading settings didn't work, create the settings file
        global_branch_coverage["load_4"] = True
        overall_branch_coverage["load_4"] = True
        self.common.log("ModeSettings", "load", f"creating {self.filename}")
        self.fill_in_defaults()
        self.just_created = True

    def save(self):
        # Save persistent setting to disk
        if not self.get("persistent", "enabled"):
            return

        if self.filename:
            with open(self.filename, "w") as file:
                file.write(json.dumps(self._settings, indent=2))

    def delete(self):
        # Delete the file from disk
        if os.path.exists(self.filename):
            os.remove(self.filename)

    @staticmethod
    def print_global_coverage():
        total_branches = len(global_branch_coverage)
        hit_branches = sum(global_branch_coverage.values())
        coverage_percentage = (hit_branches / total_branches) * 100
        for branch, hit in global_branch_coverage.items():
            print(f"{branch} was {'hit' if hit else 'not hit'}")
        print(f"Overall Test Coverage: {hit_branches}/{total_branches} branches hit ({coverage_percentage:.2f}%)")

    @staticmethod
    def print_overall_coverage():
        total_branches = len(overall_branch_coverage)
        hit_branches = sum(overall_branch_coverage.values())
        coverage_percentage = (hit_branches / total_branches) * 100
        print("\nOverall Branch Coverage Report:")
        print("=" * 25)
        for branch, hit in overall_branch_coverage.items():
            status = "HIT" if hit else "NOT HIT"
            print(f"{branch:<35} : {status:>7}")
        print("-" * 25)
        print(f"Total branches                    : {total_branches}")
        print(f"Hit branches                      : {hit_branches}")
        print(f"Overall Coverage                  : {coverage_percentage:.2f}%")
