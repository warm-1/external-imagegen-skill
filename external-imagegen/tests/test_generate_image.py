import base64
import importlib.util
import json
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "generate_image.py"
SPEC = importlib.util.spec_from_file_location("generate_image", SCRIPT)
generate_image = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(generate_image)

PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


class ApiHandler(BaseHTTPRequestHandler):
    mode = "base64"
    request_payload = None
    authorization = None
    user_agent = None

    def do_POST(self):
        length = int(self.headers["Content-Length"])
        type(self).request_payload = json.loads(self.rfile.read(length))
        type(self).authorization = self.headers.get("Authorization")
        type(self).user_agent = self.headers.get("User-Agent")
        if self.path != "/v1/images/generations":
            self.send_error(404)
            return

        if type(self).mode == "base64":
            data = {"data": [{"b64_json": base64.b64encode(PNG).decode()}]}
        else:
            data = {"data": [{"url": f"http://127.0.0.1:{self.server.server_port}/image.png"}]}
        body = json.dumps(data).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path != "/image.png":
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", "image/png")
        self.send_header("Content-Length", str(len(PNG)))
        self.end_headers()
        self.wfile.write(PNG)

    def log_message(self, format, *args):
        pass


class GenerateImageTest(unittest.TestCase):
    def setUp(self):
        ApiHandler.request_payload = None
        ApiHandler.authorization = None
        ApiHandler.user_agent = None
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), ApiHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.server.server_port}/v1"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def test_requires_all_api_environment_variables(self):
        with self.assertRaisesRegex(RuntimeError, "IMAGE_API_BASE_URL"):
            generate_image.config_from_env({})

    def test_saves_base64_response_and_sends_expected_request(self):
        ApiHandler.mode = "base64"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = generate_image.generate(
                prompt="a moon cat",
                output_path="outputs/moon-cat.png",
                base_url=self.base_url,
                api_key="test-key",
                model="image-model",
                size="1024x1024",
                root=root,
            )

            self.assertEqual(output, (root / "outputs" / "moon-cat.png").resolve())
            self.assertEqual(output.read_bytes(), PNG)
            self.assertEqual(ApiHandler.authorization, "Bearer test-key")
            self.assertEqual(ApiHandler.user_agent, "external-imagegen-skill/1.0")
            self.assertEqual(
                ApiHandler.request_payload,
                {
                    "model": "image-model",
                    "prompt": "a moon cat",
                    "size": "1024x1024",
                    "response_format": "b64_json",
                },
            )

    def test_downloads_url_response(self):
        ApiHandler.mode = "url"
        with tempfile.TemporaryDirectory() as directory:
            output = generate_image.generate(
                prompt="a moon cat",
                output_path="outputs/moon-cat.png",
                base_url=self.base_url,
                api_key="test-key",
                model="image-model",
                size="1024x1024",
                root=Path(directory),
            )

            self.assertEqual(output.read_bytes(), PNG)

    def test_rejects_output_outside_current_project(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "current project"):
                generate_image.generate(
                    prompt="a moon cat",
                    output_path="../moon-cat.png",
                    base_url=self.base_url,
                    api_key="test-key",
                    model="image-model",
                    size="1024x1024",
                    root=Path(directory),
                )


if __name__ == "__main__":
    unittest.main()
