import requests
import time
import json
from datetime import datetime
import plyer
import concurrent.futures
import os
import js2py

# ANSI color codes
class Colors:
    RESET = '\033[0m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'

def fetch_iphone_models():
    url = "https://www.apple.com/tw/shop/buy-iphone/iphone-16-pro"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"{Colors.RED}無法獲取 iPhone 型號數據。請檢查您的網絡連接。{Colors.RESET}")
        return None

    script_content = response.text
    
    start_index = script_content.find("window.PRODUCT_SELECTION_BOOTSTRAP")
    if start_index == -1:
        print(f"{Colors.RED}無法在頁面中找到產品數據。{Colors.RESET}")
        return None

    end_index = script_content.find("</script>", start_index)
    if end_index == -1:
        print(f"{Colors.RED}無法解析產品數據。{Colors.RESET}")
        return None

    js_code = script_content[start_index:end_index]
    
    try:
        context = js2py.EvalJs()
        context.execute(js_code)
        product_data = context.PRODUCT_SELECTION_BOOTSTRAP.to_dict()
        return product_data['productSelectionData']['products']
    except Exception as e:
        print(f"{Colors.RED}解析錯誤: {str(e)}{Colors.RESET}")
        print("JavaScript 代碼片段:")
        print(js_code[:500])
        return None

def parse_iphone_models(data):
    models = {}
    for product in data:
        model_name = product['familyType']
        if model_name not in models:
            models[model_name] = {
                'colors': set(),
                'capacities': set(),
                'part_numbers': []
            }
        
        color = product['dimensionColor']
        capacity = product['dimensionCapacity']
        part_number = product['partNumber']
        
        models[model_name]['colors'].add(color)
        models[model_name]['capacities'].add(capacity)
        models[model_name]['part_numbers'].append({
            'color': color,
            'capacity': capacity,
            'part_number': part_number
        })

    for model in models.values():
        model['colors'] = sorted(model['colors'])
        model['capacities'] = sorted(model['capacities'])

    return models

def get_user_preferences(models):
    selected_models = []
    while True:
        print(f"\n{Colors.BLUE}可用的 iPhone 型號：{Colors.RESET}")
        for i, model in enumerate(models.keys(), 1):
            print(f"{i}. {model}")
        
        model_choice = input("請選擇 iPhone 型號 (輸入數字): ")
        try:
            model_index = int(model_choice) - 1
            selected_model = list(models.keys())[model_index]
        except (ValueError, IndexError):
            print(f"{Colors.RED}無效的選擇，請重試。{Colors.RESET}")
            continue

        print(f"\n{Colors.BLUE}可用的顏色：{Colors.RESET}")
        for i, color in enumerate(models[selected_model]['colors'], 1):
            print(f"{i}. {color}")
        
        color_choice = input("請選擇顏色 (輸入數字): ")
        try:
            color_index = int(color_choice) - 1
            selected_color = models[selected_model]['colors'][color_index]
        except (ValueError, IndexError):
            print(f"{Colors.RED}無效的選擇，請重試。{Colors.RESET}")
            continue

        print(f"\n{Colors.BLUE}可用的容量：{Colors.RESET}")
        for i, capacity in enumerate(models[selected_model]['capacities'], 1):
            print(f"{i}. {capacity}")
        
        capacity_choice = input("請選擇容量 (輸入數字): ")
        try:
            capacity_index = int(capacity_choice) - 1
            selected_capacity = models[selected_model]['capacities'][capacity_index]
        except (ValueError, IndexError):
            print(f"{Colors.RED}無效的選擇，請重試。{Colors.RESET}")
            continue

        part_number = next((item['part_number'] for item in models[selected_model]['part_numbers'] 
                            if item['color'] == selected_color 
                            and item['capacity'] == selected_capacity), None)
        
        if part_number:
            screen_size = "6.3 吋" if "pro" in selected_model.lower() else "6.9 吋"
            model_display = f"{selected_model} {selected_capacity} {selected_color} {screen_size}"
            selected_models.append((part_number, model_display))
            print(f"{Colors.GREEN}您選擇的型號是：{model_display} (部件編號: {part_number}){Colors.RESET}")
        else:
            print(f"{Colors.RED}無法獲取該型號的部件編號。跳過此選擇。{Colors.RESET}")

        if input("是否要繼續添加其他型號？(y/n): ").lower().strip() != 'y':
            break

    return selected_models

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
    print(f"{Colors.BLUE}正在獲取最新的 iPhone 型號數據...{Colors.RESET}")
    product_data = fetch_iphone_models()
    if not product_data:
        print(f"{Colors.RED}無法獲取產品數據。程序將退出。{Colors.RESET}")
        return

    models = parse_iphone_models(product_data)
    if not models:
        print(f"{Colors.RED}無法解析產品數據。程序將退出。{Colors.RESET}")
        return

    selected_models = get_user_preferences(models)
    if not selected_models:
        print(f"{Colors.RED}未選擇任何型號。程序將退出。{Colors.RESET}")
        return

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
            
            for model_display, stock_available, available_stores in check_multiple_models(selected_models):
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