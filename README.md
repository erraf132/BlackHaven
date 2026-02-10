# BlackHaven Framework v3.0 OMEGA

**BlackHaven** is an advanced OSINT and security auditing framework designed for authorized cybersecurity research, education, and defensive security analysis.

Developed by **erraf132 and Vyrn.exe Official**

---

## Overview

BlackHaven provides a modular and secure environment for:

* OSINT investigations
* Username intelligence gathering
* Email analysis
* Network and domain reconnaissance
* System and security auditing
* Controlled and authorized security testing

BlackHaven uses a secure authentication system with a globally unique owner account and controlled access levels.

---

## Features

* Secure authentication system
* Global unique Owner account
* Modular architecture
* Automatic results logging to file
* Professional terminal interface
* Secure password hashing (Argon2 / bcrypt)
* OSINT and reconnaissance modules
* Fully local execution (no forced external servers)
* Expandable module system

---

## Installation

### Recommended method (Linux / Kali Linux)

Clone the repository:

```
git clone https://github.com/erraf132/BlackHaven.git
cd BlackHaven
```

Create virtual environment:

```
python3 -m venv venv
```

Activate virtual environment:

```
source venv/bin/activate
```

Install BlackHaven:

```
pip install -e .
```

Run BlackHaven:

```
blackhaven
```

---

## First launch

On first launch, BlackHaven will:

* Show the legal disclaimer
* Ask to create the global results file
* Require creation of the Owner account (first install only)
* Secure all future access

---

## Project Structure

```
blackhaven/
│
├── auth_pkg/          Authentication system
├── core/              Core engines
├── modules/           OSINT and security modules
├── security/          Security configuration
├── ui/                Interface and banner
├── utils/             Utilities and results logging
├── data/              Logs and activity files
│
├── main.py            Main entry point
└── __main__.py        CLI launcher
```

---

## Security Model

BlackHaven uses a secure access model:

* Owner (global root access)
* Admin (optional)
* User (standard access)

Only one Owner exists globally.

Owner privileges include:

* Full system access
* Access to all result files
* System configuration control

---

## Results Logging

All results are automatically saved to the configured results file.

This ensures:

* Audit trail
* Traceability
* Persistent intelligence storage

---

## Updating

To update BlackHaven:

```
git pull
source venv/bin/activate
pip install -e .
```

---

## Legal Disclaimer

BlackHaven is intended for:

* Educational purposes
* Authorized cybersecurity research
* Defensive security testing

Unauthorized use against systems without explicit permission is strictly prohibited.

The authors assume no responsibility for misuse.

You are responsible for complying with applicable laws.

---

## Author

Developed by:

**erraf132**
**Vyrn.exe Official**

BlackHaven Framework © 2026

---

## License

All rights reserved.

This software may not be redistributed, modified, or used without permission from the authors.
