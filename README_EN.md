# COVID-19 Italy Monitor (Odoo 18)

This module allows monitoring of COVID-19 data in Italy at the provincial and regional levels through direct integration with official data from the **Protezione Civile** (Civil Protection).

## Main Features:
- Automatic/On-demand synchronization (Lazy Loading).
- Dedicated Odoo model for historical archiving.
- JSON REST API for integration with external systems.

## Permissions and Security Configuration
After installation, the module will not be visible unless the correct permissions are assigned.

1.  Enable **Developer Mode**.
2.  Go to **Settings > Users & Companies > Users**.
3.  Select the user and, in the **Extra Rights** section, enable the group:
    * **COVID Data User** (ID: `covid_italy_monitor.group_covid_user`)
4.  **Note on Permissions (ACL):** As defined in the `ir.model.access.csv` file, users have **Read** and **Unlink** permissions, but they cannot create or modify records manually (data must only come from the official API).

---

## MODULE ARCHITECTURE
```text
covid_province/
├── models/
│    ├── covid_province.py            (Model and data fetch logic)
│    └── __init__.py
├── controllers/
│   ├──  api.py                       (REST API endpoints)
│   └──  __init__.py
├── views/
│    ├── covid_province_views.xml     (Graphical interface)
│    └── menu.xml                     (Menu structure)
├── security/
│   ├── security.xml                  (User Group definition)
│   └── ir.model.access.csv           (Access Control List)
├── static/description
│          └── icon.png 
├── __init__.py
└── __manifest__.py

## MANAGED DATA (Model: `covid.province`)
Key fields include:
* **Date** (indexed for fast searches)
* **Region** (Name and Code)
* **Province** (Name, Abbreviation, and Code)
* **Coordinates** (Latitude/Longitude)
* **Total Cases** (Integer)
* **Notes and NUTS codes** (1, 2, 3)

---

## Synchronization Logic (Lazy Load)
The module implements a smart loading system:
* **On-demand Fetch:** Upon the first launch or when a specific date is requested via API/Interface, the system checks if the records exist in the local database.
* **Remote Integration:** If data is missing, it invokes `_fetch_remote_data` to download the necessary JSON files from the official *Protezione Civile* repository.
* **Integrity Constraint:** There is a unique SQL constraint on `(date, province_code)` to prevent duplicates and ensure data consistency.

---

## REST API Endpoint
* **URL:** `/api/v1/covid/stats`
* **Method:** `POST` (JSON-RPC)
* **Authentication:** User session (requires "**COVID Data User**" group).

### Accepted Parameters:
| Parameter | Description |
| :--- | :--- |
| `start_date` / `end_date` | Time range in `YYYY-MM-DD` format. |
| `denominazione_provincia` | Text filter for a specific province name. |
| `order_by` | Sorting criteria (`total_cases`, `date`, `region_name`, `name`). |
| `group_by` | If set to `"region"`, aggregates the data by region. |

---

## POSTMAN GUIDE (Quick Examples)

### 1. Authentication (Login)
**POST** `http://<your-server>/web/session/authenticate`

**Body (JSON):**
```json
{
    "params": {
        "db": "your_database_name",
        "login": "your_username",
        "password": "your_password"
    }
}

---

*Note: Postman will automatically save the `session_id` cookie for subsequent calls after a successful authentication.*

### 2. Retrieve Filtered Data
**URL:** `http://<your-server>/api/v1/covid/stats`  
**Method:** `POST`

**Body (JSON):**
```json
{
    "params": {
        "start_date": "2020-03-01",
        "end_date": "2020-03-10",
        "denominazione_provincia": "Treviso",
        "order_by": "total_cases"
    }
}

---

### 3. Regional Aggregation (Group by)
**URL:** `http://<your-server>/api/v1/covid/stats`  
**Method:** `POST`

**Body (JSON):**
```json
{
    "params": {
        "start_date": "2021-01-01",
        "end_date": "2021-01-01",
        "group_by": "region"
    }
}

---

## REQUIREMENTS
* **Odoo Version:** 18.0
* **Permissions:** The "**COVID Data User**" group must be assigned to the user making the API call (as defined in `security.xml`).
* **Python Libraries:** * `requests`: Required for the remote data fetcher to communicate with the GitHub repository.
    * `logging`: Used for system traceability.
* **Internet Access:** The server requires an active internet connection to perform the initial data fetch from `raw.githubusercontent.com`.