-- ============================================================================
-- SeaBank Digital Twin v1.0 — Skema BigQuery
-- Skala 1/1000 dari bank sebenarnya (24.000 nasabah mewakili 24 juta)
-- Periode: 2025-01-01 s/d 2025-12-31
-- Kalibrasi: L1 (nyata) = rasio publik AR2025; L2 (sintetis) = perilaku granular
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 1. CUSTOMER MASTER
-- ---------------------------------------------------------------------------
CREATE OR REPLACE TABLE `seabank_twin.customers`
(
  customer_id              STRING    NOT NULL OPTIONS(description="PK. Format C000001"),
  join_date                DATE      NOT NULL OPTIONS(description="Tanggal akuisisi (kohort)"),
  tenure_months_at_2025    INT64              OPTIONS(description="Usia hubungan saat 2025-01-01"),
  acquisition_channel      STRING             OPTIONS(description="ORGANIC|SHOPEE_ECOSYSTEM|REFERRAL|AGENT_MITRA|PAYROLL|PROMO_CAMPAIGN"),
  city                     STRING,
  province                 STRING,
  age                      INT64,
  gender                   STRING             OPTIONS(description="M|F"),
  occupation               STRING,
  monthly_income_band      STRING             OPTIONS(description="<3jt|3-5jt|5-10jt|10-20jt|>20jt"),
  is_first_time_bank_user  BOOL               OPTIONS(description="Nasabah bank pertama kali (~30% per AR2025)"),
  kyc_status               STRING             OPTIONS(description="VERIFIED|PENDING|REJECTED"),
  last_txn_date_master     DATE               OPTIONS(description="Field master — LAG dari transaksi nyata (sumber DQ test 5)"),
  created_at               TIMESTAMP
)
PARTITION BY join_date
CLUSTER BY acquisition_channel, province;

-- ---------------------------------------------------------------------------
-- 2. ACCOUNTS
-- ---------------------------------------------------------------------------
CREATE OR REPLACE TABLE `seabank_twin.accounts`
(
  account_id        STRING NOT NULL OPTIONS(description="PK. Format ACC0000001"),
  customer_id       STRING NOT NULL,
  account_type      STRING NOT NULL OPTIONS(description="SAVINGS|DEPOSITO"),
  open_date         DATE,
  close_date        DATE   OPTIONS(description="NULL jika masih aktif"),
  status            STRING OPTIONS(description="ACTIVE|DORMANT|CLOSED|MATURED"),
  term_months       INT64  OPTIONS(description="Hanya DEPOSITO: 1|3|6|12"),
  interest_rate_pa  FLOAT64 OPTIONS(description="Suku bunga efektif tahunan"),
  principal         NUMERIC OPTIONS(description="Hanya DEPOSITO: nilai penempatan")
)
PARTITION BY open_date
CLUSTER BY account_type, status;

-- ---------------------------------------------------------------------------
-- 3. TRANSACTIONS (ledger)
-- ---------------------------------------------------------------------------
CREATE OR REPLACE TABLE `seabank_twin.transactions`
(
  transaction_id    STRING NOT NULL OPTIONS(description="PK. TXN + 12 digit"),
  account_id        STRING,
  customer_id       STRING,
  txn_date          DATE,
  txn_ts            TIMESTAMP,
  txn_type          STRING OPTIONS(description="SALARY_IN|TRANSFER_IN|TRANSFER_OUT|QRIS_PAYMENT|EWALLET_TOPUP|BILL_PAYMENT|CASH_WITHDRAW|INTEREST_CREDIT|ADMIN_FEE|DEPOSITO_PLACEMENT|DEPOSITO_MATURITY"),
  direction         STRING OPTIONS(description="CR|DR"),
  amount            NUMERIC OPTIONS(description="Selalu positif; arah dari kolom direction"),
  balance_after     NUMERIC,
  channel           STRING OPTIONS(description="APP|QRIS|ATM|TRANSFER"),
  merchant_category STRING OPTIONS(description="F&B|RETAIL|TRANSPORT|TELCO|UTILITY|E-COMMERCE|LAINNYA"),
  is_counterparty_missing BOOL OPTIONS(description="Anomali sengaja: rekening lawan tidak ada (orphan)")
)
PARTITION BY txn_date
CLUSTER BY account_id, txn_type;

-- ---------------------------------------------------------------------------
-- 4. MONTH-END BALANCES (untuk retensi kohort & CASA)
-- ---------------------------------------------------------------------------
CREATE OR REPLACE TABLE `seabank_twin.account_monthly_balances`
(
  account_id      STRING NOT NULL,
  month_end_date  DATE   NOT NULL,
  opening_balance NUMERIC,
  closing_balance NUMERIC,
  avg_balance     NUMERIC,
  total_credit    NUMERIC,
  total_debit     NUMERIC,
  txn_count       INT64
)
PARTITION BY month_end_date
CLUSTER BY account_id;

-- ---------------------------------------------------------------------------
-- 5. LOAN PARTNERS (mitra joint financing & channeling)
-- ---------------------------------------------------------------------------
CREATE OR REPLACE TABLE `seabank_twin.loan_partners`
(
  partner_id      STRING NOT NULL,
  partner_name    STRING,
  partner_type    STRING OPTIONS(description="MULTIFINANCE|P2P|KOPERASI"),
  scheme          STRING OPTIONS(description="JOINT_FINANCING|CHANNELING"),
  risk_tier       STRING OPTIONS(description="A|B|C|D"),
  onboard_date    DATE,
  revenue_share_pct FLOAT64 OPTIONS(description="Porsi bagi hasil untuk bank")
)
CLUSTER BY scheme, risk_tier;

-- ---------------------------------------------------------------------------
-- 6. PARTNER MONTHLY PERFORMANCE (inti analisis NPL per mitra)
-- ---------------------------------------------------------------------------
CREATE OR REPLACE TABLE `seabank_twin.partner_monthly_performance`
(
  partner_id          STRING NOT NULL,
  month               DATE   NOT NULL,
  disbursement        NUMERIC,
  outstanding_balance NUMERIC,
  npl_balance         NUMERIC  OPTIONS(description="DPD >90 hari"),
  dpd_30_balance      NUMERIC,
  npl_ratio           FLOAT64,
  active_borrowers    INT64
)
PARTITION BY month
CLUSTER BY partner_id;

-- ---------------------------------------------------------------------------
-- 7. DIRECT LOANS (customer-level: SeaBank Pinjam, payroll, KTA)
-- ---------------------------------------------------------------------------
CREATE OR REPLACE TABLE `seabank_twin.direct_loans`
(
  loan_id            STRING NOT NULL,
  customer_id        STRING,
  product            STRING OPTIONS(description="PINJAM|PAYROLL|KTA"),
  principal          NUMERIC,
  disbursed_date     DATE,
  term_months        INT64,
  interest_rate_pa   FLOAT64,
  outstanding        NUMERIC,
  dpd                INT64  OPTIONS(description="Days past due per 2025-12-31"),
  status             STRING OPTIONS(description="CURRENT|DPD30|DPD90|DEFAULT")
)
PARTITION BY disbursed_date
CLUSTER BY product, status;

-- ---------------------------------------------------------------------------
-- 8. PRODUCT RATES (riwayat suku bunga — untuk analisis elastisitas)
-- ---------------------------------------------------------------------------
CREATE OR REPLACE TABLE `seabank_twin.product_rates`
(
  product_code   STRING NOT NULL OPTIONS(description="SB_SAVINGS|SB_DEP_1M|SB_DEP_3M|SB_DEP_6M|SB_DEP_12M"),
  effective_date DATE   NOT NULL,
  end_date       DATE,
  rate_pa        FLOAT64,
  min_balance    NUMERIC,
  is_promo       BOOL,
  notes          STRING
)
CLUSTER BY product_code;

-- ---------------------------------------------------------------------------
-- 9. PROMO CAMPAIGNS
-- ---------------------------------------------------------------------------
CREATE OR REPLACE TABLE `seabank_twin.promo_campaigns`
(
  campaign_id     STRING NOT NULL,
  campaign_name   STRING,
  product_code    STRING,
  start_date      DATE,
  end_date        DATE,
  bonus_rate_bps  INT64 OPTIONS(description="Tambahan bunga dalam basis poin"),
  target_segment  STRING,
  budget_idr      NUMERIC
)
CLUSTER BY product_code;

-- ---------------------------------------------------------------------------
-- 10. INDUSTRY REFERENCE (LAPIS NYATA — jangkar eksternal)
-- ---------------------------------------------------------------------------
CREATE OR REPLACE TABLE `seabank_twin.ref_industry_benchmark`
(
  entity          STRING  OPTIONS(description="SEABANK|INDUSTRY_14_DIGITAL_BANKS"),
  period          STRING  OPTIONS(description="FY2025|Q3_2026"),
  metric          STRING  OPTIONS(description="loans_idr_bn|dpk_idr_bn|ldr_pct|casa_pct|npl_gross_pct|nim_pct|bopo_pct|car_pct"),
  value           FLOAT64,
  source          STRING,
  source_date     DATE
)
CLUSTER BY entity, metric;

-- ============================================================================
-- VIEW ANALITIK — definisi resmi metrik (bagian dari metric trust layer)
-- ============================================================================

CREATE OR REPLACE VIEW `seabank_twin.vw_casa_monthly` AS
SELECT
  month_end_date,
  SUM(CASE WHEN a.account_type = 'SAVINGS' THEN b.closing_balance ELSE 0 END) AS casa_balance,
  SUM(CASE WHEN a.account_type = 'DEPOSITO' THEN b.closing_balance ELSE 0 END) AS deposito_balance,
  SUM(b.closing_balance) AS total_dpk,
  SAFE_DIVIDE(SUM(CASE WHEN a.account_type = 'SAVINGS' THEN b.closing_balance ELSE 0 END),
              SUM(b.closing_balance)) AS casa_ratio
FROM `seabank_twin.account_monthly_balances` b
JOIN `seabank_twin.accounts` a USING (account_id)
GROUP BY month_end_date;

CREATE OR REPLACE VIEW `seabank_twin.vw_partner_risk` AS
SELECT
  p.partner_id, p.partner_name, p.partner_type, p.scheme, p.risk_tier,
  m.month, m.outstanding_balance, m.npl_balance, m.npl_ratio, m.disbursement,
  SAFE_DIVIDE(m.outstanding_balance, SUM(m.outstanding_balance) OVER (PARTITION BY m.month)) AS share_of_book
FROM `seabank_twin.partner_monthly_performance` m
JOIN `seabank_twin.loan_partners` p USING (partner_id);
