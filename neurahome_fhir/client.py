import logging
import requests

class FHIRClient:
    def __init__(self, url: str, headers: dict) -> None:
        self.url = url
        self.headers = headers

    def post_bundle(self, bundle: dict, timeout: int = 10) -> requests.Response:
        resp = requests.post(self.url, headers=self.headers, json=bundle, timeout=timeout)
        logging.info("Posted %d Observations | HTTP %s",
                     len(bundle.get("entry", [])), resp.status_code)
        logging.debug("Response body: %s", resp.text[:500])
        return resp
