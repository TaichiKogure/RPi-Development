"""
グラフ生成モジュール for P1_app_simple44.py
Version: 4.40
"""

import logging
import plotly.graph_objs as go
from .data_reader44 import read_csv_data

# ロガーの設定
logger = logging.getLogger(__name__)

# パラメータラベルの定義
PARAMETER_LABELS = {
    "temperature": "Temperature (°C)",
    "humidity": "Relative Humidity (%)",
    "absolute_humidity": "Absolute Humidity (g/m³)",
    "co2": "CO2 Concentration (ppm)",
    "pressure": "Pressure (hPa)",
    "gas_resistance": "Gas Resistance (Ω)"
}

def generate_graph(parameter, days=1, show_p2=True, show_p3=True, config=None):
    """指定されたパラメータのグラフを生成します。"""
    # パラメータラベルの取得
    label = PARAMETER_LABELS.get(parameter, parameter.capitalize())
    
    # P2とP3のデータを読み取り
    df_p2 = read_csv_data("P2", days, config=config) if show_p2 else None
    df_p3 = read_csv_data("P3", days, config=config) if show_p3 else None
    
    # データがあるか確認
    if (df_p2 is None or df_p2.empty) and (df_p3 is None or df_p3.empty):
        logger.warning(f"{parameter} のデータがありません")
        return {"error": f"{parameter} のデータがありません"}
    
    # 図の作成
    fig = go.Figure()
    
    # P2のデータを追加（利用可能な場合）
    if show_p2 and df_p2 is not None and not df_p2.empty and parameter in df_p2.columns:
        # 有効なデータがあるか確認（少なくとも2つの一意の非NaN値）
        p2_values = df_p2[parameter].dropna()
        if len(p2_values) > 0 and len(p2_values.unique()) >= 2:
            logger.info(f"{parameter} のP2データを追加: {len(p2_values)}ポイント, 範囲: {p2_values.min()} - {p2_values.max()}")
            fig.add_trace(go.Scatter(
                x=df_p2['timestamp'],
                y=df_p2[parameter],
                mode='lines',
                name=f'P2 {parameter.capitalize()}',
                line=dict(color='blue')
            ))
        else:
            logger.warning(f"{parameter} のP2データには十分な一意の値がありません")
    
    # P3のデータを追加（利用可能な場合）
    if show_p3 and df_p3 is not None and not df_p3.empty and parameter in df_p3.columns:
        # 有効なデータがあるか確認（少なくとも2つの一意の非NaN値）
        p3_values = df_p3[parameter].dropna()
        if len(p3_values) > 0 and len(p3_values.unique()) >= 2:
            logger.info(f"{parameter} のP3データを追加: {len(p3_values)}ポイント, 範囲: {p3_values.min()} - {p3_values.max()}")
            fig.add_trace(go.Scatter(
                x=df_p3['timestamp'],
                y=df_p3[parameter],
                mode='lines',
                name=f'P3 {parameter.capitalize()}',
                line=dict(color='red')
            ))
        else:
            logger.warning(f"{parameter} のP3データには十分な一意の値がありません")
    
    # トレースがあるか確認
    if not fig.data:
        logger.warning(f"{parameter} のプロット用の有効なデータがありません")
        return {"error": f"{parameter} のプロット用の有効なデータがありません"}
    
    # レイアウトの更新
    fig.update_layout(
        title=f"{label} over time",
        xaxis_title="Time",
        yaxis_title=label,
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        hovermode='closest',
        yaxis=dict(
            autorange=True,
            rangemode='normal'
        ),
        xaxis=dict(
            type='date'
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig.to_json()

def generate_all_graphs(days=1, show_p2=True, show_p3=True, config=None):
    """すべてのパラメータのグラフを生成します。"""
    graphs = {}
    for parameter in PARAMETER_LABELS.keys():
        graphs[parameter] = generate_graph(parameter, days, show_p2, show_p3, config)
    return graphs