# COVID Italy Monitor (Odoo 18)

Questo modulo consente di monitorare i dati COVID-19 in Italia a livello provinciale e regionale tramite integrazione diretta con i dati ufficiali della **Protezione Civile**.

## Caratteristiche principali

* Sincronizzazione automatica / on-demand (Lazy Loading)
* Modello Odoo dedicato all’archiviazione storica
* API REST JSON per integrazione con sistemi esterni

## Configurazione Permessi e Sicurezza

Dopo l’installazione, il modulo non sarà visibile senza i permessi corretti.

1. Attivare la **Modalità sviluppatore**
2. Andare in **Impostazioni > Utenti e Aziende > Utenti**
3. Selezionare l’utente e abilitare il gruppo:

   * **COVID Data User** (`covid_italy_monitor.group_covid_user`)
4. **Nota ACL:** come definito in `ir.model.access.csv`, gli utenti hanno solo permessi di **lettura** e **cancellazione**. I dati provengono esclusivamente dall’API ufficiale.

---

## Architettura del Modulo

```text
covid_province/
├── models/
│   ├── covid_province.py        # Modello e logica di fetch
│   └── __init__.py
├── controllers/
│   ├── api.py                   # Endpoint REST API
│   └── __init__.py
├── views/
│   ├── covid_province_views.xml # Interfaccia grafica
│   └── menu.xml                 # Menu
├── security/
│   ├── security.xml             # Gruppi utenti
│   └── ir.model.access.csv      # ACL
├── static/description/
│   └── icon.png
├── __init__.py
└── __manifest__.py
```

---

## Dati Gestiti (Modello: `covid.province`)

* **Data** (indicizzata)
* **Regione** (nome e codice)
* **Provincia** (nome, sigla, codice)
* **Coordinate** (latitudine / longitudine)
* **Totale casi**
* **Codici NUTS** (1, 2, 3)

---

## Logica di Sincronizzazione (Lazy Load)

* Recupero dati on-demand alla richiesta via UI o API
* Download automatico dei JSON ufficiali se i dati non sono presenti
* Vincolo SQL unico su `(date, province_code)` per evitare duplicati

---

## REST API

* **Endpoint:** `/api/v1/covid/stats`
* **Metodo:** `POST` (JSON-RPC)
* **Autenticazione:** sessione utente (gruppo **COVID Data User**)

### Parametri accettati

| Parametro                 | Descrizione                                  |
| ------------------------- | -------------------------------------------- |
| `start_date`, `end_date`  | Intervallo date (`YYYY-MM-DD`)               |
| `denominazione_provincia` | Filtro per provincia                         |
| `order_by`                | `total_cases`, `date`, `region_name`, `name` |
| `group_by`                | `region` per aggregazione regionale          |

---

## Guida Rapida Postman

### 1. Autenticazione

```json
{
  "params": {
    "db": "nome_database",
    "login": "username",
    "password": "password"
  }
}
```

### 2. Recupero dati filtrati

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

### 3. Aggregazione regionale

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

## Requisiti

* **Odoo:** 18.0
* **Permessi:** gruppo COVID Data User
* **Librerie Python:** `requests`
