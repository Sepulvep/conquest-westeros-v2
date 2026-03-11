#!/bin/bash
# Test Conquest of Westeros on your iPhone (same Wi-Fi as this Mac)

cd "$(dirname "$0")"

IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "192.168.1.1")
for PORT in 8080 8081 8082; do
  if ! lsof -i :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    break
  fi
done

URL="http://${IP}:${PORT}"

echo ""
echo "=========================================="
echo "  Conquest of Westeros - Mobile Test"
echo "=========================================="
echo ""
echo "On your phone (same Wi-Fi as this Mac):"
echo ""
echo "  1. Open Safari or Chrome"
echo "  2. Go to: $URL"
echo ""
echo "Server starting... Press Ctrl+C to stop."
echo ""

python3 -m http.server $PORT
