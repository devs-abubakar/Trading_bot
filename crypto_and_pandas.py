import pandas as pd
import sqlite3
import os
import json
import winsound

class TradingBot:
    def __init__(self):
        # 1. SETUP PATHS
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.db_path = os.path.join(self.script_dir, "Crypto_history.db")
        self.state_path = os.path.join(self.script_dir, "state.json")
        self.log_path = os.path.join(self.script_dir, "trade_history.csv")
        
        # 2. FIXED PARAMETERS
        self.fee_rate = 0.001  # 0.1% transaction fee
        self.load_state()

    def load_state(self):
        if os.path.exists(self.state_path):
            with open(self.state_path, "r") as f:
                state = json.load(f)
                self.balance_usd = state.get("balance_usd", 1000.0)
                self.pos_btc = state.get("pos_btc", 0.0)
                self.buy_price = state.get("buy_price", 0.0)
        else:
            self.balance_usd, self.pos_btc, self.buy_price = 1000.0, 0.0, 0.0

    def save_state(self):
        with open(self.state_path, "w") as f:
            json.dump({
                "balance_usd": self.balance_usd,
                "pos_btc": self.pos_btc,
                "buy_price": self.buy_price
            }, f)

    def log_trade(self, action, price, amount, pnl):
        df_log = pd.DataFrame([{
            "time": pd.Timestamp.now(),
            "action": action,
            "price": price,
            "amount": amount,
            "pnl_pct": pnl
        }])
        header = not os.path.exists(self.log_path)
        df_log.to_csv(self.log_path, mode='a', index=False, header=header)

    def fetch_data(self):
        """Worker 1: Database & Cleaning"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                df = pd.read_sql_query("SELECT * FROM Crypto_history", conn)
            
            df["time_stamp"] = pd.to_datetime(df["time_stamp"])
            cutoff = pd.Timestamp.now() - pd.Timedelta(minutes=60) # Increased window for RSI math
            recent = df[df["time_stamp"] > cutoff].copy()
            print(f"I found {len(recent)} rows of data.")

            if not recent.empty:
                return recent.pivot_table(index="time_stamp", columns="coin", values="price", aggfunc="mean")
            return None
        except Exception as e:
            print(f"Error fetching data: {e}")
            return None

    def calculate_indicators(self, pivot):
        """Worker 2: The Math Lab (Bollinger + RSI)"""
        print(f"I recieved {len(pivot)}")
        if len(pivot) < 20:
            return None
            
        # Bollinger
        sma = pivot["Bitcoin"].rolling(window=20).mean()
        std = pivot["Bitcoin"].rolling(window=20).std()
        
        # RSI (Strength of the trend)
        delta = pivot["Bitcoin"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi_series = 100 - (100 / (1 + rs))

        return {
            "curr_price": pivot["Bitcoin"].iloc[-1],
            "upper": sma.iloc[-1] + (std.iloc[-1] * 2),
            "lower": sma.iloc[-1] - (std.iloc[-1] * 2),
            "rsi": rsi_series.iloc[-1]
        }

    def execute_trade(self, sig):
        """Worker 3: The Executioner"""
        if not sig: return
        
        cp, up, lo, rsi = sig['curr_price'], sig['upper'], sig['lower'], sig['rsi']

        # LOGIC A: EXIT (Sell or Stop Loss)
        if self.pos_btc > 0:
            change_pct = ((cp - self.buy_price) / self.buy_price) * 100
            
            if change_pct <= -1.7 or cp >= up:
                reason = "STOP LOSS" if change_pct <= -1.7 else "SELL"
                revenue = self.pos_btc * cp
                self.balance_usd = revenue - (revenue * self.fee_rate)
                self.log_trade(reason, cp, self.pos_btc, change_pct)
                self.pos_btc = 0
                self.save_state()
                winsound.Beep(1200, 800)

        # LOGIC B: ENTRY (Buy)
        elif cp <= lo and rsi < 35 and self.balance_usd > 0:
            cost = self.balance_usd * self.fee_rate
            self.pos_btc = (self.balance_usd - cost) / cp
            self.buy_price = cp
            self.balance_usd = 0
            self.log_trade("BUY", cp, self.pos_btc, 0.0)
            self.save_state()
            winsound.Beep(1000, 700)

    def display(self, sig):
        """Worker 4: The Dashboard"""
        if not sig: return
        os.system('cls' if os.name == 'nt' else 'clear')
        total_equity = self.balance_usd + (self.pos_btc * sig['curr_price'])
        print("="*40)
        print(f"NET WORTH: ${total_equity:.2f}")
        print(f"RSI: {sig['rsi']:.2f} | PRICE: ${sig['curr_price']:.2f}")
        print(f"LOWER: ${sig['lower']:.2f} | UPPER: ${sig['upper']:.2f}")
        print("="*40)

    def run_monitor(self):
        """THE BOSS: Orchestration"""
        pivot = self.fetch_data()
        signals = self.calculate_indicators(pivot) if pivot is not None else None
        
        self.display(signals)
        self.execute_trade(signals)

# --- EXECUTION ---
if __name__ == "__main__":
    import time
    bot = TradingBot()
    while True:
        bot.run_monitor()
        time.sleep(60)