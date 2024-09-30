
# 1. 変数の初期設定等
from amplify import VariableGenerator
gen = VariableGenerator()
q = gen.array("Binary", 2146) # 二値変数
Cardi = 5 # データの読み込み数



# 2. TOPIX2146銘柄を取得
import csv
with open("topixweight_j.csv") as file:
    lst = list(csv.reader(file))

# データ以外の記述をリストから削除、0～2145までがデータ
lst.pop(0)
last_data = 2145
code_2022 = []
code_2023 = []
for i in range(18):
    lst.pop( last_data + 1 )

for i in range(len(lst)):
    code_2022.append(lst[i][2])
    code_2023.append(lst[i][2])
# print(code_2022) # 2146個の銘柄コード



# 3. 銘柄、購入数の決定
# 3. 1. Jquantsから株価データを取得
import requests
import json

mail_password={"mailaddress":"e.cos2612@outlook.jp", "password":"26Erika12122"}
r_ref = requests.post("https://api.jquants.com/v1/token/auth_user", data=json.dumps(mail_password))
RefreshToken = r_ref.json()["refreshToken"]
r_token = requests.post(f"https://api.jquants.com/v1/token/auth_refresh?refreshtoken={RefreshToken}")
idToken = r_token.json()["idToken"]
headers = {'Authorization': 'Bearer {}'.format(idToken)}

# 3. 2. 2020~2022,2023のtime_pointを取得
# 2022~2022のtime_point_22
time_point_22 = []
from_22 = "2020-11-01" # 取得できる期間変わるので定期的に更新しないと
to_22 = "2023-03-31"
code_ = "7203"

url = "https://api.jquants.com/v1/prices/daily_quotes"
res = requests.get(f"{url}?code={code_}&from={from_22}&to={to_22}", headers=headers)
data = res.json()
close_values = [quote["Close"] for quote in data["daily_quotes"]]
for i in range(len(close_values)):
    time_point_22.append(data["daily_quotes"][i]["Date"])
    
from datetime import datetime
from collections import defaultdict
monthly_data = defaultdict(list)
for date_str in time_point_22: # 日付を扱いやすいように辞書型に変換
    date = datetime.strptime(date_str, '%Y-%m-%d')
    month_key = date.strftime('%Y-%m')
    monthly_data[month_key].append(date_str)


# 2023のtime_point_23
time_point_23 = []
from_23 = "2023-04-01" # 取得できる期間変わるので定期的に更新しないと
to_23 = "2024-03-31"
code_ = "7203"

url = "https://api.jquants.com/v1/prices/daily_quotes"
res_23 = requests.get(f"{url}?code={code_}&from={from_23}&to={to_23}", headers=headers)
data_23 = res_23.json()
close_values_23 = [quote["Close"] for quote in data_23["daily_quotes"]]
for i in range(len(close_values_23)):
    time_point_23.append(data_23["daily_quotes"][i]["Date"])
    
from datetime import datetime
from collections import defaultdict
monthly_data_23 = defaultdict(list)
for date_str in time_point_23: # 日付を扱いやすいように辞書型に変換
    date_23 = datetime.strptime(date_str, '%Y-%m-%d')
    month_key_23 = date_23.strftime('%Y-%m')
    monthly_data_23[month_key_23].append(date_str)



# 3. 3. 月初と月末の株価を2146銘柄分取得、csvファイルに保存
# 時間計測
import time
import os
folder_path = f"Cardinality_{Cardi}"
os.makedirs(folder_path, exist_ok=True)
print(f"フォルダ '{folder_path}' が作成されました。")
start_time = time.time()

# 2022のデータ取得
count = 0
month_key_list = []
data_close_first = defaultdict(list) # 月初の全銘柄の株価を、月をkeyとして格納
data_close_last = defaultdict(list) # 月末の全銘柄の株価を、月をkeyとして格納
# data_close_first["2022-04"][0]で4月初の0番目の銘柄の株価取得

Cardi_rep = Cardi
for key in monthly_data.keys():
    date_first = monthly_data[key][0]
    date_last = monthly_data[key][-1] 
    month_key_list.append(key)   
    print(key , "Cardi_rep : ", Cardi_rep)
    # print(count)
    # print(next(iter(monthly_data)))

# 月初、月末の株価取得
    i = 182 - 1 #添え字
    count_rep = 0 #while文を繰り返した数
    non_data = 0 #その月でデータが読み取れなかった数
    while count_rep < Cardi_rep:
        # print("Cardi_rep", Cardi_rep)
        count_rep = count_rep + 1
        i = i + 1
        res_first = requests.get(f"{url}?code={code_2022[i]}&date={date_first}", headers=headers)
        res_last = requests.get(f"{url}?code={code_2022[i]}&date={date_last}", headers=headers)
        data_first = res_first.json()
        data_last = res_last.json()
        
        if not data_first["daily_quotes"]: # Jquantsに銘柄コードがない時の例外処理
            if key == next(iter(monthly_data)):
                print(code_2022[i], "(i=", i, ")はありません、最初なので銘柄コードのみ削除します___________")
            else:
                print(code_2022[i], "(i=", i, ")はありません、2ヶ月目以降なのでデータも削除します____________")
                for key_past in monthly_data.keys(): #これまでのkeyのデータ削除
                    if(key == key_past):
                        break
                    else:
                        data_close_first[key_past].pop(i)
                        data_close_last[key_past].pop(i)
                
            code_2022.pop(i)
            i = i-1 #popすると後ろの要素は前にシフトされるから
            count = count + 1
            non_data = non_data + 1
        
        else:
            data_close_first[key].append(data_first["daily_quotes"][0]["AdjustmentClose"])
            data_close_last[key].append(data_last["daily_quotes"][0]["AdjustmentClose"])
        
        print("i:", i, end="")
        for key_past in monthly_data.keys():
                    print(data_close_first[key_past], end="")
        print("")
    Cardi_rep = Cardi_rep - non_data