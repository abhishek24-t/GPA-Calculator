"""
GPA Assistant AI Agent
Supports multiple AI backends:
  1. OpenAI (keys starting with sk-)
  2. OpenAI-compatible providers via custom base_url
  3. Built-in deterministic academic engine (always works, no key needed)
"""

import os
import json
import re
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()

from .calculator import (
    calculate_sgpa,
    calculate_cgpa,
    predict_target_gpa,
    analyze_what_if,
    analyze_backlog_impact,
    DEFAULT_SPPU_SCALE,
    CalculationError,
    PASSING_GRADE_POINT,
)
from .database import list_records

# ── System prompt ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are "GPA Assistant AI", a professional and precise academic advisor for college engineering students, specialising in the SPPU (Savitribai Phule Pune University) CBCS grading system.

CRITICAL RULES:
1. NEVER invent or manually calculate GPA numbers. Call the provided tools for every numerical result.
2. Ask the student for any missing data (credits, SGPA, target GPA) before answering.
3. SPPU 10-point scale: O=10, A+=9, A=8, B+=7, B=6, C=5, P=4, F=0, Ab=0. Passing threshold = 4.0.
4. SGPA = Σ(Credit × GP) / Σ(Credits).  CGPA = Σ(Sem SGPA × Sem Credits) / Σ(Sem Credits).
5. For backlogs: failing earns 0 GP. Cleared grade replaces the 0 GP (SPPU CBCS default rule). Advise verifying branch ordinances.
6. Be encouraging but never guarantee outcomes.
7. Support English and conversational Hinglish naturally."""

TOOLS_SPEC = [
    {
        "type": "function",
        "function": {
            "name": "calculate_sgpa",
            "description": "Calculates SGPA from subjects with credits and grades.",
            "parameters": {
                "type": "object",
                "properties": {
                    "subjects": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "credit": {"type": "number"},
                                "grade": {"type": "string"},
                                "grade_point": {"type": "number"},
                            },
                            "required": ["credit"],
                        },
                    }
                },
                "required": ["subjects"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_cgpa",
            "description": "Calculates credit-weighted CGPA across semesters.",
            "parameters": {
                "type": "object",
                "properties": {
                    "semesters": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "sgpa": {"type": "number"},
                                "credits": {"type": "number"},
                            },
                            "required": ["sgpa", "credits"],
                        },
                    }
                },
                "required": ["semesters"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "predict_target_gpa",
            "description": "Predicts required average SGPA in remaining credits to reach a target CGPA.",
            "parameters": {
                "type": "object",
                "properties": {
                    "current_cgpa": {"type": "number"},
                    "completed_credits": {"type": "number"},
                    "remaining_credits": {"type": "number"},
                    "target_cgpa": {"type": "number"},
                },
                "required": [
                    "current_cgpa",
                    "completed_credits",
                    "remaining_credits",
                    "target_cgpa",
                ],
            },
        },
    },
]


# ── Tool executor ─────────────────────────────────────────────────────────────
def execute_tool(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    try:
        if name == "calculate_sgpa":
            return calculate_sgpa(args["subjects"])
        if name == "calculate_cgpa":
            return calculate_cgpa(args["semesters"])
        if name == "predict_target_gpa":
            return predict_target_gpa(
                float(args["current_cgpa"]),
                float(args["completed_credits"]),
                float(args["remaining_credits"]),
                float(args["target_cgpa"]),
            )
        return {"error": f"Unknown tool: {name}"}
    except CalculationError as e:
        return {"error": f"Calculation error: {e}"}
    except Exception as e:
        return {"error": f"Tool error: {e}"}


# ── Key / provider detection ──────────────────────────────────────────────────
def _detect_provider(api_key: str):
    """
    Returns (base_url_or_None, model).
    None base_url → use default OpenAI endpoint.
    """
    if api_key.startswith("sk-ant-"):
        # Anthropic – not OpenAI-compatible via this client; fall back to engine
        return None, None

    if api_key.startswith("sk-"):
        # Standard OpenAI key
        return "https://api.openai.com/v1", os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    if api_key.startswith("AQ.") or api_key.startswith("Aq."):
        # Cloudflare Workers AI (OpenAI-compatible endpoint)
        account_id = os.getenv("CF_ACCOUNT_ID", "")
        if account_id:
            return f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/v1", "@cf/meta/llama-3.1-8b-instruct"
        # Fallback: try generic OpenAI-compatible with the key as-is
        return None, None  # will trigger deterministic engine

    # Unknown format – attempt as generic OpenAI-compatible
    base = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    return base, model


# ── Deterministic fallback intent engine ─────────────────────────────────────
def _rule_based_reply(message: str, academic_context: Optional[Dict]) -> Dict[str, Any]:
    msg = message.lower().strip()

    # Load saved semesters
    saved = list_records(record_type="semester")
    semesters_data = [
        {"name": r.get("title", f"Sem {i+1}"), "sgpa": float(r["sgpa"]), "credits": float(r["credits"])}
        for i, r in enumerate(saved)
        if r.get("sgpa") and r.get("credits")
    ]
    total_credits = sum(s["credits"] for s in semesters_data)
    current_cgpa = None
    if semesters_data:
        try:
            res = calculate_cgpa(semesters_data)
            current_cgpa = res["cgpa"]
        except Exception:
            pass

    # --- SGPA intent ---
    if any(k in msg for k in ["sgpa", "semester gpa", "what is my sgpa", "calculate sgpa"]):
        grades = re.findall(r"\b(o|a\+|a|b\+|b|c|p|f)\b", msg, re.IGNORECASE)
        credits_found = re.findall(r"(\d+(?:\.\d+)?)\s*cr(?:edit)?s?", msg)
        if academic_context and "context_subjects" in academic_context:
            try:
                r = calculate_sgpa(academic_context["context_subjects"])
                return {"intent": "sgpa", "reply": _fmt_sgpa(r), "calculations_performed": [r]}
            except Exception:
                pass
        if grades:
            crs = [float(c) for c in credits_found] if credits_found else [3.0] * len(grades)
            subjs = [{"name": f"Course {i+1}", "credit": crs[i] if i < len(crs) else 3.0, "grade": g.upper()} for i, g in enumerate(grades)]
            try:
                r = calculate_sgpa(subjs)
                return {"intent": "sgpa", "reply": _fmt_sgpa(r), "calculations_performed": [r]}
            except Exception:
                pass
        return {
            "intent": "ask_sgpa_data",
            "reply": (
                "To calculate your **SGPA**, I need your subjects with their **Credits** and **Grades**.\n\n"
                "Example: *'Mathematics 4 credits A+, Physics 4 credits A, DSA Lab 2 credits O'*\n\n"
                "Or use the **SGPA Calculator** tab for an interactive table!"
            ),
        }

    # --- Target CGPA intent ---
    target_m = re.search(r"(?:reach|target|achieve|get|score)\s*an?\s*([7-9](?:\.\d+)?)\s*(?:cgpa|gpa)?", msg)
    if target_m or any(k in msg for k in ["target cgpa", "reach cgpa", "improve cgpa", "what grades do i need"]):
        target_val = float(target_m.group(1)) if target_m else 8.5
        cur = current_cgpa or 8.0
        comp = total_credits if total_credits > 0 else 60.0
        rem = 22.0
        rem_m = re.search(r"(\d+)\s*(?:remaining|left|future|more)\s*cr", msg)
        if rem_m:
            rem = float(rem_m.group(1))
        try:
            r = predict_target_gpa(cur, comp, rem, target_val)
            return {"intent": "target_gpa", "reply": _fmt_target(r, cur, comp, rem), "calculations_performed": [r]}
        except Exception as e:
            return {"intent": "error", "reply": f"Could not run target prediction: {e}"}

    # --- What-if intent ---
    if any(k in msg for k in ["what if", "what happens if", "score 8", "score 9", "score 10", "next semester"]):
        cur = current_cgpa or 8.25
        comp = total_credits if total_credits > 0 else 64.0
        rem = 22.0
        lines = []
        for s in [7.5, 8.0, 8.5, 9.0, 9.5, 10.0]:
            new_cgpa = round(((cur * comp) + (s * rem)) / (comp + rem), 2)
            delta = round(new_cgpa - cur, 2)
            sign = "+" if delta >= 0 else ""
            lines.append(f"- **{s:.1f} SGPA** → Final CGPA: **{new_cgpa:.2f}** ({sign}{delta:.2f})")
        return {
            "intent": "what_if",
            "reply": (
                f"🔮 **What-If Projection** (Assuming {rem:.0f} credits next semester, current CGPA {cur:.2f}):\n\n"
                + "\n".join(lines)
                + "\n\n*Each 0.1 increase in semester SGPA adds roughly 0.03-0.05 to your overall CGPA at this stage.*"
            ),
        }

    # --- Backlog intent ---
    if any(k in msg for k in ["backlog", "fail", "kt ", " kt", "failed", "arrear", "detained"]):
        return {
            "intent": "backlog",
            "reply": (
                "⚠️ **How Backlogs Affect Your GPA (SPPU CBCS)**:\n\n"
                "1. A failed course earns **0 Grade Points** and the credits are **NOT counted** until you clear it.\n"
                "2. When you clear the exam and earn, say, **A (8 GP)** in a 4-credit course:\n"
                "   - You gain **32 points** to your cumulative tally.\n"
                "   - Your CGPA jumps upward based on: `New CGPA = (Old Points + 32) / Same Total Credits`\n"
                "3. The **Backlog Manager** tab can simulate the exact CGPA boost for your specific case.\n\n"
                "📌 *Always confirm with your College exam section whether improvement replaces or is recorded separately.*"
            ),
        }

    # --- SPPU grading info ---
    if any(k in msg for k in ["sppu", "grading", "grade scale", "grade system", "cbcs", "10 point", "10-point"]):
        return {
            "intent": "sppu_info",
            "reply": (
                "🏫 **SPPU 10-Point CBCS Grading Scale**:\n\n"
                "| Grade | Points | Marks Range |\n"
                "|:---:|:---:|:---:|\n"
                "| **O** | 10 | 90–100% |\n"
                "| **A+** | 9 | 80–89% |\n"
                "| **A** | 8 | 70–79% |\n"
                "| **B+** | 7 | 60–69% |\n"
                "| **B** | 6 | 55–59% |\n"
                "| **C** | 5 | 50–54% |\n"
                "| **P** | 4 | 40–49% |\n"
                "| **F** | 0 | < 40% |\n\n"
                "**Formulas:**\n"
                "- `SGPA = Σ(Credit × GP) / Σ(Credits)`\n"
                "- `CGPA = Σ(Semester SGPA × Credits) / Σ(Credits)`"
            ),
        }

    # --- CGPA intent ---
    if any(k in msg for k in ["cgpa", "cumulative", "overall gpa"]):
        if semesters_data and current_cgpa is not None:
            try:
                r = calculate_cgpa(semesters_data)
                lines = [f"- **{s['name']}**: SGPA {s['sgpa']:.2f} × {s['credits']:.0f} cr" for s in semesters_data]
                reply = (
                    f"📊 **Your Current CGPA: {r['cgpa']:.2f} / 10.0**\n\n"
                    f"Based on your {r['semester_count']} saved semesters ({r['total_credits']:.0f} credits):\n"
                    + "\n".join(lines)
                    + f"\n\nSimple unweighted average would be **{r['simple_average']:.2f}**. "
                    f"Weighted CGPA is more accurate when semester credits vary."
                )
                return {"intent": "cgpa", "reply": reply, "calculations_performed": [r]}
            except Exception:
                pass
        return {
            "intent": "ask_cgpa_data",
            "reply": (
                "To calculate your **CGPA**, I need your semester-wise SGPA and credit load.\n\n"
                "Example:\n- *Semester 1: SGPA 8.24, 20 credits*\n- *Semester 2: SGPA 8.55, 20 credits*\n\n"
                "Or use the **CGPA Calculator** tab directly!"
            ),
        }

    # --- Default greeting ---
    return {
        "intent": "greeting",
        "reply": (
            "Hello! I'm **GPA Assistant AI** 🎓 — your personal academic advisor for SPPU engineering.\n\n"
            "I can help you with:\n"
            "- 🧮 **SGPA Calculation** — just tell me your subjects, credits, and grades\n"
            "- 📈 **CGPA Tracking** — weighted cumulative across all semesters\n"
            "- 🎯 **Target GPA** — what SGPA do you need to hit 8.5 CGPA?\n"
            "- 🔮 **What-If Scenarios** — 'What if I score 9.2 next sem?'\n"
            "- ⚠️ **Backlog Impact** — how clearing a KT boosts your CGPA\n\n"
            "What would you like to know?"
        ),
    }


def _fmt_sgpa(r: Dict) -> str:
    subj_lines = "\n".join(
        f"  - {s['name']}: {s['credit']} cr × {s['grade_point']} GP = {s['weighted_points']:.1f} pts"
        for s in (r.get("subjects") or [])
    )
    backlog = "⚠️ **Backlog detected** (F grade present)" if r.get("has_backlog") else "✅ All courses passed"
    return (
        f"📊 **Calculated SGPA: {r['sgpa']:.2f} / 10.0**\n\n"
        f"**Breakdown:**\n{subj_lines}\n\n"
        f"- Total Credits: **{r['total_credits']:.1f}**\n"
        f"- Total Weighted Points: **{r['total_weighted_points']:.2f}**\n"
        f"- Formula: `{r['formula']}`\n"
        f"- {backlog}"
    )


def _fmt_target(r: Dict, cur: float, comp: float, rem: float) -> str:
    status_emojis = {
        "already_achieved": "🏆",
        "comfortably_achieved": "✅",
        "achievable_moderate": "📈",
        "achievable_good_effort": "💪",
        "achievable_high_effort": "🔥",
        "impossible": "❌",
    }
    emoji = status_emojis.get(r["status"], "🎯")
    scenarios = "\n".join(
        f"  - **{s['hypothetical_remaining_sgpa']:.1f} SGPA** → CGPA **{s['resulting_cgpa']:.2f}** "
        f"{'🎯 Meets target' if s['meets_target'] else '⬇ Below target'}"
        for s in r.get("scenarios", [])
        if s["hypothetical_remaining_sgpa"] in [7.5, 8.0, 8.5, 9.0, 9.5, 10.0]
    )
    return (
        f"{emoji} **Target CGPA Analysis: {r['target_cgpa']:.2f}**\n\n"
        f"{r['message']}\n\n"
        f"**Your Numbers:**\n"
        f"- Current CGPA: **{cur:.2f}** across **{comp:.0f}** credits\n"
        f"- Remaining Credits: **{rem:.0f}**\n"
        f"- Required Average SGPA: **{r['required_sgpa']:.2f} / 10.0**\n"
        f"- Max Possible CGPA (perfect 10.0 in all remaining): **{r['max_achievable_cgpa']:.2f}**\n\n"
        f"**Scenario Projections:**\n{scenarios}"
    )


# ── Main entry point ─────────────────────────────────────────────────────────
async def process_chat_message(
    message: str,
    conversation_id: Optional[str] = None,
    academic_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Orchestrates the AI response.
    Priority:
      1. Try OpenAI-compatible API with the configured key.
      2. Fall back to deterministic rule-based engine (always works).
    """
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    no_key = (
        not api_key
        or api_key == "your_openai_api_key_here"
        or api_key.startswith("sk-placeholder")
    )

    if not no_key:
        base_url, model = _detect_provider(api_key)

        if base_url and model:
            try:
                from openai import AsyncOpenAI

                client = AsyncOpenAI(api_key=api_key, base_url=base_url)

                messages: List[Dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
                if academic_context:
                    messages.append({
                        "role": "system",
                        "content": f"Student academic context: {json.dumps(academic_context)}",
                    })
                messages.append({"role": "user", "content": message})

                resp = await client.chat.completions.create(
                    model=model,
                    messages=messages,
                    tools=TOOLS_SPEC,
                    tool_choice="auto",
                    temperature=0.2,
                    max_tokens=1024,
                )

                assistant_msg = resp.choices[0].message
                calculations_done = []

                if assistant_msg.tool_calls:
                    messages.append(assistant_msg)
                    for tc in assistant_msg.tool_calls:
                        fn_name = tc.function.name
                        fn_args = json.loads(tc.function.arguments)
                        result = execute_tool(fn_name, fn_args)
                        calculations_done.append({"tool": fn_name, "result": result})
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": json.dumps(result),
                        })

                    resp2 = await client.chat.completions.create(
                        model=model,
                        messages=messages,
                        temperature=0.3,
                        max_tokens=1024,
                    )
                    final_reply = resp2.choices[0].message.content
                else:
                    final_reply = assistant_msg.content

                return {
                    "reply": final_reply,
                    "conversation_id": conversation_id or "ai_session",
                    "intent": "ai_conversational",
                    "calculations_performed": calculations_done or None,
                    "sources": [f"AI ({model}) grounded in Deterministic GPA Engine"],
                }

            except Exception as e:
                # Any error → graceful fallback
                fallback = _rule_based_reply(message, academic_context)
                fallback_reply = (
                    fallback["reply"]
                    + f"\n\n*(Note: AI API call failed — `{type(e).__name__}: {e}`. "
                    f"Served by built-in GPA Engine instead.)*"
                )
                return {
                    "reply": fallback_reply,
                    "conversation_id": conversation_id or "fallback_session",
                    "intent": "engine_fallback",
                    "calculations_performed": fallback.get("calculations_performed"),
                    "sources": ["Deterministic Python GPA Engine (API fallback)"],
                }

    # No key or unsupported key → pure deterministic engine
    fallback = _rule_based_reply(message, academic_context)
    return {
        "reply": fallback["reply"],
        "conversation_id": conversation_id or "local_session",
        "intent": fallback.get("intent", "deterministic"),
        "calculations_performed": fallback.get("calculations_performed"),
        "sources": ["Deterministic Python GPA Engine (SPPU CBCS)"],
    }
