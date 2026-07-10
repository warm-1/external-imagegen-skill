#!/usr/bin/env python3
import argparse
import base64
import json
import os
import urllib.error
import urllib.request
from pathlib import Path


USER_AGENT = "external-imagegen-skill/1.0"


def config_from_env(env):
    names = ("IMAGE_API_BASE_URL", "IMAGE_API_KEY", "IMAGE_MODEL")
    missing = [name for name in names if not env.get(name)]
    if missing:
        raise RuntimeError(
            "Missing required environment variables: " + ", ".join(missing)
        )
    return env["IMAGE_API_BASE_URL"], env["IMAGE_API_KEY"], env["IMAGE_MODEL"]


def project_output_path(output_path, root):
    root = Path(root).resolve()
    output = (root / output_path).resolve()
    if output == root or root not in output.parents:
        raise ValueError("Output path must stay inside the current project")
    return output


def request_json(url, payload, api_key):
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        detail = error.read().decode(errors="replace")
        raise RuntimeError(f"Image API returned HTTP {error.code}: {detail}") from error
    except urllib.error.URLError as error:
        raise RuntimeError(f"Image API request failed: {error.reason}") from error


def image_bytes(result):
    try:
        item = result["data"][0]
    except (KeyError, IndexError, TypeError) as error:
        raise RuntimeError("Image API response has no data item") from error

    if item.get("b64_json"):
        try:
            return base64.b64decode(item["b64_json"], validate=True)
        except (ValueError, TypeError) as error:
            raise RuntimeError("Image API returned invalid Base64 image data") from error

    if item.get("url"):
        try:
            with urllib.request.urlopen(item["url"], timeout=300) as response:
                return response.read()
        except urllib.error.URLError as error:
            raise RuntimeError(f"Image download failed: {error.reason}") from error

    raise RuntimeError("Image API response has neither b64_json nor url")


def generate(prompt, output_path, base_url, api_key, model, size, root):
    output = project_output_path(output_path, root)
    result = request_json(
        f"{base_url.rstrip('/')}/images/generations",
        {
            "model": model,
            "prompt": prompt,
            "size": size,
            "response_format": "b64_json",
        },
        api_key,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(image_bytes(result))
    return output


def main():
    parser = argparse.ArgumentParser(
        description="Generate an image through an OpenAI-compatible image API"
    )
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--size", default="1024x1024")
    args = parser.parse_args()

    base_url, api_key, model = config_from_env(os.environ)
    output = generate(
        prompt=args.prompt,
        output_path=args.output,
        base_url=base_url,
        api_key=api_key,
        model=model,
        size=args.size,
        root=Path.cwd(),
    )
    print(f"IMAGE_SAVED={output}")


if __name__ == "__main__":
    main()
