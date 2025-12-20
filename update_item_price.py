#!/usr/bin/env python3

"""
Update Square Item Price
=========================

Updates a Square catalog item variation price to remove strikethrough/compare-at pricing.
When the regular price matches the "online sale price", Square Online shows just the price
without the strikethrough formatting.
"""

import os
import sys
import json
import requests
import argparse


def update_item_variation_price(square_token: str, variation_id: str, new_price_cents: int):
    """
    Update a Square catalog item variation price.
    
    Args:
        square_token: Square API access token
        variation_id: The variation ID to update
        new_price_cents: New price in cents (e.g., 450 for $4.50)
    """
    base_url = "https://connect.squareup.com/v2"
    headers = {
        "Square-Version": "2024-09-18",
        "Authorization": f"Bearer {square_token}",
        "Content-Type": "application/json"
    }
    
    print(f"🔍 Fetching current variation data for {variation_id}...")
    
    # First, retrieve the current variation
    retrieve_url = f"{base_url}/catalog/object/{variation_id}"
    response = requests.get(retrieve_url, headers=headers)
    response.raise_for_status()
    
    current_object = response.json()['object']
    current_price = current_object.get('item_variation_data', {}).get('price_money', {}).get('amount', 0)
    
    print(f"📊 Current price: ${current_price/100:.2f}")
    print(f"📊 New price: ${new_price_cents/100:.2f}")
    
    # Update the variation
    updated_object = current_object.copy()
    if 'item_variation_data' not in updated_object:
        updated_object['item_variation_data'] = {}
    
    updated_object['item_variation_data']['price_money'] = {
        'amount': new_price_cents,
        'currency': 'USD'
    }
    
    # Use UpsertCatalogObject to update
    upsert_url = f"{base_url}/catalog/object"
    upsert_data = {
        "idempotency_key": f"update-price-{variation_id}-{new_price_cents}",
        "object": updated_object
    }
    
    print(f"⏳ Updating price via Square API...")
    
    response = requests.post(upsert_url, headers=headers, json=upsert_data)
    response.raise_for_status()
    
    result = response.json()
    updated_version = result['catalog_object'].get('version', 'unknown')
    
    print(f"✅ Successfully updated variation {variation_id}")
    print(f"📦 New version: {updated_version}")
    print(f"💰 Price is now ${new_price_cents/100:.2f}")
    print(f"\n💡 This should remove the strikethrough on Square Online if it matched the 'Online sale price'")
    
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Update Square item variation price to remove strikethrough"
    )
    parser.add_argument(
        "variation_id",
        help="The variation ID to update (e.g., 4FV7QCHVQ262VEPB4UPFQQR4)"
    )
    parser.add_argument(
        "--price",
        type=float,
        required=True,
        help="New price in dollars (e.g., 4.50)"
    )
    parser.add_argument(
        "--token",
        help="Square access token (or set SQUARE_TOKEN env var)"
    )
    
    args = parser.parse_args()
    
    # Get Square token
    square_token = args.token or os.environ.get('SQUARE_ACCESS_TOKEN') or os.environ.get('SQUARE_TOKEN')
    if not square_token:
        print("❌ Error: Square token required. Set SQUARE_ACCESS_TOKEN env var or use --token")
        sys.exit(1)
    
    # Convert dollars to cents
    price_cents = int(args.price * 100)
    
    try:
        result = update_item_variation_price(square_token, args.variation_id, price_cents)
        
        if args.price < 5.00:
            print(f"\n⚠️  Note: Price was reduced from likely $5.00 to ${args.price:.2f}")
            print("   Make sure this is intentional!")
        
    except requests.exceptions.HTTPError as e:
        print(f"❌ API Error: {e}")
        if e.response is not None:
            print(f"Response: {e.response.text}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
