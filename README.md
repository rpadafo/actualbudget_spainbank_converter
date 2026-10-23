# Actual Budget: Spain Bank Converter CSV

![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)
![Build Status](https://img.shields.io/github/actions/workflow/status/rpadafo/bank_documents_to_csv/docker-publish.yml?branch=main&style=for-the-badge&logo=github)

Automated background service to convert Excel, TXT, and PDF statements from Spanish banks into CSV files, and to copy supported CSV exports unchanged, for seamless import into **[Actual Budget](https://actualbudget.org/)**.

---

> [!IMPORTANT]
> **Prerequisites:**
> * An instance of **Actual Budget** running.
> * **Docker** and **Docker Compose** installed.
> * Dedicated host folders for `/input` (source documents) and `/output` (generated CSV files).

---

## 🚀 Features

* **Automated Processing:** Monitors the `/input` directory and converts files in real time.
* **Smart Bank Detection:** Automatically routes files to the correct processor based on file names and structures.
* **Auto-Cleanup:** Deletes processed source files and automatically removes old CSVs after a configurable retention period.
* **Spanish Formatting Ready:** Properly formats dates, numbers (commas for decimals), and UTF-8 encoding.

### 🏦 Supported Banks

| Bank | Source Format | Output Prefix |
| :--- | :--- | :--- |
| **Bankinter** | `.xlsx` / `.xls` | `BK_*.csv` |
| **CaixaBank** | `.xlsx` / `.xls` | `LC_*.csv` |
| **Banco Santander** | `.xlsx` / `.xls` | `SA_*.csv` |
| **Banco Sabadell** | `.txt` | `BS_*.csv` |
| **Trade Republic** | `Exportación de transacción.csv` | `TR_*.csv` |
| **SumUp** | `SumUp*.pdf` | `SUM_*.csv` |

---

## 🛠️ Deployment & Usage

Use the following `docker-compose.yml` snippet to deploy the container:

```yaml
services:
  actualbudget_spainbank_converter:
    image: ghcr.io/rpadafo/actualbudget_spainbank_converter:latest
    container_name: actualbudget-spainbank-converter
    restart: unless-stopped
    environment:
      - RETENTION_HOUR=12 # Retention time in hours before auto-deleting CSV files
      - PREFIX_BANKINTER=BANK
      - PREFIX_CAIXA=CAIX
      - PREFIX_SABADELL=SABA
      - PREFIX_SANTANDER=SANT
      - PREFIX_TRADEREPUBLIC=TR
      - PREFIX_SUMUP=SUM
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 100M
    volumes:
      - /path/to/your/input:/input
      - /path/to/your/output:/output
#Optional >>
    networks:
        lan:
            ipv4_address: 192.168.x.x
            mac_address: "02:42:C0:xx:xx:xx"
    dns:
            - 8.8.8.8
networks:
    lan:
        external: true
#Optional <<