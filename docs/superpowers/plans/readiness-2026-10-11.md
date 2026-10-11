BACKEND=DOWN
SIMULATOR=DOWN
ENDPOINTS: /health, /health-score, /insights, /anomalies, /bottlenecks, /ai/explain, /ai/status
WIRING: live where reachable, typed fallbacks otherwise; Simulator/AI pages always handle DOWN.
