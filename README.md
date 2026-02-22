# Trading_bot
Crypto Paper Trader &amp; Scraper A lightweight, modular Python system for real-time cryptocurrency data collection and risk-free paper trading. This project allows you to simulate BTC and ETH trades using live market data without risking real capital

# Bollinger Band Crypto Trading Bot 🚀

An automated Python-based trading system using **OOP (Object-Oriented Programming)** to track prices via SQLite and execute trades based on Bollinger Band volatility.

## Features
- **Price Scraper:** Real-time data fetching from CoinGecko API.
- **SQLite Integration:** Efficient data logging and deduplication.
- **Bollinger Band Logic:** Automated Buy/Sell signals based on STD deviations.
- **State Persistence:** JSON-based recovery so the bot never forgets its balance.

## Setup
1. Clone the repo.
2. Install dependencies: `pip install -r requirements.txt`
3. Run `scraper.py` to fill the database.
4. Run `main_bot.py` to start trading.
