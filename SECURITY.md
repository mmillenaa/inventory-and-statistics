# Security Policy

## Context
This application is designed to run locally via Python and Streamlit. There is no central backend server managed by the maintainers, and no user data is collected or transmitted externally by default. The primary security risks involve vulnerabilities within the Python dependencies (e.g., Pandas, Streamlit, Plotly) running on the user's local machine.

## Supported Versions
Only the latest release on the `main` branch receives security updates and bug fixes. Users are strongly encouraged to keep their local virtual environments updated.

## Reporting a Vulnerability
Please do not open a public issue for security vulnerabilities. Instead, report them privately using one of the following methods:

1. **GitHub Private Reporting:** Go to the Security tab → Report a vulnerability.
2. **Email:** Send a message directly to millena@usp.br.

Please include the context of the vulnerability, the steps to reproduce it, and the potential impact. You will receive an acknowledgment within ten working days.

## Third-Party Libraries
We strive to keep third-party Python packages up to date. If you identify a vulnerability originating from an external library used in this project, please report it following the steps above so we can update the requirements.
