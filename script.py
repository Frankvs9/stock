import csv
import os

# -------------------------- 核心配置项（可直接修改） --------------------------
INPUT_CSV = "input.csv"  # 原始持仓数据CSV（需和脚本同目录）
OUTPUT_CSV = "zly_hold.csv"        # 最终输出文件名（固定为zly_hold.csv）
TOTAL_CAPITAL = 250000.0           # 总资金：25万元（核心计算基数）
POSITION_DECIMALS = 2              # 个股仓位百分比保留2位小数（可改1/3位）
# ------------------------------------------------------------------------------

def convert_to_float(value):
    """
    安全转换字符串为浮点数，处理空值/非数字场景
    :param value: 原始字符串（如"4278.000"、""、"abc"）
    :return: 转换后的浮点数，失败则返回0.0
    """
    try:
        clean_value = value.strip().replace(",", "")  # 去除空格和千分位逗号
        return float(clean_value) if clean_value else 0.0
    except (ValueError, AttributeError):
        return 0.0

def calculate_position_ratio(stock_market_value, total_capital):
    """
    计算个股仓位：(单只股票最新市值 / 总资金) * 100%
    :param stock_market_value: 单只股票最新市值（浮点数）
    :param total_capital: 总资金（浮点数，如250000.0）
    :return: 格式化的仓位百分比字符串（如"1.71%"）
    """
    if total_capital <= 0:  # 防止总资金为0/负数导致计算错误
        return "0.00%"
    ratio = (stock_market_value / total_capital) * 100
    return f"{ratio:.{POSITION_DECIMALS}f}%"

def clean_stock_code(code_str):
    """
    清洗证券代码：移除所有单/双引号、空格，确保纯数字后补全6位
    :param code_str: 原始代码字符串（如"'002185"、"002460 "、"\"600031\""）
    :return: 纯数字6位证券代码（如"002185"、"600031"）
    """
    # 核心修复：移除单引号、双引号、空格等特殊字符
    clean_code = code_str.strip().replace("'", "").replace('"', '').replace(" ", "")
    # 补全6位（左侧补0），确保是纯数字字符串
    return clean_code.zfill(6) if clean_code.isdigit() else clean_code

def process_stock_data():
    # 1. 检查输入文件是否存在
    if not os.path.exists(INPUT_CSV):
        print(f"❌ 错误：未找到输入文件【{INPUT_CSV}】")
        print("   请确认文件放在脚本同一目录，且文件名正确！")
        return

    processed_rows = []  # 存储处理后的所有行数据
    total_stock_market_value = 0.0  # 累计所有股票最新市值

    # 2. 读取并处理输入CSV
    try:
        with open(INPUT_CSV, "r", encoding="utf-8") as f:
            csv_reader = csv.reader(f)
            next(csv_reader)  # 跳过输入文件的表头（无表头则注释此行）
            next(csv_reader)  # 跳过输入文件的表头（无表头则注释此行）
            # 逐行处理每只股票数据
            for line_num, row in enumerate(csv_reader, start=1):
                # 输入文件字段顺序（必须匹配）：
                # 0:证券代码 1:证券名称 2:持仓数量 3:可用数量 4:成本价 5:当前价
                # 6:最新市值 7:持仓盈亏 8:持仓盈亏比例 9:当日盈亏 10:当日盈亏比例 11:操作
                if len(row) < 12:
                    print(f"⚠️ 警告：第{line_num}行数据不完整，已跳过")
                    continue

                # 提取基础字段并清洗
                raw_stock_code = row[0]  # 原始证券代码（可能带引号）
                stock_name = row[1].strip()
                hold_quantity = row[2].strip()
                available_quantity = row[3].strip()
                cost_price = row[4].strip()
                latest_price = row[5].strip()
                market_value_str = row[6].strip()  # 最新市值（原始字符串）
                hold_profit = row[7].strip()
                hold_profit_ratio = row[8].strip()
                day_profit = row[9].strip()
                day_profit_ratio = row[10].strip()

                # 3. 核心处理逻辑（重点修复证券代码）
                stock_code_6digit = clean_stock_code(raw_stock_code)  # 清洗+补全6位
                buy_avg_price = cost_price  # 买入均价 = 成本价
                market_value = convert_to_float(market_value_str)  # 最新市值转浮点数
                position_ratio = calculate_position_ratio(market_value, TOTAL_CAPITAL)  # 计算个股仓位

                # 累计总市值（用于后续核对）
                total_stock_market_value += market_value

                # 组装输出行（严格匹配指定表头顺序）
                output_row = [
                    line_num,               # 序
                    f"={stock_code_6digit}",# 【仅修改此行】证券代码前添加=符号，其余逻辑不变
                    stock_name,             # 证券名称
                    hold_quantity,          # 持仓数量
                    available_quantity,     # 可用数量
                    cost_price,             # 成本价
                    latest_price,           # 最新价
                    hold_profit_ratio,      # 持仓盈亏比例
                    hold_profit,            # 持仓盈亏
                    day_profit_ratio,       # 当日盈亏比例
                    day_profit,             # 当日盈亏
                    buy_avg_price,          # 买入均价
                    position_ratio,         # 个股仓位（核心计算项）
                    market_value_str        # 最新市值
                ]
                processed_rows.append(output_row)

        # 4. 写入输出CSV文件
        output_header = [
            "序", "证券代码", "证券名称", "持仓数量", "可用数量", "成本价",
            "最新价", "持仓盈亏比例", "持仓盈亏", "当日盈亏比例", "当日盈亏",
            "买入均价", "个股仓位", "最新市值"
        ]
        with open(OUTPUT_CSV, "w", newline="", encoding="gbk") as f:
            csv_writer = csv.writer(f)
            csv_writer.writerow(output_header)
            csv_writer.writerows(processed_rows)

        # 5. 输出核对信息（方便验证计算结果）
        total_position_ratio = (total_stock_market_value / TOTAL_CAPITAL) * 100
        print("=" * 50)
        print(f"✅ 处理完成！输出文件：{OUTPUT_CSV}")
        print(f"📊 核心计算结果核对：")
        print(f"   总资金：{TOTAL_CAPITAL:,.2f} 元")
        print(f"   持仓总市值：{total_stock_market_value:,.2f} 元")
        print(f"   整体仓位占比：{total_position_ratio:.{POSITION_DECIMALS}f}%")
        print(f"   有效处理股票数量：{len(processed_rows)} 只")
        print("=" * 50)

    except Exception as e:
        print(f"❌ 处理失败：{str(e)}")
        print("💡 排查建议：")
        print("   1. 输入CSV编码需为UTF-8")
        print("   2. 最新市值列必须是数字（如4278.000，不能是文字/空值）")
        print("   3. 输入字段顺序需严格匹配要求")

if __name__ == "__main__":
    process_stock_data()
