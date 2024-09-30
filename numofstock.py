
# 1. 変数の初期設定等
from amplify import VariableGenerator
gen = VariableGenerator()
q = gen.array("Binary", 2146) # 二値変数
Cardi = 100 # データの読み込み数



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



# 取引高・産業分野・銘柄コードの取得
volume= []
volume_ave = []
url_sector = "https://api.jquants.com/v1/listed/info"
url_numstock = "https://api.jquants.com/v1/fins/statements"
sector_list = []
code_list = []
numstock_list = []
code_list_23 = []
from_vol = "2022-04-01"
to_vol = "2023-03-31"

for i in range(Cardi):

    # 発行済み株式数の取得
    res_numstock = requests.get(f"{url_numstock}?code={code_2022[i]}&date=20230130", headers=headers)
    data_numstock = res_numstock.json()
    print(data_numstock)
    # numstock = [quote["NumberOfIssuedAndOutstandingSharesAtTheEndOfFiscalYearIncludingTreasuryStock"] for quote in data_numstock["statements"]]
    # r = requests.get("https://api.jquants.com/v1/fins/statements?code=86970&date=20230130", headers=headers)
    # r2 = r.json()
    # print(r2)
    # numstock_list.append(numstock[0])


    # # 銘柄コードの取得
    # code_list.append(code_2022[i])
