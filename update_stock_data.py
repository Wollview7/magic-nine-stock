import akshare as ak
import json
import pandas as pd
from datetime import datetime, timedelta
import os
import sys

# 扩展股票池配置 - 覆盖A股、港股、美股
STOCKS = {
    # A股核心资产 (15只)
    '600519.SH': {'name': '贵州茅台', 'ak_code': '600519', 'market': 'A'},
    '601318.SH': {'name': '中国平安', 'ak_code': '601318', 'market': 'A'},
    '600036.SH': {'name': '招商银行', 'ak_code': '600036', 'market': 'A'},
    '688981.SH': {'name': '中芯国际', 'ak_code': '688981', 'market': 'A'},
    '688041.SH': {'name': '海光信息', 'ak_code': '688041', 'market': 'A'},
    '603501.SH': {'name': '韦尔股份', 'ak_code': '603501', 'market': 'A'},
    '002371.SZ': {'name': '北方华创', 'ak_code': '002371', 'market': 'A'},
    '688012.SH': {'name': '中微公司', 'ak_code': '688012', 'market': 'A'},
    '300750.SZ': {'name': '宁德时代', 'ak_code': '300750', 'market': 'A'},
    '002594.SZ': {'name': '比亚迪', 'ak_code': '002594', 'market': 'A'},
    '601012.SH': {'name': '隆基绿能', 'ak_code': '601012', 'market': 'A'},
    '688599.SH': {'name': '天合光能', 'ak_code': '688599', 'market': 'A'},
    '002230.SZ': {'name': '科大讯飞', 'ak_code': '002230', 'market': 'A'},
    '000977.SZ': {'name': '浪潮信息', 'ak_code': '000977', 'market': 'A'},
    '603019.SH': {'name': '中科曙光', 'ak_code': '603019', 'market': 'A'},
    
    # A股CPO"易中天" (3只)
    '300502.SZ': {'name': '新易盛', 'ak_code': '300502', 'market': 'A'},
    '300308.SZ': {'name': '中际旭创', 'ak_code': '300308', 'market': 'A'},
    '300394.SZ': {'name': '天孚通信', 'ak_code': '300394', 'market': 'A'},
    
    # 港股 (3只)
    '00700.HK': {'name': '腾讯控股', 'ak_code': '00700', 'market': 'HK'},
    '01810.HK': {'name': '小米集团', 'ak_code': '01810', 'market': 'HK'},
    '09988.HK': {'name': '阿里巴巴', 'ak_code': '09988', 'market': 'HK'},
}

def get_a_stock_data(ak_code, days=30):
    """获取A股历史数据"""
    try:
        df = ak.stock_zh_a_hist(symbol=ak_code, period="daily", 
                                start_date=(datetime.now() - timedelta(days=days)).strftime('%Y%m%d'),
                                end_date=datetime.now().strftime('%Y%m%d'),
                                adjust="qfq")
        if df.empty:
            return None
        df = df[['日期', '开盘', '收盘', '最高', '最低']]
        df.columns = ['date', 'open', 'close', 'high', 'low']
        return df
    except Exception as e:
        print(f"Error fetching A {ak_code}: {e}")
        return None

def get_hk_stock_data(ak_code, days=30):
    """获取港股历史数据"""
    try:
        df = ak.stock_hk_hist(symbol=ak_code, period="daily",
                              start_date=(datetime.now() - timedelta(days=days)).strftime('%Y%m%d'),
                              end_date=datetime.now().strftime('%Y%m%d'))
        if df.empty:
            return None
        df = df[['日期', '开盘', '收盘', '最高', '最低']]
        df.columns = ['date', 'open', 'close', 'high', 'low']
        return df
    except Exception as e:
        print(f"Error fetching HK {ak_code}: {e}")
        return None

def calculate_td_sequential(prices):
    """计算神奇九转序列"""
    closes = prices['close'].values
    n = len(closes)
    
    up_sequence = [0] * n
    down_sequence = [0] * n
    
    for i in range(4, n):
        if closes[i] < closes[i - 4]:
            up_sequence[i] = up_sequence[i - 1] + 1
            if up_sequence[i] > 9:
                up_sequence[i] = 1
        else:
            up_sequence[i] = 0
    
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
    market = stock_info['market']
    ak_code = stock_info['ak_code']
    
    # 根据市场选择数据源
    if market == 'A':
        df = get_a_stock_data(ak_code)
    elif market == 'HK':
        df = get_hk_stock_data(ak_code)
    else:
        return None
    
    if df is None or len(df) < 10:
        return None
    
    up_seq, down_seq = calculate_td_sequential(df)
    df['up_sequence'] = up_seq
    df['down_sequence'] = down_seq
    
    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else latest
    
    prices = []
    for _, row in df.tail(20).iterrows():
        prices.append({
            'date': row['date'],
            'open': round(float(row['open']), 2),
            'close': round(float(row['close']), 2),
            'high': round(float(row['high']), 2),
            'low': round(float(row['low']), 2)
        })
    
    change_pct = ((latest['close'] - prev['close']) / prev['close'] * 100) if prev['close'] != 0 else 0
    
    return {
        'code': stock_code,
        'name': stock_info['name'],
        'market': market,
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

def load_existing_data():
    """加载现有数据作为fallback"""
    try:
        with open('stock_data.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None

if __name__ == '__main__':
    print("开始更新股票数据...")
    
    try:
        data = generate_stock_data()
        
        if data['count'] >= 10:  # 至少获取10只股票才保存
            with open('stock_data.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"\n✅ 数据已保存，共 {data['count']} 只股票")
        else:
            print(f"\n⚠️ 仅获取到 {data['count']} 只股票，保留现有数据")
            
    except Exception as e:
        print(f"\n❌ 更新失败: {e}")
        print("保留现有数据")
        sys.exit(0)