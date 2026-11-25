"""スクリプト共通: Claude 呼び出しと論点マスタ。"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import anthropic

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
MODEL = os.environ.get("SHAROSHI_MODEL", "claude-opus-5-5")


def load_topics() -> list[dict]:
    data = json.loads((DATA / "topics.json").read_text(encoding="utf-8"))
    out = []
    for g in data["groups"]:
        for t in g["topics"]:
            out.append({"id": t["id"], "name": t["name"], "group": g["group"], "subject": g["subject"]})
    return out


def topics_text(topics: list[dict]) -> str:
    return "\n".join(f'- {t["id"]}: {t["group"]} / {t["name"]}' for t in topics)


def call_json(client: anthropic.Anthropic, *, system: str, content: list, schema: dict,
              effort: str = "high") -> dict:
    """構造化出力(JSON)で Claude を呼ぶ。長い出力に備えてストリーミング。"""
    with client.beta.messages.stream(
        model=MODEL,
        max_tokens=64000,
        system=system,
        messages=[{"role": "user", "content": content}],
        output_config={"effort": effort, "format": {"type": "json_schema", "schema": schema}},
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
    ) as stream:
        msg = stream.get_final_message()
    if msg.stop_reason == "refusal":
        sys.exit("モデルが応答を辞退しました。")
    if msg.stop_reason == "max_tokens":
        raise RuntimeError("出力が上限に達しました。範囲を狭めて再実行してください。")
    u = msg.usage
    print(f"    tokens: in={u.input_tokens} cache_read={u.cache_read_input_tokens} out={u.output_tokens}",
          file=sys.stderr)
    text = next(b.text for b in msg.content if b.type == "text")
    return json.loads(text)
