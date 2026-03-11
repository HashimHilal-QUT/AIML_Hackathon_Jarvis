from openai import OpenAI
import tiktoken
from datetime import datetime, timedelta

client = OpenAI(
    api_key="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"
)

def count_tokens(text, model="gpt-4o-search-preview"):
    enc = tiktoken.encoding_for_model(model)
    return len(enc.encode(text))

# Get relevant dates
yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
last_week = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
last_month = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

system_prompt = (
    "You are a world-class quantitative research analyst and portfolio strategist specializing in the Nepal Stock Exchange (NEPSE). "
    "You have access to the internet and can search for the latest news, data, and statistics from reputable Nepali sources. "
    "Your job is to:\n"
    f"1. Analyze NEPSE's market condition for yesterday, last week, and last month ({yesterday}, {last_week}, {last_month}) using price, volume, volatility, and sector rotation.\n"
    "2. For each stock and sector, calculate and compare:\n"
    "   - Momentum (recent price trends)\n"
    "   - Volatility (price swings)\n"
    "   - Mean reversion (distance from 30-day average)\n"
    "   - Liquidity (volume, turnover)\n"
    "3. Detect and factor in local events (dividends, AGMs, regulatory changes, major news).\n"
    "4. Rank actionable trading ideas for tomorrow, specifying: Name, Sector, Recent Price Change, Volume Trend, News/Sentiment, Signal (buy/sell/hold), Confidence (0-100%), Risk/Reward, Position Sizing, Stop Loss, and Reasoning.\n"
    "5. Ensure recommendations are diversified and risk-managed.\n"
    "6. Present results in a table and provide a brief market outlook and risk management advice for tomorrow.\n"
    "7. Always cite multiple reputable Nepali sources for each recommendation."

)

user_prompt = (
    f"Please search the internet and provide:\n"
    f"- A summary of NEPSE's market condition and sentiment for {yesterday}, last week, and last month.\n"
    f"- For each stock and sector, analyze: momentum, volatility, mean reversion, and liquidity.\n"
    f"- Detect and factor in local events (dividends, AGMs, regulatory changes, major news).\n"
    f"- Provide a ranked table of the top stocks and sectors to buy, sell, or hold for tomorrow, including: Name, Sector, Recent Price Change, Volume Trend, News/Sentiment, Signal (buy/sell/hold), Confidence (0-100%), Risk/Reward, Position Sizing, Stop Loss, and Reasoning.\n"
    f"- Ensure recommendations are diversified and risk-managed.\n"
    f"- Compare each to historical averages if possible.\n"
    f"- Provide a brief summary of the overall market outlook and risk management advice for tomorrow.\n"
    f"- Always cite multiple reputable Nepali sources for each recommendation."
)

messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": user_prompt}
]

# Estimate input tokens
input_tokens = sum(count_tokens(m["content"]) for m in messages)
print(f"🔢 Input tokens: {input_tokens}")

resp = client.chat.completions.create(
    model="gpt-4o-search-preview",
    messages=messages,
    max_tokens=1200,  # Increased for more detailed output
)

output = resp.choices[0].message.content
print(output)

# Estimate output tokens
output_tokens = count_tokens(output)
print(f"🔢 Output tokens: {output_tokens}")

# Cost calculation
call_cost = 0.035
token_cost = (input_tokens + output_tokens) * (2.5 + 10) / 1e6
total_cost = call_cost + token_cost
print(f"💰 Estimated cost: ${total_cost:.4f}")