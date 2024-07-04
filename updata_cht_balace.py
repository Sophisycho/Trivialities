import requests
import time
import random
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials


def query_api_for_accounts(account_list):
    # 基本的 HTTP 標頭，不包括 Deviceno 和 Loginid
    # 設定 HTTP 標頭
    # 這些header從哪裡來可以透過burpsuite設一個代理去拿到 ( 中華電信app -> burpsuite代理 -> 中華電信server )
    base_headers = {
        'Idfa': '',
        'Source': 'Prepaid',
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 com.cht.prepaidcard 35version',
        'Systemversion': '',
        'Deviceno': '0911111111',
        'Appversion': '',
        'Origin': 'https://my.cht.com.tw',
        'Sec-Fetch-Dest': 'empty',
        'Ivrno': 'xxxxxxxxxxx',
        'Sec-Fetch-Site': 'same-site',
        'Identifier': 'yyyyyyyyyyyyyyyyy',
        'Accept-Language': 'zh-TW,zh-Hant;q=0.9',
        'Otpw': '',
        'Loginid': '0911111111',
        'Page': 'PrepaidSubScriber',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Encoding': 'gzip, deflate',
        'Adid': '',
        'Sec-Fetch-Mode': 'cors'
    }

    # 設定 URL
    url = 'https://service.cht.com.tw/Prepaid/GetSubscriberDAInfos'

    results = {}  # 儲存每個帳號的查詢結果

    # 遍歷所有帳號
    for account in account_list:
        # 更新 HTTP 標頭，加入 Deviceno 和 Loginid
        headers = base_headers.copy()
        headers['Deviceno'] = account
        headers['Loginid'] = account

        # 執行 GET 請求
        print(f"現在正在發送 {account} 的請求...")
        time.sleep(random.uniform(1, 3))
        response = requests.get(url, headers=headers)

        # 檢查請求是否成功
        if response.status_code == 200:
            print(f"正在接收 {account} 的回傳資料...")
            # 解析並儲存 JSON 資料
            data = response.json()
            results[account] = data
            print(f"這是 {account} 的response {results[account]}")
        else:
            results[account] = f"請求失敗，狀態碼：{response.status_code}"

    return results

def clean_data(results):
    # 創建一個空的列表用於儲存結果
    result_list = []
    # print(f"原始 results: {results}")  # 印出原始字典
    for value in results.values():
        # print(f"目前的 data: {data}")  # 印出目前迭代到的字典
        # first_voice_remaining_amount = data.get('預付卡用戶帳號之主帳餘額')
        main_account_balance = value.get('主帳資訊', {}).get(
            '預付卡用戶帳號之主帳餘額', '未知')  # 透過多層.get()來安全地取得值
        device_number = value.get('設備號碼', '未知')  # 用.get()來防止KeyError
        balance_int = int(main_account_balance)  # 將字串轉成整數
        balance_int //= 10000  # 去掉後面4個0
        balance_float = balance_int / 100
        # 創建一個新的字典
        new_dict = {'設備號碼': device_number,
                    '帳號餘額': balance_float}
        # 添加到結果列表
        result_list.append(new_dict)
    print(f"這是整理過後的資料 {result_list}")
    return result_list


def fill_data(result_list):
    # 設定 OAuth 2.0 憑證
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]
    # 在這裡要改憑證的路徑
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        r"PATH", scope)
    # 建立 Sheets 和 Drive API 客戶端
    sheets_service = build('sheets', 'v4', credentials=creds)
    drive_service = build('drive', 'v3', credentials=creds)

    # 打開 Google Sheets，這裡要改你要寫入的目標sheet
    spreadsheet_id = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    # https://docs.google.com/spreadsheets/d/xxxxxxxxxxxxxxxxxxxxxxxxxxxx/edit#gid=yyyyyyy id就是中間那段

    # 讀取 A 列的數據
    read_range = "門號清單!A:A"
    result = sheets_service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=read_range
    ).execute()

    # 獲取 A 列的所有值
    values = result.get('values', [])

    for data in result_list:
        device_number = data['設備號碼']
        balance = data['帳號餘額']

        # 在 A 列中找到相應的行號
        for i, row in enumerate(values):
            if row and row[0] == device_number:
                # 計算 I 列的格子名
                cell_name = f"I{i+1}"

                # 寫入數據
                write_range = f"門號清單!{cell_name}"
                body = {
                    'values': [[balance]]
                }
                sheets_service.spreadsheets().values().update(
                    spreadsheetId=spreadsheet_id,
                    range=write_range,
                    body=body,
                    valueInputOption="RAW"
                ).execute()

                print(f"現在處理的號碼是：{device_number}")
                print(f"更新的數值是：{balance}")
    print("google sheet已更新完畢！")


# 使用函數查詢多個帳號
account_list = ['0911111111', '0911111111', '0911111111', '0911111111']
query_results = query_api_for_accounts(account_list)
results_list = clean_data(query_results)
fill_data(results_list)
