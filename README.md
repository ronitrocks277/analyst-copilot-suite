# Analyst Co-Pilot Portal 🚀

A prototype portal built for analysts to automate stock research, evaluate material catalysts, and generate high-conviction trading signals using an agentic LLM approach.

## 🌟 Key Features

* **Automated Data Ingestion:** Triggers live queries for stock tickers (e.g., RELIANCE, HDFC).
* **Live Price Action & Moving Averages:** Visualizes the last 30 days of price action against rolling benchmarks via Recharts.
* **Agentic AI Brain:** Powered by Claude 3.5 Sonnet to execute catalyst checks, gauge relative strength, and output a Signal Score (1-10) with rigid JSON-mapped reasoning.
* **Analyst Workflows:** Built-in dashboard interactions allowing analysts to "Approve" and simulated POST hooks to "Post to App".

---

## 🏗️ System Architecture

### Frontend
* **Framework:** React.js
* **Visualizations:** Recharts for smooth, interactive financial data plotting.
* **UX/UI:** Clean, dark-themed fintech grid displaying signal cards, sentiment checks, and news feeds.

### Backend
* **Framework:** Python (Flask)
* **Market Data APIs:** Yahoo Finance wrapper for automated price and moving average queries.
* **Orchestration:** Custom agentic prompting using the official Anthropic Claude Python SDK.

---

## 💡 Engineering Solutions for Real-World Constraints

### 1. Handling API Latency
Fetching massive financial data payloads and passing them through an LLM sequence naturally incurs a slight processing lag. 
* **Solution:** I implemented smooth, async loading states on the React frontend to preserve a flawless UI experience and aggressively optimized backend processing by strictly limiting output token counts on the prompt completions.

### 2. Preventing AI Hallucinations
Generative LLMs are prone to guessing numerical metrics when handling hard financial computations.
* **Solution:** I structured the backend to execute all mathematical relative strength calculations and data scraping *before* passing execution control to Claude. By injecting the raw, truthful parsed data directly into a hard-coded prompt cage and forcing a rigid JSON schema response, the agent acts strictly as a reasoning logic engine rather than a generator.

### 3. Yahoo Finance Rate Limits & Fallbacks
Public APIs are highly susceptible to request blocking and strict rate-limiting.
* **Solution:** I built a fallback mechanism at the API layer. In the event of a rate-limit lockout or failure, the backend gracefully loads mapped localized data structures for standard stock tickers. This keeps the application fully usable for testing under edge-case downtime.

---
