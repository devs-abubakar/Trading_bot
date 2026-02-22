import sqlite3
import pandas as pd
import os
import json
import time
import winsound

class TradingBot:
    def __init__(self):
        # 1. SETUP - Everything belongs to 'self' now
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.db_path = os.path.join(self.script_dir, "Crypto_history.db")
        self.json_path = os.path.join(self.script_dir, "state.json")
        self.log_path = os.path.join(self.script_dir, "trade_history.csv")

        # 2. LOAD STATE
        state = self.load_state()
        self.balance_usd = state["balance_usd"]
        self.pos_btc = state["btc_pos"]
        self.buy_price = state["buy_price"]

    def load_state(self):
        if os.path.exists(self.json_path):
            try:
                with open(self.json_path, "r") as f:
                    return json.load(f)
            except Exception:
                print("Corrupted state file. Resetting...")
        return {"balance_usd": 1000, "btc_pos": 0, "buy_price": 0}

    def save_state(self):
        """No need to pass arguments. It saves the CURRENT self state."""
        state_data = {
            "balance_usd": self.balance_usd,
            "btc_pos": self.pos_btc,
            "buy_price": self.buy_price
        }
        with open(self.json_path, "w") as f:
            json.dump(state_data, f, indent=4)
            print(f"DEBUG: Saved -> Cash: ${self.balance_usd:.2f}, BTC: {self.pos_btc:.6f}")

    def log_trade(self, action, price, amount, pnl=0):
        new_entry = {
            "timestamp": pd.Timestamp.now(),
            "action": action,
            "price": price,
            "amount": amount,
            "balance": self.balance_usd,
            "pnl_pct": pnl
        }
        log_df = pd.DataFrame([new_entry])
        file_exists = os.path.isfile(self.log_path)
        log_df.to_csv(self.log_path, mode='a', index=False, header=not file_exists)

    def run_monitor(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        try:
            # 1. FETCH DATA
            with sqlite3.connect(self.db_path) as conn:
                df = pd.read_sql_query("SELECT * FROM Crypto_history", conn)
            
            df["time_stamp"] = pd.to_datetime(df["time_stamp"])
            recent = df[df["time_stamp"] > (pd.Timestamp.now() - pd.Timedelta(minutes=30))]

            if not recent.empty:
                pivot = recent.pivot_table(index="time_stamp", columns="coin", values="price", aggfunc="mean")
                if len(pivot) >= 20:
                    # 2. FEATURE ENGINEERING
                    pivot["SMA_20"] = pivot["Bitcoin"].rolling(window=20).mean()
                    pivot["STD"] = pivot["Bitcoin"].rolling(window=20).std()
                    upper = pivot["SMA_20"].iloc[-1] + (pivot["STD"].iloc[-1] * 2)
                    lower = pivot["SMA_20"].iloc[-1] - (pivot["STD"].iloc[-1] * 2)
                    curr_price = pivot["Bitcoin"].iloc[-1]

                    # 3. DASHBOARD
                    total_equity = self.balance_usd + (self.pos_btc * curr_price)
                    print(f"NET WORTH: ${total_equity:.2f} | CASH: ${self.balance_usd:.2f} | BTC: {self.pos_btc:.6f}")

                    # 4. TRADING LOGIC
                    # Stop Loss
                    if self.pos_btc > 0:
                        change_pct = ((curr_price - self.buy_price) / self.buy_price) * 100
                        if change_pct <= -1.7:
                            self.balance_usd = self.pos_btc * curr_price
                            self.log_trade("STOP LOSS", curr_price, self.pos_btc, change_pct)
                            self.pos_btc = 0
                            self.buy_price = 0
                            self.save_state()
                            return

                    # Sell (Upper Band)
                    if curr_price >= upper and self.pos_btc > 0:
                        profit_pct = ((curr_price - self.buy_price) / self.buy_price) * 100
                        self.balance_usd = self.pos_btc * curr_price
                        self.log_trade("SELL", curr_price, self.pos_btc, profit_pct)
                        self.pos_btc = 0
                        self.buy_price = 0
                        self.save_state()
                        winsound.Beep(1200, 800)

                    # Buy (Lower Band)
                    elif curr_price <= lower and self.balance_usd > 0:
                        self.pos_btc = self.balance_usd / curr_price
                        self.buy_price = curr_price
                        self.balance_usd = 0
                        self.log_trade("BUY", curr_price, self.pos_btc, 0.0)
                        self.save_state()
                        winsound.Beep(1000, 700)

        except Exception as e:
            print(f"System Error: {e}")

# --- EXECUTION ---
if __name__ == "__main__":
    bot = TradingBot()
    while True:
        bot.run_monitor()
        time.sleep(10)