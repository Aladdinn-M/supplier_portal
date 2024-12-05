from odoo import http
from odoo.http import request
from werkzeug.utils import redirect
import base64
import json
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime, timedelta

DEFAULT_SERVER_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class SupplierPortalController(http.Controller):
     
    @http.route(['/supplier_portal/login'], type='http', auth='public', website=True)
    def supplier_login_page(self, **kwargs):
        """Render the login page for suppliers."""
        error = kwargs.get('error', False)
        return request.render('supplier_portal.supplier_login', {'error': error})

    @http.route(['/supplier_portal/login/submit'], type='http', auth='public', website=True, methods=['POST'])
    def supplier_login_submit(self, **post):
        """Handle supplier login form submission."""
        login = post.get('login')
        password = post.get('password')

        # Authenticate supplier
        supplier = request.env['supplier.portal.supplier'].sudo().search([
            ('login', '=', login),
            ('password', '=', password)
        ], limit=1)

        if not supplier:
            # Redirect back to login with an error
            return request.render('supplier_portal.supplier_login', {
                'error': "Invalid login or password."
            })

        # Store supplier ID in session
        request.session['supplier_id'] = supplier.id
        return redirect('/supplier_portal')

    @http.route(['/supplier_portal/signup'], type='http', auth='public', website=True)
    def supplier_signup_page(self, **kwargs):
        """Render the signup page."""
        return request.render('supplier_portal.supplier_signup')

    @http.route(['/supplier_portal/signup/submit'], type='http', auth='public', website=True, methods=['POST'])
    def supplier_signup_submit(self, **post):
        """Handle the supplier signup form submission."""
        # Extract form data
        values = {
            'first_name': post.get('first_name'),
            'last_name': post.get('last_name'),
            'company_name': post.get('company_name'),
            'email': post.get('email'),
            'kyc': post.get('kyc'),
            'website': post.get('website'),
            'address': post.get('address'),
            'country_id': post.get('country_id'),
            'city': post.get('city'),
        }

        # Handle the uploaded file
        kyc_file = post.get('kyc_file')
        if kyc_file:
            # Read and encode the file data as base64
            values['kyc_file'] = base64.b64encode(kyc_file.read())
            values['kyc_file_name'] = kyc_file.filename  # Optional: Save the file name if needed

        missing_fields = [field for field in ['first_name', 'last_name','company_name','email','kyc','website','address'] if not post.get(field)]
        if missing_fields:
            return request.render('supplier_portal.supplier_signup', {
            'error': f"Missing required fields: {', '.join(missing_fields)}"})


        # Create the supplier record
        request.env['supplier.portal.supplier'].sudo().create(values)

        # Redirect to thank-you page
        return request.redirect('/contactus-thank-you')


    @http.route(['/supplier_portal'], type='http', auth='public', website=True)
    def supplier_space_page(self):
        """Render the supplier space page."""
        supplier_id = request.session.get('supplier_id')
        if not supplier_id:
            return request.redirect('/supplier_portal/login')

        supplier = request.env['supplier.portal.supplier'].sudo().browse(supplier_id)
        if not supplier.exists():
            return request.redirect('/supplier_portal/login')
        
        # Fetch demands and offers
        demands = request.env['supplier.portal.demand'].sudo().search([])
        total_demands = request.env['supplier.portal.demand'].sudo().search_count([])
        total_offers = request.env['supplier.portal.offer'].sudo().search_count([('supplier_id', '=', supplier_id)])
        offers = request.env['supplier.portal.offer'].sudo().search([('supplier_id', '=', supplier_id)])
        
        # Initialize product data
        labels_prod = []
        sales = []

        # Check if the supplier has a supp_code
        if supplier.supp_code:
            # Fetch products whose barcode starts with the supplier's supp_code
            products = request.env['product.product'].sudo().search([('barcode', 'like', f"{supplier.supp_code}%")], limit=5)

            # Get the start and end of the current month
            today = datetime.today()
            start_of_month = today.replace(day=1)
            end_of_month = (start_of_month + timedelta(days=31)).replace(day=1) - timedelta(days=1)

            # Calculate weekly sales for each product
            for product in products:
                labels_prod.append(product.default_code or f"Product {product.id}")  # Internal Reference or fallback to ID
                product_sales = [0, 0, 0, 0, 0]  # Initialize sales data for 5 weeks

                # Fetch sale order lines for the current product in the current month
                sale_lines = request.env['sale.order.line'].sudo().search([
                    ('product_id', '=', product.id),
                    ('order_id.date_order', '>=', start_of_month.strftime('%Y-%m-%d %H:%M:%S')),
                    ('order_id.date_order', '<=', end_of_month.strftime('%Y-%m-%d %H:%M:%S'))
                ])

                # Accumulate sales data per week
                for sale_line in sale_lines:
                    date_order = sale_line.order_id.date_order.date()  # Extract only the date part
                    week_number = (date_order - start_of_month.date()).days // 7
                    if 0 <= week_number < len(product_sales):  # Ensure week_number is valid
                        product_sales[week_number] += sale_line.product_uom_qty

                # Append the weekly sales data for the product
                sales.append(product_sales)

        else:
            # Handle the case where no supp_code is provided
            labels_prod = ["No products available"]  # Placeholder label
            sales = [[0, 0, 0, 0, 0]]  # Placeholder sales data

        # Render the page with all data
        return request.render('supplier_portal.supplier_space', {
            'supplier': supplier,
            'demands': demands or [],
            'offers': offers or [],
            'total_offers': total_offers or 0,
            'total_demands': total_demands or 0,
            'labels_prod': json.dumps(labels_prod),  # JSON-encoded product labels
            'sales': json.dumps(sales)  # JSON-encoded sales data
        })

    @http.route(['/supplier_portal/demand'], type='http', auth='public', website=True)
    def all_demands(self, **kwargs):
        """
        Display all demands without a limit.
        """
        supplier_id = request.session.get('supplier_id')
        if not supplier_id:
            return request.redirect('/supplier_portal/login')

        # Fetch all demands
        demands = request.env['supplier.portal.demand'].sudo().search([])
        return request.render('supplier_portal.all_demands_page', {
            'demands': demands,
        })

    @http.route(['/supplier_portal/offer'], type='http', auth='public', website=True)
    def all_offers(self, **kwargs):
        """
        Display all offers without a limit.
        """
        supplier_id = request.session.get('supplier_id')
        if not supplier_id:
            return request.redirect('/supplier_portal/login')

        # Fetch all offers for the logged-in supplier
        offers = request.env['supplier.portal.offer'].sudo().search([('supplier_id', '=', supplier_id)])
        return request.render('supplier_portal.all_offers_page', {
            'offers': offers,
        })



    @http.route(['/supplier_portal/offer/<int:offer_id>'], type='http', auth='public', website=True)
    def offer_details(self, offer_id, **kwargs):
        """Render the offer details page."""
        supplier_id = request.session.get('supplier_id')
        if not supplier_id:
            return request.redirect('/supplier_portal/login')

        # Fetch the offer
        offer = request.env['supplier.portal.offer'].sudo().browse(offer_id)

        # Ensure the offer exists and belongs to the logged-in supplier
        if not offer.exists() or offer.supplier_id.id != supplier_id:
            return request.redirect('/supplier_portal')

        return request.render('supplier_portal.offer_details_page', {
            'offer': offer
        })

    @http.route(['/supplier_portal/offer/<int:offer_id>/download'], type='http', auth='public', website=True)
    def download_offer_file(self, offer_id, **kwargs):
        """Allow downloading the offer's associated file."""
        supplier_id = request.session.get('supplier_id')
        
        # Redirect to login if not logged in
        if not supplier_id:
            return request.redirect('/supplier_portal/login')

        # Fetch the offer
        offer = request.env['supplier.portal.offer'].sudo().browse(offer_id)

        # Ensure the offer exists and belongs to the logged-in supplier
        if not offer.exists() or offer.supplier_id.id != supplier_id:
            return request.redirect('/supplier_portal')

        # Handle file download
        if offer.offer_file:
            file_data = base64.b64decode(offer.offer_file)

            # Use offer_name with .pdf extension
            file_name = f"{offer.offer_name or 'offer_file'}.pdf"
            
            headers = [
                ('Content-Type', 'application/pdf'),  # Explicitly set to PDF
                ('Content-Disposition', f'attachment; filename="{file_name}"')  # Add correct filename
            ]
            return request.make_response(file_data, headers=headers)

        # Redirect to portal if no file is available
        return request.redirect('/supplier_portal')
    
    @http.route('/supplier_portal/offer/create', type='http', auth='public', website=True)
    def create_offer_page(self, **kwargs):
        """Render the Create Offer page."""
        supplier_id = request.session.get('supplier_id')
        if not supplier_id:
            return request.redirect('/supplier_portal/login')

        demand_id = kwargs.get('demand_id')
        demand = request.env['supplier.portal.demand'].sudo().browse(int(demand_id)) if demand_id else None
        supplier = request.env['supplier.portal.supplier'].sudo().browse(supplier_id)

        return request.render('supplier_portal.create_offer_page', {
            'supplier': supplier,
            'demand': demand,
        })

    @http.route(['/supplier_portal/offer/create/submit'], type='http', auth='public', website=True, methods=['POST'])
    def create_offer_submit(self, **post):
        supplier_id = request.session.get('supplier_id')
        if not supplier_id:
            return request.redirect('/supplier_portal/login')

        # Get the logged-in supplier
        supplier = request.env['supplier.portal.supplier'].sudo().browse(supplier_id)

        # Extract form data
        values = {
            'supplier_id': supplier.id,
            'demand_id': post.get('demand_id') or None,
            'offer_name': post.get('offer_name'),
            'offer_description': post.get('offer_description'),
            'offer_amount': float(post.get('offer_amount')) if post.get('offer_amount') else 0.0,
            'validity_date': post.get('validity_date'),
        }

        # Handle uploaded file
        offer_file = post.get('offer_file')
        if offer_file:
            values['offer_file'] = base64.b64encode(offer_file.read())
        
        # Create the offer record
        request.env['supplier.portal.offer'].sudo().create(values)

        # Redirect to offers page
        return request.redirect('/supplier_portal')



    @http.route(['/supplier_portal/demand/<int:demand_id>'], type='http', auth='public', website=True)
    def demand_details(self, demand_id, **kwargs):
        """Handle demand details page."""
        # Ensure supplier is logged in
        supplier_id = request.session.get('supplier_id')
        if not supplier_id:
            return request.redirect('/supplier_portal/login')

        # Fetch the demand record
        demand = request.env['supplier.portal.demand'].sudo().browse(demand_id)

        # Check if the demand exists
        if not demand.exists():
            return request.render('website.404')  # Render a 404 page if the demand doesn't exist

        # Render the demand details page
        return request.render('supplier_portal.demand_details_page', {
            'demand': demand,
        })


    @http.route(['/supplier_portal/demand/<int:demand_id>/download'], type='http', auth='public', website=True)
    def download_demand_file(self, demand_id, **kwargs):
        """Handle demand details page."""
        # Ensure supplier is logged in
        supplier_id = request.session.get('supplier_id')
        if not supplier_id:
            return request.redirect('/supplier_portal/login')

        # Fetch the demand record
        demand = request.env['supplier.portal.demand'].sudo().browse(demand_id)

        # Check if the demand exists
        if not demand.exists():
            return request.render('website.404')  # Render a 404 page if the demand doesn't exist

        # Handle file download
        if demand.demand_file:
            file_data = base64.b64decode(demand.demand_file)

            # Use offer_name with .pdf extension
            file_name = f"{demand.demand_file_name or 'demand_file'}"
            
            headers = [
                ('Content-Type', 'application/pdf'),  # Explicitly set to PDF
                ('Content-Disposition', f'attachment; filename="{file_name}"')  # Add correct filename
            ]
            return request.make_response(file_data, headers=headers)

        # Redirect to portal if no file is available
        return request.redirect('/supplier_portal')



    @http.route(['/supplier_portal/logout'], type='http', auth='public', website=True, methods=['POST'])
    def supplier_logout(self, **post):
        """Logs out the supplier by clearing the session key specific to the supplier portal."""
        # Clear only the supplier-related session key
        if 'supplier_id' in request.session:
            del request.session['supplier_id']
        
        # Redirect to the supplier login page
        return request.redirect('/supplier_portal/login')