# KQL Queries for Kibana – Lab 5 Task 2

## Integration 1 – Nginx Logs (index: `filebeat-nginx-*`)

### 1. All Nginx access log events
```kql
event.module: "nginx" AND event.dataset: "nginx.access"
```

### 2. All HTTP 4xx errors (client errors)
```kql
event.dataset: "nginx.access" AND http.response.status_code >= 400 AND http.response.status_code < 500
```

### 3. All HTTP 5xx errors (server errors)
```kql
event.dataset: "nginx.access" AND http.response.status_code >= 500
```

### 4. Requests by specific client IP
```kql
event.dataset: "nginx.access" AND source.ip: "192.168.1.100"
```

### 5. Top requested URLs (use in TSVB/Lens bar chart)
```kql
event.dataset: "nginx.access" AND url.path: *
```

### 6. Nginx error log entries (warning or above)
```kql
event.dataset: "nginx.error" AND log.level: ("warn" OR "error" OR "crit")
```

---

## Integration 2 – Docker Container Logs (index: `filebeat-docker-*`)

### 7. All Docker container log events
```kql
event.module: "docker"
```

### 8. Logs from a specific container by name
```kql
container.name: "nginx-demo"
```

### 9. Docker logs containing errors
```kql
event.module: "docker" AND message: "error"
```

### 10. Logs from multiple containers
```kql
container.name: ("elasticsearch" OR "kibana" OR "filebeat")
```

### 11. Docker logs in the last 15 minutes
> Use the Kibana time picker: "Last 15 minutes"
```kql
event.module: "docker"
```

---

## Dashboard Panels (Kibana Lens)

### Panel 1 – HTTP Status Code Distribution (Nginx)
- Type: **Donut chart**
- Index: `filebeat-nginx-*`
- Slice by: `http.response.status_code` (Top 10)
- KQL filter: `event.dataset: "nginx.access"`

### Panel 2 – Nginx Requests Over Time
- Type: **Bar chart / Area chart**
- Index: `filebeat-nginx-*`
- X-axis: `@timestamp` (Date histogram, auto)
- Y-axis: Count of records
- KQL filter: `event.dataset: "nginx.access"`

### Panel 3 – Top Requested Paths
- Type: **Data table**
- Index: `filebeat-nginx-*`
- Group by: `url.path` (Top 10)
- Metric: Count
- KQL filter: `event.dataset: "nginx.access"`

### Panel 4 – Docker Containers Log Volume
- Type: **Bar chart**
- Index: `filebeat-docker-*`
- X-axis: `@timestamp` (Date histogram)
- Break down by: `container.name`
- KQL filter: `event.module: "docker"`
