#!/usr/bin/env bash
# test_phase1.sh — run Phase 1 completely

PORT=8000

# ❶ start server in background
uvicorn main:app --port $PORT --log-level error &
PID=$!
sleep 2                       # give uvicorn time to start

# ❷ send the 5 continue pings
for i in {1..5}; do
  curl -s -X POST http://127.0.0.1:$PORT/coder \
       -H 'Content-Type: application/json' \
       -d '{"continue":true}'
done
echo                          # add newline after curl spam

# ❸ shut server down
kill $PID