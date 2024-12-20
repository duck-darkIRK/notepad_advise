import httpx

SERVER_PORT = "http://localhost:8000"

class HTTPClientManager:
    _client = None

    @staticmethod
    def get_client():
        """Trả về client đã được khởi tạo hoặc tạo mới nếu chưa có"""
        if HTTPClientManager._client is None:
            HTTPClientManager._client = httpx.Client(follow_redirects=True)
        return HTTPClientManager._client



