"""
Billing & Pricing commands for ACRCloud CLI
"""

import os
import click
from ..api import ACRCloudAPI
from ..utils import output_json, output_table


@click.group(name='billing')
@click.pass_context
def billing(ctx):
    """Manage billing, invoices, and pricing"""
    ctx.obj['api'] = ACRCloudAPI(
        ctx.obj['access_token'],
        ctx.obj['base_url']
    )


@billing.command(name='current-bill')
@click.option('--uid', type=int, default=None, help='User ID (admin only)')
@click.option('--output', '-o', type=click.Choice(['json', 'table']), default='table', help='Output format')
@click.pass_context
def current_bill(ctx, uid, output):
    """Get the current/latest bill

    Examples:
        acrcloud billing current-bill
        acrcloud billing current-bill --uid 12345
        acrcloud billing current-bill --output json
    """
    api = ctx.obj['api']

    try:
        result = api.get_current_bill(uid=uid)

        if output == 'json':
            output_json(result)
        else:
            bill = result.get('data', {})
            if not bill:
                click.echo("No current bill found")
                return

            state_map = {0: 'Pending', 1: 'Paid', 2: 'Cancelled'}
            click.echo("Current Bill:")
            click.echo("-" * 40)
            click.echo(f"  Bill ID:        {bill.get('id')}")
            click.echo(f"  User ID:        {bill.get('uid')}")
            click.echo(f"  Charge Type:    {bill.get('charge_type')}")
            click.echo(f"  Amount:         {bill.get('amount')}")
            click.echo(f"  Credit:         {bill.get('credit')}")
            click.echo(f"  Billing Period: {bill.get('bill_begin')} ~ {bill.get('bill_end')}")
            click.echo(f"  State:          {state_map.get(bill.get('state'), bill.get('state'))}")
            click.echo(f"  Payment Method: {bill.get('payment_method')}")
            click.echo(f"  Created:        {bill.get('created_at')}")
            click.echo(f"  Updated:        {bill.get('updated_at')}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@billing.command(name='next-bill-date')
@click.option('--uid', type=int, default=None, help='User ID (admin only)')
@click.option('--output', '-o', type=click.Choice(['json', 'table']), default='table', help='Output format')
@click.pass_context
def next_bill_date(ctx, uid, output):
    """Get the next billing date and days remaining

    Examples:
        acrcloud billing next-bill-date
        acrcloud billing next-bill-date --uid 12345
        acrcloud billing next-bill-date --output json
    """
    api = ctx.obj['api']

    try:
        result = api.get_next_bill_date(uid=uid)

        if output == 'json':
            output_json(result)
        else:
            click.echo("Next Bill Date:")
            click.echo("-" * 40)
            click.echo(f"  Next Bill Date: {result.get('next_bill_date')}")
            click.echo(f"  Days Remaining: {result.get('left_days')}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@billing.command(name='invoices')
@click.option('--uid', type=int, default=None, help='User ID (admin only)')
@click.option('--per-page', '-n', default=20, help='Results per page')
@click.option('--output', '-o', type=click.Choice(['json', 'table']), default='table', help='Output format')
@click.pass_context
def list_invoices(ctx, uid, per_page, output):
    """List invoices

    Examples:
        acrcloud billing invoices
        acrcloud billing invoices --uid 12345 --per-page 50
        acrcloud billing invoices --output json
    """
    api = ctx.obj['api']

    try:
        result = api.list_invoices(uid=uid, per_page=per_page)

        if output == 'json':
            output_json(result)
        else:
            invoices = result.get('data', [])
            if not invoices:
                click.echo("No invoices found")
                return

            # Pagination info
            total = result.get('total')
            current_page = result.get('current_page')
            last_page = result.get('last_page')
            if total is not None:
                click.echo(f"Showing page {current_page}/{last_page}, total: {total}")

            state_map = {0: 'Pending', 1: 'Paid', 2: 'Cancelled'}
            headers = ['ID', 'Charge Type', 'Amount', 'Period', 'State', 'Payment Method']
            rows = []
            for inv in invoices:
                period = f"{inv.get('bill_begin')} ~ {inv.get('bill_end')}"
                rows.append([
                    inv.get('id'),
                    inv.get('charge_type'),
                    inv.get('amount'),
                    period,
                    state_map.get(inv.get('state'), inv.get('state')),
                    inv.get('payment_method', '-'),
                ])
            output_table(headers, rows)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@billing.command(name='download-invoice')
@click.argument('invoice_id')
@click.option('--output-file', '-f', default=None,
              help='Output file path (default: <invoice_id>.pdf)')
@click.pass_context
def download_invoice(ctx, invoice_id, output_file):
    """Download an invoice as PDF

    INVOICE_ID should be in the format {uid}-{bill_id}, e.g. 12345-67890

    Examples:
        acrcloud billing download-invoice 12345-67890
        acrcloud billing download-invoice 12345-67890 --output-file ~/invoices/my_invoice.pdf
    """
    api = ctx.obj['api']

    if not output_file:
        output_file = f"{invoice_id}.pdf"

    try:
        pdf_bytes = api.download_invoice(invoice_id)
        output_path = os.path.expanduser(output_file)
        with open(output_path, 'wb') as f:
            f.write(pdf_bytes)
        click.echo(f"Invoice saved to: {output_path}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@billing.command(name='prices')
@click.option('--uid', type=int, default=None, help='User ID (admin only)')
@click.option('--type', 'price_type',
              type=click.Choice(['Standard', 'All', 'Latest']),
              default=None,
              help='Price type filter (Standard/All/Latest, default: Latest)')
@click.option('--service-types', default=None,
              help='Filter by service types, comma-separated (e.g. AVR,LCD,BM)')
@click.option('--output', '-o', type=click.Choice(['json', 'table']), default='table', help='Output format')
@click.pass_context
def get_prices(ctx, uid, price_type, service_types, output):
    """Get pricing information for services

    Examples:
        acrcloud billing prices
        acrcloud billing prices --type Standard
        acrcloud billing prices --service-types AVR,LCD
        acrcloud billing prices --uid 12345 --type All --output json
    """
    api = ctx.obj['api']

    try:
        result = api.get_prices(uid=uid, price_type=price_type, service_types=service_types)

        if output == 'json':
            output_json(result)
        else:
            prices_data = result.get('data', [])
            discount = result.get('discount')

            if not prices_data:
                click.echo("No pricing data found")
                return

            headers = ['ID', 'UID', 'Service Type', 'State', 'Prices']
            rows = []
            for price in prices_data:
                prices_obj = price.get('prices', {})
                prices_str = ', '.join(f"{k}: {v}" for k, v in prices_obj.items()) if prices_obj else '-'
                rows.append([
                    price.get('id'),
                    price.get('uid'),
                    price.get('service_type'),
                    'Active' if price.get('state') == 1 else 'Inactive',
                    prices_str,
                ])
            output_table(headers, rows)

            if discount:
                click.echo()
                click.echo("Your Discount:")
                for k, v in discount.items():
                    click.echo(f"  {k}: {v}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
