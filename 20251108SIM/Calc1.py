# Python
import numpy as np
import pandas as pd

# 学習用パラメータ
E = 10e9          # Pa
nu = 0.30
sigma_y = 10e6    # Pa
H = 0.5e9         # Pa (等方硬化の接線)
h = 0.010         # m (厚み 10 mm)
A = 0.10 * 0.10   # m^2 (100 mm x 100 mm の板と同等面積)

# 荷重履歴: 0 -> 981N まで線形に負荷、保持、0へ除荷
steps_load = 50
steps_hold = 10
steps_unload = 50
F_up = np.linspace(0.0, 981.0, steps_load)
F_hold = np.full(steps_hold, 981.0)
F_down = np.linspace(981.0, 0.0, steps_unload)
F_hist = np.concatenate([F_up, F_hold, F_down])

# 内部変数
eps_p = 0.0   # 塑性ひずみ
alpha = 0.0   # 硬化変数（等方硬化）
sigma = 0.0
eps = 0.0

# 便利: 接線弾性係数と等価ヤング率（1D）
E_t = E * H / (E + H)  # 降伏後の見かけ接線（双線形の目安）

records = []
for i, F in enumerate(F_hist):
    # 単軸応力
    sigma_trial = F / A
    # 弾性試行ひずみ（仮に全ひずみを弾性で計算）
    eps_trial = (sigma_trial + E * eps_p) / E  # sigma = E (eps - eps_p) -> eps = sigma/E + eps_p
    # 降伏関数
    f_trial = abs(sigma_trial) - (sigma_y + H * alpha)

    if f_trial <= 0:
        # 弾性ステップ
        sigma = sigma_trial
        eps = eps_trial
        # eps_p, alpha 変化なし
    else:
        # 塑性修正（1Dの戻り写像）
        dgamma = f_trial / (E + H)
        # 符号
        sgn = np.sign(sigma_trial)
        # 応力修正
        sigma = sigma_trial - E * dgamma * sgn
        # 全ひずみを再計算
        eps = sigma / E + eps_p
        # 内部変数更新
        eps_p += dgamma * sgn
        alpha += dgamma

    # 厚み変化（1D近似）
    dh = eps * h
    h_inst = h * (1 + eps)
    records.append({
        "step": i, "F_N": F, "sigma_Pa": sigma, "eps": eps,
        "eps_p": eps_p, "alpha": alpha, "h_current_m": h_inst, "dh_m": dh
    })

df = pd.DataFrame(records)

# スプリングバック: 最終ステップの厚み・残留ひずみ
eps_res = df.iloc[-1]["eps"]
h_final = df.iloc[-1]["h_current_m"]

print("残留ひずみ:", eps_res)
print("最終厚み [mm]:", h_final * 1e3)
print("最小厚み [mm] (最大負荷時):", df.loc[df["F_N"].idxmax(), "h_current_m"] * 1e3)
# 必要ならCSVで保存
# df.to_csv("uniax_bilinear_result.csv", index=False)