import requests
import time
import json
from datetime import datetime, timedelta
import plyer
import concurrent.futures
import os

# ANSI color codes
class Colors:
    RESET = '\033[0m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'

# iPhone model mapping
IPHONE_MODELS = {
    'pro': {
        'desert_gold': {128: 'MYNF3ZP/A', 256: 'MYNK3ZP/A', 512: 'MYNP3ZP/A', 1024: 'MYNW3ZP/A'},
        'natural': {128: 'MYNG3ZP/A', 256: 'MYNL3ZP/A', 512: 'MYNQ3ZP/A', 1024: 'MYNX3ZP/A'},
        'white': {128: 'MYNE3ZP/A', 256: 'MYNJ3ZP/A', 512: 'MYNN3ZP/A', 1024: 'MYNT3ZP/A'},
        'black': {128: 'MYND3ZP/A', 256: 'MYNH3ZP/A', 512: 'MYNM3ZP/A', 1024: 'MYNR3ZP/A'}
    },
    'pro_max': {
        'desert_gold': {256: 'MYWX3ZP/A', 512: 'MYX23ZP/A', 1024: 'MYX63ZP/A'},
        'natural': {256: 'MYWY3ZP/A', 512: 'MYX33ZP/A', 1024: 'MYX73ZP/A'},
        'white': {256: 'MYWW3ZP/A', 512: 'MYX13ZP/A', 1024: 'MYX53ZP/A'},
        'black': {256: 'MYWV3ZP/A', 512: 'MYX03ZP/A', 1024: 'MYX43ZP/A'}
    }
}

COLOR_NAMES = {
    'desert_gold': '沙漠金',
    'natural': '原色',
    'white': '白色',
    'black': '黑色'
}

def get_user_preferences():
    models = []
    added_models = set()  # 用於跟踪已添加的型號
    while True:
        model, model_display = get_single_model_preference()
        if model in added_models:
            print(f"{Colors.YELLOW}警告：您已經添加過這個型號了。{Colors.RESET}")
            continue
        models.append((model, model_display))
        added_models.add(model)
        while True:
            response = input("是否要繼續添加其他型號？(y/n): ").lower().strip()
            if response in ['y', 'n']:
                break
            print(f"{Colors.RED}無效輸入，請輸入 'y' 或 'n'。{Colors.RESET}")
        if response == 'n':
            break
    return models

def get_single_model_preference():
    print(f"{Colors.BLUE}請回答以下問題來選擇您要查詢的 iPhone 型號：{Colors.RESET}")
    
    while True:
        model = input("1. 請選擇 iPhone 型號 (輸入 'pro' 或 'pro max'): ").lower().strip()
        if model in ['pro', 'pro max']:
            break
        print(f"{Colors.RED}無效輸入，請重試。{Colors.RESET}")
    
    valid_capacities = [256, 512, 1024] if model == 'pro max' else [128, 256, 512, 1024]
    while True:
        capacity = input(f"2. 請選擇儲存容量 (輸入 {', '.join(map(str, valid_capacities))} 中的一個): ")
        try:
            capacity = int(capacity)
            if capacity in valid_capacities:
                break
            print(f"{Colors.RED}無效輸入，請重試。{Colors.RESET}")
        except ValueError:
            print(f"{Colors.RED}請輸入有效的數字。{Colors.RESET}")
    
    color_map = {'1': 'desert_gold', '2': 'natural', '3': 'white', '4': 'black'}
    while True:
        color = input("3. 請選擇顏色 (1.沙漠金 2.原色 3.白色 4.黑色): ").strip()
        if color in color_map:
            color = color_map[color]
            break
        print(f"{Colors.RED}無效輸入，請重試。{Colors.RESET}")
    
    model_key = 'pro_max' if model == 'pro max' else 'pro'
    selected_model = IPHONE_MODELS[model_key][color][capacity]
    capacity_display = "1TB" if capacity == 1024 else f"{capacity}GB"
    model_display = f"{'Pro Max' if model == 'pro max' else 'Pro'} {capacity_display} {COLOR_NAMES[color]} ({selected_model})"
    print(f"{Colors.GREEN}您選擇的型號是：{model_display}{Colors.RESET}")
    return selected_model, model_display

def check_stock(model, model_display):
    url = "https://www.apple.com/tw-edu/shop/fulfillment-messages"
    params = {
        "pl": "true",
        "mts.0": "regular",
        "mts.1": "compact",
        "cppart": "UNLOCKED/WW",
        "parts.0": model,
        "location": "110"
    }
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            stores = data['body']['content']['pickupMessage']['stores']
            available_stores = [
                (store['storeName'], store['partsAvailability'][model]['pickupSearchQuote'])
                for store in stores
                if store['partsAvailability'][model]['pickupDisplay'] == 'available'
            ]
            
            return bool(available_stores), available_stores
        
        except requests.RequestException as e:
            if attempt < max_retries - 1:
                print(f"{Colors.YELLOW}檢查失敗，正在重試...{Colors.RESET}")
                time.sleep(2)
            else:
                print(f"{Colors.RED}發生錯誤: {e}{Colors.RESET}")
                return False, []

def send_notification(title, message):
    try:
        plyer.notification.notify(
            title=title,
            message=message,
            app_name="Apple Store 庫存查詢",
            timeout=10
        )
    except Exception as e:
        print(f"{Colors.RED}發送通知失敗: {e}{Colors.RESET}")

def check_multiple_models(models):
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(models)) as executor:
        future_to_model = {executor.submit(check_stock, model, model_display): (model, model_display) for model, model_display in models}
        for future in concurrent.futures.as_completed(future_to_model):
            model, model_display = future_to_model[future]
            try:
                yield (model_display, *future.result())
            except Exception as e:
                print(f"{Colors.RED}檢查型號 {model_display} 時發生錯誤: {e}{Colors.RESET}")
                yield (model_display, False, [])

def play_alert():
    if os.name == 'posix':  # macOS or Linux
        for _ in range(2):
            os.system('afplay /System/Library/Sounds/Ping.aiff')
            time.sleep(0.1)
    elif os.name == 'nt':  # Windows
        import winsound
        for _ in range(2):
            winsound.Beep(1000, 100)  # 1000 Hz for 100 ms
            time.sleep(0.1)

def main():
    models = get_user_preferences()
    
    while True:
        show_stats = input("是否顯示檢查次數和運行時間？(y/n): ").lower().strip()
        if show_stats in ['y', 'n']:
            show_stats = (show_stats == 'y')
            break
        print(f"{Colors.RED}無效輸入，請輸入 'y' 或 'n'。{Colors.RESET}")
    
    print(f"{Colors.BLUE}開始持續查詢選定型號的庫存...{Colors.RESET}")
    
    check_count = 0
    stock_found_count = 0
    start_time = datetime.now()
    
    try:
        while True:
            check_count += 1
            current_time = datetime.now()
            elapsed_time = current_time - start_time
            
            if show_stats:
                stats = f"檢查次數: {check_count} | 發現庫存次數: {stock_found_count} | 運行時間: {str(elapsed_time).split('.')[0]}"
                print(f"\n{Colors.BOLD}{stats}{Colors.RESET}")
            
            print(f"{Colors.BOLD}檢查時間: {current_time.strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}")
            
            for model_display, stock_available, available_stores in check_multiple_models(models):
                if stock_available:
                    stock_found_count += 1
                    print(f"{Colors.GREEN}{Colors.BOLD}庫存可用!{Colors.RESET}")
                    print(f"{Colors.YELLOW}型號: {model_display}{Colors.RESET}")
                    for store_name, pickup_quote in available_stores:
                        print(f"{Colors.YELLOW}商店: {store_name}{Colors.RESET}")
                        print(f"{Colors.YELLOW}取貨資訊: {pickup_quote}{Colors.RESET}")
                    send_notification("庫存已找到!", f"{model_display} 有庫存!")
                    play_alert()
                else:
                    print(f"{Colors.RED}型號 {model_display} 在附近商店暫無庫存。{Colors.RESET}")
            
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n{Colors.BLUE}程序已停止。總共檢查 {check_count} 次，發現庫存 {stock_found_count} 次。{Colors.RESET}")

if __name__ == "__main__":
    main()