# DealerOS

DealerOS compares two event exports and displays disagreements for one selected organization. The screen supports reason filtering and numeric sorting. The database retains the original CSV cells alongside fields used for reconciliation.

## Run from a clean clone

Use Python 3.11 or newer, Node.js 22 or newer with npm, and Git. Run these commands from the repository root. Create a virtual environment first.

```sh
python -m venv .venv
```

Activate it on Windows PowerShell with `.\.venv\Scripts\Activate.ps1`, on Windows Command Prompt with `.venv\Scripts\activate.bat`, or on macOS/Linux with `source .venv/bin/activate`. Then run:

```sh
python -m pip install -r requirements.txt
python import_data.py
python audit_data.py
python -m pytest -q
npm ci --prefix web
npm run build --prefix web
python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

Open **http://127.0.0.1:8000**. The import command creates the SQLite schema and loads the three bundled CSVs. Run it again to replace the database contents with the current exports. No separate migration or frontend server is required. For frontend development, leave the API running and start `npm run dev --prefix web` in a second terminal. Open the URL Vite prints.

## What to check

- The audit verifies all original cells across 5 locations, 120 A records and 121 B entries.
- With the supplied files and the policies in DECISIONS.md, ORG-A shows **7** findings and ORG-B shows **4**.
- In ORG-A, choose **Duplicate in B**. REC-1042 shows A as 112,837.06 and the combined B value as 225,674.12. REC-1055 is a valid split.
- Click **System A value** to reverse the order. Sorting uses A’s total when available and B’s amount for an orphan. Difference means B minus A. Unknown or withheld values are empty.
- In ORG-B, choose **Duplicate in B** to exercise the empty state.
- The API route is `GET /api/disagreements/?org=ORG-A&reason=VALUE_MISMATCH&sort=-value`. Reason is optional. Sort accepts `value` and `-value`.

## Code map and scope

| File | Responsibility |
| --- | --- |
| storage.py | SQLite schema, CSV reading, reference normalization and money parsing |
| import_data.py | Load a complete snapshot and save findings in one transaction |
| compare.py | Pure comparison rules and cross-organization redaction |
| audit_data.py | Compare every stored raw row with the original file |
| app.py | Query findings by organization, filter and sort, serve the built screen |
| web/src.jsx | Organization selector, reason filter and results table |
| tests/ | Rule tests and API/import checks against temporary databases |

FastAPI, SQLite and React keep the comparison in Python and the screen small. Authentication, pagination, deployment, editing and automated corrections are outside this assessment. The org selector is a local demonstration of scoped responses. A production deployment would need a trusted user identity and server-side authorization for organization selection. Keep the supplied exports in a private repository.

## How I worked with the agent

ChatGPT (Codex) generated the implementation, tests and documentation in response to a request to build the assessment from the supplied brief and CSVs. The candidate supplied the original materials. The code was checked by importing twice, comparing stored raw rows with the CSVs, exercising the real API and testing the screen. The repository attributes the generated code to Codex.

## Three assessment reflections

**One thing the agent got wrong and how it was found.** The initial frontend setup had a Vite development command and relative API URLs, but no proxy. Checking the development configuration showed that the UI would request data from the Vite server. A later commit forwards those requests to FastAPI. The production build uses a single origin.

[Download DealerOS source code (.zip)](https://github.com/K-REVANTH-KUMAR/dealeros/archive/refs/heads/main.zip)

**Least certain part.** The interpretation of VOIDED is the least certain business rule. System B has no status column. The current implementation compares the amounts normally. An example of an expected reversal from the data owner would clarify the intended behavior.

**First improvement with a second day.** Add a persistent import-issues report by source row and column. The raw cells are already preserved, but an operator investigating an invalid value currently has to consult the import output and source record.
