# -*- coding: utf-8 -*-
import re
import urllib.parse
from markupsafe import Markup

from odoo import _, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _clean_whatsapp_phone(self, raw_phone):
        """Sanitize phone number keeping only digits and an optional leading '+'."""
        if not raw_phone:
            return ''
        stripped = str(raw_phone).strip()
        has_plus = stripped.startswith('+')
        digits = re.sub(r'\D', '', stripped)
        if not digits:
            return ''
        return f'+{digits}' if has_plus else digits

    def _format_whatsapp_currency(self, amount):
        """Format monetary amount using the order currency symbol and position."""
        self.ensure_one()
        symbol = self.currency_id.symbol or self.currency_id.name or ''
        if self.currency_id.position == 'before':
            return f'{symbol}{amount:,.2f}'
        return f'{amount:,.2f} {symbol}'.strip()

    def action_send_whatsapp(self):
        """Build and launch a pre-filled WhatsApp message for the Quotation / Sale Order."""
        self.ensure_one()

        partner = self.partner_id
        raw_phone = (
            partner.mobile
            or partner.phone
            or partner.commercial_partner_id.mobile
            or partner.commercial_partner_id.phone
        )
        clean_phone = self._clean_whatsapp_phone(raw_phone)

        if not clean_phone:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Missing Phone Number / Numara Eksik'),
                    'message': _('Please enter a phone or mobile number on the customer card.'),
                    'type': 'danger',
                    'sticky': False,
                },
            }

        doc_type = _('Quotation') if self.state in ('draft', 'sent') else _('Sales Order')
        customer_name = partner.name or _('Valued Customer')
        company_name = self.company_id.name or ''

        item_lines = []
        for line in self.order_line:
            if line.display_type:
                continue
            item_name = (line.product_id.display_name or line.name or '').splitlines()[0].strip()
            qty = (
                int(line.product_uom_qty)
                if float(line.product_uom_qty).is_integer()
                else line.product_uom_qty
            )
            line_subtotal = self._format_whatsapp_currency(line.price_subtotal)
            item_lines.append(f'• {item_name} (x{qty}) - {line_subtotal}')

        total_formatted = self._format_whatsapp_currency(self.amount_total)

        portal_link = ''
        if hasattr(self, 'get_base_url') and hasattr(self, 'get_portal_url'):
            base_url = (self.get_base_url() or '').rstrip('/')
            portal_path = self.get_portal_url() or ''
            if base_url and portal_path:
                portal_link = f'{base_url}{portal_path}'

        message_parts = [
            f'Hello {customer_name},',
            '',
            f'Here are the details for your {doc_type} *{self.name}*:',
        ]

        if item_lines:
            message_parts.extend([
                '',
                '*Order Items:*',
                '\n'.join(item_lines),
            ])

        message_parts.extend([
            '',
            f'*Total Amount:* *{total_formatted}*',
        ])

        if portal_link:
            message_parts.extend([
                '',
                '*View & Pay Online:*',
                portal_link,
            ])

        if company_name:
            message_parts.extend([
                '',
                f'Thank you for choosing *{company_name}*!',
            ])

        message_text = '\n'.join(message_parts)
        encoded_message = urllib.parse.quote(message_text)
        whatsapp_url = f'https://api.whatsapp.com/send?phone={clean_phone}&text={encoded_message}'

        self.message_post(
            body=Markup(
                '<p>WhatsApp message triggered for order.<br/>'
                '<b>Order:</b> %s | <b>Total:</b> %s | <b>Phone:</b> %s</p>'
            ) % (self.name, total_formatted, clean_phone)
        )

        return {
            'type': 'ir.actions.act_url',
            'url': whatsapp_url,
            'target': 'new',
        }
