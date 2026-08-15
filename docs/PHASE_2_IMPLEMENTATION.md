# Phase 2 Implementation: Native PyWebView Desktop Application

**Project:** Demand Forecasting & Profit Prediction Engine  
**Desktop Framework:** PyWebView (Native macOS Cocoa / Windows Native Window) + DuckDB + Plotly  
**Status:** Completed & Validated

---

## 1. Overview & Architecture

We transformed the project into a **true native desktop software application** using **`pywebview`**.

* **Zero Browser Tabs / Zero URL Bars:** The application opens in a dedicated native OS desktop window with its own frame, titlebar, and dock icon.
* **Double-Click Execution:** Anyone on macOS or Windows can simply double-click the launcher file to open the native desktop window immediately.
* **Blazing Fast Local OLAP Engine:** Backed directly by `finance.duckdb` for instant analytical queries and aggregations.

```
+-----------------------------------------------------------------------------------+
|                        NATIVE DESKTOP APP ARCHITECTURE                            |
+-----------------------------------------------------------------------------------+
|  [Launch_Finance_App.command / .bat] (Double-click entry point)                   |
|                      │                                                            |
|                      ▼                                                            |
|             [desktop_app.py] (PyWebView Orchestrator)                             |
|                      │                                                            |
|      ┌───────────────┴────────────────┐                                           |
|      ▼                                ▼                                           |
| [Native macOS/Win Window]     [In-Process Analytics Engine]                       |
| - Cocoa / WebKit Window       - DuckDB Engine (finance.duckdb)                    |
| - Titlebar & Dark Frame       - Plotly Interactive Visuals                        |
| - Zero Browser Overhead       - Fast In-Memory Aggregations                       |
+-----------------------------------------------------------------------------------+
```

---

## 2. Key Desktop Application Components

1. **`desktop_app.py`:**
   * Initializes the native desktop window (`1350x880` resolution, min size `1000x680`, dark theme).
   * Spawns the local in-process analytics engine.
   * Manages clean exit & resource termination when the desktop window is closed.
2. **`Launch_Finance_App.command` (macOS):**
   * Double-clickable file in macOS Finder to launch the desktop app without opening terminal.
3. **`Launch_Finance_App.bat` (Windows):**
   * Double-clickable batch executable for Windows users.
4. **`app.py` & `src/components/`:**
   * **Executive Overview:** High-level KPI summary, revenue trends, regional shares, top products & customers.
   * **Demand Analytics:** Volume time-series (Monthly/Weekly/Daily), seasonality matrix, customer segment demand, price elasticity scatterplots.
   * **Profit Waterfall & Margins:** Interactive Plotly Financial Waterfall chart, direct COGS breakdown (Material, Labor, Overhead, Freight), customer profitability matrix.
   * **OpEx & Budget Variance:** Departmental overhead and management budget vs. actual targets.

---

## 3. How to Launch the Desktop Application

### Option A: Double-Click (Zero Terminal Required)
* **On macOS:** Double-click `Launch_Finance_App.command` directly from Finder.
* **On Windows:** Double-click `Launch_Finance_App.bat` from File Explorer.

### Option B: Terminal Command
```bash
.venv/bin/python desktop_app.py
```
A native macOS/Windows window will appear on your desktop.
