import requests
import time
import json
from datetime import datetime, timedelta

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

def get_user_preferences():
    print(f"{Colors.BLUE}請回答以下問題來選擇您要查詢的 iPhone 型號：{Colors.RESET}")
    
    # 1. iPhone model
    while True:
        model = input("1. 請選擇 iPhone 型號 (輸入 'pro' 或 'pro max'): ").lower().strip()
        if model in ['pro', 'pro max']:
            break
        print(f"{Colors.RED}無效輸入，請重試。{Colors.RESET}")
    
    # 2. Storage capacity
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
    
    # 3. Color
    color_map = {'1': 'desert_gold', '2': 'natural', '3': 'white', '4': 'black'}
    while True:
        color = input("3. 請選擇顏色 (1.沙漠金 2.原色 3.白色 4.黑色): ").strip()
        if color in color_map:
            color = color_map[color]
            break
        print(f"{Colors.RED}無效輸入，請重試。{Colors.RESET}")
    
    model_key = 'pro_max' if model == 'pro max' else 'pro'
    selected_model = IPHONE_MODELS[model_key][color][capacity]
    print(f"{Colors.GREEN}您選擇的型號是：{selected_model}{Colors.RESET}")
    return selected_model

def check_stock(model):
    url = "https://www.apple.com/tw-edu/shop/fulfillment-messages"
    params = {
        "pl": "true",
        "mts.0": "regular",
        "mts.1": "compact",
        "cppart": "UNLOCKED/WW",
        "parts.0": model,
        "location": "110"
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        stores = data['body']['content']['pickupMessage']['stores']
        stock_available = False
        for store in stores:
            availability = store['partsAvailability'].get(model)
            if availability and availability['pickupDisplay'] == 'available':
                print(f"{Colors.GREEN}{Colors.BOLD}庫存可用!{Colors.RESET}")
                print(f"{Colors.YELLOW}型號: {model}{Colors.RESET}")
                print(f"{Colors.YELLOW}商店: {store['storeName']}{Colors.RESET}")
                print(f"{Colors.YELLOW}取貨資訊: {availability['pickupSearchQuote']}{Colors.RESET}")
                stock_available = True
        
        if not stock_available:
            print(f"{Colors.RED}型號 {model} 在附近商店暫無庫存。{Colors.RESET}")
        
        return stock_available
    
    except requests.RequestException as e:
        print(f"{Colors.RED}發生錯誤: {e}{Colors.RESET}")
        return False

def main():
    model = get_user_preferences()
    
    # Ask if user wants to view check count and elapsed time
    show_stats = input("是否顯示檢查次數和運行時間？(y/n): ").lower().strip() == 'y'
    
    print(f"{Colors.BLUE}開始持續檢查型號 {model} 的庫存...{Colors.RESET}")
    
    check_count = 0
    start_time = datetime.now()
    
    while True:
        check_count += 1
        current_time = datetime.now()
        elapsed_time = current_time - start_time
        
        if show_stats:
            print(f"\n{Colors.BOLD}檢查次數: {check_count}{Colors.RESET}")
            print(f"{Colors.BOLD}運行時間: {str(elapsed_time).split('.')[0]}{Colors.RESET}")
        
        print(f"{Colors.BOLD}檢查時間: {current_time.strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}")
        
        check_stock(model)
        time.sleep(1.5)

if __name__ == "__main__":
    main()