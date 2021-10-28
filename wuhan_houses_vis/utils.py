import pandas as pd
import pyecharts
from pyecharts import options as opts
from pyecharts.charts import Bar, Sunburst, Geo, Map, ThemeRiver, Pie, WordCloud, Page
from pyecharts.components import Table

from pyecharts.globals import GeoType
import numpy as np
import math
from bs4 import BeautifulSoup

pyecharts.globals._WarningControl.ShowWarning = False


def get_datapairs(origin_list, item_index=0xffff, single_list=True, descend=False):
    item_list = []
    times = []

    if item_index == 0xffff and not single_list:
        raise Exception('请正确给出目标索引')

    for items in origin_list:
        if single_list:
            if items not in item_list:
                item_list.append(items)
                times.append(1)
            else:
                index = item_list.index(items)
                times[index] += 1
        else:
            if items[item_index] not in item_list:
                item_list.append(items[item_index])
                times.append(1)
            else:
                index = item_list.index(items[item_index])
                times[index] += 1

    if len(times) != len(item_list):
        raise Exception('获取次数故障！')

    data_pairs = [list(z) for z in zip(item_list, times)]
    if descend:
        data_pairs.sort(key=lambda x: x[1], reverse=True)

    return data_pairs


def get_top(origin_list, top_k, index=0xffff, others=True):
    i = 0
    top_pair = []

    if index == 0xffff:
        raise Exception('请正确给出目标索引')

    for data in origin_list:
        if i < top_k:
            top_pair.append(data)
        elif others:
            if i == top_k:
                top_pair.append(['其他', data[index]])
            else:
                top_pair[top_k][index] += data[index]
        else:
            break
        i += 1
    return top_pair


def get_pricebar(origin_data, width, height):
    # 提取将二手房数据有用的列，即价格，朝向和面积，按面积进行排序，转化成list
    houses = origin_data.iloc[:, [1, 9, 10]]
    houses = houses.values.tolist()
    houses.sort(key=lambda x: x[2], reverse=False)

    # 设置面积大小分组
    areas = ["100㎡以下", "100-150㎡", "150-200㎡", "200-250㎡", "250-300㎡", "300-350㎡", "350-400㎡", "400㎡以上", ]

    # 获取朝向数
    orients = ['西南', '东南', '东西', '南北', '其他']
    colors = ['#64C6FA', '#4585DE', '#5875F5', '#4D45DE', '#8350CC']

    # 将数据整理成方便进行绘图的格式
    orients_houses = []  # 方位数 * 2指标 * 8分组
    bar_data = []

    for i in range(len(orients)):
        orients_houses.append([])
        bar_data.append([])
        for j in range(2):
            orients_houses[i].append([])
            bar_data[i].append([])
            for k in range(8):
                orients_houses[i][j].append([])
        # 方位数 * 两指标 * 8分组

        for house in houses:
            if house[1] == orients[i]:
                price_mean = house[0] // house[2]

                if house[2] < 100.0:
                    index = 0
                elif house[2] >= 400:
                    index = 7
                else:
                    index = int((house[2] - 100.0) // 50.0) + 1

                orients_houses[i][0][index].append(house[0])
                orients_houses[i][1][index].append(price_mean)
                houses.remove(house)

        # L= np.array(bar_data)
        # print(L.shape)
        # 对8个分组的内容进行平均
        for j in range(2):
            for k in range(8):
                bar_data[i][j].append(float(np.mean(orients_houses[i][j][k])))
                bar_data[i][j][k] = 0 if math.isnan(bar_data[i][j][k]) else bar_data[i][j][k]
                bar_data[i][j][k] = round(bar_data[i][j][k], 2)

    pricebar = Bar(init_opts=opts.InitOpts(width=str(width) + "px", height=str(height) + "px"))
    pricebar.add_xaxis(areas)

    for i in range(len(orients)):
        pricebar.add_yaxis(series_name=orients[i], y_axis=bar_data[i][0], color=colors[i])
    pricebar.set_global_opts(
        title_opts=opts.TitleOpts(
            title='武汉市二手房平均房价(单位：万元)', pos_left="center", pos_top="0",
            title_textstyle_opts=opts.TextStyleOpts(font_size=15, color="white"),
        ),
        yaxis_opts=opts.AxisOpts(
            splitline_opts=opts.SplitLineOpts(is_show=True), max_=1200,
            name_textstyle_opts=opts.TextStyleOpts(color="white"),
            axisline_opts=opts.AxisLineOpts(linestyle_opts=opts.LineStyleOpts(color='white'))
        ),
        legend_opts=opts.LegendOpts(
            is_show=True, pos_left="center", pos_top='30',
            textstyle_opts=opts.TextStyleOpts(color="white")
        ),
        xaxis_opts=opts.AxisOpts(
            name_textstyle_opts=opts.TextStyleOpts(color="white"),
            axisline_opts=opts.AxisLineOpts(linestyle_opts=opts.LineStyleOpts(color='white'))
        ),
    )
    pricebar.set_series_opts(
        label_opts=opts.LabelOpts(is_show=False),
        itemstyle_opts={"barBorderRadius": [1.7, 1.7, 0, 0]}
    )
    # pricebar.render('test.html')

    return pricebar


def add_child(child_list, address, n, length):
    for child in child_list:
        if child["name"] == address[n]:  # 如果子列表里有相同的键值
            child["value"] += 1
            if n == length:  # 如果是最后一层，那么说明有两个相同的楼盘，value+1
                return
            else:  # 如果不是最后一层，那么向下递进，看看是否后面一样。
                if "children" not in child:  # 当没有孩子时，创建孩子列表递进。
                    child["children"] = []
                add_child(child["children"], address, n + 1, length)
                return
    child = {"name": address[n], "value": 1}  # 如果是新的孩子
    if n == length:  # 如果新的孩子是在最后一层，将孩子的值设为1，将新的孩子添加到孩子列表,然后返回
        child_list.append(child)
        return
    else:  # 如果新的孩子不在最后一层，那么后面的孩子其实也是新的，需要递进补充孩子
        child["children"] = []
        child_list.append(child)
        add_child(child["children"], address, n + 1, length)
        return


def get_clip(origin_dic, level_num):

    temp = []
    if level_num == 0:  # 处理第一层的孩子，即修剪第二层
        tops = 4  # 取第二层最前面4个孩子
        for child in origin_dic["children"]:
            if len(temp) < tops:  # 遍历不够四个孩子
                temp.append(child)
                continue
            for i in range(tops):  # 四个孩子之后开始取value值最大的孩子
                if child["value"] >= temp[i]["value"]:  # 找到rank
                    temp.insert(i, child)  # 插入到rank中
                    temp.pop()  # 把挤出rank的孩子删掉
                    break
        origin_dic["children"] = temp
        temp_value = 0
        for child in origin_dic["children"]:  # 递归对孩子的孩子进行修剪
            get_clip(child, level_num=1)
            temp_value += child["value"]
        origin_dic["value"] = temp_value
        return
    else:
        tops = 3  # 如果是修剪第三层，取前面3个孩子
        for child in origin_dic["children"]:
            if len(temp) < tops:
                temp.append(child)
                continue
            for i in range(tops):
                if child["value"] >= temp[i]["value"]:
                    temp.insert(i, child)
                    temp.pop()
                    break
        origin_dic["children"] = temp
        temp_value = 0
        for child in origin_dic["children"]:  # 递归对孩子的孩子进行修剪
            temp_value += child["value"]
        origin_dic["value"] = temp_value
        return


def get_sunburst(origin_data, width, height):
    addresses = origin_data.loc[:, '楼盘地址']
    addresses = addresses.loc[addresses.notna()]
    addresses = addresses.values.tolist()
    suffixs = ['路', '道', '街', '村', '桥', '堤', '墩']
    for i in range(len(addresses)):
        addresses[i] = addresses[i].split('-')
        for suffix in suffixs:
            temp = (addresses[i][2].split(suffix))[0]
            if addresses[i][2] != temp:
                addresses[i][2] = temp + suffix
    data = []
    for i in range(len(addresses)):
        add_child(data, addresses[i], 0, 2)

    for root in data:
        get_clip(root, 0)

    sunbrust = Sunburst(init_opts=opts.InitOpts(width=str(width) + "px", height=str(height) + "px"))
    sunbrust.add(
        "",
        data_pair=data,
        highlight_policy="ancestor",
        radius=[0, "95%"],
        sort_="null",
        levels=[
            {},
            {
                "r0": "15%",
                "r": "35%",
                "itemStyle": {"borderWidth": 2},
                "label": {"rotate": "tangential"},
            },
            {
                "r0": "35%",
                "r": "70%",
                "label": {"align": "right"}},
            {
                "r0": "70%",
                "r": "73%",
                "label": {"position": "outside", "padding": 3, "silent": False},
                "itemStyle": {"borderWidth": 3},
            },
        ],
    )
    sunbrust.set_global_opts()
    sunbrust.set_series_opts(label_opts=opts.LabelOpts(formatter="{b}"))
    return sunbrust


def get_distrimap_house(origin_data, supply_data, width, height):
    prices_areas = origin_data.loc[:, ['楼盘均价', '区域']]
    prices_areas = prices_areas.loc[prices_areas['楼盘均价'].notna()]
    prices_areas = prices_areas.loc[prices_areas['区域'].notna()]
    prices_areas = prices_areas.values.tolist()

    areas = []
    prices = []
    prices_mean = []
    for price_area in prices_areas:
        if price_area[1] not in areas:
            areas.append(price_area[1])
            prices.append([])
        index = areas.index(price_area[1])
        prices[index].append(price_area[0])

    for i in range(len(areas)):
        areas[i] = areas[i] + '区'

    for area in prices:
        float_price = []
        for strs in area:
            if strs != '.':
                float_price.append(float(strs))

        price_mean = int(np.mean(float_price))
        prices_mean.append(price_mean)

    absence_area = ['蔡甸区', '汉南区', '黄陂区', '新洲区']
    class_list = [[], [], [], []]
    smean_data = []
    sdatas_areas = supply_data.iloc[:, [1, 7, 10]]
    sdatas_areas = sdatas_areas.values.tolist()

    # print(sdatas_areas)
    for sdata_area in sdatas_areas:
        sdata_area[1] = sdata_area[1].split('区')
        sdata_area[1] = sdata_area[1][0] + '区'
        if sdata_area[1] in absence_area:
            index = absence_area.index(sdata_area[1])
            class_list[index].append(sdata_area[0] * 1e4 / sdata_area[2])

    for i in range(len(class_list)):
        smean_data.append(int(np.mean(class_list[i])))

    areas.extend(absence_area)
    prices_mean.extend(smean_data)

    pieces = [
        {'max': 25000.00, 'min': 22000.00, 'label': '2.2-2.5万', 'color': '#000B87'},
        {'max': 22000.00, 'min': 20000.00, 'label': '2.0-2.2万', 'color': '#0534B5'},
        {'max': 20000.00, 'min': 18000.00, 'label': '1.8-2.0万', 'color': '#085FC9'},
        {'max': 18000.00, 'min': 15000.00, 'label': '1.5-1.8万', 'color': '#027FC7'},
        {'max': 15000.00, 'min': 13000.00, 'label': '1.3-1.5万', 'color': '#0CABCF'},
        {'max': 13000.00, 'label': '1.3万以下', 'color': '#AFEAF5'}
    ]

    price_map = Map(init_opts=opts.InitOpts(width=str(width) + "px", height=str(height) + "px"))
    price_map.add("", [list(z) for z in zip(areas, prices_mean)], "武汉", is_map_symbol_show=False, )
    price_map.set_global_opts(
        visualmap_opts=opts.VisualMapOpts(
            is_piecewise=True, pieces=pieces,
            textstyle_opts=opts.TextStyleOpts(color="white")
        ),
        title_opts=opts.TitleOpts(
            title="武汉市各区二手房每平方米均价", pos_left="center", pos_top="0px",
            title_textstyle_opts=opts.TextStyleOpts(font_size=15, color="white"),
        ),
        xaxis_opts=opts.AxisOpts(name_textstyle_opts=opts.TextStyleOpts(color="white")),
        yaxis_opts=opts.AxisOpts(name_textstyle_opts=opts.TextStyleOpts(color="white")),
        legend_opts=opts.LegendOpts(textstyle_opts=opts.TextStyleOpts(color="white")),

    )
    price_map.set_series_opts(label_opts=opts.LabelOpts(is_show=False))
    # price_map.render('wuhanjiage.html')
    return price_map


def get_themeriver(origin_data, width, height):
    datas_areas = origin_data.loc[:, ['发布日期', '所属区名称']]

    datas_areas = datas_areas.loc[datas_areas['发布日期'].notna()]
    datas_areas = datas_areas.loc[datas_areas['所属区名称'].notna()]
    datas_areas = datas_areas.values.tolist()

    months = []
    areas = []
    datas = []
    times = []
    x_data = []

    for data_area in datas_areas:
        date = data_area[0].split(' ')
        date = date[0].split('-')
        months.append(date[0] + '/' + date[1])
        areas.append(data_area[1])
    months_areas = zip(months, areas)
    for month_area in months_areas:
        temp = [str(month_area[0]), 0, str(month_area[1])]
        if temp not in datas:
            datas.append(temp)
            times.append(1)
        else:
            index = datas.index(temp)
            times[index] += 1

    for i in range(len(times)):
        datas[i][1] = times[i]

    for area in areas:
        if area not in x_data:
            x_data.append(area)

    themeriver = ThemeRiver(init_opts=opts.InitOpts(width=str(width) + "px", height=str(height) + "px"))
    themeriver.add(series_name=x_data, data=datas,
                   singleaxis_opts=opts.SingleAxisOpts(pos_top="50", pos_bottom="50", type_="time"),

                   )
    themeriver.set_global_opts(
        tooltip_opts=opts.TooltipOpts(trigger="axis", axis_pointer_type="line"),
        legend_opts=opts.LegendOpts(is_show=False),
        title_opts=opts.TitleOpts(
            title="武汉市各区二手房挂牌数量变化", pos_left="center", pos_top="5px",
            title_textstyle_opts=opts.TextStyleOpts(font_size=15, color="white"),

        ),
        datazoom_opts=opts.DataZoomOpts(pos_bottom='-10px', range_start=0, range_end=100),
        xaxis_opts=opts.AxisOpts(
            name_textstyle_opts=opts.TextStyleOpts(color="white"),
            axisline_opts=opts.AxisLineOpts(linestyle_opts=opts.LineStyleOpts(color='white'))
        ),
        yaxis_opts=opts.AxisOpts(
            name_textstyle_opts=opts.TextStyleOpts(color="white"),
            axisline_opts=opts.AxisLineOpts(linestyle_opts=opts.LineStyleOpts(color='white'))
        ),
    )
    themeriver.set_series_opts(label_opts=opts.LabelOpts(is_show=False))
    # themeriver.render('river.html')
    return themeriver


def get_distrimap_eval(origin_data, width, height):
    addresses = origin_data.loc[:, ['名称', '经度', '纬度', '资质评级']]
    addresses = addresses.values.tolist()
    # print(addresses)

    city = '武汉'
    # level = ["一级", "一级分支机构", "二级"]
    data_pair = []
    pieces = [
        {'max': "一级", 'min': "一级", 'label': '一级资质公司', 'color': '#A72BFF'},
        {'max': "一级分支机构", 'min': "一级分支机构", 'label': '一级资质分支公司', 'color': '#7D1CE8'},
        {'max': "二级", 'min': "二级", 'label': '二级资质公司', 'color': '#541AB8'}
    ]

    eval_distrimap = Geo(init_opts=opts.InitOpts(width=str(width) + "px", height=str(height) + "px"))
    eval_distrimap.add_schema(
        maptype=city,
        itemstyle_opts=opts.ItemStyleOpts(color="#5284FF", border_color="#7BCAFF"),
        center=[114.378278216284688, 30.625506735739196],
    )
    for address in addresses:
        eval_distrimap.add_coordinate(address[0], address[1], address[2])
        data_pair.append([address[0], address[3]])
    eval_distrimap.add('', data_pair=data_pair, type_=GeoType.EFFECT_SCATTER, symbol_size=5)
    eval_distrimap.set_global_opts(
        visualmap_opts=opts.VisualMapOpts(
            is_piecewise=True, pieces=pieces, pos_right="0px",
            textstyle_opts=opts.TextStyleOpts(color="white"),
        ),
        title_opts=opts.TitleOpts(
            title='武汉市二手房地产资产评估公司分布', pos_left="center", pos_top="0",
            title_textstyle_opts=opts.TextStyleOpts(font_size=15, color="white"),
        ),
        legend_opts=opts.LegendOpts(textstyle_opts=opts.TextStyleOpts(color="white"))
    )
    eval_distrimap.set_series_opts(
        label_opts=opts.LabelOpts(is_show=False),
    )
    # eval_distrimap.render()
    return eval_distrimap


def get_evalpie(origin_data, width, height, top=10):
    colors = ['#8FA7FF', '#85AEFF', '#85C2FF', '#66DAFA', '#66DAFA', '#73E6C9',
              '#73E6DD', '#87FAA6', '#87FACF', '#A9FAD5', '#9385FF']
    colors = list(colors)
    unions_companies = origin_data.iloc[:, [0, 3]]
    unions_companies = unions_companies.loc[unions_companies['发布机构名称'].notna()]
    unions_companies = unions_companies.values.tolist()

    data_pairs = get_datapairs(unions_companies, item_index=1, descend=True, single_list=False)
    data_pair = get_top(data_pairs, top_k=top, index=1, others=True)

    for data in data_pair:
        if data[0] != '其他':
            data[0] = data[0].split('武汉')[1]
            data[0] = data[0].split('有限公司')[0]
            data[0] = data[0].split('不动产')[0]
            data[0] = data[0].split('房地产')[0]

    evalpie = Pie(init_opts=opts.InitOpts(width=str(width) + "px", height=str(height) + "px"))
    evalpie.add(
        series_name="", data_pair=data_pair, radius=["10%", "55%"], center=["50%", "50%"],
        label_opts=opts.LabelOpts(is_show=False, position="center")
    )
    evalpie.set_colors(colors)
    evalpie.set_global_opts(
        title_opts=opts.TitleOpts(
            title="二手房地产公司市场份额", pos_left="center", pos_top="5",
            title_textstyle_opts=opts.TextStyleOpts(font_size=15, color="#FFFFFF"),
        ),
        legend_opts=opts.LegendOpts(is_show=False),
        xaxis_opts=opts.AxisOpts(name_textstyle_opts=opts.TextStyleOpts(color="#FFFFFF")),
        yaxis_opts=opts.AxisOpts(name_textstyle_opts=opts.TextStyleOpts(color="#FFFFFF"))
    )
    evalpie.set_series_opts(
        tooltip_opts=opts.TooltipOpts(trigger="item", formatter="{a} <br/>{b}: {c} ({d}%)"),
        label_opts=opts.LabelOpts()
    )
    # evalpie.render('pie.html')
    return evalpie


def get_wordcloud(origin_data, width, height):
    estates_list = origin_data.loc[:, '小区']
    estates_list = estates_list.loc[estates_list.notna()]
    estates_list = estates_list.values.tolist()
    data_pairs = get_datapairs(estates_list, single_list=True, descend=True)
    data_pairs = get_top(data_pairs, top_k=200, index=1, others=False)
    # print(data_pairs)
    wordcloud = WordCloud(init_opts=opts.InitOpts(width=str(width) + "px", height=str(height) + "px"))
    wordcloud.add(series_name="", data_pair=data_pairs, word_size_range=[9, 40], shape='circle')
    wordcloud.set_global_opts(
        title_opts=opts.TitleOpts(
            title="热门二手房小区速览",
            title_textstyle_opts=opts.TextStyleOpts(font_size=15, color="white"),
            pos_left="center", pos_top='0'),
        tooltip_opts=opts.TooltipOpts(is_show=True),
        xaxis_opts=opts.AxisOpts(name_textstyle_opts=opts.TextStyleOpts(color="white")),
        yaxis_opts=opts.AxisOpts(name_textstyle_opts=opts.TextStyleOpts(color="white"))
    ),

    # wordcloud.render('ciyun.html')
    return wordcloud


def get_chart(houses_data):
    headers = ['二手房市场规模', '累计挂牌量', '房地产企业', '资产评价机构']
    prices = houses_data.loc[:, '发布价格_万元']
    prices = prices.loc[prices.notna()]
    prices = prices.values.tolist()
    price_sum = round(np.sum(prices) * 4 / 10000, 2)

    ins_list = houses_data.loc[:, ['发布机构名称']]
    ins_list = ins_list.values.tolist()
    ins_num = []
    for ins in ins_list:
        if ins not in ins_num:
            ins_num.append(ins)

    datas = [[f"{price_sum}亿元", "131858户", f"{len(ins_num)}家", "30家"]]

    print(headers)
    print(datas)
    table = Table()
    table.add(headers=headers, rows=datas)
    # table.render("table.html")

    return


def get_html(all_charts):
    grid = Page()
    for chart in all_charts:
        grid.add(chart)

    grid.render('vis.html')
    return


def beauty():
    op = open(r"./vis.html", "r")
    r1 = op.read()
    html_bf = BeautifulSoup(r1, "lxml")
    body = html_bf.find("body")
    divs = html_bf.find_all("div")

    top_0 = 40
    top_1 = 290
    top_2 = 580
    top_3 = 240

    left_0 = 40
    left_1 = 490
    left_2 = 1100

    width_0 = 550
    height_0 = 550
    width_1 = 380
    height_1 = 280

    divs[1]["style"] = f"width:{width_0}px;height:{height_0}px;position:absolute;top:{top_3}px;left:{left_1}px"
    divs[2]["style"] = f"width:{width_1}px;height:{height_1}px;position:absolute;top:{top_2}px;left:{left_0}px"
    divs[3]["style"] = f"width:{width_1}px;height:{height_1}px;position:absolute;top:{top_1}px;left:{left_0}px"
    divs[4]["style"] = f"width:{width_1}px;height:{height_1}px;position:absolute;top:{top_0}px;left:{left_0}px"
    divs[5]["style"] = f"width:{width_1}px;height:{height_1}px;position:absolute;top:{top_2}px;left:{left_2}px"
    divs[6]["style"] = f"width:{width_1}px;height:{height_1}px;position:absolute;top:{top_1+5}px;left:{left_2}px"
    divs[7]["style"] = f"width:{width_1}px;height:{height_1}px;position:absolute;top:{top_0}px;left:{left_2}px"
    body["style"] = "background-color:#000143"
    div_title = f"<div align=\"center\" style=\"width:600px;position:absolute;left:{470}px;top:{100}px\">\n<span " \
                "style=\"font-size:40px;color:#ffffff\"><b>武汉市二手房交易市场数据可视化</b></div> "
    body.insert(0, BeautifulSoup(div_title, "lxml").div)
    html_new = str(html_bf)
    r1 = open(r"vis.html", "w", encoding="utf-8")
    r1.write(html_new)
    return
