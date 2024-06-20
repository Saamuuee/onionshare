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
import requests

class Common:
    def log(self, *args):
        print("Log:", *args)

class Meek:
    meek_proxies = {
        "http": "http://mock_meek_proxy",
        "https": "https://mock_meek_proxy"
    }

    def __init__(self):
        self.active = False

    def activate(self):
        self.active = True

    def deactivate(self):
        self.active = False

    def get_proxies(self):
        if self.active:
            return self.meek_proxies
        else:
            return {}

class Onion:
    is_authenticated = True
    def get_tor_socks_port(self):
        return ("localhost", 9050)

class CensorshipCircumventionError(Exception):
    """
    There was a problem connecting to the Tor CensorshipCircumvention API.
    """

class CensorshipCircumvention:
    global_branch_coverage = {
        "request_map_1": False,  # if not self.api_proxies
        "request_map_2": False,  # if country
        "request_map_3": False,  # if r.status_code != 200
        "request_map_4": False,  # if "errors" in result
    }

    def __init__(self, common, meek=None, onion=None):
        self.common = common
        self.common.log("CensorshipCircumvention", "__init__")
        self.api_proxies = {}

        self.branch_coverage = {  # Initialize branch_coverage here
            "request_map_1": False,
            "request_map_2": False,
            "request_map_3": False,
            "request_map_4": False,
        }

        if meek:
            self.meek = meek
            self.common.log(
                "CensorshipCircumvention",
                "__init__",
                "Using Meek with CensorshipCircumvention API",
            )
            self.api_proxies = self.meek.meek_proxies
            
        if onion:
            self.onion = onion
            if not self.onion.is_authenticated:
                return False
            else:
                self.common.log(
                    "CensorshipCircumvention",
                    "__init__",
                    "Using Tor with CensorshipCircumvention API",
                )
                (socks_address, socks_port) = self.onion.get_tor_socks_port()
                self.api_proxies = {
                    "http": f"socks5h://{socks_address}:{socks_port}",
                    "https": f"socks5h://{socks_address}:{socks_port}",
                }

    def request_map(self, country=False):
        """
        Retrieves the Circumvention map from Tor Project and store it
        locally for further look-ups if required.

        Optionally pass a country code in order to get recommended settings
        just for that country.

        Note that this API endpoint doesn't return actual bridges,
        it just returns the recommended bridge type countries.
        """
        self.common.log("CensorshipCircumvention", "request_map", f"country={country}")
        if not self.api_proxies:
            self.branch_coverage["request_map_1"] = True
            CensorshipCircumvention.global_branch_coverage["request_map_1"] = True
            self.print_coverage()
            return False
        endpoint = "https://bridges.torproject.org/moat/circumvention/map"
        data = {}
        if country:
            self.branch_coverage["request_map_2"] = True
            CensorshipCircumvention.global_branch_coverage["request_map_2"] = True
            data = {"country": country}

        try:
            r = requests.post(
                endpoint,
                json=data,
                headers={"Content-Type": "application/vnd.api+json"},
                proxies=self.api_proxies,
            )
            if r.status_code != 200:
                self.branch_coverage["request_map_3"] = True
                CensorshipCircumvention.global_branch_coverage["request_map_3"] = True
                self.common.log(
                    "CensorshipCircumvention",
                    "request_map",
                    f"status_code={r.status_code}",
                )
                self.print_coverage()
                return False

            result = r.json()

            if "errors" in result:
                self.branch_coverage["request_map_4"] = True
                CensorshipCircumvention.global_branch_coverage["request_map_4"] = True
                self.common.log(
                    "CensorshipCircumvention",
                    "request_map",
                    f"errors={result['errors']}",
                )
                self.print_coverage()
                return False

            self.print_coverage()
            return result
        except requests.exceptions.RequestException as e:
            self.print_coverage()
            raise CensorshipCircumventionError(e)

    def request_settings(self, country=False, transports=False):
        """
        Retrieves the Circumvention Settings from Tor Project, which
        will return recommended settings based on the country code of
        the requesting IP.

        Optionally, a country code can be specified in order to override
        the IP detection.

        Optionally, a list of transports can be specified in order to
        return recommended settings for just that transport type.
        """
        self.common.log(
            "CensorshipCircumvention",
            "request_settings",
            f"country={country}, transports={transports}",
        )
        if not self.api_proxies:
            return False
        endpoint = "https://bridges.torproject.org/moat/circumvention/settings"
        data = {}
        if country:
            self.common.log(
                "CensorshipCircumvention",
                "request_settings",
                f"Trying to obtain bridges for country={country}",
            )
            data = {"country": country}
        if transports:
            data.append({"transports": transports})
        try:
            r = requests.post(
                endpoint,
                json=data,
                headers={"Content-Type": "application/vnd.api+json"},
                proxies=self.api_proxies,
            )
            if r.status_code != 200:
                self.common.log(
                    "CensorshipCircumvention",
                    "request_settings",
                    f"status_code={r.status_code}",
                )
                return False

            result = r.json()
            self.common.log(
                "CensorshipCircumvention",
                "request_settings",
                f"result={result}",
            )

            if "errors" in result:
                self.common.log(
                    "CensorshipCircumvention",
                    "request_settings",
                    f"errors={result['errors']}",
                )
                return False

            # There are no settings - perhaps this country doesn't require censorship circumvention?
            # This is not really an error, so we can just check if False and assume direct Tor
            # connection will work.
            if not "settings" in result or result["settings"] is None:
                self.common.log(
                    "CensorshipCircumvention",
                    "request_settings",
                    "No settings found for this country",
                )
                return False

            return result
        except requests.exceptions.RequestException as e:
            raise CensorshipCircumventionError(e)

    def request_builtin_bridges(self):
        """
        Retrieves the list of built-in bridges from the Tor Project.
        """
        if not self.api_proxies:
            return False
        endpoint = "https://bridges.torproject.org/moat/circumvention/builtin"
        try:
            r = requests.post(
                endpoint,
                headers={"Content-Type": "application/vnd.api+json"},
                proxies=self.api_proxies,
            )
            if r.status_code != 200:
                self.common.log(
                    "CensorshipCircumvention",
                    "request_builtin_bridges",
                    f"status_code={r.status_code}",
                )
                return False

            result = r.json()

            if "errors" in result:
                self.common.log(
                    "CensorshipCircumvention",
                    "request_builtin_bridges",
                    f"errors={result['errors']}",
                )
                return False

            return result
        except requests.exceptions.RequestException as e:
            raise CensorshipCircumventionError(e)

    def save_settings(self, settings, bridge_settings):
        """
        Checks the bridges and saves them in settings.
        """
        self.common.log(
            "CensorshipCircumvention",
            "save_settings",
            f"bridge_settings: {bridge_settings}",
        )

        bridges_ok = False
        self.settings = settings

        # @TODO there might be several bridge types recommended.
        # Should we attempt to iterate over each type if one of them fails to connect?
        # But if so, how to stop it starting 3 separate Tor connection threads?
        # for bridges in request_bridges["settings"]:
        bridges = bridge_settings["settings"][0]["bridges"]
        bridge_strings = bridges["bridge_strings"]

        self.settings.set("bridges_type", "custom")

        # Sanity check the bridges provided from the Tor API before saving
        bridges_checked = self.common.check_bridges_valid(bridge_strings)

        if bridges_checked:
            self.settings.set("bridges_custom", "\n".join(bridges_checked))
            bridges_ok = True

        # If we got any good bridges, save them to settings and return.
        if bridges_ok:
            self.common.log(
                "CensorshipCircumvention",
                "save_settings",
                "Saving settings with automatically-obtained bridges",
            )
            self.settings.set("bridges_enabled", True)
            self.settings.save()
            return True
        else:
            self.common.log(
                "CensorshipCircumvention",
                "save_settings",
                "Could not use any of the obtained bridges.",
            )
            return False

    def request_default_bridges(self):
        """
        Retrieves the list of default fall-back bridges from the Tor Project.

        These are intended for when no censorship settings were found for a
        specific country, but maybe there was some connection issue anyway.
        """
        if not self.api_proxies:
            return False
        endpoint = "https://bridges.torproject.org/moat/circumvention/defaults"
        try:
            r = requests.get(
                endpoint,
                headers={"Content-Type": "application/vnd.api+json"},
                proxies=self.api_proxies,
            )
            if r.status_code != 200:
                self.common.log(
                    "CensorshipCircumvention",
                    "request_default_bridges",
                    f"status_code={r.status_code}",
                )
                return False

            result = r.json()

            if "errors" in result:
                self.common.log(
                    "CensorshipCircumvention",
                    "request_default_bridges",
                    f"errors={result['errors']}",
                )
                return False

            return result
        except requests.exceptions.RequestException as e:
            raise CensorshipCircumventionError(e)

    def print_coverage(self):
        total_branches = len(self.branch_coverage)
        hit_branches = sum(self.branch_coverage.values())
        coverage_percentage = (hit_branches / total_branches) * 100
        for branch, hit in self.branch_coverage.items():
            print(f"{branch} was {'hit' if hit else 'not hit'}")
        print(f"Coverage: {hit_branches}/{total_branches} branches hit ({coverage_percentage:.2f}%)")

    @staticmethod
    def print_global_coverage():
        total_branches = len(CensorshipCircumvention.global_branch_coverage)
        hit_branches = sum(CensorshipCircumvention.global_branch_coverage.values())
        coverage_percentage = (hit_branches / total_branches) * 100
        for branch, hit in CensorshipCircumvention.global_branch_coverage.items():
            print(f"{branch} was {'hit' if hit else 'not hit'}")
        print(f"Global Coverage: {hit_branches}/{total_branches} branches hit ({coverage_percentage:.2f}%)")

