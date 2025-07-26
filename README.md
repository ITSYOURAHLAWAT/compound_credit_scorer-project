# DeFi Wallet Risk Scoring: A Compound V2 Case Study

## Project Goal

This project was all about building a system to assess the risk profile of cryptocurrency wallets interacting with the Compound V2 lending protocol. The core task was to assign a "risk score" between 0 and 1000 to each wallet, based purely on their historical on-chain transaction behavior. A higher score signifies more reliable and responsible usage, while a lower score points towards riskier patterns or potentially less desirable activity.

## The Data: Unpacking Compound V2 Interactions

Our starting point was a list of 103 wallet addresses. The challenge was to retrieve their transaction history specifically from the Compound V2 protocol.

### Data Collection Approach: The Etherscan Pivot

Initially, I explored using The Graph Protocol's subgraphs for direct Compound event data. However, accessing consistent and comprehensive data via public subgraph endpoints proved challenging due to strict rate limits and authentication complexities (like wallet connect). This led to a crucial pivot in my data collection strategy.

I transitioned to using the **Etherscan API** as a more accessible alternative. While Etherscan provides more raw blockchain transaction data, rather than pre-labeled Compound events, it offered a more straightforward API key acquisition process.

**My Etherscan Data Collection Process:**

1.  **Wallet List Intake:** The project started by loading the 103 target wallet addresses from a CSV file (`Wallet id.xlsx - Sheet1.csv`).
2.  **Dual Transaction Fetching:** For each wallet, I made two types of API calls to Etherscan:
    * **Normal Transactions (`txlist` action):** This captured direct interactions with smart contracts. I specifically filtered for transactions where the `to` or `from` address matched a known Compound V2 contract (like the Comptroller or major cToken addresses).
    * **ERC-20 Token Transfers (`tokentx` action):** This focused on the movement of specific tokens (like cTokens) to or from the wallet. Queries were made for common Compound cToken addresses (e.g., cUSDC, cDAI, cETH).
3.  **API Key Management:** A personal Etherscan API key was integrated for authentication.
4.  **Rate Limit Handling:** Given Etherscan's free-tier rate limits, a significant delay of **5 seconds** was introduced between fetching data for each wallet. This was vital to prevent connection errors (`Connection aborted`, `RemoteDisconnected`) and ensure requests were processed successfully.
5.  **Data Assembly:** All retrieved transaction data (JSON format) was parsed and compiled into a single Pandas DataFrame.
6.  **Robust Fallback:** A critical safeguard was implemented: if, after attempting to fetch data for all 103 wallets, no real transactions were successfully retrieved, the system would gracefully fall back to generating and using a set of **dummy transactions** for demonstration purposes. This ensures the entire scoring pipeline always has data to process.

**Result of Data Collection (Important Observation):**
Despite successfully implementing robust Etherscan fetching with delays, a total of **[YOUR ACTUAL NUMBER FROM TERMINAL, e.g., 40] real transactions** were fetched across all 103 wallets. This indicates that a large majority of the provided wallet addresses likely had no significant or discernible Compound V2 activity visible via standard Etherscan API calls, or their activity was very sparse. The system handled this by assigning default scores to inactive wallets.

## Feature Engineering: Unearthing Risk Signals

With the raw Etherscan transaction data, the next step was to transform it into meaningful features that could signal a wallet's risk. Since Etherscan's raw data doesn't provide direct "borrow" or "repay" labels (which require complex transaction decoding), I focused on features derived from general on-chain activity and interactions with Compound contracts.

**Key Features Engineered:**
--- Engineered Risk Features per Wallet (Head) ---
| wallet_address                           | num_total_transactions | num_compound_related_transactions | num_erc20_transfers | total_eth_value_in_compound_txs | total_erc20_value_in_compound_txs | num_unique_assets_involved | num_liquidations | wallet_age_days |
|:-----------------------------------------|-----------------------:|----------------------------------:|--------------------:|--------------------------------:|----------------------------------:|---------------------------:|-----------------:|----------------:|
| 0x0039f22efb07a647557c7c5d17854cfd6d489ef3 |                      6 |                                 6 |                   4 |                               0 |                         1900000 |                          2 |                0 |              22 |
| 0x4814be124d7fe3b240eb46061f7ddfab468fe122 |                     25 |                                25 |                  15 |                     73499426986 |                        10200000 |                          2 |                0 |             150 |
| 0x70d8e4ab175dfe0eab4e9a7f33e0a2d19f44001e |                      5 |                                 5 |                   3 |                       897530000 |                           70000 |                          1 |                0 |              18 |
| 0x8d900f213db5205c529aaba5d10e71a0ed2646db |                      4 |                                 4 |                   2 |                        10000000 |                             0 |                          1 |                0 |               3 |

* **`num_total_transactions`**: The overall count of all Etherscan transactions associated with the wallet. A basic measure of activity.
* **`num_compound_related_transactions`**: Specifically, the number of transactions directly involving Compound V2 contract addresses. This pinpoints direct protocol engagement.
* **`num_erc20_transfers`**: The count of ERC-20 token transfer events linked to Compound's cTokens. Useful for inferring minting or redeeming activity or collateral transfers.
* **`total_eth_value_in_compound_txs`**: The sum of ETH values transferred in normal transactions directly related to Compound contracts. Represents the scale of ETH-based interaction.
* **`total_erc20_value_in_compound_txs`**: The sum of raw token values (not USD) transferred in ERC-20 transactions related to Compound cTokens. Reflects asset movement scale.
* **`num_unique_assets_involved`**: The count of distinct `tokenSymbol`s observed in the wallet's ERC-20 transfers. Indicates diversification of assets.
* **`num_liquidations`**: This feature counts transactions explicitly labeled as 'liquidate' from **dummy data**. For real Etherscan data, precisely identifying liquidations would require advanced transaction input decoding, which was beyond the scope here. Hence, for real data, this feature typically remains zero.
* **`wallet_age_days`**: The lifespan of the wallet's activity, calculated from its earliest to latest fetched transaction timestamp. Indicates longevity and stability.

**Data Preparation Highlights:**
Before feature engineering, raw Etherscan fields like `timeStamp` and `value` were meticulously converted to numeric types and datetime objects. Missing values and potential inconsistencies were carefully handled to ensure robust calculations. Addresses were standardized to lowercase for consistent comparison.

## Risk Scoring Methodology: A Transparent Approach
Sample of final scores (showing some default scores as well):
| wallet_id                                  |   score |
|:-------------------------------------------|--------:|
| 0x4814be124d7fe3b240eb46061f7ddfab468fe122 |     800 |
| 0x0039f22efb07a647557c7c5d17854cfd6d489ef3 |     600 |
| 0x8d900f213db5205c529aaba5d10e71a0ed2646db |     576 |
| 0x70d8e4ab175dfe0eab4e9a7f33e0a2d19f44001e |     542 |
| 0x0fe383e5abc200055a7f391f94a5f5d1f844b9ae |     500 |
| 0x0aaa79f1a86bc8136cd0d1ca0d51964f4e3766f9 |     500 |
| 0x06b51c6882b27cb05e712185531c1f74996dd988 |     500 |
| 0x111c7208a7e2af345d36b6d4aace8740d61a3078 |     500 |
| 0x124853fecb522c57d9bd5c21231058696ca6d596 |     500 |
| 0x1656f1886c5ab634ac19568cd571bc72f385fdf7 |     500 |
| wallet_id                                  |   score |
|:-------------------------------------------|--------:|
| 0x06b51c6882b27cb05e712185531c1f74996dd988 |     500 |
| 0x0795732aacc448030ef374374eaae57d2965c16c |     500 |
| 0x0aaa79f1a86bc8136cd0d1ca0d51964f4e3766f9 |     500 |
| 0x0fe383e5abc200055a7f391f94a5f5d1f844b9ae |     500 |
| 0x111c7208a7e2af345d36b6d4aace8740d61a3078 |     500 |
| 0x104ae61d8d487ad689969a17807ddc338b445416 |     500 |
| 0x124853fecb522c57d9bd5c21231058696ca6d596 |     500 |
| 0x13b1c8b0e696aff8b4fee742119b549b605f3cbc |     500 |
| 0x1ab2ccad4fc97c9968ea87d4435326715be32872 |     500 |
| 0x1656f1886c5ab634ac19568cd571bc72f385fdf7 |     500 |
| wallet_id                                  |   score |
|:-------------------------------------------|--------:|
| 0x06b51c6882b27cb05e712185531c1f74996dd988 |     500 |
| 0x0795732aacc448030ef374374eaae57d2965c16c |     500 |
| 0x0aaa79f1a86bc8136cd0d1ca0d51964f4e3766f9 |     500 |
| 0x0fe383e5abc200055a7f391f94a5f5d1f844b9ae |     500 |
| 0x104ae61d8d487ad689969a17807ddc338b445416 |     500 |

--- Score Distribution Analysis (for all 100 wallets) ---
Score Distribution across ranges:
| score_range   |   count |
|:--------------|--------:|
| wallet_id                                  |   score |
|:-------------------------------------------|--------:|
| 0x06b51c6882b27cb05e712185531c1f74996dd988 |     500 |
| 0x0795732aacc448030ef374374eaae57d2965c16c |     500 |
| 0x0aaa79f1a86bc8136cd0d1ca0d51964f4e3766f9 |     500 |
| 0x0fe383e5abc200055a7f391f94a5f5d1f844b9ae |     500 |
| 0x104ae61d8d487ad689969a17807ddc338b445416 |     500 |

--- Score Distribution Analysis (for all 100 wallets) ---
Score Distribution across ranges:
| score_range   |   count |
|:--------------|--------:|
|:-------------------------------------------|--------:|
| 0x06b51c6882b27cb05e712185531c1f74996dd988 |     500 |
| 0x0795732aacc448030ef374374eaae57d2965c16c |     500 |
| 0x0aaa79f1a86bc8136cd0d1ca0d51964f4e3766f9 |     500 |
| 0x0fe383e5abc200055a7f391f94a5f5d1f844b9ae |     500 |
| 0x104ae61d8d487ad689969a17807ddc338b445416 |     500 |

--- Score Distribution Analysis (for all 100 wallets) ---
Score Distribution across ranges:
| score_range   |   count |
|:--------------|--------:|
| 0x0795732aacc448030ef374374eaae57d2965c16c |     500 |
| 0x0aaa79f1a86bc8136cd0d1ca0d51964f4e3766f9 |     500 |
| 0x0fe383e5abc200055a7f391f94a5f5d1f844b9ae |     500 |
| 0x104ae61d8d487ad689969a17807ddc338b445416 |     500 |

--- Score Distribution Analysis (for all 100 wallets) ---
Score Distribution across ranges:
| score_range   |   count |
|:--------------|--------:|
| 0x0aaa79f1a86bc8136cd0d1ca0d51964f4e3766f9 |     500
| 0x0fe383e5abc200055a7f391f94a5f5d1f844b9ae |     500 |
| 0x104ae61d8d487ad689969a17807ddc338b445416 |     500 |

--- Score Distribution Analysis (for all 100 wallets) ---
Score Distribution across ranges:
| score_range   |   count |
|:--------------|--------:|
| 0x0fe383e5abc200055a7f391f94a5f5d1f844b9ae |     500 |
| 0x104ae61d8d487ad689969a17807ddc338b445416 |     500 |



I implemented a **rule-based scoring model** to assign a risk score between 0 and 1000, where **higher scores indicate lower risk** and **lower scores indicate higher risk**. This method provides transparency and direct interpretability, aligning with the available Etherscan features.

* **Base Score**: Every wallet starts with a neutral score of **500 points**.

* **Positive Adjustments (Rewarding Lower Risk Behaviors):**
    * **Compound Engagement (`num_compound_related_transactions`) (Up to +150 points):** Wallets showing more direct interaction with Compound contracts (via normal transactions or ERC-20 transfers) receive a bonus.
    * **Wallet Longevity (`wallet_age_days`) (Up to +100 points):** Older, more established wallets are considered more stable and receive a bonus.
    * **Value of Interaction (`total_eth_value_in_compound_txs`) (Up to +100 points):** Higher total value (in ETH) involved in Compound-related transactions earn up to **100 points**, indicating more significant participation.
    * **Asset Diversity (`num_unique_assets_involved`) (Up to +50 points):** A small bonus of up to **50 points** is given for interacting with a wider variety of unique assets.

* **Negative Adjustments (Penalizing Higher Risk Behaviors):**
    * **Liquidations (`num_liquidations`) (Up to -800 points):** If a liquidation event is identified (primarily via dummy data for this Etherscan approach), it triggers a severe penalty of up to **800 points deduction**. This reflects the critical nature of such events.

**Final Score Calculation:**
All individual contributions are summed. The final score is then mathematically adjusted (clamped) to fit precisely within the **0 to 1000** range. Crucially, any wallets from the initial list of 103 for which no real transaction data could be fetched were assigned a default score of **500**, ensuring all wallets receive a score in the final output.

## Justification of Risk Indicators

The selected risk indicators, while adapted for Etherscan's raw data format, directly relate to core aspects of risk and reliability in DeFi lending:

* **Activity & Engagement:** Consistent participation (`num_total_transactions`, `num_compound_related_transactions`) suggests a user who understands and actively uses the protocol, generally implying lower risk.
* **Wallet Maturity:** An older `wallet_age_days` can indicate a long-term participant, potentially more stable than a new, fleeting address.
* **Value of Interaction:** `total_eth_value_in_compound_txs` and `total_erc20_value_in_compound_txs` quantify the economic significance of a wallet's Compound interactions. Higher value often correlates with more established or serious users.
* **Liquidations:** Despite the challenges in real-data detection via Etherscan's raw API, the principle holds: any `liquidate` event is a paramount indicator of risk, signifying a failure to manage loan health effectively. Its high penalty reflects its importance.

**Important Caveat:** It's important to acknowledge that this Etherscan-based model provides a *general* risk assessment. Without sophisticated transaction decoding (e.g., parsing `input` data using smart contract ABIs), direct Compound actions like `borrow`, `repay`, and `mint`/`redeem` cannot be precisely identified from Etherscan's standard API `txlist` or `tokentx`. Therefore, features like `net_borrow_ratio` (used in my prior Aave project) are not directly applicable here. The current approach offers a pragmatic solution given the API constraints.

## Score Distribution Overview

After generating scores for all 103 wallets, here's how the scores are distributed across predefined ranges:
Score Distribution across ranges:
| score_range   |   count |
|:--------------|--------:|
| 0-99          |       0 |
| score_range   |   count |
|:--------------|--------:|
| 0-99          |       0 |
| 0-99          |       0 |
| 100-199       |       0 |
| 200-299       |       0 |
| 300-399       |       0 |
| 100-199       |       0 |
| 200-299       |       0 |
| 300-399       |       0 |
| 400-499       |       0 |
| 300-399       |       0 |
| 400-499       |       0 |
| 400-499       |       0 |
| 500-599       |     101 |
| 600-699       |       1 |
| 500-599       |     101 |
| 500-599       |     101 |
| 500-599       |     101 |
| 500-599       |     101 |
| 600-699       |       1 |
| 700-799       |       0 |
| 800-899       |       1 |
| 500-599       |     101 |
| 600-699       |       1 |
| 700-799       |       0 |
| 800-899       |       1 |
| 500-599       |     101 |
| 600-699       |       1 |
| 700-799       |       0 |
| 800-899       |       1 |
| 500-599       |     101 |
| 600-699       |       1 |
| 700-799       |       0 |
| 800-899       |       1 |
| 600-699       |       1 |
| 700-799       |       0 |
| 800-899       |       1 |
| 700-799       |       0 |
| 800-899       |       1 |
| 800-899       |       1 |
| 900-1000      |       0 |
