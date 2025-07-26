# Compound V2 Wallet Risk Scoring: Methodology and Analysis

## 1. Data Collection Method

To assess wallet risk, transaction history for each provided wallet address was retrieved from the **Etherscan API**. This method was chosen to ensure reliable data fetching given the challenges with direct subgraph queries.

* **Source:** The **Etherscan API** (`https://api.etherscan.io/api`) was utilized as the primary data source. This API provides access to raw blockchain transaction data on the Ethereum Mainnet. A personal Etherscan API key was used for authentication and to adhere to API rate limits.
* **Process:**
    1.  A list of 103 target `wallet_id`s was loaded from `Wallet id.xlsx - Sheet1.csv`.
    2.  For each wallet, two types of transactions were fetched from Etherscan:
        * **Normal Transactions (`txlist` action):** These represent direct contract interactions (e.g., calls to Compound's main Comptroller contract or cToken contracts). Transactions where the `to` or `from` address matched a known Compound V2 contract (Comptroller or major cTokens) were filtered and collected.
        * **ERC-20 Token Transfers (`tokentx` action):** These represent movements of specific tokens (like cTokens) to or from the wallet address. Queries were made for common Compound cToken addresses (e.g., cUSDC, cDAI, cETH).
    3.  The `requests` Python library was used to send GET requests to the Etherscan API endpoint.
    4.  Robust error handling was implemented to manage network issues (`ConnectionResetError`, `RemoteDisconnected`) and API responses (e.g., 'No transactions found').
    5.  A significant delay of **5 seconds** was incorporated between fetching data for each wallet to strictly adhere to Etherscan's free-tier rate limits (typically 5 calls per second, but a longer delay between wallets is safer due to multiple calls per wallet).
    6.  Retrieved data (JSON format) was parsed and converted into a flat Pandas DataFrame (`all_transactions_df`) for subsequent processing.
    7.  **Fallback Mechanism:** If, after attempting to fetch data for all 103 wallets, no real transactions were retrieved (e.g., `Total real transactions fetched: 0`), a set of **dummy transactions** was generated and used instead, ensuring the scoring pipeline could still run for demonstration purposes.

## 2. Feature Selection Rationale
--- Engineered Risk Features per Wallet (Head) ---
| wallet_address                           | num_total_transactions | num_compound_related_transactions | num_erc20_transfers | total_eth_value_in_compound_txs | total_erc20_value_in_compound_txs | num_unique_assets_involved | num_liquidations | wallet_age_days |
|:-----------------------------------------|-----------------------:|----------------------------------:|--------------------:|--------------------------------:|----------------------------------:|---------------------------:|-----------------:|----------------:|
| 0x0039f22efb07a647557c7c5d17854cfd6d489ef3 |                      6 |                                 6 |                   4 |                               0 |                         1900000 |                          2 |                0 |              22 |
| 0x4814be124d7fe3b240eb46061f7ddfab468fe122 |                     25 |                                25 |                  15 |                     73499426986 |                        10200000 |                          2 |                0 |             150 |
| 0x70d8e4ab175dfe0eab4e9a7f33e0a2d19f44001e |                      5 |                                 5 |                   3 |                       897530000 |                           70000 |                          1 |                0 |              18 |
| 0x8d900f213db5205c529aaba5d10e71a0ed2646db |                      4 |                                 4 |                   2 |                        10000000 |                             0 |                          1 |                0 |               3 |

Given that Etherscan provides more raw transaction data (without readily available direct "borrow," "repay," or "liquidate" labels without complex decoding), the feature engineering was adapted to leverage the data available. The following features were derived to reflect wallet activity and potential risk within the Compound V2 ecosystem:

* **`num_total_transactions`**: Total count of all Etherscan transactions (normal and ERC-20 transfers) fetched for the wallet. *Rationale: Indicates overall activity level.*
* **`num_compound_related_transactions`**: Count of transactions where the wallet interacted with known Compound V2 contract addresses (Comptroller or cTokens). *Rationale: Focuses on direct engagement with the Compound protocol.*
* **`num_erc20_transfers`**: Count of ERC-20 token transfers related to Compound cTokens. *Rationale: Captures minting/redeeming activity or transfers of collateral tokens.*
* **`total_eth_value_in_compound_txs`**: Sum of the `value` field (in Wei, typically ETH value) for normal transactions related to Compound contracts. *Rationale: Quantifies the total ETH (or wrapped ETH) value involved in direct Compound interactions.*
* **`total_erc20_value_in_compound_txs`**: Sum of the `value` field (raw token units, not USD) for ERC-20 transfers related to Compound cTokens. *Rationale: Quantifies the total value of ERC-20 tokens moved in/out of Compound via cTokens.*
* **`num_unique_assets_involved`**: Count of distinct `tokenSymbol`s involved in ERC-20 transfers. *Rationale: Diversity of assets traded could indicate broader engagement.*
* **`num_liquidations`**: This feature counts transactions explicitly labeled as 'liquidate' from **dummy data**. *Rationale: For real Etherscan data, identifying liquidations accurately requires complex transaction input decoding against Compound's ABI, which is outside the scope of this "easy way" assignment. Thus, for real data, this feature will largely be zero unless manually identified.*
* **`wallet_age_days`**: The duration in days between the wallet's earliest and latest fetched transaction timestamp. *Rationale: Indicates stability and longevity of presence on-chain.*

**Data Preprocessing:**
* `timeStamp` and `value` fields from Etherscan were converted to numeric types (`timeStamp_numeric`, `value_numeric`).
* `tokenDecimal` was converted to numeric, with missing values filled with `0`.
* `timeStamp_numeric` was converted to `datetime` objects (`timestamp_dt`).
* Missing numeric values were filled with `0`.
* `from` and `to` addresses were converted to lowercase for consistent comparison with contract addresses.
* `action_etherscan_category` was handled (created during fetching, used for filtering).

## 3. Risk Scoring Method
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
| 0x0aaa79f1a86bc8136cd0d1ca0d51964f4e3766f9 |     500 |
| 0x0fe383e5abc200055a7f391f94a5f5d1f844b9ae |     500 |
| 0x104ae61d8d487ad689969a17807ddc338b445416 |     500 |

--- Score Distribution Analysis (for all 100 wallets) ---
Score Distribution across ranges:
| score_range   |   count |
|:--------------|--------:|
| 0x0fe383e5abc200055a7f391f94a5f5d1f844b9ae |     500 |
| 0x104ae61d8d487ad689969a17807ddc338b445416 |     500 |


A **rule-based scoring model** was implemented to assign a risk score between 0 and 1000, where **higher scores indicate lower risk** and **lower scores indicate higher risk**. This method provides transparency and direct interpretability, aligning with the available Etherscan features.

* **Base Score**: Each wallet starts with a score of **500 points**.

* **Positive Score Adjustments (indicating lower risk):**
    * **Compound-Related Activity (`num_compound_related_transactions`) (Up to +150 points):** Wallets with more direct interactions (normal transactions or ERC-20 transfers) with Compound contracts receive a bonus.
    * **Wallet Age (`wallet_age_days`) (Up to +100 points):** Older, more established wallets are considered more stable and receive a bonus.
    * **Value Transferred (`total_eth_value_in_compound_txs`) (Up to +100 points):** Higher total value (in ETH) involved in Compound-related transactions receives a bonus, reflecting significant engagement.
    * **Unique Assets (`num_unique_assets_involved`) (Up to +50 points):** Wallets interacting with a wider variety of assets may receive a small bonus, indicating broader engagement.

* **Negative Score Adjustments (indicating higher risk):**
    * **Liquidations (`num_liquidations`) (Up to -800 points):** This is the strongest penalty. If any 'liquidate' actions are detected (primarily from dummy data, as real Etherscan data requires complex parsing), they severely reduce the score. This penalty is high to reflect the critical nature of liquidations.

* **Normalization and Clamping:** Feature contributions are normalized relative to their maximum observed values in the dataset to ensure fair weighting. The final sum is then **clamped between 0 and 1000** to fit the required score range. Wallets for which no real transactions were fetched are assigned a default score of **500**.

## 4. Justification of Risk Indicators Used

The chosen risk indicators are pragmatic adaptations given the Etherscan API's raw data, focusing on observable activity patterns:

* **General Activity (`num_total_transactions`, `num_compound_related_transactions`, `num_erc20_transfers`):** A consistent presence and interaction with Compound contracts suggests a more engaged and potentially responsible user.
* **Wallet Age (`wallet_age_days`):** Longevity in the ecosystem can imply stability and experience, making older wallets less likely to be flash-in-the-pan exploiters (though not foolproof).
* **Value Transferred (`total_eth_value_in_compound_txs`, `total_erc20_value_in_compound_txs`):** Higher values transacted in Compound-related activities indicate a more significant user. While not directly "borrow" or "repay" volume, it reflects the scale of their interaction.
* **Liquidations (`num_liquidations`):** Despite the difficulty in extracting this from raw Etherscan, the principle remains: any detected liquidation is a severe negative signal, reflecting failure to manage collateral. Its high penalty reflects its importance.
* **Compromise Acknowledgment:** It's important to note that without advanced transaction decoding (e.g., parsing `input` data using smart contract ABIs), direct Compound actions like `borrow`, `repay`, `mint`, and `redeem` cannot be precisely identified from Etherscan's standard API `txlist` or `tokentx`. Therefore, features like `net_borrow_ratio` from the Aave assignment cannot be directly applied here. The current features provide a more general risk assessment based on observable on-chain movements.

## 5. Score Distribution Analysis

After scoring all 103 wallets, the distribution of scores across ranges provides insights into the overall risk profile of the sampled wallets.

Score Distribution across ranges:
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