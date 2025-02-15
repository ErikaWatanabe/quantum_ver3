# 制約条件をコスト関数に入れるもの、()^2の形で

# 1. 変数の初期設定等
Cardi = 1000 # データの読み込み数
Cardi_want = 100 # カーディナリティ制約
Budget_want = 600000 # 予算制約
Volume_want = 100000 # 流動性制約
import time
start_time = time.time()



# 3. 銘柄、購入数の決定
# 3. 1. Jquantsから株価データを取得
import requests
import json
with open('config.json', 'r') as config_file:
    config = json.load(config_file)
email = config['email']
api_password = config['api_password']
token = config['token']

mail_password={"mailaddress":email, "password":api_password}
r_ref = requests.post("https://api.jquants.com/v1/token/auth_user", data=json.dumps(mail_password))
RefreshToken = r_ref.json()["refreshToken"]
r_token = requests.post(f"https://api.jquants.com/v1/token/auth_refresh?refreshtoken={RefreshToken}")
idToken = r_token.json()["idToken"]
headers = {'Authorization': 'Bearer {}'.format(idToken)}

# 3. 2. time_pointを先に取得
time_point = []
from_ = "2020-11-01" # 取得できる期間変わるので定期的に更新しないと
to_ = "2023-03-31"
code_ = "7203"
url = "https://api.jquants.com/v1/prices/daily_quotes"
res = requests.get(f"{url}?code={code_}&from={from_}&to={to_}", headers=headers)
data = res.json()
close_values = [quote["Close"] for quote in data["daily_quotes"]]
for i in range(len(close_values)):
    time_point.append(data["daily_quotes"][i]["Date"])
    
from datetime import datetime
from collections import defaultdict
monthly_data = defaultdict(list)
for date_str in time_point: # 日付を扱いやすいように辞書型に変換
    date = datetime.strptime(date_str, '%Y-%m-%d')
    month_key = date.strftime('%Y-%m')
    monthly_data[month_key].append(date_str)


# 4. 量子アニーリングで組み入れ銘柄決定
# 4. 1. 目的関数の生成
from amplify import VariableGenerator
gen = VariableGenerator()
q = gen.array("Binary", 2146) # 二値変数
print(q)
object_f = 0
over_return = []


# 4. 2. CSVファイルからデータ読み込み
import csv
import numpy as np
real_cardi = -1 # 銘柄コード除外した分の個数
real_cardi_23 = -1
dumyy = 0

# 2022年度のTOPIX, 株価の読み込み
def read_data(array, filename):
    with open(f"Cardinality_{Cardi}/{filename}.csv", mode='r', encoding='utf-8') as file:
        csv_reader = csv.reader(file)
        for row in csv_reader:
            array.append(row)
    array_np = np.array(array[1:], dtype=float)
    return array_np

topix_first = []
topix_first_np = read_data(topix_first, f"topix_first_{Cardi}")

topix_last = []
topix_last_np = read_data(topix_last, f"topix_last_{Cardi}")

stock_price = []
stock_price_np = read_data(stock_price, f"stockprice_{Cardi}")

topix_first_23 = []
topix_first_np_23 = read_data(topix_first_23, f"topix_first_{Cardi}_23")

topix_last_23 = []
topix_last_np_23 = read_data(topix_last_23, f"topix_last_{Cardi}_23")


def read_portfolio(array, filename, rc):
    with open(f"Cardinality_{Cardi}/{filename}.csv", mode='r', encoding='utf-8') as file:
        csv_reader = csv.reader(file)
        for row in csv_reader:
            array.append(row)
            rc += 1
    array_np = np.array(array[1:], dtype=float)
    return array_np, rc

portfolio_first = []
portfolio_first_np, real_cardi = read_portfolio(portfolio_first, f"data_first_{Cardi}", real_cardi)

portfolio_last = []
portfolio_last_np, dumyy = read_portfolio(portfolio_last, f"data_last_{Cardi}", dumyy)

portfolio_first_23 = []
portfolio_first_np_23, real_cardi_23 = read_portfolio(portfolio_first_23, f"data_first_{Cardi}_23", real_cardi_23)

portfolio_last_23 = []
portfolio_last_np_23, dumyy = read_portfolio(portfolio_last_23, f"data_last_{Cardi}_23", dumyy)


# 取引高、産業分野、銘柄コードの読み込み
def read_other(array, filename):
    with open(f"Cardinality_{Cardi}/{filename}.csv", mode='r', encoding='utf-8') as file:
        csv_reader = csv.reader(file)
        for row in csv_reader:
            array.append(row)
    array_np = np.array(array, dtype=float)
    return array_np

volume_ave = []
volume_ave_np = read_other(volume_ave, f"volume_{Cardi}")

code_2022 = []
code_2022_np = read_other(code_2022, f"code_{Cardi}")

code_2023 = []
code_2023_np = read_other(code_2023, f"code_{Cardi}_23")

sector = []
with open(f"Cardinality_{Cardi}/sector_{Cardi}.csv", mode='r', encoding='utf-8') as file:
    csv_reader = csv.reader(file)
    for row in csv_reader:
        sector.append(row)

# 重みの計算
weight = []
sum_weight = 0
for i in range(real_cardi):
    sum_weight = sum_weight + portfolio_first_np[i][0]
for i in range(real_cardi):
    weight.append(portfolio_first_np[i][0] / sum_weight)

weight_23 = []
sum_weight_23 = 0
for i in range(real_cardi_23):
    sum_weight_23 = sum_weight_23 + portfolio_first_np_23[i][0]
for i in range(real_cardi_23):
    weight_23.append(portfolio_first_np_23[i][0] / sum_weight_23)


# 4. 2. 超過リターンの計算
import math
for i in range(len(topix_first_np[0])):
    topix_return = (topix_last_np[0][i] - topix_first_np[0][i]) / topix_first_np[0][i]
    portfolio_return = 0
    for j in range(real_cardi):
        # ここで二値変数q[i]、重みをかける！
        # portfolio_return = portfolio_return + weight[j] * (portfolio_last_np[j][i] - portfolio_first_np[j][i]) * q[j] / portfolio_first_np[j][i]
        portfolio_return = portfolio_return + weight[j] * (portfolio_last_np[j][i] - portfolio_first_np[j][i]) * q[j] / portfolio_first_np[j][i]
    over_return.append(portfolio_return - topix_return)

over_return_ave = np.mean(over_return)

# 目的関数
diff_sum = 0
for i in range(len(over_return)):  # len(over_return)は観測期間の数、つまり月の数=29
    diff_sum = diff_sum + (over_return[i] - over_return_ave) ** 2
f = diff_sum / ( len(over_return) - 1 )

# 1. カーディナリティ制約
Cardi_sum = 0
for i in range(real_cardi):
        Cardi_sum += q[i]
f += 0.1 * (Cardi_want - Cardi_sum) ** 2

# 2. 予算の拡充度制約
Budget_sum = 0
for i in range(real_cardi):
        Budget_sum += stock_price_np[i][0] * q[i]

# f += 0.001 * ((Budget_want - Budget_sum) * 1/10000) ** 2

# 3. 取引の流動性制約
count_volume = 0
true = True
false = False
for i in range(real_cardi):
    if(volume_ave_np[0][i] >= float(Volume_want)):
        count_volume += q[i] * true
    else:
        count_volume += q[i] * false
        # print("20万以下 : ", i)
f += 0.1 * (Cardi_want - count_volume) ** 2


# 4. 産業の構成割合制約
def add_to_dict(key, dict, value):
    if key in dict:
        dict[key] += value
    else:
        dict[key] = value

dict_sector_t = {}
dict_sector_p = {}
for i in range(real_cardi):
    add_to_dict(sector[0][i], dict_sector_t, 1)
    add_to_dict(sector[0][i], dict_sector_p, q[i])

for key in dict_sector_t.keys():
    f += 0.001*(( dict_sector_t[key] / real_cardi ) - ( dict_sector_p[key] / real_cardi )) ** 2


# 5. ボラティリティ制約





from amplify import FixstarsClient
client = FixstarsClient()
client.token = token 
client.parameters.timeout = 1000
from amplify import solve
result = solve(f, client)

# print(result.best.values)
# print(result.best.objective)
# print(f"{q} = {q.evaluate(result.best.values)}")
filtered_result = {str(key).replace('Poly', '').strip('()'): value for key, value in result.best.values.items() if value == 1}
# print(filtered_result)
count_q_equals_one = sum(1 for key, value in result.best.values.items() if value == 1)
print(f"q[i] = 1 の数: {count_q_equals_one}")


Budget_sum = 0
selected_indices = []
volume_result = []

for key, value in result.best.values.items() :
    if value == 1:
        index = str(key).replace('q_', '')
        if not (index.isdigit()):
            index = index.replace('{', '').replace('}', '')
        index = int(index)
        selected_indices.append(index)


# 2023年度のトラッキングエラー計算
# グラフ用に2022のポイント格納
selected_indices_2023 = []
pr_array = []
tp_array = []
# print("over_return_ave", over_return_ave)
# print("over_return", over_return)
for i in range(len(topix_first_np[0])):
    pr = 0
    for item in selected_indices:
        pr = pr + portfolio_first_np[item][i]
    pr_array.append(pr)
    tp_array.append(topix_first_np[0][i])

for item in selected_indices:
    for i in range(len(code_2023_np[0])):
        if(code_2022_np[0][item] == code_2023_np[0][i]):
            selected_indices_2023.append(i)
            # print(code_2022_np[0][item], code_2023_np[0][i])
            continue


over_return_23 = []
pr_array_23 = []
tp_array_23 = []


for i in range(12):
    topix_return_23 = (topix_last_np_23[0][i] - topix_first_np_23[0][i]) / topix_first_np_23[0][i]
    portfolio_return_23 = 0
    pr = 0
    for item in selected_indices_2023:
        # print("portfolio_first_np_23[", item, "][", i, "]", portfolio_first_np_23[item][i])
        pr = pr + portfolio_first_np_23[item][i]
        portfolio_return_23 = portfolio_return_23 + weight_23[item] * (portfolio_last_np_23[item][i] - portfolio_first_np_23[item][i]) / portfolio_first_np_23[item][i]
        # print(portfolio_return_23)
    over_return_23.append(portfolio_return_23 - topix_return_23)
    pr_array_23.append(pr)
    tp_array_23.append(topix_first_np_23[0][i])
    # print("pr", pr)
    # print("")



over_return_ave_23 = np.mean(over_return_23)

mult_23 = 0
for i in range(len(over_return_23)):
    mult_23 = mult_23 + (over_return_23[i] - over_return_ave_23) ** 2
f_23 = mult_23 / (len(over_return_23) - 1)



# 産業分野の割合、予算合計、流動性の結果計算
dict_sector_p_res = {}
for select_i in selected_indices:
    Budget_sum += stock_price_np[select_i][0]
    volume_result.append(volume_ave_np[0][select_i] / 1000)
    add_to_dict(sector[0][select_i], dict_sector_p_res, 1)

import unicodedata
def width_adjusted_string(s, width):
    count = 0
    for char in s:
        if unicodedata.east_asian_width(char) in 'WF':  # 全角
            count += 2
        else:  # 半角
            count += 1
    return s + ' ' * (width - count)
for key in dict_sector_p_res.keys():
    adjusted_key = width_adjusted_string(str(key), 25)
    # print(f"{adjusted_key} || TOPIX : {dict_sector_t[key] / real_cardi:.2f} | Portfolio : {dict_sector_p_res[key] / count_q_equals_one:.2f}")


print("Budget_sum:", Budget_sum)
# print("volume_result:", volume_result)
print("float(Volume_want):", float(Volume_want))
print("----------------------------------------------------")
print("トラッキングエラー(2022) : ", math.sqrt(result.best.objective) * 100)
print("トラッキングエラー(2023) : ", math.sqrt(f_23) * 100)

# 実行時間表示
end_time = time.time()
execution_time = end_time - start_time
print(f"実行時間: {execution_time}秒")


# グラフ書いてみる
import matplotlib.pyplot as plt
import japanize_matplotlib
from matplotlib.ticker import MaxNLocator
japanize_matplotlib.japanize()


# fig1, ax1 = plt.subplots()
# ax1.set_title('2022年のTOPIXとポートフォリオの比較')
# ax1.plot(tp_array, label='TOPIX', color='blue')
# ax1.set_ylabel('TOPIX', color='blue')
# ax1.tick_params(axis='y', labelcolor='blue')
# ax2 = ax1.twinx()
# ax2.plot(pr_array, label='Portfolio', color='green')
# ax2.set_ylabel('ポートフォリオ', color='green')
# ax2.tick_params(axis='y', labelcolor='green')


# fig2, ax1 = plt.subplots()
# ax1.set_title('2023年のTOPIXとポートフォリオの比較')
# ax1.plot(tp_array_23, label='TOPIX', color='blue')
# ax1.set_ylabel('TOPIX', color='blue')
# ax1.tick_params(axis='y', labelcolor='blue')
# ax2 = ax1.twinx()
# ax2.plot(pr_array_23, label='Portfolio', color='green')
# ax2.set_ylabel('ポートフォリオ', color='green')
# ax2.tick_params(axis='y', labelcolor='green')

pr_sum = pr_array + pr_array_23
tp_sum = tp_array + tp_array_23
# print("tp_array", pr_array)
# print("tp_array_23", pr_array_23)
# print(tp_sum)
fig3, ax1 = plt.subplots()
ax1.set_title('過去3年のTEを最小化するようなポートフォリオ')
ax1.plot(tp_sum, label='TOPIX', color='blue')
ax1.set_ylabel('TOPIX', color='blue')
ax1.tick_params(axis='y', labelcolor='blue')
ax2 = ax1.twinx()
ax2.plot(pr_sum, label='Portfolio', color='green')
ax2.set_ylabel('ポートフォリオ', color='green')
ax2.tick_params(axis='y', labelcolor='green')

plt.show()



