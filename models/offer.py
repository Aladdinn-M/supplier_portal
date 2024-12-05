from odoo import models, fields

class Offer(models.Model):
    _name = 'supplier.portal.offer'
    _description = 'Supplier Offer'

    offer_name = fields.Char(string="Offer Name", required=True)

    offer_file = fields.Binary(string='Offer File', attachment=True)

    # Reference to Supplier
    supplier_id = fields.Many2one('supplier.portal.supplier', string='Supplier', required=True, ondelete='cascade')

    # Reference to Demand
    demand_id = fields.Many2one('supplier.portal.demand', string='Demand', ondelete='cascade')

    # Offer Details
    offer_description = fields.Text(string='Offer Description', required=True)
    offer_amount = fields.Float(string='Offer Amount', required=True)

    # Offer Status
    status = fields.Selection(
        [('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')],
        string='Status',
        default='pending'
    )

    # Other Fields
    created_date = fields.Datetime(string='Created Date', default=fields.Datetime.now)
    validity_date = fields.Date(string='Validity Date')


    # Related fields to display supplier name and demand name
    supplier_name = fields.Char(string="Name of Supplier", related='supplier_id.full_name', store=True)
    demand_name = fields.Char(string="Name of Demand", related='demand_id.demand_name', store=True)