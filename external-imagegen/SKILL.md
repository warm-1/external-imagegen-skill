---
name: external-imagegen
description: Use when the user asks Codex to generate, create, draw, render, or produce a raster image, picture, poster, illustration, concept art, product visual, cover, thumbnail, or image variant through an external OpenAI-compatible image API.
---

# External Image Generator

Require `IMAGE_API_BASE_URL`, `IMAGE_API_KEY`, and `IMAGE_MODEL` in the environment.

Use the bundled script for every raster image generation request:

```bash
python3 "<skill-directory>/scripts/generate_image.py" \
  --prompt "<complete production prompt>" \
  --output "outputs/<descriptive-name>.png" \
  --size "1024x1024"
```

Replace `<skill-directory>` with this Skill's absolute directory. Keep output inside the current project. Use the user's requested path when provided; otherwise use `outputs/`.

After generation, inspect the saved image, verify it matches the request, and show it to the user. Report the absolute saved path and final prompt.

If the external API fails, report the error. Do not use Codex's built-in image generator or another image provider as a fallback.
