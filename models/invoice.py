from odoo import models, fields

class Invoice(models.Model):
    _name = 'supplier.portal.invoice'
    _description = 'Supplier Invoice'

    supplier_id = fields.Many2one('supplier.portal.supplier', string='Supplier', required=True, ondelete='cascade')
    invoice_number = fields.Char(string='Invoice Number', required=True)
    amount = fields.Float(string='Amount', required=True)
    status = fields.Selection(
        [('draft', 'Draft'), ('sent', 'Sent'), ('paid', 'Paid'), ('cancelled', 'Cancelled')],
        string='Status',
        default='draft'
    )
    invoice_date = fields.Date(string='Invoice Date', required=True)
    due_date = fields.Date(string='Due Date')

    # Supplier Information for display purposes
    supplier_name = fields.Char(related='supplier_id.full_name', string="Supplier Name", store=True)
