def build_fp_prompt(finding) -> tuple:
    system = """You are an expert security engineer specialising in Static Application Security Testing (SAST).
Your task is to determine whether a SAST finding is a TRUE vulnerability or a FALSE POSITIVE.

Respond ONLY in this exact format:
VERDICT: TRUE_POSITIVE or FALSE_POSITIVE
CONFIDENCE: HIGH or MEDIUM or LOW
REASON: One to three sentences explaining your verdict."""

    user = f"""Analyse this SAST finding:

Rule ID: {finding.rule_id}
CWE: {finding.cwe_id}
Title: {finding.title}
Severity: {finding.severity}
File: {finding.file_path}
Line: {finding.line_number}

Code:
{finding.code_snippet}

Is this a true vulnerability or a false positive?"""

    return system, user


def build_severity_prompt(finding) -> tuple:
    system = """You are an expert security engineer specialising in vulnerability severity assessment.
Your task is to classify the severity of a confirmed vulnerability using CVSS guidelines.

Respond ONLY in this exact format:
SEVERITY: CRITICAL or HIGH or MEDIUM or LOW
REASON: One to three sentences explaining the classification."""

    user = f"""Classify the severity of this confirmed vulnerability:

CWE: {finding.cwe_id}
Title: {finding.title}
File: {finding.file_path}
Line: {finding.line_number}

Code:
{finding.code_snippet}

What is the correct severity level?"""

    return system, user
