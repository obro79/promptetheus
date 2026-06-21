#!/usr/bin/env python3
"""Generate the README setup walkthrough GIF.

The generator uses only local system tools available on macOS:

- qlmanage renders SVG frames to PNG thumbnails.
- ffmpeg assembles the PNG sequence into an animated GIF.
"""

from __future__ import annotations

import html
import shutil
import subprocess
import tempfile
from pathlib import Path


WIDTH = 960
HEIGHT = 540
CROP_HEIGHT = 676
REPO_ROOT = Path(__file__).resolve().parents[1]
OUT = REPO_ROOT / "docs" / "assets" / "promptetheus-install.gif"

FRAMES = [
    (
        "Install the SDK",
        [
            "$ pip install promptetheus",
            "Collecting promptetheus",
            "Installing collected packages: promptetheus",
            "Successfully installed promptetheus",
        ],
    ),
    (
        "Bootstrap a project key",
        [
            '$ export PROMPTETHEUS_CONSOLE_TOKEN="..."',
            "$ promptetheus init \\",
            '    --workspace-name "Acme" --project-name "Browser Agent" \\',
            "    --write-env .env",
            "Created workspace: Acme",
            "Created project: Browser Agent",
            "Wrote .env",
        ],
    ),
    (
        "Wrap the agent run",
        [
            "import promptetheus as pt",
            "with pt.trace.start(",
            '    agent="browser-agent", user_goal=goal,',
            ") as session:",
            "    session.user_message(goal)",
            "    result = agent.run(goal)",
            "    session.goal_check(result.ok,",
            "        mismatches=result.mismatches)",
        ],
    ),
    (
        "Inspect local delivery",
        [
            "$ promptetheus doctor",
            "API URL: https://api.promptetheus.dev",
            "API key: configured",
            "Spool: 0 pending sessions",
            "$ promptetheus replay sess_demo --tree",
        ],
    ),
    (
        "Connect MCP evidence",
        [
            "$ promptetheus mcp install --client codex \\",
            "    --workspace acme \\",
            "    --project-ref abcdefghijklmnopqrst",
            "Server: promptetheus",
            "Transport: stdio bridge to hosted MCP",
            "Scope: read-only Supabase evidence for this project",
        ],
    ),
]


def main() -> int:
    _require("qlmanage")
    _require("ffmpeg")
    OUT.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(
        prefix="promptetheus-readme-gif-", dir="/tmp"
    ) as raw_tmp:
        tmp = Path(raw_tmp)
        svg_dir = tmp / "svg"
        png_dir = tmp / "png"
        frames_dir = tmp / "frames"
        svg_dir.mkdir()
        png_dir.mkdir()
        frames_dir.mkdir()

        svg_paths = []
        for index, (title, lines) in enumerate(FRAMES):
            path = svg_dir / f"frame{index:03d}.svg"
            path.write_text(_svg(title, lines), encoding="utf-8")
            svg_paths.append(path)

        for index, path in enumerate(svg_paths):
            _run(
                [
                    "qlmanage",
                    "-t",
                    "-s",
                    str(WIDTH),
                    "-o",
                    str(png_dir),
                    str(path),
                ]
            )
            rendered = png_dir / f"{path.name}.png"
            if not rendered.exists():
                raise FileNotFoundError(f"Quick Look did not render {path.name}")
            shutil.copyfile(rendered, frames_dir / f"frame{index:03d}.png")

        palette = tmp / "palette.png"
        _run(
            [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-framerate",
                "1",
                "-start_number",
                "0",
                "-i",
                str(frames_dir / "frame%03d.png"),
                "-vf",
                f"fps=8,crop={WIDTH}:{CROP_HEIGHT}:0:0,scale=960:540:flags=lanczos,palettegen",
                str(palette),
            ]
        )
        _run(
            [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-framerate",
                "1",
                "-start_number",
                "0",
                "-i",
                str(frames_dir / "frame%03d.png"),
                "-i",
                str(palette),
                "-filter_complex",
                f"fps=8,crop={WIDTH}:{CROP_HEIGHT}:0:0,scale=960:540:flags=lanczos[x];[x][1:v]paletteuse=dither=bayer",
                "-loop",
                "0",
                str(OUT),
            ]
        )

    print(f"Wrote {OUT}")
    return 0


def _require(command: str) -> None:
    if shutil.which(command) is None:
        raise SystemExit(f"Missing required command: {command}")


def _run(args: list[str]) -> None:
    result = subprocess.run(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    if result.returncode != 0:
        command = " ".join(args)
        raise RuntimeError(f"Command failed ({command}):\n{result.stdout}")


def _svg(title: str, lines: list[str]) -> str:
    line_nodes = []
    y = 176
    for line in lines:
        color = "#f9fafb"
        if line.startswith("$"):
            color = "#7dd3fc"
        elif line.startswith(" ") or line.startswith("with ") or line.startswith("import "):
            color = "#d1d5db"
        elif line == "":
            y += 24
            continue
        line_nodes.append(
            f'<text x="72" y="{y}" class="code" fill="{color}" xml:space="preserve">{html.escape(line)}</text>'
        )
        y += 32

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#0f172a"/>
      <stop offset="1" stop-color="#111827"/>
    </linearGradient>
    <style>
      .title {{ font: 700 30px Menlo, Monaco, Consolas, monospace; letter-spacing: 0; }}
      .caption {{ font: 500 17px Menlo, Monaco, Consolas, monospace; letter-spacing: 0; }}
      .code {{ font: 500 21px Menlo, Monaco, Consolas, monospace; letter-spacing: 0; }}
    </style>
  </defs>
  <rect width="960" height="540" fill="url(#bg)"/>
  <rect x="48" y="52" width="864" height="420" rx="16" fill="#020617" stroke="#334155" stroke-width="2"/>
  <rect x="48" y="52" width="864" height="58" rx="16" fill="#111827"/>
  <circle cx="76" cy="82" r="8" fill="#ef4444"/>
  <circle cx="102" cy="82" r="8" fill="#f59e0b"/>
  <circle cx="128" cy="82" r="8" fill="#22c55e"/>
  <text x="164" y="88" class="caption" fill="#9ca3af">promptetheus setup</text>
  <text x="72" y="138" class="title" fill="#f8fafc">{html.escape(title)}</text>
  {''.join(line_nodes)}
  <text x="72" y="438" class="caption" fill="#94a3b8">Observe -> replay -> retrieve evidence -> fix</text>
</svg>
"""


if __name__ == "__main__":
    raise SystemExit(main())
