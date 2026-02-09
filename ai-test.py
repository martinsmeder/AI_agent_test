# My code:

import requests

url = "http://localhost:11434/api/generate"

payload = {
    "model": "mistral:7b-instruct",
    "prompt": "Write a Python function that checks if a number is prime.",
    "stream": False
}

r = requests.post(url, json=payload)
print(r.json()["response"])

# Output from local model:

def check_prime(n):
    if n <= 1:
        return False
    elif n <= 3:
        return True
    elif n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True

print(check_prime(5))  # True
print(check_prime(10))  # False
print(check_prime(17))  # True
print(check_prime(25))  # False