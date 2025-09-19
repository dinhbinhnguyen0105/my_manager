import io, pycurl, json
from urllib.parse import urlparse


def get_proxy(proxy_raw: str) -> dict:
    buffer = io.BytesIO()
    curl = pycurl.Curl()
    curl.setopt(pycurl.URL, proxy_raw.strip())
    curl.setopt(pycurl.CONNECTTIMEOUT, 60)
    curl.setopt(pycurl.TIMEOUT, 60)
    headers = [
        "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept: application/json, text/plain, */*",
        "Accept-Language: en-US,en;q=0.9",
        "Connection: keep-alive",
    ]
    curl.setopt(pycurl.HTTPHEADER, headers)
    curl.setopt(pycurl.WRITEFUNCTION, buffer.write)
    curl.perform()
    try:
        code = curl.getinfo(pycurl.RESPONSE_CODE)
        if code != 200:
            return {"status": code, "message": "Error fetching proxy"}
        body = buffer.getvalue().decode("utf-8")
        res = json.loads(body)
        data = None
        parsed_url = urlparse(proxy_raw)
        domain = parsed_url.netloc
        if domain in ["proxyxoay.shop", "proxyxoay.org", "api.proxyxoay.org"]:
            if "proxyhttp" in res:
                raw = res["proxyhttp"]
                ip, port, user, pwd = raw.split(":", 3)
                data = {
                    "username": user,
                    "password": pwd,
                    "server": f"{ip}:{port}",
                }
        # if domain in ["api.proxyxoay.org"]:
        #     res["status"] = 100
        else:
            raise Exception(f"Invalid domain ({domain})")
        # res["status"] = 100
        return {
            "data": data,
            "status": res.get("status"),
            "message": res.get("message"),
        }
    except Exception as e:
        raise Exception(e)
