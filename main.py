import asyncio
import aiohttp
import pandas as pd
from datetime import datetime
from solders.keypair import Keypair
import base58


async def check_meteora_points():
    with open("private_keys.txt", 'r') as f:
        keys = [line.strip() for line in f if line.strip()]

    headers = {
        'content-type': 'application/json',
        'origin': 'https://www.meteora.ag',
        'referer': 'https://www.meteora.ag/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    async def get_points(session, pk):
        try:
            keypair = Keypair.from_bytes(base58.b58decode(pk))
            message = f"Sign with your wallet to verify ownership, allowing you to view your points. Time: {datetime.now().strftime('%m/%d/%Y, %I:%M:%S %p')}"
            signature = str(keypair.sign_message(message.encode('utf-8')))

            payload = {
                "publicKey": str(keypair.pubkey()),
                "message": message,
                "signature": signature
            }

            async with session.post('https://points-api.meteora.ag/points', headers=headers, json=payload) as resp:
                data = await resp.json()
                dlmm_2025 = next((x for x in data.get('2025', []) if x['product'] == 'dlmm'), {})
                dlmm_2024 = next((x for x in data.get('2024', []) if x['product'] == 'dlmm'), {})
                launch_dlmm = next((x for x in data.get('launchPools', []) if x['product'] == 'dlmm'), {})

                return {
                    'Wallet': str(keypair.pubkey())[:6] + '...' + str(keypair.pubkey())[-6:],
                    '2025_Total': dlmm_2025.get('total', 0),
                    '2025_TVL': dlmm_2025.get('tvl', 0),
                    '2025_Fees': dlmm_2025.get('fees', 0),
                    '2024_Total': dlmm_2024.get('total', 0),
                    '2024_Fees': dlmm_2024.get('fees', 0),
                    'LaunchPools': launch_dlmm.get('total', 0),
                    'Eligible': data.get('pointsEligibility', 'N/A')
                }
        except Exception as e:
            return {'Wallet': 'Error', '2025_Total': 0, '2025_TVL': 0, '2025_Fees': 0, '2024_Total': 0, '2024_Fees': 0,
                    'LaunchPools': 0, 'Eligible': str(e)}

    async with aiohttp.ClientSession() as session:
        results = await asyncio.gather(*[get_points(session, pk) for pk in keys])

    df = pd.DataFrame(results)
    print(df.to_string(index=False))
    total_points = df['2025_Total'].sum() + df['2024_Total'].sum() + df['LaunchPools'].sum()
    print(f"\nTotal Points: {total_points:,}")
    print(f"Total 2025 TVL: {df['2025_TVL'].sum():,}")
    print(f"Total 2025 Fees: {df['2025_Fees'].sum():,}")
    print(f"Total 2024 Fees: {df['2024_Fees'].sum():,}")


asyncio.run(check_meteora_points())
