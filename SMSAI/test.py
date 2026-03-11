import requests

TEXTBELT_KEY = "3a5edbc0db952b9043572e678a103fabef5fd218IpQuOMdqcolaRilUE6aEuawT3"
to_number = "+61426367966"  # your Australian number
message = "How are you doing?"

def send_sms(phone: str, message: str):
    """Send SMS using Textbelt."""
    url = "https://textbelt.com/text"
    payload = {
        "phone": phone,
        "message": message,
        "key": TEXTBELT_KEY
    }
    res = requests.post(url, data=payload)
    return res.json()

if __name__ == "__main__":
    result = send_sms(to_number, message)
    print("Textbelt result:", result)
