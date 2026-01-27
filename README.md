# PandaLedger
**Personal Yearly/Monthly Budget App**

PandaLedger is a professional-grade personal finance and payroll forecasting tool built with Python and PySide6. It is designed to help users visualize their annual income, taxes, and savings based on highly customizable payroll schedules and tax configurations.

## 🚀 Key Features
* **Dynamic Payroll Forecasting**: Support for Weekly, Bi-Weekly, Semi-Monthly, and Monthly pay schedules.
* **Advanced Accounting Logic**: Handles both Hourly and Salary income types with automatic period distribution.
* **Custom Tax Rules**: Configure Federal, State, and additional payroll taxes to see your true take-home pay.
* **Yearly & Monthly Overviews**: Detailed breakdowns of every paycheck and a monthly "remaining balance" tracker after expenses.
* **Deduction Management**: Support for both Pre-Tax (401k, HSA) and Post-Tax (Insurance, Roth) deductions.
* **Modern UI**: High-fidelity Light and Dark themes with a professional dashboard feel.
* **Export Ready**: One-click "Copy for Excel" feature to move your data into external spreadsheets.

## 🛠️ Installation & Setup

### Prerequisites
* Python 3.12 or higher
* [PySide6](https://pypi.org/project/PySide6/) (Qt for Python)
* [pytest](https://pypi.org/project/pytest/) (for running the test suite)

### Development Setup
1. Clone the repository:
   ```bash
   git clone [https://github.com/pythonpandastudios/pandaledger.git](https://github.com/pythonpandastudios/pandaledger.git)
   cd pandaledger
   ```
2. Install dependencies:
   ```bash
   pip install PySide6 pytest
   ```
3. Run the application:
   ```bash
   python src/main.py
   ```

## 🧪 Testing
We maintain a robust test suite to ensure accounting accuracy. To run the tests, use:
```bash
pytest
```

## 📦 Build & Release Pipeline
PandaLedger uses GitHub Actions to automate the release process.
* **Continuous Integration**: Every push to `dev` or `main` triggers an automated test run on a virtual Linux display.
* **Automated Releases**: Creating a version tag (e.g., `v0.1.0`) automatically triggers a Windows build using PyInstaller and publishes the `.exe` to GitHub Releases.

## ⚖️ License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---
*Developed by Python Panda Studios*