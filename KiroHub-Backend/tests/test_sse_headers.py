import unittest

from app.api.routes.v1 import _sse_no_buffer_headers


class TestSSEHeaders(unittest.TestCase):
    def test_sse_no_buffer_headers(self) -> None:
        headers = _sse_no_buffer_headers()
        self.assertEqual(headers.get("X-Accel-Buffering"), "no")
        self.assertEqual(headers.get("Connection"), "keep-alive")
        self.assertIn("no-cache", headers.get("Cache-Control") or "")
        self.assertIn("no-transform", headers.get("Cache-Control") or "")


if __name__ == "__main__":
    unittest.main()

