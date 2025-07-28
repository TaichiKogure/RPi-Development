"""
APIルートモジュール for P1_app_simple44.py
Version: 4.40
"""

import os
import time
import logging
import datetime
import pandas as pd
from flask import render_template_string, jsonify, request, send_file
from .data_reader44 import read_csv_data
from .graph_generator44 import generate_graph

# ロガーの設定
logger = logging.getLogger(__name__)

# デフォルト設定
DEFAULT_CONFIG = {
    "data_dir": "/var/lib(FromThonny)/raspap_solo/data",
    "rawdata_p2_dir": "RawData_P2",
    "rawdata_p3_dir": "RawData_P3"
}

def setup_routes(app, template, config=None):
    """APIルートを設定します。"""
    if config is None:
        config = DEFAULT_CONFIG
    
    @app.route('/')
    def index():
        """メインダッシュボードページをレンダリングします。"""
        return render_template_string(template)
    
    @app.route('/data/<parameter>')
    def get_graph_data(parameter):
        """特定のパラメータのグラフデータを取得するAPIエンドポイント。"""
        days = request.args.get('days', default=1, type=int)
        show_p2 = request.args.get('show_p2', default='true').lower() == 'true'
        show_p3 = request.args.get('show_p3', default='true').lower() == 'true'
        
        # グラフの生成
        graph_data = generate_graph(parameter, days, show_p2, show_p3, config)
        
        # エラーの確認
        if isinstance(graph_data, dict) and "error" in graph_data:
            return jsonify(graph_data)
        
        # グラフデータの返却
        return graph_data
    
    @app.route('/api/connection/status')
    def get_connection_status():
        """P2とP3の接続状態を取得するAPIエンドポイント。"""
        # 通常は接続モニターAPIを呼び出します
        # 今はダミーデータを返します
        status = {
            "P2": {
                "signal_strength": -65,
                "ping_ms": 12,
                "noise": -95,
                "last_update": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            "P3": {
                "signal_strength": -70,
                "ping_ms": 15,
                "noise": -92,
                "last_update": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        }
        
        return jsonify(status)
    
    @app.route('/api/export/<device_id>')
    def export_data(device_id):
        """特定のデバイスまたはすべてのデバイスのデータをエクスポートするAPIエンドポイント。"""
        if device_id not in ["P2", "P3", "all"]:
            return jsonify({"error": "無効なデバイスID"}), 400
        
        start_date = request.args.get('start_date', default=(datetime.datetime.now() - datetime.timedelta(days=7)).strftime("%Y-%m-%d"))
        end_date = request.args.get('end_date', default=datetime.datetime.now().strftime("%Y-%m-%d"))
        
        try:
            # 日付の解析
            start_date_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d")
            end_date_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d")
            
            # データの読み取り
            if device_id == "all":
                df_p2 = read_csv_data("P2", config=config)
                df_p3 = read_csv_data("P3", config=config)
                
                # 日付範囲でフィルタリング
                if df_p2 is not None:
                    df_p2 = df_p2[(df_p2['timestamp'].dt.date >= start_date_dt.date()) & 
                                  (df_p2['timestamp'].dt.date <= end_date_dt.date())]
                
                if df_p3 is not None:
                    df_p3 = df_p3[(df_p3['timestamp'].dt.date >= start_date_dt.date()) & 
                                  (df_p3['timestamp'].dt.date <= end_date_dt.date())]
                
                # データの結合
                if df_p2 is not None and df_p3 is not None:
                    df = pd.concat([df_p2, df_p3], ignore_index=True)
                elif df_p2 is not None:
                    df = df_p2
                elif df_p3 is not None:
                    df = df_p3
                else:
                    return jsonify({"error": "エクスポート用のデータがありません"}), 404
            else:
                df = read_csv_data(device_id, config=config)
                
                # 日付範囲でフィルタリング
                if df is not None:
                    df = df[(df['timestamp'].dt.date >= start_date_dt.date()) & 
                            (df['timestamp'].dt.date <= end_date_dt.date())]
                else:
                    return jsonify({"error": "エクスポート用のデータがありません"}), 404
            
            # データがあるか確認
            if df is None or df.empty:
                return jsonify({"error": "指定された日付範囲のデータがありません"}), 404
            
            # ダウンロード用の一時ファイルを作成
            temp_file = os.path.join(config["data_dir"], f"export_{device_id}_{int(time.time())}.csv")
            df.to_csv(temp_file, index=False)
            
            return send_file(temp_file, 
                            mimetype='text/csv',
                            as_attachment=True,
                            download_name=f"{device_id}_data_{start_date}_to_{end_date}.csv")
        
        except Exception as e:
            logger.error(f"データのエクスポート中にエラーが発生しました: {e}")
            return jsonify({"error": f"データのエクスポート中にエラーが発生しました: {e}"}), 500
    
    return app