# COVID Italy Monitor (Odoo 18)

This module allows monitoring of COVID-19 data in Italy at the provincial and regional levels through direct integration with official data from the **Protezione Civile** (Civil Protection).

## Main Features

* Automatic / on-demand synchronization (Lazy Loading)
* Dedicated Odoo model for historical archiving
* JSON REST API for integration with external systems

## Permissions and Security Configuration

After installation, the module will not be visible unless the correct permissions are assigned.

1. Enable **Developer Mode**
2. Go to **Settings > Users & Companies > Users**
3. Select the user and, in the **Extra Rights** section, enable the group:

   * **COVID Data User** (`covid_italy_monitor.group_covid_user`)
4. **ACL Note:** As defined in `ir.model.access.csv`, users have **Read** and **Unlink** permissions only. Records cannot be created or modified manually; data is sourced exclusively from the official API.

---

## Module Architecture

```text
covid_province/
├── models/
│   ├── covid_province.py        # Model and data fetch logic
│   └── __init__.py
├── controllers/
│   ├── api.py                   # REST API endpoints
│   └── __init__.py
├── views/
│   ├── covid_province_views.xml # UI views
│   └── menu.xml                 # Menu structure
├── security/
│   ├── security.xml             # User group definition
│   └── ir.model.access.csv      # Access Control List
├── static/description/
│   └── icon.png
├── __init__.py
└── __manifest__.py
```

---

## Managed Data (Model: `covid.province`)

Key fields include:

* **Date** (indexed)
* **Region** (name and code)
* **Province** (name, abbreviation, code)
* **Coordinates** (latitude / longitude)
* **Total cases** (integer)
* **NUTS codes** (levels 1, 2, 3)

---

## Synchronization Logic (Lazy Load)

* **On-demand fetch:** When a date is requested via UI or API, the system checks for existing records.
* **Remote integration:** Missing data triggers `_fetch_remote_data`, downloading JSON files from the official Protezione Civile repository.
* **Integrity constraint:** Unique SQL constraint on `(date, province_code)` prevents duplicates.

---

## REST API

* **Endpoint:** `/api/v1/covid/stats`
* **Method:** `POST` (JSON-RPC)
* **Authentication:** User session (requires **COVID Data User** group)

### Accepted Parameters

| Parameter                 | Description                                  |
| ------------------------- | -------------------------------------------- |
| `start_date`, `end_date`  | Date range (`YYYY-MM-DD`)                    |
| `denominazione_provincia` | Province name filter                         |
| `order_by`                | `total_cases`, `date`, `region_name`, `name` |
| `group_by`                | If `region`, aggregates by region            |

---

## Postman Quick Guide

### 1. Authentication

**POST** `/web/session/authenticate`

```json
{
  "params": {
    "db": "your_database",
    "login": "username",
    "password": "password"
  }
}
```

> Postman automatically stores the `session_id` cookie.

### 2. Retrieve Filtered Data

```json
{
  "params": {
    "start_date": "2020-03-01",
    "end_date": "2020-03-10",
    "denominazione_provincia": "Treviso",
    "order_by": "total_cases"
  }
}
```

### 3. Regional Aggregation

```json
{
  "params": {
    "start_date": "2021-01-01",
    "end_date": "2021-01-01",
    "group_by": "region"
  }
}
```

---

## Requirements

* **Odoo:** 18.0
* **Permissions:** COVID Data User group
* **Python libraries:** `requests`, `logging`
