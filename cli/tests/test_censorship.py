import unittest
from unittest.mock import patch
from cli.onionshare_cli.censorship import Common, Meek, Onion, CensorshipCircumvention, CensorshipCircumventionError

class TestCensorshipCircumvention(unittest.TestCase):

    def test_request_map(self):
        common = Common()
        meek = Meek()
        onion = Onion()
        circumvention = CensorshipCircumvention(common, meek, onion)

        with patch('requests.post') as mock_post:
            # Mock the response to avoid actual network calls
            mock_response = mock_post.return_value

            # Test 1: No proxies configured (request_map_1)
            print("Test Case 1: No proxies configured")
            circumvention.api_proxies = {}
            circumvention.branch_coverage = {key: False for key in circumvention.branch_coverage}  # Reset coverage
            result = circumvention.request_map(country="US")
            self.assertFalse(result)
            circumvention.print_coverage()
            print()

            # Test 2: Valid country code (request_map_2)
            print("Test Case 2: Valid country code")
            circumvention.api_proxies = meek.meek_proxies
            mock_response.status_code = 200
            mock_response.json.return_value = {}
            circumvention.branch_coverage = {key: False for key in circumvention.branch_coverage}  # Reset coverage
            result = circumvention.request_map(country="US")
            self.assertEqual(result, {})
            circumvention.print_coverage()
            print()

            # Test 3: Response with an error (request_map_4)
            print("Test Case 3: Response with an error")
            mock_response.status_code = 200
            mock_response.json.return_value = {"errors": ["error"]}
            circumvention.branch_coverage = {key: False for key in circumvention.branch_coverage}  # Reset coverage
            result = circumvention.request_map(country="US")
            self.assertFalse(result)
            circumvention.print_coverage()
            print()

            # Test 4: Non-200 status code (request_map_3)
            print("Test Case 4: Non-200 status code")
            mock_response.status_code = 500
            mock_response.json.return_value = {}
            circumvention.branch_coverage = {key: False for key in circumvention.branch_coverage}  # Reset coverage
            result = circumvention.request_map(country="US")
            self.assertFalse(result)
            circumvention.print_coverage()
            print()

            # Test 5: Valid response without country (default case)
            print("Test Case 5: Valid response without country")
            mock_response.status_code = 200
            mock_response.json.return_value = {"some_key": "some_value"}
            circumvention.branch_coverage = {key: False for key in circumvention.branch_coverage}  # Reset coverage
            result = circumvention.request_map(country=None)
            self.assertEqual(result, {"some_key": "some_value"})
            circumvention.print_coverage()
            print()

        # Print global coverage
        print("Final Global Coverage Report for request_map:")
        CensorshipCircumvention.print_global_coverage()

    def test_request_settings(self):
        common = Common()
        meek = Meek()
        onion = Onion()
        circumvention = CensorshipCircumvention(common, meek, onion)

        with patch('requests.post') as mock_post:
            # Mock the response to avoid actual network calls
            mock_response = mock_post.return_value

            # Test 1: No proxies configured
            print("Test Case 1: No proxies configured")
            circumvention.api_proxies = {}
            circumvention.branch_coverage = {key: False for key in circumvention.branch_coverage}  # Reset coverage
            result = circumvention.request_settings(country="US")
            self.assertFalse(result)
            circumvention.print_coverage()
            print()

            # Test 2: Valid country code
            print("Test Case 2: Valid country code")
            circumvention.api_proxies = meek.meek_proxies
            mock_response.status_code = 200
            mock_response.json.return_value = {"settings": {"bridge_strings": ["bridge1", "bridge2"]}}
            circumvention.branch_coverage = {key: False for key in circumvention.branch_coverage}  # Reset coverage
            result = circumvention.request_settings(country="US")
            self.assertEqual(result, {"settings": {"bridge_strings": ["bridge1", "bridge2"]}})
            circumvention.print_coverage()
            print()

            # Test 3: Response with an error
            print("Test Case 3: Response with an error")
            mock_response.status_code = 200
            mock_response.json.return_value = {"errors": ["error"]}
            circumvention.branch_coverage = {key: False for key in circumvention.branch_coverage}  # Reset coverage
            result = circumvention.request_settings(country="US")
            self.assertFalse(result)
            circumvention.print_coverage()
            print()

            # Test 4: Non-200 status code
            print("Test Case 4: Non-200 status code")
            mock_response.status_code = 500
            mock_response.json.return_value = {}
            circumvention.branch_coverage = {key: False for key in circumvention.branch_coverage}  # Reset coverage
            result = circumvention.request_settings(country="US")
            self.assertFalse(result)
            circumvention.print_coverage()
            print()

            # Test 5: Valid response without country
            print("Test Case 5: Valid response without country")
            mock_response.status_code = 200
            mock_response.json.return_value = {"settings": {"bridge_strings": ["bridge1", "bridge2"]}}
            circumvention.branch_coverage = {key: False for key in circumvention.branch_coverage}  # Reset coverage
            result = circumvention.request_settings(country=None)
            self.assertEqual(result, {"settings": {"bridge_strings": ["bridge1", "bridge2"]}})
            circumvention.print_coverage()
            print()

        # Print global coverage
        print("Final Global Coverage Report for request_settings:")
        CensorshipCircumvention.print_global_coverage()

if __name__ == "__main__":
    unittest.main()
