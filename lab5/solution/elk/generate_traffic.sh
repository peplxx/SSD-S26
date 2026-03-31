#!/usr/bin/env bash
# Generate HTTP traffic against the Nginx container so that Filebeat
# has log data to ship into Elasticsearch.
#
# Run this after: docker compose up -d
set -euo pipefail

NGINX_URL="${1:-http://localhost:8081}"
REQUESTS="${2:-100}"

echo "Sending $REQUESTS requests to $NGINX_URL ..."

for i in $(seq 1 "$REQUESTS"); do
    path="/"
    case $(( i % 5 )) in
        0) path="/health"  ;;
        1) path="/missing" ;;   # triggers 404 / error log
        2) path="/admin"   ;;   # 404
        *) path="/"        ;;
    esac
    curl -s -o /dev/null "$NGINX_URL$path"
    sleep 0.05
done

echo "Done. Check Kibana -> Discover -> filebeat-nginx-* for log entries."
