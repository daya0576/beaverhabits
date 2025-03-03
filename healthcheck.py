import sys
import requests


def check_service():
    try:
        response = requests.get("http://localhost:8080/health")
        if response.status_code == 200:
            sys.exit(0)
    except requests.exceptions.RequestException as e:
        print(f"Health check failed: {e}")

    sys.exit(1)


if __name__ == "__main__":
    check_service()
