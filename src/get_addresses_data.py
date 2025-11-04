import requests
import pandas as pd
import time

API_KEY = "freekey"  # replace with personal key for larger pulls
BASE_URL = "https://api.ethplorer.io"
OUTPUT_FILE = "eth_whale_dataset.xlsx"

# ---------------- GLOBAL API CALL FUNCTION ----------------
def call_api(endpoint, params=None):
    if params is None:
        params = {}
    params['apiKey'] = API_KEY
    url = f"{BASE_URL}{endpoint}"
    try:
        print(f"🌐 Calling: {url}")
        res = requests.get(url, params=params, timeout=15)
        res.raise_for_status()
        data = res.json()
        if 'error' in data:
            print(f"⚠️ Error: {data['error']['message']}")
            return None
        time.sleep(10)  # ⏳ Global delay to prevent rate limiting
        return data
    except Exception as e:
        print(f"❌ API Error for {endpoint}: {e}")
        return None

# ---------------- HELPER: Convert UNIX timestamps ----------------
def convert_unix_timestamps(df: pd.DataFrame) -> pd.DataFrame:
    """Convert any UNIX timestamp columns in DataFrame to readable datetimes."""
    if df.empty:
        return df
    for col in df.columns:
        if "timestamp" in col.lower() or col.lower().endswith(".ts"):
            try:
                df[col] = pd.to_datetime(df[col], unit="s", errors="coerce", utc=True)
                df[col] = df[col].dt.tz_convert(None)  # make timezone-naive for Excel
            except Exception:
                pass
    return df

# ---------------- STEP 1: Fetch Top Tokens ----------------
def get_top_tokens(limit=20):
    data = call_api("/getTop", {"criteria": "cap", "limit": limit})
    if not data or "tokens" not in data:
        return pd.DataFrame()
    df = pd.json_normalize(data["tokens"])
    return convert_unix_timestamps(df)

# ---------------- STEP 2: Fetch Holders for Each Token ----------------
def get_top_holders(token_address, limit=100):
    data = call_api(f"/getTopTokenHolders/{token_address}", {"limit": limit})
    if not data or "holders" not in data:
        return pd.DataFrame()
    df = pd.json_normalize(data["holders"])
    df["token_address"] = token_address
    return convert_unix_timestamps(df)

# ---------------- STEP 3: Fetch Holder Info ----------------
def get_address_info(address):
    data = call_api(f"/getAddressInfo/{address}")
    if not data:
        return None
    record = {
        "address": data.get("address"),
        "isContract": "contractInfo" in data,
        "ethBalance": data.get("ETH", {}).get("balance", 0),
        "ethPriceUSD": data.get("ETH", {}).get("price", {}).get("rate"),
        "totalTokensHeld": len(data.get("tokens", [])) if "tokens" in data else 0,
        "txCount": data.get("countTxs", 0),
    }
    return record

# ---------------- STEP 4: Get Address Transactions ----------------
def get_address_transactions(address, limit=30):
    data = call_api(f"/getAddressTransactions/{address}", {"limit": limit})
    if not isinstance(data, list):
        return pd.DataFrame()
    df = pd.json_normalize(data)
    df["address"] = address
    return convert_unix_timestamps(df)

# ---------------- STEP 5: Fetch Newly Added Tokens ----------------
def get_new_tokens(limit=100):
    data = call_api("/getTokensNew", {"limit": limit})
    if not data:
        return pd.DataFrame()
    if isinstance(data, list):
        df = pd.json_normalize(data)
    else:
        df = pd.DataFrame([data])
    return convert_unix_timestamps(df)

# ---------------- MAIN EXECUTION ----------------
def main():
    print("🚀 Gathering Ethereum on-chain data from Ethplorer...\n")

    top_tokens = get_top_tokens(limit=20)
    print(f"✅ Collected {len(top_tokens)} top tokens.")

    print("🔍 Fetching 100 newly added tokens...")
    new_tokens = get_new_tokens(limit=100)
    print(f"✅ Collected {len(new_tokens)} new tokens.")

    holders_list = []
    for _, token in top_tokens.iterrows():
        addr = token["address"]
        print(f"🔍 Fetching top holders for {token.get('name', 'Unknown')} ({addr})...")
        df_holders = get_top_holders(addr, limit=100)
        if not df_holders.empty:
            holders_list.append(df_holders)

    all_holders = pd.concat(holders_list, ignore_index=True) if holders_list else pd.DataFrame()
    print(f"✅ Collected {len(all_holders)} total holder entries.")

    unique_addresses = all_holders["address"].unique().tolist()[:50]
    address_infos = []
    transactions_all = []

    for i, addr in enumerate(unique_addresses):
        print(f"📬 Address {i+1}/{len(unique_addresses)}: {addr}")
        info = get_address_info(addr)
        if info:
            address_infos.append(info)
        tx_df = get_address_transactions(addr, limit=20)
        if not tx_df.empty:
            transactions_all.append(tx_df)

    df_address_info = pd.DataFrame(address_infos)
    df_transactions = pd.concat(transactions_all, ignore_index=True) if transactions_all else pd.DataFrame()

    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
        top_tokens.to_excel(writer, sheet_name="Top Tokens", index=False)
        new_tokens.to_excel(writer, sheet_name="New Tokens", index=False)
        all_holders.to_excel(writer, sheet_name="Top Holders", index=False)
        df_address_info.to_excel(writer, sheet_name="Address Info", index=False)
        df_transactions.to_excel(writer, sheet_name="Transactions", index=False)

    print(f"\n✅ Dataset saved as {OUTPUT_FILE}")
    print("Sheets: Top Tokens | New Tokens | Top Holders | Address Info | Transactions")

if __name__ == "__main__":
    main()
