"""Local eval loop — runs agent over dataset, scores responses, no GCP needed."""

import asyncio
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from dotenv import load_dotenv

load_dotenv()

# LiteLLM needs OPENAI_API_KEY for OpenAI-compatible providers
if os.getenv("HERMES_API_KEY") and not os.getenv("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = os.getenv("HERMES_API_KEY")

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.agent import root_agent

DATASET_PATH = Path("tests/eval/datasets/basic-dataset.json")
RESULTS_DIR = Path("artifacts/eval_results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def load_dataset(path: Path) -> list[dict]:
    with open(path) as f:
        data = json.load(f)
    return data["eval_cases"]


async def run_agent(prompt_text: str, timeout_sec: int = 300) -> dict:
    session_service = InMemorySessionService()
    runner = Runner(
        agent=root_agent,
        session_service=session_service,
        app_name="app",
    )
    session = session_service.create_session_sync(
        user_id="eval_user", app_name="app"
    )

    content = types.Content(role="user", parts=[types.Part.from_text(text=prompt_text)])
    events = []
    start = time.time()
    async for event in runner.run_async(
        session_id=session.id,
        user_id="eval_user",
        new_message=content,
    ):
        if time.time() - start > timeout_sec:
            break
        events.append({
            "author": event.author,
            "type": str(type(event.content).__name__) if event.content else None,
            "text": _get_text(event),
            "function_call": _get_func_call(event),
            "function_response": _get_func_resp(event),
        })
    return {"session_id": session.id, "events": events}


def _get_text(event) -> str | None:
    if not event.content or not event.content.parts:
        return None
    for p in event.content.parts:
        if p.text:
            return p.text
    return None


def _get_func_call(event) -> dict | None:
    if not event.content or not event.content.parts:
        return None
    for p in event.content.parts:
        if p.function_call:
            return {"name": p.function_call.name, "args": _simplify(p.function_call.args)}
    return None


def _get_func_resp(event) -> dict | None:
    if not event.content or not event.content.parts:
        return None
    for p in event.content.parts:
        if p.function_response:
            return {"name": p.function_response.name, "response": _simplify(p.function_response.response)}
    return None


def _simplify(val):
    if isinstance(val, dict):
        return {k: _simplify(v) for k, v in val.items()}
    if hasattr(val, "items"):
        return dict(val)
    return val


def score_response(events: list[dict]) -> dict:
    agent_texts = [e["text"] for e in events if e["author"] != "user" and e["text"]]
    final = agent_texts[-1] if agent_texts else ""
    tool_calls = [e for e in events if e["function_call"]]
    errors = [e for e in events if e.get("type") == "ErrorPart"]

    score = 1
    reasons = []

    if errors:
        score = 1
        reasons.append(f"Agent error: {errors[-1].get('text', 'unknown')}")
    elif not agent_texts:
        score = 1
        reasons.append("No agent response")
    elif not tool_calls:
        score = 2
        reasons.append("Agent did not call any tools")
    else:
        score = 3
        reasons.append("Agent called tools")

    if final and len(final) > 50:
        score = min(score + 1, 5)
        reasons.append("Final response detailed (>50 chars)")

    return {
        "score": score,
        "max_score": 5,
        "reasons": reasons,
        "tool_call_count": len(tool_calls),
        "final_response_length": len(final) if final else 0,
        "has_error": len(errors) > 0,
    }


async def main():
    cases = load_dataset(DATASET_PATH)
    print(f"Loaded {len(cases)} eval cases from {DATASET_PATH}\n")

    results = []
    for i, case in enumerate(cases):
        cid = case.get("eval_case_id", f"case_{i}")
        prompt = case.get("prompt", {}).get("parts", [{}])[0].get("text", "")
        if not prompt:
            print(f"  [{i+1}/{len(cases)}] {cid}: SKIP (no prompt)")
            continue

        print(f"  [{i+1}/{len(cases)}] {cid}: running...", end=" ", flush=True)
        try:
            trace = await run_agent(prompt)
            score = score_response(trace["events"])
            results.append({
                "eval_case_id": cid,
                "prompt": prompt,
                "score": score,
                "event_count": len(trace["events"]),
            })
            status = f"score={score['score']}/5 tools={score['tool_call_count']}"
            if score["has_error"]:
                status += " ERROR"
            print(status)
        except Exception as e:
            print(f"FAILED: {e}")
            results.append({
                "eval_case_id": cid,
                "prompt": prompt,
                "score": {"score": 0, "max_score": 5, "reasons": [str(e)], "tool_call_count": 0, "final_response_length": 0, "has_error": True},
                "event_count": 0,
            })

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    out_path = RESULTS_DIR / f"results_{timestamp}.json"
    with open(out_path, "w") as f:
        json.dump({"eval_cases": results, "summary": {
            "total": len(results),
            "avg_score": sum(r["score"]["score"] for r in results) / len(results) if results else 0,
            "passed": sum(1 for r in results if r["score"]["score"] >= 3),
            "failed": sum(1 for r in results if r["score"]["score"] < 3),
        }}, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*50}")
    print(f"Results written to {out_path}")
    print(f"Summary: {len(results)} cases, avg score {sum(r['score']['score'] for r in results) / len(results):.1f}/5")
    print(f"Passed (>=3): {sum(1 for r in results if r['score']['score'] >= 3)}")
    print(f"Failed (<3):  {sum(1 for r in results if r['score']['score'] < 3)}")
    print(f"{'='*50}")

    for r in results:
        s = r["score"]
        color = "PASS" if s["score"] >= 3 else "FAIL"
        print(f"  [{color}] {r['eval_case_id']}: {s['score']}/5 — {s['reasons'][0]}")


if __name__ == "__main__":
    asyncio.run(main())
