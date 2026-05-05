from __future__ import annotations

import unittest
from unittest.mock import patch

from CamComs import CamComsHttpClient, decode_envelope, encode_envelope


class FakeResponse:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self) -> bytes:
        return self.payload


class CamComsTransportTests(unittest.TestCase):
    def test_encode_decode_envelope(self) -> None:
        envelope = {"kind": "camcoms.encrypted", "ciphertext": "abc"}

        encoded = encode_envelope(envelope)

        self.assertEqual(decode_envelope(encoded), envelope)
        self.assertIsInstance(encoded, str)

    def test_http_client_posts_encoded_message_and_reads_encoded_response(self) -> None:
        envelope = {"kind": "camcoms.encrypted", "ciphertext": "abc"}
        encoded = encode_envelope(envelope)

        with patch("CamComs.transport.request.urlopen", return_value=FakeResponse(encoded.encode("ascii"))) as urlopen:
            client = CamComsHttpClient(host="192.168.4.1", port=8080, timeout_seconds=2.0)

            response = client.send_envelope(envelope)

        self.assertEqual(response, envelope)
        http_request = urlopen.call_args.args[0]
        self.assertEqual(http_request.full_url, "http://192.168.4.1:8080/")
        self.assertEqual(http_request.data, encoded.encode("ascii"))


if __name__ == "__main__":
    unittest.main()
