import requests
import logging
from odoo import models, fields, api
from datetime import date, timedelta

_logger = logging.getLogger(__name__)

class CovidProvince(models.Model):
    _name = 'covid.province'
    _description = 'COVID Data by Province'
    _order = 'date desc, name asc' 
    
    date = fields.Date(string="Date", required=True, index=True)
    state = fields.Char(string="State")
    region_code = fields.Char(string="Region Code")
    region_name = fields.Char(string="Region", required=True, index=True)
    province_code = fields.Char(string="Province Code", required=True)
    name = fields.Char(string="Province", required=True, index=True)
    acronym_province = fields.Char(string="Acronym Province")
    lat = fields.Float(string='Latitude', digits=(12, 10))
    long = fields.Float(string='Longitude', digits=(12, 10))
    total_cases = fields.Integer(string="Total Cases", required=True)
    note = fields.Text(string="Note")
    nuts_code_1 = fields.Char(string="Nuts Code 1")
    nuts_code_2 = fields.Char(string="Nuts Code 2")
    nuts_code_3 = fields.Char(string="Nuts Code 3")

    # Ensure data integrity: No duplicate entries for the same province on the same day
    _sql_constraints = [
        ('unique_province_date', 
         'unique(date, province_code)', 
         'Data for this province and date already exists!')
    ]

    
    @api.model
    def search_fetch(self, domain, field_names=None, offset=0, limit=None, order=None):
        """
        Override search_fetch to implement 'Lazy Loading'.
        If data for the requested date is missing in the DB, it triggers a remote fetch.
        """
        # Context check to prevent infinite recursion during internal searches
        if self.env.context.get('skip_covid_fetch'):
            return super().search_fetch(domain, field_names, offset, limit, order)

        today = date.today()
        target_date = False

        # Attempt to extract a specific 'date' filter from the search domain
        for leaf in domain:
            if isinstance(leaf, (list, tuple)) and leaf[0] == 'date' and leaf[1] == '=':
                target_date = fields.Date.to_date(leaf[2])
                break

        # Prepare a sudo environment with the skip flag to perform check/fetch
        self_skip = self.with_context(skip_covid_fetch=True).sudo()

        try:
            if target_date:
                # If searching for a specific date and it's missing, fetch it
                if not self_skip.search_count([('date', '=', target_date)]):
                    self_skip._fetch_remote_data(target_date=target_date)
            else:
                # If no specific date in domain, ensure today's data (or latest available) is present
                if not self_skip.search_count([('date', '=', today)]):
                    success = self_skip._fetch_remote_data(target_date=today)
                    # Fallback strategy: if today's fetch fails and DB is empty, get whatever is latest
                    if not success and not self_skip.search_count([]):
                        _logger.info("Fallback: Fetching latest available.")
                        self_skip._fetch_remote_data()
        except Exception as e:
            _logger.error("Sync failed: %s", str(e))

        return super().search_fetch(domain, field_names, offset, limit, order)

    @api.model
    def _fetch_remote_data(self, target_date=None, start_date=None, end_date=None):
        """
        Connects to the official PCM-DPC GitHub repository to download JSON data.
        Handles both daily 'latest' files and the full historical archive.
        """
        base_url = "https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-json/"
        # Decide which endpoint to use: the complete history or just the latest file
        is_history = (target_date and target_date != date.today()) or start_date
        url = f"{base_url}dpc-covid19-ita-province.json" if is_history else f"{base_url}dpc-covid19-ita-province-latest.json"

        try:
            response = requests.get(url, timeout=30)
            if response.status_code != 200:
                _logger.warning("Failed to fetch data from %s", url)
                return False

            json_data = response.json()

            # --- Data Filtering ---
            # If a specific date is requested, filter the JSON response
            if target_date:
                json_data = [
                    item for item in json_data
                    if fields.Date.to_date(item['data'][:10]) == target_date
                ]
            
            # If a range is requested, filter accordingly
            if start_date and end_date:
                json_data = [
                    item for item in json_data
                    if fields.Date.to_date(item['data'][:10]) >= start_date and fields.Date.to_date(item['data'][:10]) <= end_date
                ]

            if not json_data:
                return False

            # --- Database Persistence ---
            with self.env.cr.savepoint():
                # Get existing records to prevent duplicates (Security: Data Integrity)
                search_domain = [('date', '=', fields.Date.to_date(json_data[0]['data'][:10]))]
                if start_date and end_date:
                    search_domain = [('date', '>=', start_date), ('date', '<=', end_date)]
                
                existing_keys = set(self.with_context(skip_covid_fetch=True).sudo().search(search_domain).mapped(
                    lambda r: f"{r.date}_{r.province_code}"
                ))
                
                # Mapping JSON fields to Odoo Model fields
                records_to_create = []
                for item in json_data:
                    # 1. SECURITY: Input Sanitization & Type Casting
                    # We cast to avoid injection or malformed strings from the source
                    try:
                        p_code = str(item.get('codice_provincia', ''))
                        raw_date = fields.Date.to_date(item.get('data', '')[:10])
                        sigla = item.get('sigla_provincia')
                        prov_name = item.get('denominazione_provincia', '')
                        
                        # Use max(0, ...) to mitigate invalid negative numbers
                        cases = max(0, int(item.get('totali_casi') or item.get('totale_casi', 0)))
                        
                        # Handle Lat/Long with float conversion and range check
                        lat = float(item.get('lat')) if item.get('lat') else 0.0
                        lng = float(item.get('long')) if item.get('long') else 0.0
                    except (ValueError, TypeError):
                        _logger.warning("Security: Skipping malformed record for province %s", item.get('denominazione_provincia'))
                        continue

                    # 2. VALIDATION: Catching Invalid/Placeholder Entries
                    # We skip 'In fase di definizione', 'Fuori Regione' or missing sigla
                    if not sigla or sigla.strip() in ['', 'FT', 'null'] or p_code == '999':
                        continue
                    
                    # 3. SECURITY: Prevent Future Dates
                    if raw_date > date.today():
                        continue

                    # Deduplication check
                    if f"{raw_date}_{p_code}" not in existing_keys:
                        records_to_create.append({
                            'date': raw_date,
                            'state': item.get('stato'),
                            'region_code': item.get('codice_regione'),
                            'region_name': item.get('denominazione_regione'),
                            'province_code': p_code,
                            'name': prov_name,
                            'acronym_province': item.get('sigla_provincia'),
                            'lat': lat,
                            'long': lng,
                            'total_cases': cases,
                            'note': item.get('note'),
                            'nuts_code_1': item.get('codice_nuts_1'),
                            'nuts_code_2': item.get('codice_nuts_2'),
                            'nuts_code_3': item.get('codice_nuts_3'),
                        })
                
                # Batch create records for better performance
                if records_to_create:
                    self.create(records_to_create)
            return True
        except Exception as e:
            _logger.error("Fetch error: %s", str(e))
            return False

    @api.model
    def read_group(self, domain, fields_group, groupby, offset=0, limit=None, orderby=False, lazy=True):
        """
        Customizes the behavior of group_by views.
        Forces sorting by highest case count when grouping by region.
        """
        if groupby and groupby[0] == 'region_name':
            orderby = 'total_cases desc, region_name asc'
        return super().read_group(domain, fields_group, groupby, offset, limit, orderby, lazy)