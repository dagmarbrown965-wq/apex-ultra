"""Risk layer: SIGNAL METADATA generation — not trading risk management.

This layer produces the descriptive contract fields stop_loss, take_profit, and
risk_percent. It is NOT order sizing, margin, leverage, or position management.
It has no access to balance, equity, or account state by design.
"""
