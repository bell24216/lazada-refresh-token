import json 
import lazop
from google.cloud import storage
import os
import json
import time
import hmac
import hashlib
import requests
import logging
from google.cloud import storage


def re_token(request):
    logging.warning("🔥 LAZADA FUNCTION STARTED 🔥")

    appkey = os.environ["APPKEY"]
    url = os.environ["URL"]
    appSecret = os.environ["APPSECRET"]

    bucket_name = 'token_shopee_lazada_file'
    file_name_old = 'token_lazada_new.json'

    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(file_name_old)

    data = json.loads(blob.download_as_string())

    access_token = data['access_token']
    refresh_token = data['refresh_token']
    expires_at = data.get('expires_at')

    now = int(time.time())

    # refresh ก่อนหมด 1 วัน
    if expires_at and now < (expires_at - 86400):
        logging.warning("Token ยังไม่ถึงเวลา refresh")
        return

    logging.warning("Token ใกล้หมดอายุ → Refresh token")

    lazada_client = lazop.LazopClient(url, appkey ,appSecret)

    request = lazop.LazopRequest('/auth/token/refresh')
    request.add_api_param('refresh_token', refresh_token)

    response_new = lazada_client.execute(request)
    content = response_new.body

    access_token_new = content.get("access_token")
    refresh_token_new = content.get("refresh_token")
    expires_in_new = content.get("expires_in")

    if not access_token_new or not refresh_token_new:
        logging.error(content)
        return

    expires_at_new = int(time.time()) + expires_in_new

    data_new = {
        "access_token": access_token_new,
        "refresh_token": refresh_token_new,
        "expires_in": expires_in_new,
        "expires_at": expires_at_new
    }

    blob.upload_from_string(json.dumps(data_new))

    logging.warning("Token refreshed และบันทึกเรียบร้อย")