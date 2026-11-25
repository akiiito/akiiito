"""社労士 自分専用学習アプリ「Score」 - FastAPI + Jinja2 + SQLite"""
from __future__ import annotations

import base64
import os
import secrets
from pathlib import Path
from urllib.parse import quote

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import advisor, db, stats
from .exam import SUBJECTS, Store, load_store, question_label

APP_DIR = Path(__file__).resolve().parent
app = FastAPI(title="Score - 社労士学習")
app.mount("/static", StaticFiles(directory=APP_DIR / "static"), name="static")
templates = Jinja2Templates(directory=APP_DIR / "templates")

store: Store = load_store()
db.init_db()

templates.env.globals.update(
    SUBJECTS=SUBJECTS,
    store=store,
    qlabel=question_label,
    yt_search=lambda name: "https://www.youtube.com/results?search_query=" + quote(f"社労士 {name}"),
)

# ---- 任意のパスワード保護（APP_PASSWORD を設定した場合のみ有効） ----
APP_PASSWORD = os.environ.get("APP_PASSWORD", "")


@app.middleware("http")
async def basic_auth(request: Request, call_next):
    if APP_PASSWORD and not request.url.path.startswith("/static"):
        header = request.headers.get("authorization", "")
        ok = False
        if header.startswith("Basic "):
            try:
                _, pw = base64.b64decode(header[6:]).decode().split(":", 1)
                ok = secrets.compare_digest(pw, APP_PASSWORD)
            except Exception:
                ok = False
        if not ok:
            return HTMLResponse("認証が必要です", status_code=401,
                                headers={"WWW-Authenticate": 'Basic realm="score"'})
    return await call_next(request)


def render(request: Request, name: str, tab: str, **ctx):
    return templates.TemplateResponse(request, name, {"tab": tab, **ctx})


def reload_store() -> None:
    global store
    store = load_store()
    templates.env.globals["store"] = store


# ---------------- ホーム ----------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    settings = db.get_settings()
    return render(request, "home.html", "home",
                  ov=stats.overview(store, settings),
                  subjects=stats.subject_stats(store, settings),
                  advice=db.latest_advice("overall"),
                  settings=settings)


# ---------------- 演習 ----------------
@app.get("/practice", response_class=HTMLResponse)
def practice(request: Request, subject: str = ""):
    settings = db.get_settings()
    tstats = stats.topic_stats(store)
    pool = stats.eligible_questions(store, settings)
    topic_counts: dict[str, int] = {}
    for q in pool:
        topic_counts[q["topic"]] = topic_counts.get(q["topic"], 0) + 1
    return render(request, "practice.html", "practice",
                  subjects=stats.subject_stats(store, settings),
                  selected=subject, tstats=tstats, topic_counts=topic_counts,
                  settings=settings, exams=store.exams,
                  ov=stats.overview(store, settings))


@app.post("/practice/start")
def practice_start(subject: str = Form(""), topic: str = Form(""), fmt: str = Form(""),
                   order: str = Form("smart"), count: int = Form(10)):
    settings = db.get_settings()
    qids = stats.select_questions(store, settings, subject=subject, topic=topic,
                                  fmt=fmt, order=order, count=count)
    if not qids:
        return RedirectResponse("/practice?empty=1", status_code=303)
    parts = []
    if topic:
        parts.append(store.topic_name(topic))
    elif subject:
        parts.append(SUBJECTS[subject])
    else:
        parts.append("全科目")
    if fmt:
        parts.append(fmt)
    parts.append({"wrong": "誤答復習", "new": "未着手", "random": "ランダム"}.get(order, "おまかせ"))
    mode = "review" if order == "wrong" else "practice"
    sid = db.create_session(mode, " / ".join(parts), qids)
    return RedirectResponse(f"/s/{sid}/0", status_code=303)


@app.post("/mock/start")
def mock_start(exam: str = Form(...), fmt: str = Form("")):
    settings = db.get_settings()
    qs = [q for q in stats.eligible_questions(store, settings, for_mock=True) if q["exam"] == exam]
    if fmt:
        qs = [q for q in qs if q["format"] == fmt]
    qs.sort(key=lambda q: (q["format"] != "選択式", q["number"]))
    if not qs:
        raise HTTPException(404, "問題がありません")
    title = f"{exam} 試験回" + (f"（{fmt}）" if fmt else "")
    sid = db.create_session("mock", title, [q["id"] for q in qs])
    return RedirectResponse(f"/s/{sid}/0", status_code=303)


def _load(sid: int, idx: int):
    sess = db.get_session(sid)
    if not sess or idx < 0 or idx >= len(sess["question_ids"]):
        raise HTTPException(404)
    q = store.questions.get(sess["question_ids"][idx])
    if not q:
        raise HTTPException(404, "問題データが見つかりません")
    return sess, q


@app.get("/s/{sid}/{idx:int}", response_class=HTMLResponse)
def question_page(request: Request, sid: int, idx: int):
    sess, q = _load(sid, idx)
    return render(request, "question.html", "practice", sess=sess, q=q, idx=idx,
                  total=len(sess["question_ids"]), topic_name=store.topic_name(q["topic"]))


@app.post("/s/{sid}/{idx:int}")
async def answer(request: Request, sid: int, idx: int):
    sess, q = _load(sid, idx)
    form = await request.form()
    skipped = form.get("action") == "skip"
    try:
        time_ms = int(form.get("elapsed_ms") or 0) or None
    except ValueError:
        time_ms = None

    if q["format"] == "選択式":
        total = len(q["blanks"])
        selected = {}
        correct = 0
        if not skipped:
            for b in q["blanks"]:
                v = form.get(f"blank_{b['label']}")
                selected[b["label"]] = int(v) if v else None
                if selected[b["label"]] == b["answer"]:
                    correct += 1
        db.record_answer(sid, idx, q["id"], None if skipped else selected, skipped, correct, total, time_ms)
    else:
        sel = form.get("choice")
        if not sel and not skipped:
            return RedirectResponse(f"/s/{sid}/{idx}", status_code=303)
        correct = int(sel == q["answer"]) if not skipped else 0
        db.record_answer(sid, idx, q["id"], None if skipped else sel, skipped, correct, 1, time_ms)

    if sess["mode"] == "mock":
        return RedirectResponse(_next_url(sess, sid, idx), status_code=303)
    return RedirectResponse(f"/s/{sid}/{idx}/feedback", status_code=303)


def _next_url(sess, sid, idx):
    if idx + 1 < len(sess["question_ids"]):
        return f"/s/{sid}/{idx + 1}"
    return f"/s/{sid}/result"


@app.get("/s/{sid}/{idx:int}/feedback", response_class=HTMLResponse)
def feedback(request: Request, sid: int, idx: int):
    sess, q = _load(sid, idx)
    ans = db.session_answers(sid).get(idx)
    return render(request, "feedback.html", "practice", sess=sess, q=q, idx=idx, ans=ans,
                  total=len(sess["question_ids"]), next_url=_next_url(sess, sid, idx),
                  topic_name=store.topic_name(q["topic"]), videos=store.videos_for(q["topic"]))


@app.get("/s/{sid}/result", response_class=HTMLResponse)
def result(request: Request, sid: int):
    sess = db.get_session(sid)
    if not sess:
        raise HTTPException(404)
    db.finish_session(sid)
    settings = db.get_settings()
    answers = db.session_answers(sid)
    rows = []
    for i, qid in enumerate(sess["question_ids"]):
        q = store.questions.get(qid)
        if q:
            rows.append({"i": i, "q": q, "a": answers.get(i)})
    done = [r["a"] for r in rows if r["a"] and not r["a"]["skipped"]]
    summary = {
        "correct": sum(a["correct_units"] for a in done),
        "units": sum(r["a"]["total_units"] if r["a"] else (len(r["q"]["blanks"]) if r["q"]["format"] == "選択式" else 1)
                     for r in rows),
        "skipped": sum(1 for r in rows if not r["a"] or r["a"]["skipped"]),
    }
    summary["pct"] = round(100 * summary["correct"] / summary["units"]) if summary["units"] else 0
    mock = stats.score_mock(store, settings, sess["question_ids"], answers) if sess["mode"] == "mock" else None
    return render(request, "result.html", "practice", sess=sess, rows=rows, summary=summary, mock=mock,
                  advice=db.latest_advice(f"session:{sid}"))


@app.get("/q/{qid}", response_class=HTMLResponse)
def question_detail(request: Request, qid: str):
    q = store.questions.get(qid)
    if not q:
        raise HTTPException(404)
    return render(request, "feedback.html", "history", sess=None, q=q, idx=0, ans=None, total=1,
                  next_url=None, topic_name=store.topic_name(q["topic"]), videos=store.videos_for(q["topic"]))


# ---------------- 学習（動画） ----------------
@app.get("/learn", response_class=HTMLResponse)
def learn(request: Request, open: str = ""):
    return render(request, "learn.html", "learn", tstats=stats.topic_stats(store), open_topic=open)


# ---------------- 履歴・アドバイス ----------------
@app.get("/history", response_class=HTMLResponse)
def history(request: Request):
    settings = db.get_settings()
    return render(request, "history.html", "history",
                  subjects=stats.subject_stats(store, settings),
                  ov=stats.overview(store, settings),
                  sessions=db.recent_sessions(20),
                  advice=db.latest_advice("overall"))


def _back_url(scope: str) -> str:
    if scope.startswith("session:"):
        return f"/s/{int(scope.split(':', 1)[1])}/result"
    return "/history"


@app.get("/advice", response_class=HTMLResponse)
def advice_page(request: Request, scope: str = "overall", error: str = "", text: str = ""):
    """Claudeに渡す学習ログのコピーと、Claudeの返答の貼り付け。"""
    settings = db.get_settings()
    sid = int(scope.split(":", 1)[1]) if scope.startswith("session:") else None
    ctx = advisor.build_context(store, settings, sid)
    return render(request, "advice.html", "history", scope=scope, error=error, pasted=text,
                  export=advisor.export_text(ctx, scope), back=_back_url(scope))


@app.post("/advice/import")
def advice_import(scope: str = Form("overall"), text: str = Form("")):
    try:
        advice = advisor.parse_advice(text)
    except advisor.AdviceParseError as e:
        return RedirectResponse(f"/advice?scope={quote(scope)}&error={quote(str(e))}", status_code=303)
    db.save_advice(scope, advice)
    if scope != "overall":  # セッション単位のアドバイスはホーム/履歴にも反映
        db.save_advice("overall", advice)
    return RedirectResponse(_back_url(scope) + "#advice", status_code=303)


# ---------------- 設定 ----------------
@app.get("/settings", response_class=HTMLResponse)
def settings_page(request: Request, saved: str = ""):
    return render(request, "settings.html", "settings", settings=db.get_settings(),
                  exams=store.exams, saved=saved,
                  n_questions=len(store.questions), n_videos=len(store.videos),
                  n_revised=sum(1 for q in store.questions.values() if q.get("law_check") == "revised"),
                  n_uncertain=sum(1 for q in store.questions.values() if q.get("law_check") == "uncertain"))


@app.post("/settings")
async def settings_save(request: Request):
    form = await request.form()
    values = {k: str(v) for k, v in form.items()}
    values["include_uncertain"] = "1" if form.get("include_uncertain") else "0"
    db.save_settings(values)
    return RedirectResponse("/settings?saved=1", status_code=303)


@app.post("/reload")
def reload_data():
    reload_store()
    return RedirectResponse("/settings?saved=1", status_code=303)
