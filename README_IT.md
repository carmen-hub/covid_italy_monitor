# COVID-19 Italy Monitor (Odoo 18)

Questo modulo permette di monitorare i dati COVID-19 in Italia a livello provinciale e regionale tramite integrazione diretta con i dati ufficiali della **Protezione Civile**.

## Caratteristiche principali:
- Sincronizzazione automatica/on-demand (Lazy Loading).
- Modello Odoo dedicato per l'archiviazione storica.
- API REST JSON per l'integrazione con sistemi esterni.

## Configurazione Permessi e Sicurezza
Dopo l'installazione, il modulo non sarà visibile se non vengono assegnati i permessi corretti.

1.  Attivare la **Modalità Sviluppatore**.
2.  Andare in **Impostazioni > Utenti e Aziende > Utenti**.
3.  Selezionare l'utente e, nella sezione **Extra Rights**, abilitare il gruppo:
    * **COVID Data User** (ID: `covid_italy_monitor.group_covid_user`)
4.  **Nota sui permessi (ACL):** Come definito nel file `ir.model.access.csv`, gli utenti hanno permessi di **Lettura** e **Cancellazione**, ma non possono creare o modificare i record manualmente (i dati devono arrivare solo dall'API ufficiale).

---

ARCHITETTURA DEL MODULO
--------------------------
covid_province/
├── models/
│    ├── covid_province.py            (Modello e logica di fetch dati)
│    └── __init__.py
├── controllers/
│   ├──  api.py                       (Endpoint REST API)
│   └──  __init__.py
├── views/
│    ├── covid_province_views.xml     (Interfaccia grafica)
│    └── menu.xml                     (Struttura menu)
├── security/
│   ├── security.xml                  (Definizione del Gruppo Utente)
│   └── ir.model.access.csv           (Access Control List)
├── static/description
│          └── icon.png 
├── __init__.py
└── __manifest__.py

DATI GESTITI (Modello: covid.province)
-----------------------------------------
I campi principali includono:
- Data (indicizzata per ricerche rapide)
- Regione (Nome e Codice)
- Provincia (Nome, Sigla e Codice)
- Coordinate (Latitudine/Longitudine)
- Totale casi (Intero)
- Note e codici NUTS (1, 2, 3)

---

## Logica di Sincronizzazione (Lazy Load)
Il modulo implementa un sistema di caricamento intelligente:
* Al primo avvio o alla richiesta di una data specifica tramite API/Interfaccia, il sistema controlla se i record esistono.
* Se i dati mancano, invoca `_fetch_remote_data` per scaricare i file JSON necessari dal repository della Protezione Civile.
* **Vincolo di integrità:** È presente un vincolo SQL unico su `(date, province_code)` per prevenire duplicati.

---

## REST API Endpoint
**URL:** `/api/v1/covid/stats`  
**Metodo:** `POST` (JSON-RPC)  
**Autenticazione:** Sessione utente (richiede il gruppo "COVID Data User").

---

Parametri accettati:
- `start_date` / `end_date`: Intervallo temporale (YYYY-MM-DD).
- `denominazione_provincia`: Filtro testuale per provincia.
- `order_by`: Ordinamento (total_cases, date, region_name, name).
- `group_by`: Se "region", aggrega i dati per regione.

---

GUIDA POSTMAN (Esempi Rapidi)
--------------------------------

#### 1. Autenticazione (Login)
**POST** `http://<your-server>/web/session/authenticate`
```json
{
    "params": {
        "db": "nome_database",
        "login": "tuo_username",
        "password": "tua_password"
    }
}

- Nota: Postman salverà automaticamente il cookie "session_id"

#### 2. Recupero Dati Filtrati 

**POST** http://<your-server>/api/v1/covid/stats

```json
{
    "params": {
        "start_date": "2020-03-01",
        "end_date": "2020-03-10",
        "denominazione_provincia": "Treviso",
        "order_by": "total_cases"
    }
}

#### 3. Aggregazione Regionale (Group by)

```json
{
    "params": {
        "start_date": "2021-01-01",
        "end_date": "2021-01-01",
        "group_by": "region"
    }
}

REQUISITI
------------
- Odoo 18.0
- Permessi "COVID Data User" assegnati all'utente che effettua la chiamata.
- Libreria Python requests