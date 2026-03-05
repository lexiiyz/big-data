# Big Data Pipeline for Twitter Data Scraping

## Project Overview

This project involves the development of a comprehensive big data infrastructure designed to scrape, store, process, and visualize data from X (formerly Twitter). The pipeline is orchestrated using Docker Compose and integrates several microservices to ensure scalability and reliability.

## System Architecture

The system consists of the following core components:

1. **Data Lake (MongoDB)**: Serves as the primary, unstructured raw data storage for the scraped tweets.
2. **Data Warehouse (PostgreSQL)**: Planned structured storage for processed data and reporting needs.
3. **Automation Engine (n8n)**: Acts as the orchestrator to automate workflows, data processing, and integration between services.
4. **Visualization (Metabase)**: Provides a business intelligence interface to query and create dashboards from the collected data.
5. **Twitter Scraper API**: A custom Python FastAPI microservice utilizing Playwright to asynchronously scrape tweet data based on specific queries.
6. **MongoDB GUI (Mongo Express)**: A web-based administrative interface for managing the MongoDB database instances.

## Project Structure

- `.github/workflows/deploy.yml`: Contains the CI/CD pipeline configuration for automated deployment to a VPS via SSH.
- `scraper/`: Contains the source code for the Twitter Scraper Microservice.
  - `scraper.py`: The main FastAPI application script.
  - `Dockerfile`: Container configuration for the scraper service.
  - `requirements.txt`: Python dependencies.
- `docker-compose.yml`: Defines the multi-container Docker application environment.
- `.env.example`: Template for required environment variables.

## Deployment and Setup Instructions

### Prerequisites

- Docker Engine and Docker Compose installed on the host machine.
- Git installed.

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/lexiiyz/big-data.git
   cd big-data
   ```

2. Environment Configuration:
   Create a `.env` file in the root directory and configure the necessary credentials based on the `.env.example` structure.

3. Build and Run Services:
   Execute the following command to build the images and start the containers in detached mode:
   ```bash
   docker compose up -d --build
   ```

## API Endpoints (Scraper Service)

- `POST /api/scrape`: Initiates a background scraping task. Requires a JSON payload with `query` and optional `max_tweets`.
- `GET /health`: Health check endpoint to verify service status.

## Continuous Integration / Continuous Deployment (CI/CD)

The project utilizes GitHub Actions to automate the deployment process. Upon pushing changes to the `main` branch, the pipeline automatically connects to the designated VPS via SSH, pulls the latest code, and rebuilds the `twitter_scraper` container without causing downtime to other services.
