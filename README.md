# 🚀 HyperTrail - Trailing Limit Order System for Hyperliquid

<div align="center">

**[Hyperliquid](https://hyperliquid.xyz) - Advanced Trailing Limit Order Management via TUI Dashboard**

![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)
![Python: 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)
![Status: Production Ready](https://img.shields.io/badge/status-production%20ready-green.svg)

</div>

---

## 🎯 What is HyperTrail?

**HyperTrail** is a cutting-edge **trailing limit order manager** built specifically for [Hyperliquid DEX](https://hyperliquid.xyz). It provides a sleek Text-based User Interface (TUI) dashboard for creating, monitoring, and managing automated trailing orders that dynamically adjust to market movements.

### Key Features

- 📊 **Interactive TUI Dashboard** - Full-screen terminal interface with keyboard navigation
- 🔗 **Dual-Network Support** - Configurable for Mainnet or Testnet operations
- 🤖 **Automated Trailing Orders** - Buy dips / Sell rallies with intelligent trail logic
- 💾 **Persistent Storage** - SQLite database ensures bots survive restarts
- ⌨️ **Keyboard Shortcuts** - Fast, efficient operation (Ctrl/CMD + q to quit)
- 🎨 **Modern UI** - Clean, responsive design using Textual framework

---

## 📦 Installation Guide

### Prerequisites

- Python 3.12 or higher
- pip package manager
- Hyperliquid API credentials (Testnet recommended for first use)

### Quick Start

```bash
# Clone the repository
git clone https://github.com/franciscomvargas/HyperTrail.git
cd HyperTrail

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# or: .venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Configure API credentials (see Configuration section)
cp config.example.env .env

# Start the TUI dashboard
python app.py
```

---

## 🎮 Usage & Keyboard Navigation

Once launched, control HyperTrail with these keyboard shortcuts:

| Key | Action | Description |
|-----|--------|-------------|
| **`c`** | Create Bot | Opens modal to create new trailing order bot |
| **`d`** | Delete Bot | Removes selected bot from active list |
| **`m`** | Monitor Mode | Toggles real-time monitoring notification |
| **`h`** | Help Modal | Shows all available keyboard shortcuts |
| **`q`** | Quit Application | Gracefully exits the TUI (or escape) |

### Creating a Trailing Order Bot

1. Press **[c]** or select "Create Bot" button
2. Fill in required fields:
   - **Trail Type**: long_entry, short_entry, long_exit, short_exit
   - **Coin Symbol**: BTC, ETH, SOL, etc.
   - **Side**: Buy (dip buy) or Sell (rally sell)
   - **Size ($)**: Order size in USD (min $50 recommended)
   - **Offset (%)**: Trail offset percentage from market price
3. Press Enter to submit or ESC to cancel
4. Bot appears immediately in the dashboard table

### Trailing Order Types Explained

| Type | Strategy | Use Case |
|------|----------|----------|
| **Long Entry** | Buy dips - descend as price falls, lock on bounce up | Accumulation during market dip |
| **Short Entry** | Sell rallies - ascend as price rises, lock on bounce down | Profit taking during market rally |
| **Long Exit** | Take profit trails upward behind long position | Protect profits on open longs |
| **Short Exit** | Dip buy - trail downward then up (exit short) | Cover shorts at better prices |

---

## 🔧 Configuration

### 1. API Credentials Setup

Create your `.env` file with required credentials:

```bash
cp config.example.env .env
```

Edit `.env` and add your Hyperliquid keys:

```env
# Network Selection (TESTNET or MAINNET)
HYPERLIQUID_NETWORK=TESTNET

# API Keys - Get these from https://hyperliquid.xyz/understanding_api
HYPERLIQUID_MAINNET_PUBLIC_KEY=your_mainnet_public_key
HYPERLIQUID_MAINNET_SECRET_KEY=your_mainnet_secret_key

# Testnet Keys (for development)
HYPERLIQUID_TESTNET_PUBLIC_KEY=your_testnet_public_key  
HYPERLIQUID_TESTNET_SECRET_KEY=your_testnet_secret_key
```

### 2. Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `HYPERLIQUID_NETWORK` | Yes | TESTNET | Network mode (TESTNET/MAINNET) |
| `HYPERLIQUID_SECRET_KEY_*` | Yes | None | API secret keys per network |
| `LOGS_DIR` | No | logs | Database storage directory |

### 3. Starting the Dashboard

```bash
cd /path/to/HyperTrail
source .venv/bin/activate
python app.py
```

**Output:**
- Console displays startup information and API validation status
- TUI dashboard appears with all bots and available actions
- Keyboard shortcuts shown in footer for quick reference

---

## 🔍 Database & Persistence

All bot configurations are stored in a SQLite database:

```bash
# Default location
logs/hypertrail_bots.db

# Custom path (configure via persistence.py)
```

### Features:
- ✅ Bots persist across application restarts
- ✅ Full history of bot creation/deletion
- ✅ Real-time balance updates from Hyperliquid API
- ✅ Automatic WAL mode for concurrent access

---

## 🛠️ Troubleshooting

### Common Issues

| Problem | Solution |
|---------|----------|
| "API Authentication Failed" | Verify secret keys in `.env` and ensure correct network selected |
| Terminal shows garbled output | Update terminal to UTF-8 encoding, resize window larger than 80x24 |
| No bots persist after restart | Run `python -c "from engine.persistence import DatabasePersistence; p=DatabasePersistence(); print(p.load_all_bots())"` to verify DB |
| DataTable doesn't render | Check Textual version: `pip install --upgrade textual` |

### Debug Mode

See detailed console output during operation:

```bash
source .venv/bin/activate
python app.py 2>&1 | tee hypertrail_debug.log
```

---

## 📋 Technical Architecture

### Project Structure

```
HyperTrail/
├── engine/                   # Core engine module
│   ├── __init__.py
│   ├── config.py            # Configuration management
│   ├── models.py            # Pydantic data models (BotConfig, BotState)
│   ├── persistence.py       # SQLite database layer
│   └── types.py             # TrailType enum and other types
├── logs/                    # Database storage location
│   └── hypertrail_bots.db  # SQLite database file
├── tests/                   # Test suite
│   └── test_ui_smoke_test.py
├── .env                     # Environment variables (gitignored)
├── .venv/                   # Virtual environment
├── app.py                   # Main TUI application entry point
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

### Dependencies

- [textual](https://github.com/Textualize/textual) - Modern TUI framework
- [pydantic](https://docs.pydantic.dev/) - Data validation and settings management
- [hyperliquid-sdk](https://www.npmjs.com/package/hyperliquid-sdk) - Hyperliquid API client

---

## 🤝 Contributing & Support

We welcome contributions! Here's how to help:

1. **Report Issues**: Create a GitHub Issue with bug description
2. **Submit Features**: Fork repository and submit PR
3. **Share Use Cases**: Tell us about your trailing order strategies

**Contact:** Open an issue on the [GitHub repository](https://github.com/franciscomvargs/HyperTrail/issues)

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🔎 Keywords & Search Tags

*trailing limit order system, Hyperliquid trading bot, crypto trailing order, liquid staking, automated market making, limit order management, decentralized exchange tools, perpetual futures trading, DeFi automation, Terminal UI dashboard, Python trading application, crypto algorithmic trading, high-frequency trading tools, order flow analytics, liquidity provision*

---

## 🙏 Acknowledgments

- Built for the Hyperliquid community
- Inspired by advanced market making strategies
- Powered by innovative [Textual](https://github.com/Textualize/textual) framework

---

<div align="center">

**Star this project if it helps with your trading! ⭐**

Made with ❤️ by the Trading Technology Team

[📊 Live Dashboard](#usage-and-keyboard-navigation) | [🔧 Configuration](#configuration) | [🐛 Reporting Issues](#troubleshooting)

</div>
