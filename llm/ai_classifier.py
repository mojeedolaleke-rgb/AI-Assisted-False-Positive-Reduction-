import os
import re
import time
import config
from llm.prompt_builder import build_fp_prompt, build_severity_prompt

BATCH_SIZE  = 25
MAX_RETRIES = 3
TIMEOUT     = 90

_BAD_CACHE = ("timed out", "failed", "error", "connection", "rate limit")


def _is_bad_cache(text: str) -> bool:
    if not text:
        return True
    return any(p in text.lower() for p in _BAD_CACHE)


def _call_openai(system_prompt: str, user_prompt: str, max_tokens=400) -> str:
    import openai
    key = config.OPENAI_API_KEY
    if not key:
        raise ValueError("OpenAI API key not set. Go to Settings and paste your API key.")
    client = openai.OpenAI(api_key=key, timeout=TIMEOUT)
    last_err = None
    for attempt in range(MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": user_prompt},
                ],
                temperature=0,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content.strip()
        except openai.APITimeoutError:
            last_err = "Request timed out"
            if attempt < MAX_RETRIES - 1:
                time.sleep(2)
        except openai.RateLimitError:
            last_err = "Rate limit — retrying"
            time.sleep(5)
        except openai.APIConnectionError as e:
            last_err = f"Connection error: {e}"
            if attempt < MAX_RETRIES - 1:
                time.sleep(3)
        except Exception as e:
            last_err = str(e)
            break
    raise RuntimeError(last_err or "API call failed after retries")


def classify_false_positive(finding) -> dict:
    try:
        from database.db_manager import DBManager
        cached = DBManager().get_validation(finding.finding_id)
        if cached:
            reason = cached.get("fp_reason", "")
            if not _is_bad_cache(reason):
                return {
                    "is_false_positive": bool(cached.get("is_false_positive", 0)),
                    "confidence": "HIGH",
                    "reason": reason or "Loaded from cache.",
                }
            try:
                conn = DBManager().get_connection()
                conn.execute(
                    "DELETE FROM validations WHERE finding_id=?",
                    (finding.finding_id,)
                )
                conn.commit()
            except Exception:
                pass
    except Exception:
        pass

    system, user = build_fp_prompt(finding)
    try:
        raw = _call_openai(system, user)
        is_fp = "FALSE_POSITIVE" in raw
        conf_match = re.search(r"CONFIDENCE:\s*(HIGH|MEDIUM|LOW)", raw)
        reason_match = re.search(r"REASON:\s*(.+)", raw, re.DOTALL)
        return {
            "is_false_positive": is_fp,
            "confidence": conf_match.group(1) if conf_match else "MEDIUM",
            "reason": reason_match.group(1).strip() if reason_match else raw,
        }
    except Exception as e:
        return {"is_false_positive": False, "confidence": "LOW",
                "reason": f"AI analysis failed: {e}"}


def classify_severity(finding) -> dict:
    try:
        from database.db_manager import DBManager
        cached = DBManager().get_validation(finding.finding_id)
        if cached and cached.get("ai_severity"):
            reason = cached.get("sev_reason", "")
            if not _is_bad_cache(reason):
                return {"severity": cached["ai_severity"],
                        "reason": reason or "Loaded from cache."}
    except Exception:
        pass

    system, user = build_severity_prompt(finding)
    try:
        raw = _call_openai(system, user)
        sev_match    = re.search(r"SEVERITY:\s*(CRITICAL|HIGH|MEDIUM|LOW)", raw)
        reason_match = re.search(r"REASON:\s*(.+)", raw, re.DOTALL)
        return {
            "severity": sev_match.group(1) if sev_match else finding.severity,
            "reason": reason_match.group(1).strip() if reason_match else raw,
        }
    except Exception as e:
        return {"severity": finding.severity, "reason": f"AI analysis failed: {e}"}


def _build_batch_prompt(findings: list) -> str:
    lines = [
        "You are an expert security engineer specialising in SAST analysis.\n"
        "Analyse each finding below. For EACH finding respond in EXACTLY this format:\n\n"
        "FINDING_ID: {finding_id}\n"
        "VERDICT: TRUE_POSITIVE or FALSE_POSITIVE\n"
        "CONFIDENCE: HIGH or MEDIUM or LOW\n"
        "FP_REASON: One to three sentences explaining the verdict.\n"
        "SEVERITY: CRITICAL or HIGH or MEDIUM or LOW\n"
        "SEV_REASON: One to two sentences explaining the severity.\n"
        "---END_FINDING---\n\n"
        "Note: Only provide SEVERITY and SEV_REASON for TRUE_POSITIVE findings.\n"
        "For FALSE_POSITIVE findings set SEVERITY: N/A and SEV_REASON: N/A\n\n"
        "=" * 60 + "\n"
    ]
    for f in findings:
        snippet = f.code_snippet or f"[Line {f.line_number} in {f.file_path}]"
        snippet_lines = snippet.split("\n")
        if len(snippet_lines) > 12:
            snippet = "\n".join(snippet_lines[:12]) + "\n... (truncated)"
        lines.append(
            f"FINDING_ID: {f.finding_id}\n"
            f"Rule: {f.rule_id}\n"
            f"CWE: {f.cwe_id}\n"
            f"Title: {f.title}\n"
            f"Severity: {f.severity}\n"
            f"File: {f.file_path}, line {f.line_number}\n\n"
            f"Code:\n{snippet}\n\n"
            f"{'=' * 60}\n"
        )
    return "\n".join(lines)


def _parse_batch_response(raw: str, findings: list) -> dict:
    results = {}
    blocks = re.split(r"---END_FINDING---", raw)

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        id_match = re.search(r"FINDING_ID:\s*([a-f0-9\-]{36})", block)
        if not id_match:
            continue
        finding_id = id_match.group(1).strip()

        verdict_match = re.search(r"VERDICT:\s*(TRUE_POSITIVE|FALSE_POSITIVE)", block)
        conf_match    = re.search(r"CONFIDENCE:\s*(HIGH|MEDIUM|LOW)", block)
        fp_r_match    = re.search(r"FP_REASON:\s*(.+?)(?=SEVERITY:|SEV_REASON:|$)", block, re.DOTALL)
        sev_match     = re.search(r"SEVERITY:\s*(CRITICAL|HIGH|MEDIUM|LOW|N/A)", block)
        sev_r_match   = re.search(r"SEV_REASON:\s*(.+?)(?=$)", block, re.DOTALL)

        is_fp      = (verdict_match.group(1) == "FALSE_POSITIVE") if verdict_match else False
        confidence = conf_match.group(1) if conf_match else "MEDIUM"
        fp_reason  = fp_r_match.group(1).strip() if fp_r_match else ""
        severity   = sev_match.group(1) if sev_match else "MEDIUM"
        sev_reason = sev_r_match.group(1).strip() if sev_r_match else ""

        if severity == "N/A":
            severity = "MEDIUM"

        fp_result  = {"is_false_positive": is_fp, "confidence": confidence, "reason": fp_reason}
        sev_result = {"severity": severity, "reason": sev_reason}
        results[finding_id] = (fp_result, sev_result)

    return results


def validate_findings_batch(findings: list, progress_callback=None) -> list:
    from database.db_manager import DBManager
    db = DBManager()

    needs_api = []

    for f in findings:
        cached = db.get_validation(f.finding_id)
        if cached:
            fp_reason = cached.get("fp_reason", "")
            if not _is_bad_cache(fp_reason):
                f.is_false_positive  = bool(cached.get("is_false_positive", 0))
                f.fp_reason          = fp_reason
                f.ai_severity        = cached.get("ai_severity", f.severity)
                f.ai_severity_reason = cached.get("sev_reason", "")
                f.validated          = True
                continue
        needs_api.append(f)

    if not needs_api:
        if progress_callback:
            progress_callback("All findings loaded from cache.", len(findings), len(findings))
        return findings

    batches = [needs_api[i:i + BATCH_SIZE] for i in range(0, len(needs_api), BATCH_SIZE)]
    processed = len(findings) - len(needs_api)

    for batch_num, batch in enumerate(batches, 1):
        if progress_callback:
            progress_callback(
                f"AI validation — batch {batch_num}/{len(batches)} ({len(batch)} findings)...",
                processed, len(findings)
            )

        prompt = _build_batch_prompt(batch)
        batch_results = {}

        for attempt in range(MAX_RETRIES):
            try:
                raw = _call_openai(
                    "You are an expert SAST security engineer. Follow the exact format.",
                    prompt,
                    max_tokens=min(4000, 160 * len(batch))
                )
                batch_results = _parse_batch_response(raw, batch)
                break
            except Exception as e:
                if "rate" in str(e).lower():
                    time.sleep(2 ** (attempt + 1))
                elif attempt < MAX_RETRIES - 1:
                    time.sleep(3)

        for f in batch:
            if f.finding_id in batch_results:
                fp_result, sev_result = batch_results[f.finding_id]
                f.is_false_positive  = fp_result["is_false_positive"]
                f.fp_reason          = fp_result["reason"]
                f.validated          = True
                if not f.is_false_positive:
                    f.ai_severity        = sev_result["severity"]
                    f.ai_severity_reason = sev_result["reason"]
                else:
                    f.ai_severity        = f.severity
                    f.ai_severity_reason = ""
            else:
                fp  = classify_false_positive(f)
                sev = classify_severity(f) if not fp["is_false_positive"] else {"severity": f.severity, "reason": ""}
                f.is_false_positive  = fp["is_false_positive"]
                f.fp_reason          = fp["reason"]
                f.ai_severity        = sev["severity"]
                f.ai_severity_reason = sev["reason"]
                f.validated          = True

            # Save to DB
            db.save_validation(
                f.finding_id,
                f.is_false_positive,
                getattr(f, "fp_reason", ""),
                getattr(f, "ai_severity", f.severity),
                getattr(f, "ai_severity_reason", ""),
                f.severity,
                "gpt-4o-mini"
            )

        processed += len(batch)

        if batch_num < len(batches):
            time.sleep(1)

    if progress_callback:
        progress_callback(
            f"Validation complete — {len(findings)} findings processed.",
            len(findings), len(findings)
        )

    return findings