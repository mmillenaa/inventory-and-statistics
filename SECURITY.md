# Security Policy

## Context
The applications in this repository are static pages: there is no backend server, no login mechanism, and no user data collection. The realistic security risks are confined to the browser environment — for example, script injection through crafted data or a compromised third-party library.

## Supported Versions
Only the latest release on the `main` branch receives security updates and bug fixes.

## Reporting a Vulnerability
Please do not open a public issue for security vulnerabilities. Instead, report them privately using one of the following methods:

1. **GitHub Private Reporting:** Go to the Security tab → Report a vulnerability.
2. **Email:** Send a message directly to millena@usp.br.

Please include the affected page, the steps to reproduce the issue, and the expected impact. You will receive an acknowledgment within ten working days.

## Third-Party Libraries
We strive to keep third-party dependencies up to date and load them securely. If you identify a vulnerability originating from an external library used in this project, please report it following the steps above so we can patch or replace the dependency.
