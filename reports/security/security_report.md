# Security Audit & Scan Report

*Timestamp:* 2026-06-27T12:10:36.599Z
*Auditing Engines:* npm audit (JS), Bandit (Python), Regex Secret Scanner

## Security Scorecard
* **Exposed Credentials / Keys:** 1 instances
* **Backend Static Security Vulnerabilities (Bandit):** Not Executed (bandit)
* **Frontend Dependency Vulnerabilities (npm audit):** 28

## Bandit Security Audit Detail
*Bandit security sweep was not executed. Install bandit via pip.*

## Secrets & Credentials Scan
| File path | Line | Exposed Token Snippet |
|-----------|------|------------------------|
| scripts\profile_backend.py | 54 | `password="SecurePassword123"...` |
