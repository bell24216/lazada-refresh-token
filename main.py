import json
import lazop
import os
import time
import logging
from google.cloud import storage

import functions_framework

@functions_framework.http
def re_token(request):
    logging.warning("🔥 LAZADA FUNCTION STARTED 🔥")

    appkey = os.environ["APPKEY"]
    url = os.environ["URL"]
    appSecret = os.environ["APPSECRET"]

    bucket_name = "token_shopee_lazada_file"
    file_name = "token_lazada_new.json"

    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(file_name)

    data = json.loads(blob.download_as_string())

    refresh_token = data["refresh_token"]
    expires_at = data.get("expires_at")

    now = int(time.time())

    # refresh ก่อนหมด 1 วัน
    if expires_at and now < (expires_at - 86400):
        logging.warning("Token ยังไม่ถึงเวลา refresh")
        return "Token still valid"

    logging.warning("Token ใกล้หมดอายุ → Refresh token")

    lazada_client = lazop.LazopClient(url, appkey, appSecret)

    req = lazop.LazopRequest("/auth/token/refresh")
    req.add_api_param("refresh_token", refresh_token)

    response_new = lazada_client.execute(req)
    content = response_new.body

    access_token_new = content.get("access_token")
    refresh_token_new = content.get("refresh_token")
    expires_in_new = content.get("expires_in")

    if not access_token_new or not refresh_token_new:
        logging.error(content)
        return "Refresh failed"

    expires_at_new = int(time.time()) + expires_in_new

    data_new = {
        "access_token": access_token_new,
        "refresh_token": refresh_token_new,
        "expires_in": expires_in_new,
        "expires_at": expires_at_new
    }

    blob.upload_from_string(json.dumps(data_new))

    logging.warning("Token refreshed และบันทึกเรียบร้อย")

    return "Token refreshed"