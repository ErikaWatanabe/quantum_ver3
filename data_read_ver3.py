
# 1. 変数の初期設定等
from amplify import VariableGenerator
gen = VariableGenerator()
q = gen.array("Binary", 2146) # 二値変数
Cardi = 2000 # データの読み込み数



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

with open('config.json', 'r') as config_file:
    config = json.load(config_file)
email = config['email']
api_password = config['api_password']

mail_password={"mailaddress":email, "password":api_password}
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
    i = -1
    count_rep = 0 #while文を繰り返した数
    non_data = 0 #その月でデータが読み取れなかった数
    while count_rep < Cardi_rep:
        count_rep = count_rep + 1
        i = i + 1
        try:
            res_first = requests.get(f"{url}?code={code_2022[i]}&date={date_first}", headers=headers)
            res_last = requests.get(f"{url}?code={code_2022[i]}&date={date_last}", headers=headers)
            data_first = res_first.json()
            data_last = res_last.json()
            if (not data_first["daily_quotes"]) or (not data_last["daily_quotes"]): # Jquantsに銘柄コードがない時の例外処理
                if key == next(iter(monthly_data)):
                    print(code_2022[i], "はありません、最初なので銘柄コードのみ削除します")
                else:
                    print(code_2022[i], "はありません、2ヶ月目以降なのでデータも削除します")
                    for key_past in monthly_data.keys(): #これまでのkeyのデータ削除
                        if(key == key_past):
                            break
                        else:
                            data_close_first[key_past].pop(i)
                            data_close_last[key_past].pop(i)
                # print(data_first)
                code_2022.pop(i)
                # print(code_2022[i-1], code_2022[i], code_2022[i+1])
                i = i-1 #popすると後ろの要素は前にシフトされるから
                count = count + 1
                non_data = non_data + 1
            
            else:
                data_close_first[key].append(data_first["daily_quotes"][0]["AdjustmentClose"])
                data_close_last[key].append(data_last["daily_quotes"][0]["AdjustmentClose"])
        except Exception as e:
            print(f"株価読み込みで予期しないエラーが発生しました! ", i, "番目, 銘柄は", code_2022[i]," {e}")
            if key == next(iter(monthly_data)):
                print(code_2022[i], "はありません、最初なので銘柄コードのみ削除します")
            else:
                print(code_2022[i], "はありません、2ヶ月目以降なのでデータも削除します")
                for key_past in monthly_data.keys(): #これまでのkeyのデータ削除
                    if(key == key_past):
                        break
                    else:
                        data_close_first[key_past].pop(i)
                        data_close_last[key_past].pop(i)
            code_2022.pop(i)
            # print(code_2022[i-1], code_2022[i], code_2022[i+1])
            i = i-1 #popすると後ろの要素は前にシフトされるから
            count = count + 1
            non_data = non_data + 1
            continue

        
    Cardi_rep = Cardi_rep - non_data
        


# 2023のデータ取得
count_23 = 0
month_key_list_23 = []
data_close_first_23 = defaultdict(list) # 月初の全銘柄の株価を、月をkeyとして格納
data_close_last_23 = defaultdict(list) # 月末の全銘柄の株価を、月をkeyとして格納
Cardi_rep = Cardi
for key in monthly_data_23.keys():
    date_first_23 = monthly_data_23[key][0]
    date_last_23 = monthly_data_23[key][-1] 
    month_key_list_23.append(key)   
    print(key , "Cardi_rep : ", Cardi_rep)
    # print(count_23)
    # print(next(iter(monthly_data)))

# 月初、月末の株価取得
    i = -1
    count_rep = 0 #while文を繰り返した数
    non_data = 0 #その月でデータが読み取れなかった数
    while count_rep < Cardi_rep:
        count_rep = count_rep + 1
        i = i + 1
        try:
            res_first_23 = requests.get(f"{url}?code={code_2023[i]}&date={date_first_23}", headers=headers)
            res_last_23 = requests.get(f"{url}?code={code_2023[i]}&date={date_last_23}", headers=headers)
            data_first_23 = res_first_23.json()
            data_last_23 = res_last_23.json()
        except Exception as e:
            print(f"株価読み込みで予期しないエラーが発生しました!!!!!!!: {e}")
            if key == next(iter(monthly_data_23)):
                print(code_2023[i], "はありません、最初なので銘柄コードのみ削除します(2023)")
            else:
                print(code_2023[i], "はありません、2ヶ月目以降なのでデータも削除します(2023)")
                for key_past in monthly_data_23.keys(): #これまでのkeyのデータ削除
                    if(key == key_past):
                        break
                    else:
                        data_close_first_23[key_past].pop(i)
                        data_close_last_23[key_past].pop(i)
            code_2023.pop(i)
            i = i-1
            count_23 = count_23 + 1
            non_data = non_data + 1
        
        if (not data_first_23["daily_quotes"]) or (not data_last_23["daily_quotes"]): # Jquantsに銘柄コードがない時の例外処理
            if key == next(iter(monthly_data_23)):
                print(code_2023[i], "はありません、最初なので銘柄コードのみ削除します(2023)")
            else:
                print(code_2023[i], "はありません、2ヶ月目以降なのでデータも削除します(2023)")
                for key_past in monthly_data_23.keys(): #これまでのkeyのデータ削除
                    if(key == key_past):
                        break
                    else:
                        data_close_first_23[key_past].pop(i)
                        data_close_last_23[key_past].pop(i)
            code_2023.pop(i)
            i = i-1
            count_23 = count_23 + 1
            non_data = non_data + 1

        else:
            data_close_first_23[key].append(data_first_23["daily_quotes"][0]["AdjustmentClose"])
            data_close_last_23[key].append(data_last_23["daily_quotes"][0]["AdjustmentClose"])
    Cardi_rep = Cardi_rep - non_data
        

print("********** 株価読み取り終了 **********")
real_cardi = Cardi - count
real_cardi_23 = Cardi - count_23
print("real_cardi :", real_cardi)
print("real_cardi_23 :", real_cardi_23)


# 取引高・産業分野・銘柄コードの取得
volume= []
volume_ave = []
url_sector = "https://api.jquants.com/v1/listed/info"
url_numstock = "https://api.jquants.com/v1/fins/statements"
sector_list = []
company_name_list = []
code_list = []
numstock_list = []
code_list_23 = []
from_vol = "2022-04-01"
to_vol = "2023-03-31"
import yfinance as yf

i = -1
real_cardi_rep = real_cardi
count_rep = 0
while count_rep < real_cardi_rep:
    count_rep = count_rep + 1
    i = i + 1
    # 産業分野（Sector）の取得
    res_sector = requests.get(f"{url_sector}?code={code_2022[i]}&date={from_22}", headers=headers)
    data_sector = res_sector.json()
    sector = [quote["Sector17CodeName"] for quote in data_sector["info"]]
    sector_list.append(sector[0])
    company_name = [quote["CompanyName"] for quote in data_sector["info"]]
    company_name_list.append(company_name[0])


    # 取引高（Volume）の取得
    res_volume = requests.get(f"{url}?code={code_2022[i]}&from={from_vol}&to={to_vol}", headers=headers)
    data_volume = res_volume.json()
    volume = [quote["Volume"] for quote in data_volume["daily_quotes"]]
    volume_sum = 0
    volume_flag = True
    for k in range(len(volume)):
        if volume[k] is not None:
            volume_sum += volume[k]
        else:
            print(code_2022[i], "のvolumeでNoneあり、銘柄コードを削除します")
            volume_flag = False
            for key in monthly_data.keys():
                data_close_first[key].pop(i)
                data_close_last[key].pop(i)
            break
    
    if volume_flag :
        volume_ave.append(volume_sum / len(volume))
    else:
        code_2022.pop(i)
        real_cardi = real_cardi - 1
        i = i - 1
        # real_cardi_rep = real_cardi_rep - 1
        volume_flag = True

print("********** 産業分野、取引高、銘柄名の読み込み終了 **********")
print("real_cardi :", real_cardi)
print("len(volume_ave) :", len(volume_ave))

i = -1
count_rep = 0
real_cardi_rep = real_cardi
while count_rep < real_cardi_rep:
    count_rep = count_rep + 1
    i = i + 1
    stock = yf.Ticker(f"{code_2022[i]}.T")
    shares_outstanding = stock.info.get("sharesOutstanding")
    if shares_outstanding is not None:
        numstock_list.append(shares_outstanding)
        # 銘柄コードの取得
        code_list.append(code_2022[i])
    else:
        print(code_2022[i], "のnumstockでNoneあり、銘柄コードを削除します(2022)")
        for key in monthly_data.keys():
            data_close_first[key].pop(i)
            data_close_last[key].pop(i)
        volume_ave.pop(i)
        code_2022.pop(i)
        real_cardi = real_cardi - 1
        # real_cardi_rep = real_cardi_rep - 1
        i = i - 1
print("********** numstock_listの読み込み終了 **********")
print("real_cardi :", real_cardi)
print("len(volume_ave) :", len(volume_ave))
print("len(numstock_list) :", len(numstock_list))


numstock_list_23 = []
i = -1
count_rep = 0
real_cardi_23_rep = real_cardi_23
while count_rep < real_cardi_23_rep:
    count_rep = count_rep + 1
    i = i + 1
    stock = yf.Ticker(f"{code_2023[i]}.T")
    shares_outstanding = stock.info.get("sharesOutstanding")
    if shares_outstanding is not None:
        numstock_list_23.append(shares_outstanding)
        code_list_23.append(code_2023[i])
    else:
        print(code_2023[i], "のnumstockでNoneあり、銘柄コードを削除します(2023)")
        for key in monthly_data_23.keys():
            data_close_first_23[key].pop(i)
            data_close_last_23[key].pop(i)
        code_2023.pop(i)
        real_cardi_23 = real_cardi_23 - 1
        # real_cardi_23_rep = real_cardi_23_rep - 1
        i = i - 1

print("********** numstock_list_23の読み込み終了 **********")
print("real_cardi_23 :", real_cardi_23)
print("len(numstock_list_23) :", len(numstock_list_23))
# print(numstock_list)
# print(numstock_list_23)
# print(data_close_first)
# print(data_close_first_23)

# csvファイルに株価、volumeの書き込み
with open (f"Cardinality_{Cardi}/volume_{Cardi}.csv", "w", newline='') as f:
    writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
    writer.writerow(volume_ave)

with open (f"Cardinality_{Cardi}/sector_{Cardi}.csv", "w", newline='', encoding='utf-8') as f:
    writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
    writer.writerow(sector_list)

with open (f"Cardinality_{Cardi}/company_name_{Cardi}.csv", "w", newline='', encoding='utf-8') as f:
    writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
    writer.writerow(company_name_list)

with open (f"Cardinality_{Cardi}/code_{Cardi}.csv", "w", newline='', encoding='utf-8') as f:
    writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
    writer.writerow(code_list)

with open (f"Cardinality_{Cardi}/code_{Cardi}_23.csv", "w", newline='', encoding='utf-8') as f:
    writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
    writer.writerow(code_list_23)

with open (f"Cardinality_{Cardi}/data_first_{Cardi}.csv", "w", newline='') as f:
    writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
    writer.writerow(month_key_list)
    for i in range(real_cardi):
        data_csv = []
        for key in monthly_data.keys():
            data_csv.append(numstock_list[i] * data_close_first[key][i]) # 時価総額を格納
        writer.writerow(data_csv)

with open (f"Cardinality_{Cardi}/stockprice_{Cardi}.csv", "w", newline='') as f:
    writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
    writer.writerow(month_key_list)
    for i in range(real_cardi):
        data_csv = []
        for key in monthly_data.keys():
            data_csv.append(data_close_first[key][i]) # 株価だけ
        writer.writerow(data_csv)

with open (f"Cardinality_{Cardi}/data_last_{Cardi}.csv", "w", newline='') as f:
    writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
    writer.writerow(month_key_list)
    for i in range(real_cardi):
        data_csv = []
        for key in monthly_data.keys():
            data_csv.append(numstock_list[i] * data_close_last[key][i])
        writer.writerow(data_csv)

with open (f"Cardinality_{Cardi}/data_first_{Cardi}_23.csv", "w", newline='') as f:
    writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
    writer.writerow(month_key_list_23)
    for i in range(real_cardi_23):
        data_csv = []
        for key in monthly_data_23.keys():
            # if i == 11:
                # print(key, ":", data_close_first_23[key][i])
            data_csv.append(numstock_list_23[i] * data_close_first_23[key][i])
        writer.writerow(data_csv)

with open (f"Cardinality_{Cardi}/data_last_{Cardi}_23.csv", "w", newline='') as f:
    writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
    writer.writerow(month_key_list_23)
    for i in range(real_cardi_23):
        data_csv = []
        for key in monthly_data_23.keys():
            data_csv.append(numstock_list_23[i] * data_close_last_23[key][i])
        writer.writerow(data_csv)


# 3. 4. TOPIXの株価取得
import pandas_datareader.data as web
from datetime import date
import pandas as pd

# 2022
point_topix = []
source = 'stooq'
dt_s = date(2020, 11, 1)
dt_e = date(2023, 3, 31)
symbol = '^TPX'
df_topix = web.DataReader(symbol, source, dt_s, dt_e)
df_topix = df_topix.sort_values("Date").reset_index()
# print(df_topix.loc[df_topix['Date'] == '2022-04-18', 'Close'].values[0])

for i in range(len(df_topix)):
    point_topix.append(df_topix.at[i, "Close"])


# 月初・月末のDateの時のCloseを取得、csvファイルに保存
topix_first = []
topix_last = []

for key in monthly_data.keys():
    date_first = monthly_data[key][0]
    date_last = monthly_data[key][-1]
    topix_first.append(df_topix.loc[df_topix['Date'] == date_first, 'Close'].values[0])
    topix_last.append(df_topix.loc[df_topix['Date'] == date_last, 'Close'].values[0])

with open (f"Cardinality_{Cardi}/topix_first_{Cardi}.csv", "w", newline='') as f:
    writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
    writer.writerow(month_key_list)
    writer.writerow(topix_first)

with open (f"Cardinality_{Cardi}/topix_last_{Cardi}.csv", "w", newline='') as f:
    writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
    writer.writerow(month_key_list)
    writer.writerow(topix_last)
    

# 2023
point_topix_23 = []
source = 'stooq'
dt_s_23 = date(2023, 4, 1)
dt_e_23 = date(2024, 3, 31)
symbol = '^TPX'
df_topix_23 = web.DataReader(symbol, source, dt_s_23, dt_e_23)
df_topix_23 = df_topix_23.sort_values("Date").reset_index()
# print(df_topix.loc[df_topix['Date'] == '2022-04-18', 'Close'].values[0])

for i in range(len(df_topix_23)):
    point_topix_23.append(df_topix_23.at[i, "Close"])


# 月初・月末のDateの時のCloseを取得、csvファイルに保存
topix_first_23 = []
topix_last_23 = []

for key in monthly_data_23.keys():
    date_first_23 = monthly_data_23[key][0]
    date_last_23 = monthly_data_23[key][-1]
    topix_first_23.append(df_topix_23.loc[df_topix_23['Date'] == date_first_23, 'Close'].values[0])
    topix_last_23.append(df_topix_23.loc[df_topix_23['Date'] == date_last_23, 'Close'].values[0])

with open (f"Cardinality_{Cardi}/topix_first_{Cardi}_23.csv", "w", newline='') as f:
    writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
    writer.writerow(month_key_list_23)
    writer.writerow(topix_first_23)

with open (f"Cardinality_{Cardi}/topix_last_{Cardi}_23.csv", "w", newline='') as f:
    writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
    writer.writerow(month_key_list_23)
    writer.writerow(topix_last_23)
    


# 実行時間表示
end_time = time.time()
execution_time = end_time - start_time
print(f"実行時間: {execution_time}秒")