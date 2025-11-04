# OnChainIQ

**OnChainIQ** is an on-chain data analyzer designed to extract, process, and visualize blockchain activity.  
It provides actionable insights into token movements, whale activity, and emerging assets, helping researchers, traders, and developers make informed decisions.

## Features
- Fetch Ethereum (and other chain) on-chain data
  - Top tokens, newly minted tokens, top holders
  - Address-level transaction history
- Transform and normalize data for analysis
- Export datasets to Excel, CSV, or JSON
- Integration with Power BI, Tableau, or custom dashboards
- Scalable framework for multi-chain analytics

## Tech Stack
- Python 3.11+
- Libraries: Pandas, Requests, Web3.py, OpenPyXL
- APIs: Ethplorer, Etherscan, custom RPC endpoints

## Installation
```bash
git clone https://github.com/<your-username>/OnChainIQ.git
cd OnChainIQ
pip install -r requirements.txt
