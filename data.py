# Synthetic data for NimbusPay TriageBot

FAQ = [
    {"q": "Why was I charged a $2 fee?", "a": "NimbusPay charges a $2 monthly maintenance fee for accounts with a balance under $100."},
    {"q": "How do I reset my password?", "a": "Go to the login page and click 'Forgot Password'. You'll receive a reset link via email within 2 minutes."},
    {"q": "What is the refund policy?", "a": "Refunds under $50 are auto-approved. Refunds over $50 require human review and take 3-5 business days."},
    {"q": "How long do transfers take?", "a": "Domestic transfers take 1-2 business days. International transfers take 3-7 business days."},
    {"q": "What are the wire transfer fees?", "a": "Domestic wire transfers cost $15. International wire transfers cost $35."},
    {"q": "How do I close my account?", "a": "To close your account, contact support at support@nimbuspay.com or call 1-800-NIMBUS."},
    {"q": "Is my money insured?", "a": "Yes, deposits are FDIC insured up to $250,000 per depositor."},
    {"q": "How do I add a beneficiary?", "a": "Log in, go to Settings > Account > Beneficiaries, and click 'Add Beneficiary'."},
]

ACCOUNTS = {
    "4821": {"name": "Alice Johnson", "balance": 1340.50, "last_transaction": "Netflix $15.99 on 2025-06-10"},
    "3390": {"name": "Bob Smith",    "balance": 42.00,   "last_transaction": "ATM withdrawal $60 on 2025-06-08"},
    "7712": {"name": "Carol White",  "balance": 5820.00, "last_transaction": "Salary deposit $3200 on 2025-06-01"},
    "1005": {"name": "Dan Brown",    "balance": 0.00,    "last_transaction": "Account opened 2025-05-15"},
}

REFUND_CAP = 50.0  # auto-approve threshold
