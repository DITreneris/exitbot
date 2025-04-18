#!/bin/bash

# Script to set up basic monitoring for ExitBot application
echo "Setting up monitoring for ExitBot..."

# Configuration
LOG_DIR="../logs"
PROMETHEUS_DIR="../monitoring/prometheus"
GRAFANA_DIR="../monitoring/grafana"

# Create necessary directories
mkdir -p ${LOG_DIR}
mkdir -p ${PROMETHEUS_DIR}/config
mkdir -p ${GRAFANA_DIR}/dashboards
mkdir -p ${GRAFANA_DIR}/datasources

# Generate Prometheus configuration
cat > ${PROMETHEUS_DIR}/config/prometheus.yml << EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'exitbot_api'
    metrics_path: '/api/metrics'
    static_configs:
      - targets: ['api:8000']

  - job_name: 'exitbot_frontend'
    metrics_path: '/metrics'
    static_configs:
      - targets: ['frontend:3000']

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']

  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
EOF

# Generate Grafana datasource configuration
cat > ${GRAFANA_DIR}/datasources/prometheus.yml << EOF
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
EOF

# Generate sample dashboard
cat > ${GRAFANA_DIR}/dashboards/exitbot_dashboard.json << EOF
{
  "annotations": {
    "list": []
  },
  "editable": true,
  "fiscalYearStartMonth": 0,
  "graphTooltip": 0,
  "id": 1,
  "links": [],
  "liveNow": false,
  "panels": [
    {
      "datasource": {
        "type": "prometheus",
        "uid": "prometheus"
      },
      "description": "API Request Rate",
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "palette-classic"
          },
          "custom": {
            "axisCenteredZero": false,
            "axisColorMode": "text",
            "axisLabel": "",
            "axisPlacement": "auto",
            "barAlignment": 0,
            "drawStyle": "line",
            "fillOpacity": 10,
            "gradientMode": "none",
            "hideFrom": {
              "legend": false,
              "tooltip": false,
              "viz": false
            },
            "lineInterpolation": "smooth",
            "lineWidth": 2,
            "pointSize": 5,
            "scaleDistribution": {
              "type": "linear"
            },
            "showPoints": "never",
            "spanNulls": false,
            "stacking": {
              "group": "A",
              "mode": "none"
            },
            "thresholdsStyle": {
              "mode": "off"
            }
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              },
              {
                "color": "red",
                "value": 80
              }
            ]
          },
          "unit": "reqps"
        },
        "overrides": []
      },
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 0,
        "y": 0
      },
      "id": 1,
      "options": {
        "legend": {
          "calcs": [],
          "displayMode": "list",
          "placement": "bottom",
          "showLegend": true
        },
        "tooltip": {
          "mode": "single",
          "sort": "none"
        }
      },
      "targets": [
        {
          "datasource": {
            "type": "prometheus",
            "uid": "prometheus"
          },
          "expr": "rate(http_requests_total[1m])",
          "refId": "A"
        }
      ],
      "title": "API Request Rate",
      "type": "timeseries"
    }
  ],
  "refresh": "5s",
  "schemaVersion": 38,
  "style": "dark",
  "tags": [],
  "templating": {
    "list": []
  },
  "time": {
    "from": "now-1h",
    "to": "now"
  },
  "timepicker": {},
  "timezone": "",
  "title": "ExitBot Dashboard",
  "uid": "exitbot",
  "version": 1,
  "weekStart": ""
}
EOF

# Create docker-compose file for monitoring
cat > ../docker-compose.monitoring.yml << EOF
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: exitbot_prometheus
    volumes:
      - ./monitoring/prometheus/config:/etc/prometheus
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
    ports:
      - "9090:9090"
    restart: unless-stopped
    networks:
      - monitoring
      - exitbot-network
  
  grafana:
    image: grafana/grafana:latest
    container_name: exitbot_grafana
    volumes:
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - grafana_data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=exitbot_admin
      - GF_USERS_ALLOW_SIGN_UP=false
    ports:
      - "3001:3000"
    restart: unless-stopped
    networks:
      - monitoring
      - exitbot-network
  
  node-exporter:
    image: prom/node-exporter:latest
    container_name: exitbot_node_exporter
    restart: unless-stopped
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.rootfs=/rootfs'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
    ports:
      - "9100:9100"
    networks:
      - monitoring

volumes:
  prometheus_data:
  grafana_data:

networks:
  monitoring:
  exitbot-network:
    external: true
EOF

# Create a basic logging configuration
cat > ../app/core/logging_config.py << EOF
import logging
import os
from logging.handlers import RotatingFileHandler

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

def setup_logging(app_name="exitbot"):
    """Configure application logging"""
    
    # Create logs directory if it doesn't exist
    os.makedirs(LOG_DIR, exist_ok=True)
    
    # Set up root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, LOG_LEVEL))
    
    # Clear existing handlers
    logger.handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(console_handler)
    
    # File handler - rotating file handler to prevent large log files
    file_handler = RotatingFileHandler(
        os.path.join(LOG_DIR, f"{app_name}.log"),
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(file_handler)
    
    # Add separate error log
    error_handler = RotatingFileHandler(
        os.path.join(LOG_DIR, f"{app_name}_error.log"),
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(error_handler)
    
    # Disable propagation for third-party loggers to avoid double logging
    logging.getLogger("uvicorn").propagate = False
    logging.getLogger("uvicorn.access").propagate = False
    
    return logger
EOF

echo "Monitoring setup complete!"
echo "You can start the monitoring stack with:"
echo "  docker-compose -f docker-compose.monitoring.yml up -d"
echo
echo "Grafana will be available at: http://localhost:3001"
echo "Prometheus will be available at: http://localhost:9090"
echo "Default Grafana credentials: admin / exitbot_admin" 