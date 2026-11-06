# -*- coding: utf-8 -*-
import re
import urllib.parse
from markupsafe import Markup

from odoo import _, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

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

    def action_send_whatsapp_tracking(self):
        """Build and launch a pre-filled WhatsApp shipment tracking message."""
        self.ensure_one()

        partner = self.partner_id
        raw_phone = False
        if partner:
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

        customer_name = (partner.name if partner else '') or _('Valued Customer')
        company_name = self.company_id.name or ''
        carrier_name = self.carrier_id.name if self.carrier_id else ''
        tracking_ref = self.carrier_tracking_ref or ''
        tracking_url = self.carrier_tracking_url or ''

        order_ref_clause = f' (Order *{self.origin}*)' if self.origin else ''

        message_parts = [
            f'Hello {customer_name},',
            '',
            f'Great news! Your shipment *{self.name}*{order_ref_clause} is on its way.',
        ]

        shipping_details = []
        if carrier_name:
            shipping_details.append(f'• *Carrier:* {carrier_name}')
        if tracking_ref:
            shipping_details.append(f'• *Tracking Number:* {tracking_ref}')

        if shipping_details:
            message_parts.extend([
                '',
                '*Shipping Details:*',
                '\n'.join(shipping_details),
            ])

        if tracking_url:
            message_parts.extend([
                '',
                '*Track Your Shipment Live:*',
                tracking_url,
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
                '<p>WhatsApp shipping &amp; tracking notification sent.<br/>'
                '<b>Delivery:</b> %s | <b>Carrier:</b> %s | <b>Tracking Ref:</b> %s | <b>Phone:</b> %s</p>'
            ) % (
                self.name,
                carrier_name or _('N/A'),
                tracking_ref or _('N/A'),
                clean_phone,
            )
        )

        return {
            'type': 'ir.actions.act_url',
            'url': whatsapp_url,
            'target': 'new',
        }
