# Image generation backend policy

## Primary backend

The primary image-generation backend for this workspace is **ComfyUI**.

## Why

- It is already configured locally.
- It fits the long-term plan of routing heavier generation work to Diego's more powerful Windows workstation later.
- It gives more control over workflows than cloud-only image generation.
- It aligns well with the design-agent role.

## Operational rule

- Prefer ComfyUI first for image generation.
- Treat cloud image providers as optional future fallbacks.
- Do not assume Google/Imagen is the default image backend anymore.

## Current local endpoint

- `http://127.0.0.1:8188`

## Future target architecture

- Craw orchestrates image work.
- Design agent owns image-generation tasks logically.
- ComfyUI remains the backend, even if execution later moves off the Mac to Diego's Windows workstation.

## Notes

- Current generation times on the Mac can be slow.
- When fallbacks are added later, document explicit routing priorities rather than letting the system silently drift to a cloud provider.
