from odoo import http, fields
from odoo.http import request
from datetime import date, timedelta
import logging

_logger = logging.getLogger(__name__)

class CovidApiController(http.Controller):

    @http.route('/api/v1/covid/stats', type='json', auth='user', methods=['POST'], csrf=False)
    def get_stats(self, **kwargs):
        """
        Main API endpoint to retrieve COVID statistics.
        Supported filters: date ranges, region/province codes, and names.
        Params JSON example:
        {
            "start_date": "2020-02-24",                
            "end_date": "2020-03-01",                 
            "data": "2020-02-25T17:00:00",             
            "codice_regione": 5,                        
            "denominazione_regione": "Veneto",         
            "codice_provincia": 26,                    
            "denominazione_provincia": "Treviso",      
            "order_by": "total_cases",                 
            "group_by": "region"                      
        }
        """
        
        params = kwargs

        # --- 1. Optional start/end date parsing and validation ---
        # Logic: If start_date is missing, it falls back to 'data' parameter or today's date.
        # If end_date is missing, it defaults to the start_date.
        try:
            if 'start_date' in params:
                sd = fields.Date.to_date(params['start_date'])
            elif 'data' in params:
                sd = fields.Date.to_date(params['data'][:10])
            else:
                sd = date.today()

            if 'end_date' in params:
                ed = fields.Date.to_date(params['end_date'])
            else:
                ed = sd
            # Logical validation to ensure the date range is chronologically correct
            if ed < sd:
                return {'status': 'error', 'message': 'end_date cannot be before start_date'}

        except Exception as e:
            return {'status': 'error', 'message': f'Invalid date format: {str(e)}'}

        # --- 2. Domain construction for Odoo search ---
        # Initialize domain with the validated date range
        domain = [('date', '>=', sd), ('date', '<=', ed)]

        # Dynamically append filters to the domain based on provided parameters
        if 'codice_regione' in params:
            domain.append(('codice_regione', '=', params['codice_regione']))
        if 'denominazione_regione' in params:
            domain.append(('region_name', '=', params['denominazione_regione']))
        if 'codice_provincia' in params:
            domain.append(('province_code', '=', str(params['codice_provincia'])))
        if 'denominazione_provincia' in params:
            domain.append(('name', '=', params['denominazione_provincia']))

        # --- 3. Lazy load/Data synchronization ---
        # Access the model with sudo to bypass ACLs and skip recursive fetch via context
        covid_model = request.env['covid.province'].sudo().with_context(skip_covid_fetch=True)
        order_by = params.get('order_by', 'total_cases')
        records = covid_model.search(domain, order=f"{order_by} desc")
        if not records :
            # Trigger the remote data fetcher for the specified date range
            covid_model._fetch_remote_data(target_date=None, start_date=sd,end_date=ed)
            # Execute search with the constructed domain and secure order clause
            records = covid_model.search(domain, order=f"{order_by} desc")

        # --- 4. Secure sorting logic ---
        # Whitelist approach to prevent SQL injection or invalid field sorting
        valid_order_fields = ['total_cases', 'province_code', 'date', 'region_name', 'name']
        if order_by not in valid_order_fields:
            return {'status': 'error', 'message': 'Invalid order_by field'}

        # --- 5. Optional Data Grouping and Formatting ---
        group_by = params.get('group_by')
        data = []
        if group_by == 'region':
            # Aggregate total_cases by region name
            grouped = {}
            for r in records:
                grouped.setdefault(r.region_name, 0)
                grouped[r.region_name] += r.total_cases
            # Convert dictionary to list of objects and sort by cases
            for reg, total in grouped.items():
                data.append({'region': reg, 'total_cases': total})
            data.sort(key=lambda x: x['total_cases'], reverse=True)
        else:
            # Standard output
            for r in records:
                data.append({
                    'date': str(r.date),
                    'region': r.region_name,
                    'province': r.name,
                    'province_code': r.province_code,
                    'total_cases': r.total_cases
                })
        
        # Return structured JSON response
        
        return {'status': 'success', 'count': len(data), 'data': data}
    