import requests
import random


def send_otp_to_phone(phone_number):
    try:
        otp = random.randint(100000, 999999)
        url = "https://notify.eskiz.uz/api/message/sms/send"
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MjU3NzcwNzIsImlhdCI6MTcyMzE4NTA3Miwicm9sZSI6InRlc3QiLCJzaWduIjoiOTU4MzYzMjViOWQ2M2ExMzg2YzFkZjA2N2I5MThhNDdkODc1NThmYTIzODJmYTljNGM2NmYzMmRjZmQxM2NlZCIsInN1YiI6IjgwODAifQ.rbicPIVX1AiKW8qWTKLK0Gqx5MM60Z8pYu31BYREcfE"
        headers = {
            'Authorization': f'Bearer {token}'
        }
        payload = {'mobile_phone': f'{phone_number}',
                   'message': 'Bu Eskiz dan test',
                   'from': '4546',
                   'callback_url': 'http://0000.uz/test.php'}
        files = []
        response = requests.request("POST", url, headers=headers, data=payload, files=files)
        print(response.text)
        return otp
    except Exception as e:
        print(e)
        return None
