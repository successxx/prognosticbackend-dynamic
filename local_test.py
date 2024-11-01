import random
import string
import unittest

import requests

# Base URL for the endpoints
BASE_URL = 'http://127.0.0.1:5001'

# Endpoints to test
ENDPOINTS = {
    'insert_user': f'{BASE_URL}/insert_user',
    'get_user': f'{BASE_URL}/get_user',
    'insert_user_one': f'{BASE_URL}/insert_user_one',
    'get_user_one': f'{BASE_URL}/get_user_one',
    'insert_user_two': f'{BASE_URL}/insert_user_two',
    'get_user_two': f'{BASE_URL}/get_user_two',
    'insert_user_psych': f'{BASE_URL}/insert_user_psych',
    'get_user_psych': f'{BASE_URL}/get_user_psych',
}

# Function to generate random email addresses
def generate_random_email():
    name = ''.join(random.choices(string.ascii_lowercase, k=10))
    domain = 'testing.com'
    return f'{name}@{domain}'

# Function to generate random text of at least 2000 characters
def generate_random_text(min_length=2000):
    return ''.join(random.choices(string.ascii_letters + string.digits + string.punctuation, k=min_length))

class TestAPIEndpoints(unittest.TestCase):

    def test_insert_user(self):
        email = generate_random_email()
        text = generate_random_text()
        data = {
            'user_email': email,
            'text': text,
            'booking_button_name': 'Test Booking Name',
            'booking_button_redirection': 'https://example.com'
        }

        # Send POST request to the insert_user endpoint
        response = requests.post(ENDPOINTS['insert_user'], json=data)
        self.assertIn(response.status_code, [200, 201])
        print(f'INSERT /insert_user: Status Code: {response.status_code}, Response: {response.json()}')

        # Verify that the user was inserted by retrieving it
        get_response = requests.post(ENDPOINTS['get_user'], json={'user_email': email})
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(get_response.json().get('user_email'), email)
        print(f'GET /get_user: Status Code: {get_response.status_code}, Response: {get_response.json()}')

    def test_insert_user_one(self):
        email = generate_random_email()
        text = generate_random_text()
        data = {
            'user_email': email,
            'text': text,
            'booking_button_name': 'Test Booking Name One',
            'booking_button_redirection': 'https://example.com/one'
        }

        # Send POST request to the insert_user_one endpoint
        response = requests.post(ENDPOINTS['insert_user_one'], json=data)
        self.assertIn(response.status_code, [200, 201])
        print(f'INSERT /insert_user_one: Status Code: {response.status_code}, Response: {response.json()}')

        # Verify that the user was inserted by retrieving it
        get_response = requests.post(ENDPOINTS['get_user_one'], json={'user_email': email})
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(get_response.json().get('user_email'), email)
        print(f'GET /get_user_one: Status Code: {get_response.status_code}, Response: {get_response.json()}')

    def test_insert_user_two(self):
        email = generate_random_email()
        text = generate_random_text()
        data = {
            'user_email': email,
            'text': text,
            'booking_button_name': 'Test Booking Name Two',
            'booking_button_redirection': 'https://example.com/two'
        }

        # Send POST request to the insert_user_two endpoint
        response = requests.post(ENDPOINTS['insert_user_two'], json=data)
        self.assertIn(response.status_code, [200, 201])
        print(f'INSERT /insert_user_two: Status Code: {response.status_code}, Response: {response.json()}')

        # Verify that the user was inserted by retrieving it
        get_response = requests.post(ENDPOINTS['get_user_two'], json={'user_email': email})
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(get_response.json().get('user_email'), email)
        print(f'GET /get_user_two: Status Code: {get_response.status_code}, Response: {get_response.json()}')

    def test_insert_user_psych(self):
        email = generate_random_email()
        text = generate_random_text()
        data = {
            'user_email': email,
            'text': text,
            'booking_button_name': 'Test Booking Name Psych',
            'booking_button_redirection': 'https://example.com/psych'
        }

        # Send POST request to the insert_user_psych endpoint
        response = requests.post(ENDPOINTS['insert_user_psych'], json=data)
        self.assertIn(response.status_code, [200, 201])
        print(f'INSERT /insert_user_psych: Status Code: {response.status_code}, Response: {response.json()}')

        # Verify that the user was inserted by retrieving it
        get_response = requests.post(ENDPOINTS['get_user_psych'], json={'user_email': email})
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(get_response.json().get('user_email'), email)
        print(f'GET /get_user_psych: Status Code: {get_response.status_code}, Response: {get_response.json()}')

if __name__ == '__main__':
    unittest.main()
