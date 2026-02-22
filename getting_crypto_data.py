import sqlite3
import requests
import time
from datetime import datetime
import os

class CryptoBot:
    def __init__(self):
        # Persistent state: The bot needs these as long as it lives
        self.url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd"
        self.headers = {'User-Agent': 'Mozilla/5.0'}
        self.db_path = os.path.join(os.path.dirname(__file__), "Crypto_history.db")
        self.btc_price = None
        self.eth_price = None

    def fetch_and_save(self):
        try:
            req = requests.get(self.url, headers=self.headers)
            if req.status_code == 200:
                data = req.json() # Local: We only need this right now
                
                # Update class state (The "Bank Book")
                self.btc_price = data.get("bitcoin", {}).get("usd")
                self.eth_price = data.get("ethereum", {}).get("usd")
                
                # Local variable: Just for this specific DB entry
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                if self.btc_price and self.eth_price:
                    # connection/cursor are TOOLS. Keep them local.
                    with sqlite3.connect(self.db_path) as conn:
                        cursor = conn.cursor()
                        cursor.execute("CREATE TABLE IF NOT EXISTS crypto_history(id INTEGER PRIMARY KEY AUTOINCREMENT, coin TEXT, price REAL, time_stamp TEXT)")
                        
                        entries = [("Bitcoin", self.btc_price, current_time), 
                                   ("Ethereum", self.eth_price, current_time)]
                        
                        cursor.executemany("INSERT INTO crypto_history(coin, price, time_stamp) VALUES(?,?,?)", entries)
                        conn.commit()
                    print(f" [{current_time}] BTC: ${self.btc_price}")
                else:
                    print(" Data missing in response")
            else:
                print(f" HTTP Error {req.status_code}")

        except Exception as e:
            print(f" Error: {e}")

    def start_scraping(self):
        print("Scraper Online.")
        while True:
            self.fetch_and_save()
            time.sleep(60)

if __name__ == "__main__":
    bot = CryptoBot()
    bot.start_scraping()