# 💎 Commit Pulse

[![PyPI version](https://badge.fury.io/py/commitpulse.svg)](https://pypi.org/project/commitpulse/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**High-fidelity Git analytics for the modern developer.**
Analyze your repositories, track contributor impact, and visualize your engineering legacy in seconds.

[**Explore the Registry**](https://commitpulse.pxxl.click/explore) | [**GitHub Repository**](https://github.com/samolubukun/commitpulse) | [**PyPI Package**](https://pypi.org/project/commitpulse/)

---

## 🚀 Quick Start

### 1. Installation
```bash
pip install commitpulse
```

### 2. Pulse to Cloud (Default)
Host your dashboard globally and get a unique, shareable URL.
```bash
commitpulse
```
*Output: `✨ Successfully published! Share your Pulse at: https://commitpulse.pxxl.click/v/unique-id`*

---

## 🛠️ Advanced Usage

### Local-First Analysis
Generate a self-contained, interactive HTML dashboard strictly on your machine.
```bash
commitpulse --local
```
> [!IMPORTANT]
> This will prompt for a security confirmation (y/n) before generating local files.

### Targets & Options
- `commitpulse /path/to/repo`: Analyze a specific directory.
- `--no-open`: Analyze and sync without automatically opening the browser.

---

## 🧬 Engineering Intelligence
- **Robust Language Detection**: Uses byte-count analysis and an expanded polyglot map for high-precision stack breakdown.
- **Privacy by Design**: Raw code never leaves your machine. We only analyze Git metadata to build your visual profile.
- **Premium Aesthetics**: Interactive heatmaps, productivity distributions, and contributor impact visualizations.

---

## 🤝 Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---
**Sync your pulse. Reveal your impact.**  

Built with ❤️ by [Samuel Olubukun](https://github.com/samolubukun)
