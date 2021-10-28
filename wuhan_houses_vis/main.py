import pandas as pd
import utils
import warnings
warnings.filterwarnings("ignore")

if __name__ == "__main__":
    wufang_data = pd.read_excel('./武房网二手房数据.xlsx')
    houses_data = pd.read_excel('./二手房挂牌信息内容.xlsx')
    eval_ins = pd.read_excel('./评价机构表.xlsx')

    print('-----------------------------------------------------')

    all_charts = []
    print("旭日图生成中·······\n")
    house_sunburst = utils.get_sunburst(wufang_data, width=500, height=500)  # 统计各分区二手楼盘数量 基本完成
    all_charts.append(house_sunburst)
    print("旭日图生成完成！\n")

    print("二手房分布图生成中·······\n")
    house_distri = utils.get_distrimap_house(wufang_data, houses_data, width=400, height=300)  # 统计均价分布 基本完成 修改完成
    all_charts.append(house_distri)
    print("分布图生成完成！\n")

    print("河流图生成中·······\n")
    house_themeriver = utils.get_themeriver(houses_data, width=400, height=300)  # 河流图 基本完成 修改完成
    all_charts.append(house_themeriver)
    print("河流图生成完成！\n")

    print("柱状图生成中·······\n")
    all_charts.append(utils.get_pricebar(houses_data, width=400, height=300))  # 价格趋势变化图使用挂牌信息表格 基本完成 修改完成
    print("柱状图生成完成！\n")

    print("评价机构分布图生成中·······\n")
    eval_map = utils.get_distrimap_eval(eval_ins, width=400, height=300)   # 资产评估分布地图 基本完成 修改完成
    all_charts.append(eval_map)
    print("分布图生成完成！\n")

    print("饼状图生成中·······\n")
    eval_pie = utils.get_evalpie(houses_data, width=400, height=300)  # 统计二手房房地产企业市场份额 基本完成 修改完成
    all_charts.append(eval_pie)
    print("饼状图生成完成！\n")

    print("词云生成中·······\n")
    wordcloud = utils.get_wordcloud(houses_data, width=400, height=300)  # 统计热门小区 基本完成 修改完成
    all_charts.append(wordcloud)
    print("词云生成完成！\n")

    # print("表格生成中·······\n")
    # chart = utils.get_chart(houses_data)
    # all_charts.append(chart)
    # print("表格生成完成！\n")

    print("图标组合优化中·······\n")
    utils.get_html(all_charts=all_charts)
    utils.beauty()
    print("所有工作完成！\n")

    print('-----------------------------------------------------')
