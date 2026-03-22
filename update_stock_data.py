import akshare as ak
import json
import pandas as pd
from datetime import datetime, timedelta
import os

# 股票池配置
STOCKS = {
    '688981.SH': {'name': '中芯国际', 'ak_code': '688981'},
    '688041.SH': {'name': '海光信息', 'ak_code': '688041'},
    '603501.SH': {'name': '韦尔股份', 'ak_code': '603501'},
    '002371.SZ': {'name': '北方华创', 'ak_code': '002371'},
    '688012.SH': {'name': '中微公司', 'ak_code': '688012'},
    '300750.SZ': {'name': '宁德时代', 'ak_code': '300750'},
    '002594.SZ': {'name': '比亚迪', 'ak_code': '002594'},
    '601012.SH': {'name': '隆基绿能', 'ak_code': '601012'},
    '688599.SH': {'name': '天合光能', 'ak_code': '688599'},
    '002230.SZ': {'name': '科大讯飞', 'ak_code': '002230'},
    '000977.SZ': {'name': '浪潮信息', 'ak_code': '000977'},
    '603019.SH': {'name': '中科曙光', 'ak_code': '603019'},
    '600519.SH': {'name': '贵州茅台', 'ak_code': '600519'},
    '601318.SH': {'name': '中国平安', 'ak_code': '601318'},
    '600036.SH': {'name': '招商银行', 'ak_code': '600036'},
}

def get_stock_data(ak_code, days=30):
    """获取股票历史数据"""
    try:
        # 使用akshare获取日线数据
        df = ak.stock_zh_a_hist(symbol=ak_code, period="daily", 
                                start_date=(datetime.now() - timedelta(days=days)).strftime('%Y%m%d'),
                                end_date=datetime.now().strftime('%Y%m%d'),
                                adjust="qfq")
        if df.empty:
            return None
        
        # 只保留需要的列
        df = df[['日期', '开盘', '收盘', '最高', '最低']]
        df.columns = ['date', 'open', 'close', 'high', 'low']
        return df
    except Exception as e:
        print(f"Error fetching {ak_code}: {e}")
        return None

def calculate_td_sequential(prices):
    """计算神奇九转序列"""
    closes = prices['close'].values
    n = len(closes)
    
    up_sequence = [0] * n
    down_sequence = [0] * n
    
    # 上涨九转（熊市反转信号）
    for i in range(4, n):
        if closes[i] < closes[i - 4]:
            up_sequence[i] = up_sequence[i - 1] + 1
            if up_sequence[i] > 9:
                up_sequence[i] = 1
        else:
            up_sequence[i] = 0
    
    # 下跌九转（牛市反转信号）
    for i in range(4, n):
        if closes[i] > closes[i - 4]:
            down_sequence[i] = down_sequence[i - 1] + 1
            if down_sequence[i] > 9:
                down_sequence[i] = 1
        else:
            down_sequence[i] = 0
    
    return up_sequence, down_sequence

def process_stock(stock_code, stock_info):
    """处理单只股票数据"""
    df = get_stock_data(stock_info['ak_code'])
    if df is None or len(df) < 10:
        return None
    
    # 计算九转序列
    up_seq, down_seq = calculate_td_sequential(df)
    df['up_sequence'] = up_seq
    df['down_sequence'] = down_seq
    
    # 获取最新数据
    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else latest
    
    # 构建价格历史（最近20天）
    prices = []
    for _, row in df.tail(20).iterrows():
        prices.append({
            'date': row['date'],
            'open': round(float(row['open']), 2),
            'close': round(float(row['close']), 2),
            'high': round(float(row['high']), 2),
            'low': round(float(row['low']), 2)
        })
    
    # 计算涨跌幅
    change_pct = ((latest['close'] - prev['close']) / prev['close'] * 100) if prev['close'] != 0 else 0
    
    return {
        'code': stock_code,
        'name': stock_info['name'],
        'currentPrice': round(float(latest['close']), 2),
        'changePercent': round(float(change_pct), 2),
        'upSequence': int(up_seq[-1]),
        'downSequence': int(down_seq[-1]),
        'prices': prices,
        'updateTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

def generate_stock_data():
    """生成所有股票数据"""
    result = []
    
    for stock_code, stock_info in STOCKS.items():
        print(f"Processing {stock_info['name']} ({stock_code})...")
        data = process_stock(stock_code, stock_info)
        if data:
            result.append(data)
    
    return {
        'stocks': result,
        'updateTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'count': len(result)
    }

if __name__ == '__main__':
    # 生成数据
    data = generate_stock_data()
    
    # 保存为JSON
    output_path = 'stock_data.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 数据已保存到 {output_path}")
    print(f"📊 共 {data['count']} 只股票")
    print(f"🕐 更新时间: {data['updateTime']}")
    
    # 打印信号统计
    up_signals = [s for s in data['stocks'] if s['upSequence'] == 9]
    down_signals = [s for s in data['stocks'] if s['downSequence'] == 9]
    
    if up_signals:
        print(f"\n🔴 上涨9转信号 ({len(up_signals)}只):")
        for s in up_signals:
            print(f"   {s['name']} ({s['code']})")
    
    if down_signals:
        print(f"\n🟢 下跌9转信号 ({len(down_signals)}只):")
        for s in down_signals:
            print(f"   {s['name']} ({s['code']})")
    
    if not up_signals and not down_signals:
        print("\n⚪ 暂无九转信号")