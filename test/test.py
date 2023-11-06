import unittest
import os
import json
import tempfile
import shutil
import subprocess
import logging
from generic_credential_provider import generic_credential_provider_utilities

class TestUtilities(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for the tests
        self.test_directory = tempfile.mkdtemp()
        logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
        logging.disable(logging.DEBUG)

    def tearDown(self):
        # Remove the temporary directory and its contents
        shutil.rmtree(self.test_directory)

    def test_get_repository_base(self):
        base_name = generic_credential_provider_utilities.get_image_repository({'image':"some.example.org:12345/someuser/someimage:19700101-0000"})
        self.assertEqual(base_name, 'some.example.org')

    def test_get_possible_filenames(self):
        possible_filenames = generic_credential_provider_utilities.generate_possible_filenames("some.example.org")
        test_filenames = {}
        for possible_filename in possible_filenames:
            test_filenames[possible_filename] = True
        self.assertTrue('org' in test_filenames)
        self.assertTrue('example.org' in test_filenames)
        self.assertTrue('some.example.org' in test_filenames)
        self.assertFalse('some.example' in test_filenames)
        self.assertFalse('example' in test_filenames)
        self.assertFalse('nothing' in test_filenames)

    def test_find_existing_json_file(self):
        # Create a sample JSON file in the temporary directory
        registry_name = "example.org"
        json_filename = "example.org.json"
        json_file_content = {"username": "testuser", "password": "testpassword"}
        json_file_path = os.path.join(self.test_directory, json_filename)

        with open(json_file_path, "w") as json_file:
            json.dump(json_file_content, json_file)

        # Test the find_json_file function from the imported module
        found_json_file = generic_credential_provider_utilities.find_json_file([registry_name], self.test_directory)

        # Assert that the correct JSON file is found
        self.assertEqual(found_json_file, json_file_path)

    def test_find_nonexistent_json_file(self):
        # Test the find_json_file function from the imported module
        registry_name = "nonexistent.registry"
        found_json_file = generic_credential_provider_utilities.find_json_file([registry_name], self.test_directory)

        # Assert that no JSON file is found
        self.assertIsNone(found_json_file)

class TestRunningConditions(unittest.TestCase):
    def test_version_check(self):
        cmd = "python3 generic_credential_provider.py -v"
        result = subprocess.check_output(cmd, cwd=os.path.dirname(os.path.abspath(__file__)), shell=True, text=True)
        expected_result = "generic-credential-provider version 1.0.0\n"
        self.assertEqual(result, expected_result)

    def test_normal_run(self):
        cmd = "python3 generic_credential_provider.py --credroot . < test-input.json"
        result = subprocess.check_output(cmd, cwd=os.path.dirname(os.path.abspath(__file__)), shell=True, text=True)
        expected_result = '{"kind": "CredentialProviderResponse", "apiVersion": "credentialprovider.kubelet.k8s.io/v1", "cacheKeyType": "Registry", "cacheDuration": "0h5m0s", "auth": {"provider.example.com": {"username": "bloggsf", "password": "decafbad"}}}'
        self.assertEqual(result, expected_result)

    def test_normal_run_with_debugging(self):
        cmd = "python3 generic_credential_provider.py --debug --credroot . < test-input.json"
        with subprocess.Popen(cmd, cwd=os.path.dirname(os.path.abspath(__file__)), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as process:
            exit_code = process.wait()
            stdout = process.stdout.read().decode('utf-8').split("\n")
            stderr = process.stderr.read().decode('utf-8').split("\n")
            expected_stderr = [
                'DEBUG: Got repository name: provider.example.com',
                'DEBUG: Testing json_file_path: ./provider.example.com.json',
                'DEBUG: Testing json_file_path: ./example.com.json',
                'DEBUG: Got it',
                "DEBUG: Got credentials: {'username': 'bloggsf', 'password': 'decafbad'}",
                ''
            ]
            expected_stdout = [
                '{"kind": "CredentialProviderResponse", "apiVersion": "credentialprovider.kubelet.k8s.io/v1", "cacheKeyType": "Registry", "cacheDuration": "0h5m0s", "auth": {"provider.example.com": {"username": "bloggsf", "password": "decafbad"}}}'
            ]
            self.assertEqual(exit_code, 0)
            self.assertEqual(len(stdout), len(expected_stdout))
            for i in range(len(stdout)):
                self.assertEqual(stdout[i], expected_stdout[i])
            for i in range(len(stderr)):
                self.assertEqual(stderr[i], expected_stderr[i])
            self.assertEqual(len(stderr), len(expected_stderr))

    def test_failed_run(self):
        cmd = "python3 generic_credential_provider.py --credroot . < test-input-fail.json"
        with subprocess.Popen(cmd, cwd=os.path.dirname(os.path.abspath(__file__)), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as process:
            exit_code = process.wait()
            self.assertEqual(exit_code, 1)
            expected_result = "ERROR: Error running credential provider plugin: provider.example.org is an unknown source\n"
            stderr_output = process.stderr.read().decode('utf-8')
            self.assertEqual(stderr_output, expected_result)

if __name__ == '__main__':
    unittest.main()
