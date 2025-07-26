import pandas as pd
import requests
import json
import time
import random # For dummy data generation

# --- Configuration for Etherscan API ---
# Get your Etherscan API Key from https://etherscan.io/myapikey
ETHERSCAN_API_KEY = "CNR3QU2XXZ584WZ9N3CVFCYJGTDV2JPCQM" 
ETHERSCAN_API_URL = "https://api.etherscan.io/api"

# Compound V2 Contract Addresses (Mainnet)
# We focus on the Comptroller (main logic) and some common cToken addresses
COMPOUND_V2_COMPTROLLER_ADDRESS = "0x3d9819210a31b402932df2a9bcf0798ee3ad0f9e"
COMPOUND_CTOKEN_ADDRESSES = {
    "cUSDC": "0x39aa39c021dfbae8fae8a5ddf309899ef88b8e07",
    "cDAI": "0x5d3a53686de40e2d11ae0b98fbc1855a0210f344",
    "cETH": "0x4ddc2d193948926d02f9b1fe9e1da681be2d7b80",
    "cWBTC": "0xc11b1268c1a3848e23fbc0cf5f1a53d6c7c6792f",
    "cUSDT": "0xf650c3d88d12db855b8bf7d11be6c55a4e07dcc9",
    # You can add more cToken addresses if needed, but these cover common ones
}
ALL_COMPOUND_CONTRACTS = [COMPOUND_V2_COMPTROLLER_ADDRESS] + list(COMPOUND_CTOKEN_ADDRESSES.values())
ALL_COMPOUND_CONTRACTS_LOWER = [addr.lower() for addr in ALL_COMPOUND_CONTRACTS]

# --- Function to Fetch Transactions from Etherscan ---
def fetch_etherscan_transactions(wallet_address, api_key, api_url, comptroller_address, ctoken_addresses, startblock=0):
    """
    Fetches normal transactions and ERC-20 token transfers for a wallet from Etherscan.
    Filters transactions related to Compound contract addresses.
    """
    all_wallet_transactions = []
    # print(f"\nFetching Etherscan transactions for wallet: {wallet_address}...") # Commented for cleaner output during full run

    # 1. Get Normal Transactions (contract interactions, including Compound calls)
    params_normal = {
        "module": "account",
        "action": "txlist",
        "address": wallet_address,
        "startblock": startblock,
        "endblock": 99999999, # Latest block
        "sort": "asc",
        "apikey": api_key
    }
    try:
        response = requests.get(api_url, params=params_normal)
        response.raise_for_status()
        data = response.json()
        if data['status'] == '1' and data['message'] == 'OK':
            for tx in data['result']:
                if (tx.get('to') and tx['to'].lower() in ALL_COMPOUND_CONTRACTS_LOWER) or \
                   (tx.get('from') and tx['from'].lower() in ALL_COMPOUND_CONTRACTS_LOWER):
                    tx_copy = tx.copy()
                    tx_copy['action_etherscan_category'] = 'normal_tx_compound_related'
                    tx_copy['wallet_address'] = wallet_address
                    all_wallet_transactions.append(tx_copy)
        elif data['status'] == '0' and data['message'] == 'No transactions found':
            pass
        else:
            print(f"Etherscan Normal TX Error for {wallet_address}: {data.get('message', 'Unknown error')}")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching normal TXs for {wallet_address}: {e}")
    except Exception as e:
        print(f"Unexpected error for normal TXs {wallet_address}: {e}")

    time.sleep(0.2)

    # 2. Get ERC-20 Token Transfers (cToken movements from/to wallet)
    for symbol, ctoken_address in ctoken_addresses.items():
        params_erc20 = {
            "module": "account",
            "action": "tokentx",
            "address": wallet_address,
            "contractaddress": ctoken_address, # Filter by specific cToken contract
            "startblock": startblock,
            "endblock": 99999999,
            "sort": "asc",
            "apikey": api_key
        }
        try:
            response = requests.get(api_url, params=params_erc20)
            response.raise_for_status()
            data = response.json()
            if data['status'] == '1' and data['message'] == 'OK':
                for tx in data['result']:
                    tx_copy = tx.copy()
                    tx_copy['action_etherscan_category'] = f'erc20_transfer_{symbol}'
                    tx_copy['wallet_address'] = wallet_address
                    all_wallet_transactions.append(tx_copy)
            elif data['status'] == '0' and data['message'] == 'No transactions found':
                pass
        except requests.exceptions.RequestException as e:
            print(f"Error fetching ERC20 TXs for {wallet_address} ({symbol}): {e}")
        except Exception as e:
            print(f"Unexpected error for ERC20 TXs {wallet_address} ({symbol}): {e}")

        time.sleep(0.2)

    # print(f"Fetched {len(all_wallet_transactions)} Etherscan-related transactions for {wallet_address}.") # Commented for cleaner output
    return all_wallet_transactions

# --- Dummy Data Generator (Fallback if no real data is fetched) ---
def generate_dummy_transactions():
    print("No real transactions fetched for any wallet. Generating dummy data for demonstration purposes...")
    dummy_data = []
    # Dummy wallet 1: Good behavior
    for _ in range(5):
        dummy_data.append({
            'wallet_address': '0xDummyGoodWallet1', 'action_etherscan_category': 'erc20_transfer_cUSDC',
            'value': str(random.randint(100, 500) * 10**6), 'tokenSymbol': 'cUSDC',
            'timeStamp': str(int(time.time() - random.randint(100000, 1000000))), 'hash': '0xDummyTxGood' + str(random.randint(1, 1000)),
            'from': '0xDummyGoodWallet1', 'to': COMPOUND_CTOKEN_ADDRESSES['cUSDC']
        })
    dummy_data.append({
        'wallet_address': '0xDummyGoodWallet1', 'action_etherscan_category': 'normal_tx_compound_related',
        'value': str(0), 'timeStamp': str(int(time.time() - 50000)), 'hash': '0xDummyTxGood' + str(random.randint(1, 1000)),
        'functionName': 'repayBorrow', 'from': '0xDummyGoodWallet1', 'to': COMPOUND_V2_COMPTROLLER_ADDRESS
    })

    # Dummy wallet 2: Bad behavior (liquidations)
    dummy_data.append({
        'wallet_address': '0xDummyBadWallet2', 'action_etherscan_category': 'normal_tx_compound_related',
        'value': str(random.randint(1, 5) * 10**18), 'timeStamp': str(int(time.time() - 200000)), 'hash': '0xDummyTxBad' + str(random.randint(1, 1000)),
        'functionName': 'borrow', 'from': '0xDummyBadWallet2', 'to': COMPOUND_V2_COMPTROLLER_ADDRESS
    })
    # Simulate a liquidation (this 'action' won't truly come from Etherscan but helps dummy scoring)
    dummy_data.append({
        'wallet_address': '0xDummyBadWallet2', 'action_etherscan_category': 'liquidate',
        'value': str(0), 'timeStamp': str(int(time.time() - 190000)), 'hash': '0xDummyTxBad' + str(random.randint(1, 1000)),
        'functionName': 'liquidateBorrow', 'from': '0xLiquidator', 'to': COMPOUND_V2_COMPTROLLER_ADDRESS,
        'collateralAmount': str(10 * 10**18), # Dummy collateral liquidated value
        'profitUSD': str(50) # Dummy profit
    })
    dummy_data.append({
        'wallet_address': '0xDummyBadWallet2', 'action_etherscan_category': 'liquidate',
        'value': str(0), 'timeStamp': str(int(time.time() - 150000)), 'hash': '0xDummyTxBad' + str(random.randint(1, 1000)),
        'functionName': 'liquidateBorrow', 'from': '0xLiquidator', 'to': COMPOUND_V2_COMPTROLLER_ADDRESS,
        'collateralAmount': str(5 * 10**18), # Dummy collateral liquidated value
        'profitUSD': str(20) # Dummy profit
    })

    # Dummy wallet 3: Safe behavior (only deposits/withdraws)
    for _ in range(3):
        dummy_data.append({
            'wallet_address': '0xDummySafeWallet3', 'action_etherscan_category': 'erc20_transfer_cDAI',
            'value': str(random.randint(500, 1000) * 10**18), 'tokenSymbol': 'cDAI',
            'timeStamp': str(int(time.time() - random.randint(50000, 2000000))), 'hash': '0xDummyTxSafe' + str(random.randint(1, 1000)),
            'from': '0xDummySafeWallet3', 'to': COMPOUND_CTOKEN_ADDRESSES['cDAI']
        })
    dummy_data.append({
        'wallet_address': '0xDummySafeWallet3', 'action_etherscan_category': 'erc20_transfer_cUSDT',
        'value': str(random.randint(10, 50) * 10**6), 'tokenSymbol': 'cUSDT', # USDT has 6 decimals
        'timeStamp': str(int(time.time() - 10000)), 'hash': '0xDummyTxSafe' + str(random.randint(1, 1000)),
        'from': COMPOUND_CTOKEN_ADDRESSES['cUSDT'], 'to': '0xDummySafeWallet3'
    })
    
    # Ensure all dummy data has the essential columns Etherscan would provide, even if None
    # This prepares it for the same processing as real data.
    required_etherscan_cols = ['blockNumber', 'timeStamp', 'hash', 'from', 'to', 'value', 'gasUsed', 'cumulativeGasUsed', 'input', 'methodId', 'functionName', 'contractAddress', 'tokenName', 'tokenSymbol', 'tokenDecimal', 'collateralAmount', 'profitUSD']
    for entry in dummy_data:
        for col in required_etherscan_cols:
            if col not in entry:
                entry[col] = None # Fill missing with None

    return dummy_data


# --- Main Script Execution ---
if __name__ == "__main__":
    # 1. Load Wallet IDs
    wallet_ids_file = 'Wallet id.xlsx'
    try:
        wallets_df = pd.read_excel(wallet_ids_file)  # Read directly from Excel
        # If the sheet name is not the first/default, specify sheet_name='Sheet1' or as needed
        # wallets_df = pd.read_excel(wallet_ids_file, sheet_name='Sheet1')
        wallet_addresses = wallets_df['wallet_id'].tolist()
        print(f"Successfully loaded {len(wallet_addresses)} wallet IDs.")
        # print("First 5 wallet IDs:") # Commented for cleaner output
        # for i in range(min(5, len(wallet_addresses))):
        #     print(wallet_addresses[i])
    except FileNotFoundError:
        print(f"Error: The file '{wallet_ids_file}' was not found.")
        exit()
    except Exception as e:
        print(f"An error occurred while reading the wallet IDs: {e}")
        exit()

    # 2. Fetch Transaction History (using Etherscan API for all 103 wallets)
    total_fetched_transactions = []
    print("\nStarting to fetch transactions for all wallets via Etherscan (this may take a few minutes)...")

    for i, wallet_address in enumerate(wallet_addresses): # Loop through ALL 103 wallets
        
        fetched_txs = fetch_etherscan_transactions(
            wallet_address,
            ETHERSCAN_API_KEY,
            ETHERSCAN_API_URL,
            COMPOUND_V2_COMPTROLLER_ADDRESS,
            COMPOUND_CTOKEN_ADDRESSES
        )
        total_fetched_transactions.extend(fetched_txs)
        time.sleep(5) # Etherscan free tier is 5 calls/sec. Each wallet can be 1+N_ctokens calls. So 0.5s is safer.

    print(f"\nTotal real transactions fetched for ALL wallets: {len(total_fetched_transactions)}")

    # Fallback to dummy data if no real transactions were fetched after trying all wallets
    if not total_fetched_transactions:
        print("No real transactions fetched after trying all wallets. Generating dummy data for demonstration purposes...")
        all_transactions_df = pd.DataFrame(generate_dummy_transactions())
    else:
        print("Successfully fetched real transactions. Proceeding with real data.")
        all_transactions_df = pd.DataFrame(total_fetched_transactions)
    
    print("\nSample of fetched (real or dummy) transactions:")
    print(all_transactions_df.head())
    print("\nInfo on fetched (real or dummy) transactions:")
    print(all_transactions_df.info())

    # 3. Data Preparation and Feature Engineering (Adapted for Etherscan Data)
    print("\n--- Starting Phase 2: Data Preparation & Feature Engineering ---")

    # Ensure necessary columns exist for Etherscan data and convert types
    # Etherscan provides 'timeStamp' and 'value', not 'timestamp' and 'amount'
    all_transactions_df['timeStamp_numeric'] = pd.to_numeric(all_transactions_df['timeStamp'], errors='coerce')
    all_transactions_df['value_numeric'] = pd.to_numeric(all_transactions_df['value'], errors='coerce') # This is typically in Wei for ETH, or raw token value

    # tokenDecimal is often present for ERC20 transfers but not always for normal txs.
    # We use .get() to avoid KeyError if the column doesn't exist for some txs.
    all_transactions_df['tokenDecimal_numeric'] = pd.to_numeric(all_transactions_df.get('tokenDecimal'), errors='coerce').fillna(0)
    
    # Etherscan has 'from' and 'to' fields, which are objects. Need to make them lowercase for consistency.
    all_transactions_df['from_lower'] = all_transactions_df['from'].str.lower()
    all_transactions_df['to_lower'] = all_transactions_df['to'].str.lower()

    # Convert timestamp to datetime objects (Etherscan uses 'timeStamp')
    all_transactions_df['timestamp_dt'] = pd.to_datetime(all_transactions_df['timeStamp_numeric'], unit='s')

    # Fill NaN numeric values with 0
    all_transactions_df[['timeStamp_numeric', 'value_numeric', 'tokenDecimal_numeric']] = \
        all_transactions_df[['timeStamp_numeric', 'value_numeric', 'tokenDecimal_numeric']].fillna(0)
    
    # Fill any NaNs in action_etherscan_category with 'unknown' (e.g. dummy data 'liquidate')
    all_transactions_df['action_etherscan_category'] = all_transactions_df['action_etherscan_category'].fillna('unknown')


    print("\n--- Engineering Features per Wallet ---")

    wallet_risk_features = all_transactions_df.groupby('wallet_address').agg(
        num_total_transactions=('hash', 'count'), # Total transactions involving wallet (hash is unique tx id)
        
        # Compound-related transactions (where 'to' or 'from' is a Compound contract)
        num_compound_related_transactions=('action_etherscan_category', lambda x: (
            (x == 'normal_tx_compound_related') | x.str.startswith('erc20_transfer')
        ).sum()),
        
        num_erc20_transfers=('action_etherscan_category', lambda x: x.str.startswith('erc20_transfer').sum()),
        
        # Total value transferred in normal transactions related to Compound (mainly ETH if applicable)
        total_eth_value_in_compound_txs=('value_numeric', lambda x: x[all_transactions_df.loc[x.index, 'action_etherscan_category'] == 'normal_tx_compound_related'].sum()),
        
        # Total value transferred in ERC20 transfers related to Compound (raw token value)
        total_erc20_value_in_compound_txs=('value_numeric', lambda x: x[all_transactions_df.loc[x.index, 'action_etherscan_category'].str.startswith('erc20_transfer')].sum()),

        # Count of unique token symbols involved in ERC20 transfers
        num_unique_assets_involved=('tokenSymbol', lambda x: x.nunique() if x.any() else 0), # Use tokenSymbol from Etherscan
        
        # Identify 'liquidate' action ONLY if it comes from dummy data.
        # For real Etherscan, this column usually requires complex decoding.
        # We will count it if present, but it's not expected for real data without decoding.
        num_liquidations=('action_etherscan_category', lambda x: (x == 'liquidate').sum()), 

        # Time-based features
        first_tx_timestamp=('timestamp_dt', 'min'),
        last_tx_timestamp=('timestamp_dt', 'max')
    )

    wallet_risk_features.fillna(0, inplace=True)
    wallet_risk_features['wallet_age_days'] = (wallet_risk_features['last_tx_timestamp'] - wallet_risk_features['first_tx_timestamp']).dt.days.fillna(0)
    wallet_risk_features = wallet_risk_features.drop(columns=['first_tx_timestamp', 'last_tx_timestamp'])
    wallet_risk_features.replace([float('inf'), -float('inf')], 0, inplace=True)


    print("\n--- Engineered Risk Features per Wallet (Head) ---")
    print(wallet_risk_features.head())
    print("\n--- Engineered Risk Features per Wallet (Info) ---")
    print(wallet_risk_features.info())

    # 4. Risk Scoring Model (Adapted for Etherscan Features)
    print("\n--- Starting Phase 3: Risk Scoring Model ---")

    risk_scores_revised = pd.Series(500.0, index=wallet_risk_features.index, dtype=float)

    # Scoring Logic based on Etherscan Features (Simplified)
    # Remember: Higher score = Lower risk. Lower score = Higher risk.

    # 1. Compound-Related Activity (num_compound_related_transactions)
    # Rewards wallets that have a decent number of interactions directly with Compound contracts/cTokens.
    max_comp_txs = wallet_risk_features['num_compound_related_transactions'].max()
    if max_comp_txs > 0:
        normalized_comp_txs = (wallet_risk_features['num_compound_related_transactions'] / max_comp_txs).clip(upper=1)
        risk_scores_revised += normalized_comp_txs * 150 # Max 150 points

    # 2. Wallet Age (Older Wallet = Potentially Lower Risk/More Stable)
    max_age = wallet_risk_features['wallet_age_days'].max()
    if max_age > 0:
        normalized_age = (wallet_risk_features['wallet_age_days'] / max_age).clip(upper=1)
        risk_scores_revised += normalized_age * 100 # Max 100 points

    # 3. Value Transferred (in ETH if normal txs, or raw token value if ERC20)
    # Higher value in Compound-related transactions indicates more significant engagement.
    # Using total_eth_value for general value, could also use total_erc20_value if tokens are key.
    max_eth_value = wallet_risk_features['total_eth_value_in_compound_txs'].max()
    if max_eth_value > 0:
        normalized_eth_value = (wallet_risk_features['total_eth_value_in_compound_txs'] / max_eth_value).clip(upper=1)
        risk_scores_revised += normalized_eth_value * 100 # Max 100 points

    # 4. Num unique assets (Diversity might be neutral or slight bonus)
    max_unique_assets = wallet_risk_features['num_unique_assets_involved'].max()
    if max_unique_assets > 0:
        normalized_unique_assets = (wallet_risk_features['num_unique_assets_involved'] / max_unique_assets).clip(upper=1)
        risk_scores_revised += normalized_unique_assets * 50 # Max 50 points for diversity

    # 5. Penalty for "Liquidations" (Highly impactful, if detected from dummy data)
    # For real Etherscan data, this will mostly be 0 without explicit decoding.
    risk_scores_revised -= wallet_risk_features['num_liquidations'].apply(lambda x: min(x * 400, 800)) # Strong penalty for any liquidation


    # --- Final Score Normalization and Merging ---
    risk_scores_revised = risk_scores_revised.clip(lower=0, upper=1000).astype(int)

    scored_wallets_with_activity = pd.DataFrame({
        'wallet_id': risk_scores_revised.index,
        'score': risk_scores_revised.values
    })

    all_original_wallets_df = pd.DataFrame({'wallet_id': wallet_addresses})

    final_output_df = pd.merge(
        all_original_wallets_df,
        scored_wallets_with_activity,
        on='wallet_id',
        how='left'
    )

    final_output_df['score'] = final_output_df['score'].fillna(500).astype(int) # Default 500 for inactive
    final_output_df['score'] = final_output_df['score'].clip(lower=0, upper=1000).astype(int)


    # --- Prepare Final Deliverable: CSV File ---
    output_csv_file = 'wallet_risk_scores.csv'
    final_output_df.to_csv(output_csv_file, index=False)

    print("\n--- Risk Scoring Complete ---")
    print(f"Generated {len(final_output_df)} wallet scores (including defaults for inactive wallets).")
    print(f"Scores saved to: {output_csv_file}")
    print("\nSample of final scores (showing some default scores as well):")
    print(final_output_df.sort_values('score', ascending=False).head(10).to_markdown(index=False))
    print(final_output_df.sort_values('score', ascending=True).head(10).to_markdown(index=False))
    print(final_output_df[final_output_df['score'] == 500].head(5).to_markdown(index=False))


    # --- Score Distribution Analysis (for all 100 wallets) ---
    print("\n--- Score Distribution Analysis (for all 100 wallets) ---")
    bins = [0, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1001]
    labels = ['0-99', '100-199', '200-299', '300-399', '400-499', '500-599', '600-699', '700-799', '800-899', '900-1000']
    final_output_df['score_range'] = pd.cut(final_output_df['score'], bins=bins, labels=labels, right=False)
    score_distribution = final_output_df['score_range'].value_counts().sort_index()
    print("Score Distribution across ranges:")
    print(score_distribution.to_markdown())