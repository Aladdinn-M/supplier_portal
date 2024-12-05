from odoo import models, fields, api, exceptions, _
import string
import secrets
from odoo.exceptions import UserError


class Supplier(models.Model):
    _name = 'supplier.portal.supplier'
    _description = 'Supplier'

    # Supplier Information Fields
    first_name = fields.Char(string='First Name', required=True)
    last_name = fields.Char(string='Last Name', required=True)
    company_name = fields.Char(string='Company Name', required=True)
    
    # KYC Fields
    kyc = fields.Char(string='kyc', required=True)
    kyc_file = fields.Binary(string='KYC Document', attachment=True)  # KYC as file attachment
    kyc_file_name = fields.Char(string="KYC File Name") 
    
    email = fields.Char(string='Email', required=True)
    website = fields.Char(string='Website', required=True)
    supp_code=fields.Char(string='Supplier Code')
    # Address Fields
    address = fields.Char(string='Address',required=True)
    country_id = fields.Many2one('res.country', string='Country', required=True)    
    city = fields.Char(string='City',required=True)
    
    # Authentication Fields
    login = fields.Char(string='Login')
    password = fields.Char(string='Password', required=True,default='************')
    
    # Full Name Computed Field
    full_name = fields.Char(string='Full Name', compute='_compute_full_name', store=True)

    @api.depends('first_name', 'last_name')
    def _compute_full_name(self):
        for supplier in self:
            supplier.full_name = f"{supplier.first_name} {supplier.last_name}"

    def action_generate_password(self):
        """Generate a secure random password with specific character set and set it on the password field."""
        # Define the allowed characters: uppercase, lowercase, digits, and @#$%
        characters = string.ascii_letters + string.digits + '@#$%'
        # Generate a 12-character password
        password = ''.join(secrets.choice(characters) for _ in range(12))
        # Set the password field with the generated password
        self.password = password

    def name_get(self):
        result = []
        for supplier in self:
            result.append((supplier.id, supplier.full_name))
        return result
    
     # Method to verify credentials
    @api.model
    def authenticate_supplier(self, login, password):
        supplier = self.search([('login', '=', login), ('password', '=', password)], limit=1)
        if not supplier:
            raise exceptions.AccessError(_("Invalid login credentials"))
        return supplier.id
    

    def action_send_login_email(self):
        """Send login credentials to the supplier via email."""
        for record in self:
            if not record.email:
                raise UserError(_("The supplier does not have an email address."))
            if not record.login or not record.password:
                raise UserError(_("The supplier must have a login and password."))

            # Prepare email content
            subject = "Your Supplier Portal Login Credentials"
            body = f"""
            Dear {record.first_name} {record.last_name},

            Welcome to the Supplier Portal!

            Here are your login credentials:
            - **Login:** {record.login}
            - **Password:** {record.password}

            You can log in at: /supplier_portal

            Regards,
            GALEN
            """

            # Send the email
            template = self.env['mail.mail'].create({
                'subject': subject,
                'body_html': body,
                'email_to': record.email,
            })
            template.send()

            # Notify the user that the email has been sent
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success!'),
                    'message': _('The login credentials have been sent to the supplier.'),
                    'type': 'success',
                    'sticky': False,
                }
            }
    



