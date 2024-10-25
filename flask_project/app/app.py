#Flaskとrender_template（HTMLを表示させるための関数）をインポート
from flask import Flask, render_template, request, send_file, redirect, url_for, make_response, session
import pandas as pd
import io

give_data = []

#Flaskオブジェクトの生成
app = Flask(__name__)
app.secret_key = 'your_secret_key'


@app.route("/", methods=['GET', 'POST'])
def form():
    if request.method == 'POST':
        # フォームデータをセッションに保存
        session['lamda1'] = request.form.get('lamda1')
        session['lamda2'] = request.form.get('lamda2')
        session['lamda3'] = request.form.get('lamda3')
        session['lamda4'] = request.form.get('lamda4')
        session['position1'] = request.form.get('position1')
        session['position2'] = request.form.get('position2')
        session['position3'] = request.form.get('position3')
        return redirect(url_for('submit'))

    # 1回目は初期値、2回目以降はセッションからデータを取得
    lamda1 = session.get('lamda1', '0.1')
    lamda2 = session.get('lamda2', '0.1')
    lamda3 = session.get('lamda3', '0.1')
    lamda4 = session.get('lamda4', '0.1')
    position1 = session.get('position1', '100')
    position2 = session.get('position2', '100000')
    position3 = session.get('position3', '100000')

    return render_template('form.html', lamda1=lamda1, lamda2=lamda2,
                                        lamda3=lamda3, lamda4=lamda4,
                                        position1=position1, position2=position2,
                                        position3=position3)

@app.route('/return_to_form')
def return_to_form():
    response = make_response(render_template('form.html'))
    
    return response

@app.route('/submit', methods=['GET', 'POST'])
def submit():
    if request.method == 'POST':
        # ここでセッションに保存
        session['lamda1'] = request.form.get('lamda1')
        session['lamda2'] = request.form.get('lamda2')
        session['lamda3'] = request.form.get('lamda3')
        session['lamda4'] = request.form.get('lamda4')
        session['position1'] = request.form.get('position1')
        session['position2'] = request.form.get('position2')
        session['position3'] = request.form.get('position3')

    # フォームから送信されたデータを取得
    lamda1 = float(session.get('lamda1', 0.1))
    position1 = int(session.get('position1', '100'))
    lamda2 = float(session.get('lamda2', 0.1))
    position2 = int(session.get('position2', '100000'))
    lamda3 = float(session.get('lamda3', 0.1))
    position3 = int(session.get('position3', '100000'))
    lamda4 = float(session.get('lamda4', 0.1))


    # 1. 変数の初期設定等
    Cardi = 2000 # データの読み込み数
    Cardi_want = int(position1) # カーディナリティ制約
    Budget_want = int(position2) # 予算制約
    Volume_want = int(position3) # 流動性制約
    # Cardi_want = 100 # カーディナリティ制約
    # Budget_want = 600000 # 予算制約
    # Volume_want = 100000 # 流動性制約
    import time
    start_time = time.time()

    # 2.1. Jquantsトークン等取得
    import requests
    import json

    with open('flask_project/app/config.json', 'r') as config_file:
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

    # 2. 2. time_pointを先に取得
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

    # 2. 3. 二値変数の生成
    from amplify import VariableGenerator
    gen = VariableGenerator()
    q = gen.array("Binary", 2146) # 二値変数
    print(q)
    object_f = 0
    over_return = []

    # 2. 4. CSVファイルからデータ読み込み
    import csv
    import os
    import numpy as np
    real_cardi = -1 # 銘柄コード除外した分の個数
    real_cardi_23 = -1
    dumyy = 0

    def read_data(array, filename):
        data_file_path = os.path.join(os.path.dirname(__file__), f'../data/Cardinality_{Cardi}/{filename}.csv')
        with open(data_file_path, 'r', encoding='utf-8') as file:
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
        data_file_path = os.path.join(os.path.dirname(__file__), f'../data/Cardinality_{Cardi}/{filename}.csv')
        with open(data_file_path, 'r', encoding='utf-8') as file:
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

    def read_other(array, filename):
        data_file_path = os.path.join(os.path.dirname(__file__), f'../data/Cardinality_{Cardi}/{filename}.csv')
        with open(data_file_path, 'r', encoding='utf-8') as file:
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
    data_file_path = os.path.join(os.path.dirname(__file__), f'../data/Cardinality_{Cardi}/sector_{Cardi}.csv')
    with open(data_file_path, 'r', encoding='utf-8') as file:
        csv_reader = csv.reader(file)
        for row in csv_reader:
            sector.append(row)
    
    company_name = []
    data_file_path = os.path.join(os.path.dirname(__file__), f'../data/Cardinality_{Cardi}/company_name_{Cardi}.csv')
    with open(data_file_path, 'r', encoding='utf-8') as file:
        csv_reader = csv.reader(file)
        for row in csv_reader:
            company_name.append(row)
    
    #2.5. 重みの計算
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


    # 3. 1. 超過リターンの計算
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
    f += lamda1 * (Cardi_want - Cardi_sum) ** 2

    # 2. 予算の拡充度制約
    Budget_sum = 0
    for i in range(real_cardi):
            Budget_sum += stock_price_np[i][0] * q[i]

    f += lamda2 * ((Budget_want - Budget_sum) * 1/10000) ** 2

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
    f += lamda3 * (Cardi_want - count_volume) ** 2


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
        f += lamda4*(( dict_sector_t[key] / real_cardi ) - ( dict_sector_p[key] / real_cardi )) ** 2




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

    count_same = 0
    for item in selected_indices:
        for i in range(len(code_2023_np[0])):
            if(code_2022_np[0][item] == code_2023_np[0][i]):
                selected_indices_2023.append(i)
                count_same += 1
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


    sum_seleceted_weight_23 = 0
    for item in selected_indices_2023:
        sum_seleceted_weight_23 += weight_23[item]

    # 産業分野の割合、予算合計、流動性の結果計算
    dict_sector_p_res = {}
    i = 0
    count_equal = 0
    give_data = []
    for item in selected_indices:
        for item_23 in selected_indices_2023:
            if(code_2022_np[0][item] == code_2023_np[0][item_23]):
                count_equal += 1
                Budget_sum += stock_price_np[item][0]
                volume_result.append(volume_ave_np[0][item] / 1000)
                add_to_dict(sector[0][item], dict_sector_p_res, 1)
                # result.htmlに渡すデータ準備
                # ratio = round((weight_23[item_23]/sum_seleceted_weight_23)*100, 2)
                ratio = (weight_23[item_23]/sum_seleceted_weight_23) * 100
                give_data.append([int(code_2022_np[0][item]), company_name[0][item], sector[0][item], float(round(ratio, 2))])
                i += 1
                break
        
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
    # graph_date = ["2023-04", "2023-05", "2023-06", "2023-07", "2023-08", "2023-09",
    #              "2023-10", "2023-11", "2023-12", "2024-01", "2024-02", "2024-03"]
    graph_date = ["2023-4", "5", "6", "7", "8", "9",
                 "10", "11", "12", "2024-1", "2", "3"]

    fig2, ax1 = plt.subplots()
    ax1.set_title(f'1年後のTOPIXとポートフォリオ比較 C={Cardi_want}')
    ax1.plot(tp_array_23, label='TOPIX', color='#4D606E')
    ax1.set_ylabel('TOPIX', color='#4D606E')
    ax1.tick_params(axis='y', labelcolor='#4D606E')

    ax2 = ax1.twinx()
    ax2.plot(pr_array_23, label='Portfolio', color='#3FBAC2')
    ax2.set_ylabel('ポートフォリオ', color='#3FBAC2')
    ax2.tick_params(axis='y', labelcolor='#3FBAC2')
    plt.xticks(ticks=range(len(graph_date)), labels=graph_date)


    plt.savefig('flask_project/app/static/portfolio_graph.png', dpi=300, bbox_inches='tight')
    # plt.savefig('static/portfolio_graph.png', dpi=300, bbox_inches='tight')

    # plt.show()

    # result.html にデータを渡して表示する
    return render_template('result.html', 
                           lamda1=lamda1, position1=position1,
                           lamda2=lamda2, position2=position2,
                           lamda3=lamda3, position3=position3,
                           lamda4=lamda4, 
                           tracking_error22 = math.sqrt(result.best.objective)*100,
                           tracking_error23 = float(round(math.sqrt(f_23) * 100, 2)),
                           count_q_equals_one = count_q_equals_one,
                           lest_of_money = Budget_want - Budget_sum,
                           give_data = give_data)


@app.route('/download')
def download():
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # あと銘柄名、pfにおける割合、時価総額も表にしたい
        # df = pd.DataFrame(give_data, columns=['銘柄コード', '銘柄名', '産業分野'])
        df = pd.DataFrame(give_data, columns=['銘柄コード', '銘柄名', '産業分野', '構成割合'])
        df.to_excel(writer, index=False, sheet_name='データ')
    output.seek(0)

    return send_file(output, as_attachment=True, download_name='data.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')