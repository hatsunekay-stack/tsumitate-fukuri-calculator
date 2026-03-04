# ファイル名: tsumitate_app.py
# 実行方法:   streamlit run tsumitate_app.py

import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(page_title="積立複利計算機（米国株向け）", layout="wide")

st.title("自分用 積立複利シミュレーション（ドルコスト平均法）")
st.caption("毎月積立 × 複利運用　の資産推移を計算します")

# ------------------- 入力部分 -------------------
col1, col2, col3 = st.columns(3)

with col1:
    monthly_invest = st.number_input(
        "毎月の積立額 (円 or $)", 
        min_value=0, 
        value=30000, 
        step=1000,
        format="%d"
    )

with col2:
    annual_rate = st.slider(
        "期待年利（%）", 
        min_value=0.0, 
        max_value=15.0, 
        value=7.0, 
        step=0.1
    ) / 100

with col3:
    years = st.slider(
        "投資期間（年）", 
        min_value=1, 
        max_value=50, 
        value=20, 
        step=1
    )

initial = st.number_input("初期投資額（円 or $）", min_value=0, value=0, step=10000)

# 税金考慮（簡易・NISA想定なら0のまま）
tax_rate = st.slider("実現益への税率（%） ※NISAなら0", 0.0, 30.0, 0.0, 0.1) / 100

# ------------------- 計算 -------------------
months = years * 12
monthly_rate = (1 + annual_rate) ** (1/12) - 1

# 毎月積立の将来価値（複利）
fv = initial * (1 + monthly_rate) ** months

for m in range(1, months + 1):
    fv += monthly_invest * (1 + monthly_rate) ** (months - m)

# 総積立額
total_invested = initial + monthly_invest * months

# 運用益
profit = fv - total_invested

# 税引き後（簡易）
profit_after_tax = profit * (1 - tax_rate)
fv_after_tax = total_invested + profit_after_tax

# 年ごとの推移を作る（グラフ用）
# ------------------- グラフ用データフレーム -------------------
df = pd.DataFrame(index=range(years + 1))
df["年"] = df.index.astype(int)  # intでOK

# 列を事前にfloatで作成（これが大事！）
df["積立総額"] = 0.0
df["資産評価額"] = 0.0
df["運用益"] = 0.0

for y in range(years + 1):
    m = y * 12
    val = initial * (1 + annual_rate) ** y
    
    # 月次積立の複利部分（元のループのまま）
    for mm in range(1, m + 1):
        val += monthly_invest * (1 + annual_rate) ** ((m - mm) / 12)
    
    df.loc[y, "積立総額"] = initial + monthly_invest * m
    df.loc[y, "資産評価額"] = val
    df.loc[y, "運用益"] = val - df.loc[y, "積立総額"]

# 念のため全列をfloatに変換（保険）
df["積立総額"] = df["積立総額"].astype(float)
df["資産評価額"] = df["資産評価額"].astype(float)
df["運用益"] = df["運用益"].astype(float)

# ------------------- 結果表示 -------------------
st.divider()
st.subheader("結果サマリー")

col_a, col_b, col_c = st.columns(3)
col_a.metric("最終資産評価額", f"¥{fv:,.0f}")
col_b.metric("総積立額", f"¥{total_invested:,.0f}")
col_c.metric("運用益（税引前）", f"¥{profit:,.0f}", delta=f"{profit/total_invested*100:.1f}%")

if tax_rate > 0:
    st.metric("税引後資産（簡易）", f"¥{fv_after_tax:,.0f}")

st.markdown(f"**期待年利 {annual_rate*100:.1f}% で {years}年後**")

# グラフ
st.subheader("資産推移グラフ（年単位）")

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import os

font_dir = os.path.join(os.getcwd(), 'fonts')  # Cloudではos.getcwd()がアプリルート
font_path = os.path.join(font_dir, 'NotoSansJP-VariableFont_wght.ttf')

try:
    if os.path.exists(font_path):
        fm.fontManager.addfont(font_path)
        prop = fm.FontProperties(fname=font_path)
        plt.rcParams['font.family'] = prop.get_name()
        plt.rcParams['axes.unicode_minus'] = False
        print("Noto Sans JP loaded successfully!")  # ログに出る
    else:
        print(f"Font not found at: {font_path}")
except Exception as e:
    print(f"Font loading error: {e}")

fig, ax = plt.subplots(figsize=(10, 5))
sns.lineplot(data=df, x="年", y="積立総額", label="積立総額", ax=ax, linewidth=2)
sns.lineplot(data=df, x="年", y="資産評価額", label="資産評価額（複利）", ax=ax, linewidth=3)
ax.fill_between(df["年"], df["積立総額"], df["資産評価額"], alpha=0.15, color="green")
ax.legend()
ax.grid(True, alpha=0.3)
st.pyplot(fig)

# 詳細テーブル（任意で表示）
with st.expander("年ごとの詳細テーブルを見る"):
    st.dataframe(df.style.format({
        "積立総額": "{:,.0f}",
        "資産評価額": "{:,.0f}",
        "運用益": "{:,.0f}"
    }))


st.caption("※これは単純化したモデルです。実際の投資では為替・手数料・変動リスク・税制変更等を考慮してください")
