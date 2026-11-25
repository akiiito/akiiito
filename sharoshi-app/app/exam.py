"""社労士試験の構造と、問題・論点・動画データの読み込み。"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# 科目（選択式は8科目、択一式は労一+社一を「一般常識」として1科目扱い）
SUBJECTS: dict[str, str] = {
    "roki": "労基・安衛",
    "rosai": "労災・徴収",
    "koyo": "雇用・徴収",
    "roippan": "労一",
    "shaippan": "社一",
    "kenpo": "健保",
    "konen": "厚年",
    "kokunen": "国年",
}

# 択一式の採点単位（基準点判定用）: 一般常識は労一+社一の合算
TAKUITSU_GROUPS: dict[str, list[str]] = {
    "roki": ["roki"],
    "rosai": ["rosai"],
    "koyo": ["koyo"],
    "ippan": ["roippan", "shaippan"],
    "kenpo": ["kenpo"],
    "konen": ["konen"],
    "kokunen": ["kokunen"],
}
TAKUITSU_GROUP_NAMES = {**SUBJECTS, "ippan": "一般常識"}

# 1問あたりの目安時間（秒）: 択一 210分/70問、選択 80分/8問
TARGET_SECONDS = {"択一式": 180, "選択式": 600, "一問一答": 36}


@dataclass
class Topic:
    id: str
    name: str
    group: str
    subject: str


@dataclass
class Video:
    id: str
    channel: str
    title: str
    url: str
    topic: str
    kind: str = "講義"
    minutes: int | None = None
    published: str | None = None


@dataclass
class Store:
    topics: dict[str, Topic] = field(default_factory=dict)
    groups: list[dict] = field(default_factory=list)
    questions: dict[str, dict] = field(default_factory=dict)
    exams: list[dict] = field(default_factory=list)  # [{exam, year_num, count}]
    exam_meta: dict[str, dict] = field(default_factory=dict)  # 試験回ごとの合格基準など
    videos: list[Video] = field(default_factory=list)

    def topic_name(self, tid: str) -> str:
        t = self.topics.get(tid)
        return t.name if t else tid

    def videos_for(self, tid: str) -> list[Video]:
        return [v for v in self.videos if v.topic == tid]


def _load_json(path: Path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def load_store() -> Store:
    s = Store()
    tdata = _load_json(DATA_DIR / "topics.json")
    for g in tdata["groups"]:
        s.groups.append(g)
        for t in g["topics"]:
            s.topics[t["id"]] = Topic(t["id"], t["name"], g["group"], g["subject"])

    qdir = DATA_DIR / "questions"
    for path in sorted(qdir.glob("*.json")):
        data = _load_json(path)
        exam = data.get("exam", path.stem)
        year_num = data.get("year_num", 0)
        n = 0
        for q in data.get("questions", []):
            q.setdefault("law_check", "ok")
            q["exam"] = exam
            q["year_num"] = year_num
            q["is_sample"] = exam == "サンプル"
            s.questions[q["id"]] = q
            n += 1
        mockable = any(q["format"] in ("択一式", "選択式") for q in data.get("questions", []))
        s.exams.append({"exam": exam, "year_num": year_num, "count": n, "mockable": mockable})
    s.exams.sort(key=lambda e: e["year_num"], reverse=True)

    mpath = DATA_DIR / "exams.json"
    if mpath.exists():
        s.exam_meta = {k: v for k, v in _load_json(mpath).items() if not k.startswith("_")}

    vpath = DATA_DIR / "videos.json"
    if vpath.exists():
        for v in _load_json(vpath).get("videos", []):
            s.videos.append(Video(**{k: v.get(k) for k in Video.__dataclass_fields__ if k in v}))
    return s


def question_label(q: dict) -> str:
    if q["format"] == "一問一答":
        return f'{q["exam"]} 択一問{q["number"]}-{q["branch"]}'
    prefix = "選択" if q["format"] == "選択式" else "択一"
    return f'{q["exam"]} {prefix}問{q["number"]}'
