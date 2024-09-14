# Apple Store 庫存查詢工具

這是一個用於持續查詢 Apple Store 特定 iPhone 型號庫存的 Python 腳本。

## 功能

- 允許用戶選擇特定的 iPhone 型號、容量和顏色
- 持續查詢選定型號的庫存狀態
- 顯示每次查詢的時間戳
- 可選擇顯示查詢次數和總運行時間
- 使用彩色輸出以提高可讀性

## 安裝

1. 確保您的系統已安裝 Python 3.6 或更高版本。

2. 克隆此倉庫：
   ```
   git clone https://github.com/yanggu0t/iPhone-stock-checker.git
   cd iPhone-stock-checker
   ```

3. 安裝所需的依賴：
   ```
   pip install -r requirements.txt
   ```

## 使用方法

1. 運行腳本：
   ```
   python stock_checker.py
   ```

2. 按照提示選擇 iPhone 型號、容量和顏色。

3. 選擇是否顯示查詢次數和運行時間統計信息。

4. 腳本將開始持續查詢所選型號的庫存情況，每 1.5 秒查詢一次。

5. 如果發現庫存，腳本會以綠色高亮顯示相關信息。

6. 要停止腳本，請按 Ctrl+C。

## 注意事項

- 此腳本僅用於教育和個人使用目的。
- 頻繁查詢可能會對 Apple 的服務器造成負擔，請負責任地使用。
- 腳本的運行時間包括了每次查詢之間的等待時間（1.5 秒）。

## 貢獻

歡迎提交 Issues 和 Pull Requests 來幫助改進這個工具。

## 許可證

[MIT License](https://opensource.org/licenses/MIT)