import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib import font_manager, rc
from datetime import datetime, timedelta
import time
import io
import base64
import json
import os
from scipy.optimize import minimize
from collections import defaultdict
import yfinance as yf
import platform


# 한글 폰트 설정
def set_korean_font():
    system_os = platform.system()

    if system_os == "Windows":  # 윈도우의 경우
        font_name = "Malgun Gothic"  # 윈도우 기본 한글 폰트
        plt.rcParams['font.family'] = font_name

    elif system_os == "Darwin":  # macOS의 경우
        font_name = "AppleGothic"  # macOS 기본 한글 폰트
        plt.rcParams['font.family'] = font_name

    else:  # Linux 등 기타 OS의 경우
        # NanumGothic 폰트가 설치되어 있다고 가정
        # 만약 설치되어 있지 않다면 기본 sans-serif 폰트 사용
        try:
            font_list = font_manager.findSystemFonts(fontpaths=None, fontext='ttf')
            nanum_fonts = [f for f in font_list if 'NanumGothic' in f]
            if nanum_fonts:
                path = nanum_fonts[0]
                font_name = font_manager.FontProperties(fname=path).get_name()
                plt.rcParams['font.family'] = font_name
            else:
                plt.rcParams['font.family'] = 'DejaVu Sans'
        except:
            plt.rcParams['font.family'] = 'DejaVu Sans'

    # 마이너스 기호 깨짐 방지
    plt.rcParams['axes.unicode_minus'] = False


# 한글 폰트 설정 적용
set_korean_font()

# 페이지 설정
st.set_page_config(
    page_title="ETF 포트폴리오 최적화 도구",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 앱 제목 및 설명
st.title("ETF 포트폴리오 최적화 도구")
st.markdown("""
    다양한 투자 전략과 최적화 알고리즘을 사용하여 ETF 포트폴리오를 구성하고 분석하세요.
    배당 수익, 자본 이득, 또는 균형 잡힌 접근법 중에서 선택할 수 있습니다.
""")


# ====================================
# 1. ETF 데이터 관리 모듈
# ====================================
class ETFDataManager:
    def __init__(self, csv_filename="etf_data.csv", max_age_days=7):
        self.csv_filename = csv_filename
        self.max_age_days = max_age_days
        self.tickers = self.get_tickers()
        self.etf_list = self.load_etf_data()

    def get_tickers(self):
        """ETF 목록과 메타데이터를 반환합니다."""
        return {
            # Dividend-Focused ETFs (DIV) - Stable, income-generating
            "SCHD": {"name": "Schwab U.S. Dividend Equity ETF", "risk_level": 3, "category": "DIV"},
            "VIG": {"name": "Vanguard Dividend Appreciation ETF", "risk_level": 3, "category": "DIV"},
            "VYM": {"name": "Vanguard High Dividend Yield ETF", "risk_level": 3, "category": "DIV"},
            "DVY": {"name": "iShares Select Dividend ETF", "risk_level": 4, "category": "DIV"},
            "NOBL": {"name": "ProShares S&P 500 Dividend Aristocrats ETF", "risk_level": 3, "category": "DIV"},
            "SDY": {"name": "SPDR S&P Dividend ETF", "risk_level": 3, "category": "DIV"},
            "HDV": {"name": "iShares Core High Dividend ETF", "risk_level": 3, "category": "DIV"},
            "SPHD": {"name": "Invesco S&P 500 High Dividend Low Volatility ETF", "risk_level": 3, "category": "DIV"},
            "FVD": {"name": "First Trust Value Line Dividend Index Fund", "risk_level": 3, "category": "DIV"},
            "DGRO": {"name": "iShares Core Dividend Growth ETF", "risk_level": 3, "category": "DIV"},
            "DHS": {"name": "WisdomTree U.S. High Dividend Fund", "risk_level": 4, "category": "DIV"},
            "DLN": {"name": "WisdomTree U.S. LargeCap Dividend ETF", "risk_level": 3, "category": "DIV"},
            "FDVV": {"name": "Fidelity High Dividend ETF", "risk_level": 4, "category": "DIV"},
            "SPYD": {"name": "SPDR Portfolio S&P 500 High Dividend ETF", "risk_level": 4, "category": "DIV"},
            "DIV": {"name": "Global X SuperDividend U.S. ETF", "risk_level": 5, "category": "DIV"},
            "SDIV": {"name": "Global X SuperDividend ETF", "risk_level": 5, "category": "DIV"},
            "ALTY": {"name": "Global X Alternative Income ETF", "risk_level": 4, "category": "DIV"},
            "YYY": {"name": "Amplify High Income ETF", "risk_level": 5, "category": "DIV"},

            # Covered Call ETFs (CC) - High-yield, income-generating with options strategy
            "QYLD": {"name": "Global X NASDAQ 100 Covered Call ETF", "risk_level": 4, "category": "CC"},
            "XYLD": {"name": "Global X S&P 500 Covered Call ETF", "risk_level": 4, "category": "CC"},
            "RYLD": {"name": "Global X Russell 2000 Covered Call ETF", "risk_level": 5, "category": "CC"},
            "JEPI": {"name": "JPMorgan Equity Premium Income ETF", "risk_level": 4, "category": "CC"},
            "JEPQ": {"name": "JPMorgan Nasdaq Equity Premium Income ETF", "risk_level": 4, "category": "CC"},
            "DIVO": {"name": "Amplify CWP Enhanced Dividend Income ETF", "risk_level": 4, "category": "CC"},
            "NUSI": {"name": "Nationwide Nasdaq-100 Risk-Managed Income ETF", "risk_level": 4, "category": "CC"},
            "PBP": {"name": "Invesco S&P 500 BuyWrite ETF", "risk_level": 4, "category": "CC"},
            "KNG": {"name": "FT Cboe Vest S&P 500 Dividend Aristocrats Target Income ETF", "risk_level": 4,
                    "category": "CC"},
            "SPYI": {"name": "NEOS S&P 500 High Income ETF", "risk_level": 4, "category": "CC"},
            "APLY": {"name": "YieldMax AAPL Option Income Strategy ETF", "risk_level": 5, "category": "CC"},
            "SVOL": {"name": "Simplify Volatility Premium ETF", "risk_level": 4, "category": "CC"},
            "QYLG": {"name": "Global X Nasdaq 100 Covered Call & Growth ETF", "risk_level": 4, "category": "CC"},
            "NVDY": {"name": "YieldMax NVDA Option Income Strategy ETF", "risk_level": 5, "category": "CC"},
            "QDTE": {"name": "Roundhill Innovation S&P 500 0DTE Covered Call Strategy ETF", "risk_level": 5,
                     "category": "CC"},

            # Bond ETFs (BND) - Very stable, fixed-income focused
            "BND": {"name": "Vanguard Total Bond Market ETF", "risk_level": 2, "category": "BND"},
            "AGG": {"name": "iShares Core U.S. Aggregate Bond ETF", "risk_level": 2, "category": "BND"},
            "TIP": {"name": "iShares TIPS Bond ETF", "risk_level": 2, "category": "BND"},
            "BNDX": {"name": "Vanguard Total International Bond ETF", "risk_level": 2, "category": "BND"},
            "LQD": {"name": "iShares iBoxx $ Investment Grade Corporate Bond ETF", "risk_level": 3, "category": "BND"},
            "HYG": {"name": "iShares iBoxx $ High Yield Corporate Bond ETF", "risk_level": 4, "category": "BND"},
            "MUB": {"name": "iShares National Muni Bond ETF", "risk_level": 2, "category": "BND"},
            "TLT": {"name": "iShares 20+ Year Treasury Bond ETF", "risk_level": 3, "category": "BND"},
            "IEF": {"name": "iShares 7-10 Year Treasury Bond ETF", "risk_level": 2, "category": "BND"},
            "SHY": {"name": "iShares 1-3 Year Treasury Bond ETF", "risk_level": 1, "category": "BND"},
            "BIL": {"name": "SPDR Bloomberg 1-3 Month T-Bill ETF", "risk_level": 1, "category": "BND"},
            "SGOV": {"name": "iShares 0-3 Month Treasury Bond ETF", "risk_level": 1, "category": "BND"},
            "TLTW": {"name": "iShares 20+ Year Treasury Bond LNAV ETF", "risk_level": 3, "category": "BND"},  # 추가

            # Large-Cap ETFs (LC) - Broad market, stable growth
            "VOO": {"name": "Vanguard S&P 500 ETF", "risk_level": 5, "category": "LC"},
            "SPY": {"name": "SPDR S&P 500 ETF Trust", "risk_level": 5, "category": "LC"},
            "IVV": {"name": "iShares Core S&P 500 ETF", "risk_level": 5, "category": "LC"},
            "VTI": {"name": "Vanguard Total Stock Market ETF", "risk_level": 6, "category": "LC"},
            "ITOT": {"name": "iShares Core S&P Total U.S. Stock Market ETF", "risk_level": 6, "category": "LC"},
            "SCHX": {"name": "Schwab U.S. Large-Cap ETF", "risk_level": 5, "category": "LC"},
            "VV": {"name": "Vanguard Large-Cap ETF", "risk_level": 5, "category": "LC"},
            "IWB": {"name": "iShares Russell 1000 ETF", "risk_level": 5, "category": "LC"},
            "QQQ": {"name": "Invesco QQQ Trust", "risk_level": 6, "category": "LC"},
            "SCHG": {"name": "Schwab U.S. Large-Cap Growth ETF", "risk_level": 6, "category": "LC"},

            # Mid-Cap ETFs (MC) - Moderate stability with growth potential
            "IJH": {"name": "iShares Core S&P Mid-Cap ETF", "risk_level": 6, "category": "MC"},
            "MDY": {"name": "SPDR S&P MidCap 400 ETF Trust", "risk_level": 6, "category": "MC"},
            "VO": {"name": "Vanguard Mid-Cap ETF", "risk_level": 6, "category": "MC"},
            "SCHM": {"name": "Schwab U.S. Mid-Cap ETF", "risk_level": 6, "category": "MC"},

            # Small-Cap ETFs (SC) - Slightly higher risk, but diversified
            "VB": {"name": "Vanguard Small-Cap ETF", "risk_level": 6, "category": "SC"},
            "IJR": {"name": "iShares Core S&P Small-Cap ETF", "risk_level": 6, "category": "SC"},
            "SCHA": {"name": "Schwab U.S. Small-Cap ETF", "risk_level": 6, "category": "SC"},

            # Sector ETFs (SEC) - Stable sectors with moderate risk
            "XLU": {"name": "Utilities Select Sector SPDR Fund", "risk_level": 3, "category": "SEC"},
            "XLP": {"name": "Consumer Staples Select Sector SPDR Fund", "risk_level": 4, "category": "SEC"},
            "XLV": {"name": "Health Care Select Sector SPDR Fund", "risk_level": 5, "category": "SEC"},
            "XLF": {"name": "Financial Select Sector SPDR Fund", "risk_level": 6, "category": "SEC"},
            "XLI": {"name": "Industrial Select Sector SPDR Fund", "risk_level": 6, "category": "SEC"},
            "XLB": {"name": "Materials Select Sector SPDR Fund", "risk_level": 6, "category": "SEC"},
            "XLE": {"name": "Energy Select Sector SPDR Fund", "risk_level": 6, "category": "SEC"},

            # Real Estate ETFs (RE) - Stable income with moderate risk
            "VNQ": {"name": "Vanguard Real Estate ETF", "risk_level": 5, "category": "RE"},  # 이미 포함됨
            "SCHH": {"name": "Schwab U.S. REIT ETF", "risk_level": 5, "category": "RE"},
            "IYR": {"name": "iShares U.S. Real Estate ETF", "risk_level": 5, "category": "RE"},
            "XLRE": {"name": "Real Estate Select Sector SPDR Fund", "risk_level": 5, "category": "RE"},
            "ICF": {"name": "iShares Cohen & Steers REIT ETF", "risk_level": 5, "category": "RE"},
            "RWR": {"name": "SPDR Dow Jones REIT ETF", "risk_level": 5, "category": "RE"},

            # International ETFs (INT) - Diversified global exposure
            "VEA": {"name": "Vanguard FTSE Developed Markets ETF", "risk_level": 5, "category": "INT"},
            "VXUS": {"name": "Vanguard Total International Stock ETF", "risk_level": 6, "category": "INT"},
            "EFA": {"name": "iShares MSCI EAFE ETF", "risk_level": 5, "category": "INT"},
            "IEFA": {"name": "iShares Core MSCI EAFE ETF", "risk_level": 5, "category": "INT"},
            "VEU": {"name": "Vanguard FTSE All-World ex-US ETF", "risk_level": 6, "category": "INT"},
            "IXUS": {"name": "iShares Core MSCI Total International Stock ETF", "risk_level": 6, "category": "INT"},
            "EWJ": {"name": "iShares MSCI Japan ETF", "risk_level": 5, "category": "INT"},
            "EWU": {"name": "iShares MSCI United Kingdom ETF", "risk_level": 5, "category": "INT"},
            "EZU": {"name": "iShares MSCI Eurozone ETF", "risk_level": 5, "category": "INT"},

            # Commodities ETFs (COM) - Stable alternative assets
            "GLD": {"name": "SPDR Gold Shares", "risk_level": 2, "category": "COM"},
            "SLV": {"name": "iShares Silver Trust", "risk_level": 3, "category": "COM"},
            "IAU": {"name": "iShares Gold Trust", "risk_level": 2, "category": "COM"},
            "DBC": {"name": "Invesco DB Commodity Index Tracking Fund", "risk_level": 4, "category": "COM"},
            "USO": {"name": "United States Oil Fund LP", "risk_level": 5, "category": "COM"},

            # Low Volatility ETFs (LV) - Focused on stability
            "USMV": {"name": "iShares MSCI USA Min Vol Factor ETF", "risk_level": 3, "category": "LV"},
            "SPLV": {"name": "Invesco S&P 500 Low Volatility ETF", "risk_level": 3, "category": "LV"},
            "LVHD": {"name": "Franklin U.S. Low Volatility High Dividend ETF", "risk_level": 3, "category": "LV"},
            "EFAV": {"name": "iShares MSCI EAFE Min Vol Factor ETF", "risk_level": 3, "category": "LV"},
            "ACWV": {"name": "iShares MSCI Global Min Vol Factor ETF", "risk_level": 3, "category": "LV"},

            # Growth ETFs (GRO) - High-growth focus
            "ARKK": {"name": "ARK Innovation ETF", "risk_level": 7, "category": "GRO"},
            "ARKW": {"name": "ARK Next Generation Internet ETF", "risk_level": 7, "category": "GRO"},
            "VUG": {"name": "Vanguard Growth ETF", "risk_level": 6, "category": "GRO"},
            "MGK": {"name": "Vanguard Mega Cap Growth ETF", "risk_level": 6, "category": "GRO"},
            "IWY": {"name": "iShares Russell Top 200 Growth ETF", "risk_level": 6, "category": "GRO"},
            "TQQQ": {"name": "ProShares UltraPro QQQ", "risk_level": 8, "category": "GRO"},
            "XLK": {"name": "Technology Select Sector SPDR Fund", "risk_level": 6, "category": "GRO"},
            "SOXL": {"name": "Direxion Daily Semiconductor Bull 3X Shares", "risk_level": 9, "category": "GRO"},
            "QQQM": {"name": "Invesco NASDAQ 100 ETF", "risk_level": 6, "category": "GRO"},
            "IWF": {"name": "iShares Russell 1000 Growth ETF", "risk_level": 6, "category": "GRO"},

            # Additional Stable ETFs Across Categories
            "PFF": {"name": "iShares Preferred & Income Securities ETF", "risk_level": 4, "category": "DIV"},
            "SCHZ": {"name": "Schwab U.S. Aggregate Bond ETF", "risk_level": 2, "category": "BND"},
            "VGSH": {"name": "Vanguard Short-Term Treasury ETF", "risk_level": 1, "category": "BND"},
            "VCSH": {"name": "Vanguard Short-Term Corporate Bond ETF", "risk_level": 2, "category": "BND"},
            "SCHB": {"name": "Schwab U.S. Broad Market ETF", "risk_level": 6, "category": "LC"},
            "SCHV": {"name": "Schwab U.S. Large-Cap Value ETF", "risk_level": 5, "category": "LC"},
            "DON": {"name": "WisdomTree U.S. MidCap Dividend Fund", "risk_level": 5, "category": "DIV"},
            "DES": {"name": "WisdomTree U.S. SmallCap Dividend Fund", "risk_level": 6, "category": "DIV"},
            "REET": {"name": "iShares Global REIT ETF", "risk_level": 5, "category": "RE"},
            "IDV": {"name": "iShares International Select Dividend ETF", "risk_level": 5, "category": "DIV"},
            "SPAB": {"name": "SPDR Portfolio Aggregate Bond ETF", "risk_level": 2, "category": "BND"},
            "SPTI": {"name": "SPDR Portfolio Intermediate Term Treasury ETF", "risk_level": 2, "category": "BND"},
            "SPTL": {"name": "SPDR Portfolio Long Term Treasury ETF", "risk_level": 3, "category": "BND"},
        }

    def load_etf_data(self, force_update=False):
        """CSV 파일에서 ETF 데이터를 로드하거나 필요 시 업데이트합니다."""
        file_exists = os.path.exists(self.csv_filename)
        update_needed = False

        if file_exists and not force_update:
            file_age = (time.time() - os.path.getmtime(self.csv_filename)) / (24 * 3600)
            if file_age > self.max_age_days:
                update_needed = True
                st.info(f"ETF 데이터가 {self.max_age_days}일 이상 경과하여 업데이트합니다.")

        if force_update or not file_exists or update_needed:
            with st.spinner('ETF 데이터를 가져오는 중...'):
                self.generate_mock_data()  # 실제 API 대신 모의 데이터 사용

        try:
            df = pd.read_csv(self.csv_filename)
            return df.to_dict('records')
        except Exception as e:
            st.error(f"ETF 데이터 로드 중 오류 발생: {e}")
            return self.generate_mock_data()

    def generate_mock_data(self):
        """야후 파이낸스 API가 사용 불가능할 때 테스트용 모의 데이터를 생성합니다."""
        mock_data = []
        for ticker, info in self.tickers.items():
            # 카테고리에 따른 모의 수익률 및 배당률 생성
            category = info["category"]
            risk_level = info["risk_level"]

            # 카테고리별 배당률 기준값
            div_yields = {
                "DIV": 0.03, "CC": 0.08, "BND": 0.04, "LC": 0.015,
                "GRO": 0.005, "RE": 0.035, "INT": 0.025, "COM": 0.0
            }

            # 카테고리별 수익률 기준값
            returns = {
                "DIV": 0.08, "CC": 0.06, "BND": 0.04, "LC": 0.10,
                "GRO": 0.12, "RE": 0.07, "INT": 0.07, "COM": 0.05
            }

            # 위험도에 따른 변동성 조정
            risk_factor = risk_level / 5.0
            base_div_yield = div_yields.get(category, 0.02)
            base_return = returns.get(category, 0.07)

            # 배당률 및 수익률에 약간의 랜덤성 추가
            dividend_yield = base_div_yield * (0.9 + 0.2 * np.random.random())
            cagr_1y = base_return * (0.8 + 0.4 * np.random.random())
            cagr_3y = cagr_1y * (0.9 + 0.2 * np.random.random())
            cagr_5y = cagr_3y * (0.9 + 0.2 * np.random.random())

            # 변동성 및 베타 계산
            volatility = 0.08 * risk_factor * (0.8 + 0.4 * np.random.random())
            beta = 0.8 + 0.4 * risk_factor
            max_drawdown = -0.1 - 0.2 * risk_factor * np.random.random()

            # ETF 데이터 추가
            mock_data.append({
                "ticker": ticker,
                "name": info["name"],
                "dividend_yield": dividend_yield,
                "expected_dividend_yield": dividend_yield,
                "cagr_1y": cagr_1y,
                "cagr_3y": cagr_3y,
                "cagr_5y": cagr_5y,
                "volatility": volatility,
                "beta": beta,
                "max_drawdown": max_drawdown,
                "risk_level": risk_level,
                "category": category,
                # 배당 품질 추가 (개선된 기능)
                "dividend_quality": 0.7 * np.random.random() + 0.3 if category in ["DIV", "CC"] else 0.2,
                "dividend_growth": 0.04 * np.random.random() if category == "DIV" else 0.01,
                "dividend_consistency": 0.8 * np.random.random() + 0.2 if category in ["DIV", "CC"] else 0.3
            })

        # 모의 데이터를 CSV로 저장
        df = pd.DataFrame(mock_data)
        df.to_csv(self.csv_filename, index=False)
        return mock_data


# ====================================
# 2. 포트폴리오 최적화 모듈
# ====================================
class PortfolioOptimizer:
    def __init__(self, etf_list):
        self.etf_list = etf_list

    def recommend_portfolio(self, investment_focus, seed_money, target_value, investor_profile=None,
                            optimization_method="sharpe"):
        """투자 목표에 맞는 포트폴리오를 추천합니다."""
        # 유효 ETF 필터링
        valid_etfs = self.filter_valid_etfs(self.etf_list, target_value, seed_money)

        if not valid_etfs:
            st.error("유효한 ETF가 없습니다.")
            return []

        # 투자자 프로필에 따른 ETF 선정 (개선된 기능)
        if investor_profile:
            top_etfs = self.select_etfs_by_profile(valid_etfs, investor_profile, target_value, seed_money)
        else:
            # 기존 방식으로 투자 초점에 따른 ETF 선정
            top_etfs = self.select_top_etfs(valid_etfs, investment_focus, target_value, seed_money)

        # 최적화 방법에 따른 가중치 계산
        if optimization_method == "sharpe":
            # 샤프 비율 최적화
            optimized_weights = self.optimize_weights_sharpe(top_etfs)
        elif optimization_method == "risk_parity":
            # 위험 패리티 최적화
            optimized_weights = self.optimize_risk_parity(top_etfs)
        elif optimization_method == "min_variance":
            # 최소 분산 최적화
            optimized_weights = self.optimize_min_variance(top_etfs)
        elif optimization_method == "target_return":
            # 목표 수익률 최적화
            if investment_focus == 'dividend':
                target_div_yield = (target_value * 12) / seed_money if seed_money > 0 else 0
                optimized_weights = self.optimize_target_dividend(top_etfs, target_div_yield)
            else:
                optimized_weights = self.optimize_target_return(top_etfs, target_value)
        else:
            # 기본 균등 가중치
            optimized_weights = np.array([1.0 / len(top_etfs)] * len(top_etfs))

        # 최종 포트폴리오 구성
        final_portfolio = self.build_portfolio(top_etfs, optimized_weights, seed_money)

        # 효율적 프론티어 데이터 생성 (개선된 기능)
        ef_data = self.generate_efficient_frontier(top_etfs)
        for p in final_portfolio:
            p["efficient_frontier"] = ef_data

        return final_portfolio

    def filter_valid_etfs(self, etf_list, target_value, seed_money):
        """유효한 ETF를 필터링합니다."""
        valid_etfs = []
        for etf in etf_list:
            # 1년 수익률이 0 이하인 경우 확인
            if etf.get("cagr_1y", 0) <= 0:
                continue

            # 배당 수익률 확인
            current_dy = etf.get("dividend_yield", 0)
            expected_dy = etf.get("expected_dividend_yield", 0)
            effective_dy = expected_dy if (expected_dy > 0 and current_dy > expected_dy * 1.5) else current_dy

            category = etf.get("category", "UNKNOWN")
            risk_level = etf.get("risk_level", 5)

            valid_etfs.append({
                "ticker": etf["ticker"],
                "name": etf["name"],
                "dividend_yield": effective_dy,
                "cagr_1y": etf["cagr_1y"],
                "cagr_3y": etf.get("cagr_3y", etf["cagr_1y"] * 0.9),  # 3년 데이터 없으면 추정
                "cagr_5y": etf.get("cagr_5y", etf["cagr_1y"] * 0.8),  # 5년 데이터 없으면 추정
                "volatility": etf.get("volatility", 0.15),  # 변동성 기본값
                "beta": etf.get("beta", 1.0),  # 베타 기본값
                "max_drawdown": etf.get("max_drawdown", -0.2),  # 최대 낙폭 기본값
                "risk_level": risk_level,
                "category": category,
                "dividend_quality": etf.get("dividend_quality", 0.5),  # 배당 품질
                "dividend_growth": etf.get("dividend_growth", 0.02),  # 배당 성장률
                "dividend_consistency": etf.get("dividend_consistency", 0.5)  # 배당 일관성
            })

        return valid_etfs

    def select_top_etfs(self, valid_etfs, investment_focus, target_value, seed_money):
        """투자 초점에 따라 상위 ETF를 선정합니다."""
        if investment_focus == 'dividend':
            target_div_yield = (target_value * 12) / seed_money if seed_money > 0 else 0  # 목표 배당 수익률
            valid_etfs.sort(key=lambda x: abs(x["dividend_yield"] - target_div_yield))  # 목표에 가까운 순 정렬
            real_target = target_value  # 월 배당 목표
            category_count = defaultdict(int)
            selected = []
            for etf in valid_etfs:
                if category_count[etf["category"]] < 3:  # 카테고리별 최대 3개
                    selected.append(etf)
                    category_count[etf["category"]] += 1
            valid_etfs = selected
        else:
            real_target = target_value  # 연 수익률 목표
            valid_etfs.sort(key=lambda x: abs(x["cagr_1y"] - real_target))
            category_count = defaultdict(int)
            selected = []
            for etf in valid_etfs:
                if len(selected) >= 5:
                    break
                if category_count[etf["category"]] < 2:  # 카테고리별 최대 2개
                    selected.append(etf)
                    category_count[etf["category"]] += 1
            if len(selected) < 3:
                for etf in valid_etfs:
                    if etf not in selected and category_count[etf["category"]] < 2:
                        selected.append(etf)
                        category_count[etf["category"]] += 1
                        if len(selected) >= 3:
                            break
            valid_etfs = selected

        # 상위 ETF 선별 (최대 8개)
        top_etfs = []
        category_count = defaultdict(int)
        for etf in valid_etfs:
            if len(top_etfs) >= 8:
                break
            if investment_focus == 'dividend' and category_count[etf["category"]] >= 3:
                continue
            top_etfs.append(etf)
            category_count[etf["category"]] += 1

        if len(top_etfs) < 3:
            extra_needed = 3 - len(top_etfs)
            remaining = [e for e in valid_etfs if e not in top_etfs]
            if investment_focus == 'dividend':
                remaining.sort(key=lambda x: abs(x["dividend_yield"] - target_div_yield))
            else:
                remaining.sort(key=lambda x: abs(x["cagr_1y"] - target_value))
            for etf in remaining:
                if len(top_etfs) >= 8 or (investment_focus == 'dividend' and category_count[etf["category"]] >= 3):
                    break
                top_etfs.append(etf)
                category_count[etf["category"]] += 1
                extra_needed -= 1
                if extra_needed <= 0:
                    break

        return top_etfs

    def select_etfs_by_profile(self, valid_etfs, investor_profile, target_value, seed_money):
        """투자자 프로필에 맞는 ETF 선정"""
        # 위험 선호도에 따른 최대 위험 수준
        risk_limits = {
            'conservative': 4,
            'moderate': 6,
            'aggressive': 10
        }
        max_risk = risk_limits.get(investor_profile.get('risk_tolerance', 'moderate'), 6)

        # 투자 기간에 따른 카테고리 가중치
        horizon_weights = {
            'short': {'BND': 2.0, 'DIV': 1.5, 'LV': 1.2},
            'medium': {'DIV': 1.5, 'LV': 1.2, 'LC': 1.2},
            'long': {'GRO': 1.5, 'LC': 1.2, 'SC': 1.2}
        }
        horizon = investor_profile.get('investment_horizon', 'medium')

        # 소득 필요성에 따른 카테고리 가중치
        income_weights = {
            'low': {'GRO': 1.5, 'LC': 1.2},
            'medium': {'DIV': 1.2, 'CC': 1.2},
            'high': {'DIV': 2.0, 'CC': 1.8, 'BND': 1.5}
        }
        income_need = investor_profile.get('income_needs', 'medium')

        # 투자 초점(배당/성장)
        investment_focus = investor_profile.get('investment_focus', 'balanced')
        focus_weights = {
            'dividend': {'DIV': 2.0, 'CC': 1.8, 'RE': 1.3},
            'growth': {'GRO': 2.0, 'LC': 1.5},
            'balanced': {'DIV': 1.3, 'LC': 1.3, 'BND': 1.3}
        }

        # ETF 점수 계산
        scored_etfs = []
        for etf in valid_etfs:
            # 기본 점수 (위험 수준 역으로 반영)
            risk_score = 1.0 - (etf['risk_level'] / 10)

            # 위험 한도 초과 시 감점
            if etf['risk_level'] > max_risk:
                risk_penalty = (etf['risk_level'] - max_risk) * 0.2
                risk_score = max(risk_score - risk_penalty, 0)

            # 카테고리 가중치 적용
            category = etf.get('category', '')
            horizon_multiplier = horizon_weights.get(horizon, {}).get(category, 1.0)
            income_multiplier = income_weights.get(income_need, {}).get(category, 1.0)
            focus_multiplier = focus_weights.get(investment_focus, {}).get(category, 1.0)

            # 목표에 맞는 추가 점수
            target_score = 1.0
            if investment_focus == 'dividend':
                target_div_yield = (target_value * 12) / seed_money if seed_money > 0 else 0
                target_score = 1.0 / (1.0 + abs(etf['dividend_yield'] - target_div_yield) * 10)
            else:  # 성장 또는 균형
                target_score = 1.0 / (1.0 + abs(etf['cagr_1y'] - target_value) * 5)

            # 배당 품질 고려 (배당 초점일 경우)
            dividend_factor = 1.0
            if investment_focus == 'dividend' or income_need == 'high':
                dividend_factor = 0.5 + 0.5 * etf.get('dividend_quality', 0.5)

            # 최종 점수 계산
            final_score = (
                    risk_score *
                    horizon_multiplier *
                    income_multiplier *
                    focus_multiplier *
                    target_score *
                    dividend_factor
            )

            scored_etfs.append({
                **etf,
                'profile_score': final_score
            })

        # 점수 기준 정렬 및 상위 선택 (최대 8개)
        selected_etfs = sorted(scored_etfs, key=lambda x: x.get('profile_score', 0), reverse=True)[:8]

        # 카테고리 다양성 확인 (최소 3개 카테고리)
        categories = set(etf['category'] for etf in selected_etfs)
        if len(categories) < 3 and len(valid_etfs) > len(selected_etfs):
            missing_categories = [e for e in valid_etfs
                                  if e['category'] not in categories
                                  and e not in selected_etfs]
            missing_categories.sort(key=lambda x: x.get('profile_score', 0), reverse=True)

            for etf in missing_categories:
                if len(categories) >= 3 or len(selected_etfs) >= 8:
                    break
                selected_etfs.append(etf)
                categories.add(etf['category'])

        return selected_etfs

    def optimize_weights_sharpe(self, etfs, risk_free_rate=0.03):
        """샤프 비율 최대화 기반 포트폴리오 최적화"""
        n = len(etfs)
        if n == 0:
            return []

        # 수익률 벡터
        returns = np.array([etf['cagr_1y'] for etf in etfs])

        # 간소화된 공분산 행렬 (완전한 공분산 행렬이 없는 경우)
        volatilities = np.array([etf.get('volatility', 0.15) for etf in etfs])
        corr_matrix = np.full((n, n), 0.5)
        np.fill_diagonal(corr_matrix, 1.0)
        cov_matrix = np.outer(volatilities, volatilities) * corr_matrix

        def negative_sharpe(weights):
            port_return = np.sum(returns * weights)
            port_stddev = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
            sharpe = (port_return - risk_free_rate) / port_stddev if port_stddev > 0 else 0
            return -sharpe  # 최소화 문제로 변환

        constraints = {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}
        bounds = [(0.05, 0.4) for _ in range(n)]
        initial_weights = np.array([1.0 / n for _ in range(n)])

        try:
            result = minimize(negative_sharpe, initial_weights,
                              method='SLSQP', bounds=bounds, constraints=constraints)
            return result.x if result.success else initial_weights
        except:
            st.warning("샤프 비율 최적화 실패, 초기 가중치 사용")
            return initial_weights

    def optimize_risk_parity(self, etfs):
        """위험 분산을 균등하게 하는 Risk Parity 포트폴리오 구성"""
        n = len(etfs)
        if n == 0:
            return []

        # 간소화된 공분산 행렬
        volatilities = np.array([etf.get('volatility', 0.15) for etf in etfs])
        corr_matrix = np.full((n, n), 0.5)
        np.fill_diagonal(corr_matrix, 1.0)
        cov_matrix = np.outer(volatilities, volatilities) * corr_matrix

        def risk_contribution(weights):
            port_var = np.dot(weights.T, np.dot(cov_matrix, weights))
            marginal_contrib = np.dot(cov_matrix, weights)
            risk_contrib = np.multiply(marginal_contrib, weights) / port_var if port_var > 0 else weights
            return risk_contrib

        def risk_parity_objective(weights):
            rc = risk_contribution(weights)
            target_risk = 1.0 / n  # 균등 위험 기여도
            return np.sum((rc - target_risk) ** 2)

        constraints = {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}
        bounds = [(0.05, 0.4) for _ in range(n)]
        initial_weights = np.array([1.0 / n for _ in range(n)])

        try:
            result = minimize(risk_parity_objective, initial_weights,
                              method='SLSQP', bounds=bounds, constraints=constraints)
            return result.x if result.success else initial_weights
        except:
            st.warning("위험 패리티 최적화 실패, 초기 가중치 사용")
            return initial_weights

    def optimize_min_variance(self, etfs):
        """최소 분산 포트폴리오 최적화"""
        n = len(etfs)
        if n == 0:
            return []

        # 간소화된 공분산 행렬
        volatilities = np.array([etf.get('volatility', 0.15) for etf in etfs])
        corr_matrix = np.full((n, n), 0.5)
        np.fill_diagonal(corr_matrix, 1.0)
        cov_matrix = np.outer(volatilities, volatilities) * corr_matrix

        def portfolio_variance(weights):
            return np.dot(weights.T, np.dot(cov_matrix, weights))

        constraints = {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}
        bounds = [(0.05, 0.4) for _ in range(n)]
        initial_weights = np.array([1.0 / n for _ in range(n)])

        try:
            result = minimize(portfolio_variance, initial_weights,
                              method='SLSQP', bounds=bounds, constraints=constraints)
            return result.x if result.success else initial_weights
        except:
            st.warning("최소 분산 최적화 실패, 초기 가중치 사용")
            return initial_weights

    def optimize_target_return(self, etfs, target_return):
        """목표 수익률 기반 최적화"""
        n = len(etfs)
        if n == 0:
            return []

        # 수익률 및 위험 데이터
        returns = np.array([etf['cagr_1y'] for etf in etfs])
        volatilities = np.array([etf.get('volatility', 0.15) for etf in etfs])

        # 간소화된 공분산 행렬
        corr_matrix = np.full((n, n), 0.5)
        np.fill_diagonal(corr_matrix, 1.0)
        cov_matrix = np.outer(volatilities, volatilities) * corr_matrix

        def portfolio_variance(weights):
            return np.dot(weights.T, np.dot(cov_matrix, weights))

        def objective(weights):
            port_return = np.sum(returns * weights)
            penalty = (port_return - target_return) ** 2 * 100
            var_penalty = portfolio_variance(weights) * 10
            return penalty + var_penalty

        constraints = {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}
        bounds = [(0.05, 0.4) for _ in range(n)]
        initial_weights = np.array([1.0 / n for _ in range(n)])

        try:
            result = minimize(objective, initial_weights,
                              method='SLSQP', bounds=bounds, constraints=constraints)
            return result.x if result.success else initial_weights
        except:
            st.warning("목표 수익률 최적화 실패, 초기 가중치 사용")
            return initial_weights

    def optimize_target_dividend(self, etfs, target_div_yield):
        """목표 배당 수익률 기반 최적화"""
        n = len(etfs)
        if n == 0:
            return []

        # 배당 수익률 및 품질 데이터
        div_yields = np.array([etf['dividend_yield'] for etf in etfs])
        div_qualities = np.array([etf.get('dividend_quality', 0.5) for etf in etfs])

        def objective(weights):
            port_div_yield = np.sum(div_yields * weights)
            # 배당 품질을 고려한 페널티
            quality_score = np.sum(div_qualities * weights)
            # 목표 배당률과의 차이 + 품질 패널티
            return (port_div_yield - target_div_yield) ** 2 * 100 - quality_score

        constraints = {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}
        bounds = [(0.05, 0.4) for _ in range(n)]
        initial_weights = np.array([1.0 / n for _ in range(n)])

        try:
            result = minimize(objective, initial_weights,
                              method='SLSQP', bounds=bounds, constraints=constraints)
            return result.x if result.success else initial_weights
        except:
            st.warning("목표 배당 최적화 실패, 초기 가중치 사용")
            return initial_weights

    def build_portfolio(self, etfs, weights, seed_money):
        """최적화된 가중치로 포트폴리오를 구성합니다."""
        portfolio = []
        total_weight = sum(weights)

        # 가중치 조정 (합이 1이 되도록)
        if abs(total_weight - 1.0) > 1e-6:
            weights = [w / total_weight for w in weights]

        for etf, weight in zip(etfs, weights):
            invest_amount = seed_money * weight
            portfolio.append({
                "name": etf["name"],
                "ticker": etf["ticker"],
                "weight": weight,
                "invest_amount": invest_amount,
                "dividend_yield": etf["dividend_yield"],
                "annual_return": etf["cagr_1y"],
                "risk_level": etf["risk_level"],
                "category": etf["category"],
                "volatility": etf.get("volatility", 0.15),
                "beta": etf.get("beta", 1.0),
                "expected_monthly_dividend": invest_amount * etf["dividend_yield"] / 12,
                "expected_annual_return_value": invest_amount * etf["cagr_1y"],
                "dividend_quality": etf.get("dividend_quality", 0.5)
            })

        return sorted(portfolio, key=lambda x: x["weight"], reverse=True)

    def generate_efficient_frontier(self, etfs, num_portfolios=100):
        """효율적 프론티어를 생성합니다."""
        if len(etfs) < 2:
            return {}

        # 수익률 및 위험 데이터
        returns = np.array([etf['cagr_1y'] for etf in etfs])
        tickers = [etf['ticker'] for etf in etfs]

        # 간소화된 공분산 행렬
        volatilities = np.array([etf.get('volatility', 0.15) for etf in etfs])
        corr_matrix = np.full((len(etfs), len(etfs)), 0.5)
        np.fill_diagonal(corr_matrix, 1.0)
        cov_matrix = np.outer(volatilities, volatilities) * corr_matrix

        # 랜덤 포트폴리오 생성
        results = []
        np.random.seed(42)  # 재현성을 위한 시드 설정

        for _ in range(num_portfolios):
            # 랜덤 가중치 생성
            weights = np.random.random(len(etfs))
            weights /= np.sum(weights)

            # 포트폴리오 수익률
            portfolio_return = np.sum(returns * weights)

            # 포트폴리오 변동성
            portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))

            # 샤프 비율 (무위험 수익률 3% 가정)
            sharpe_ratio = (portfolio_return - 0.03) / portfolio_volatility if portfolio_volatility > 0 else 0

            results.append({
                "return": portfolio_return,
                "volatility": portfolio_volatility,
                "sharpe": sharpe_ratio,
                "weights": weights.tolist()
            })

        # 효율적 프론티어의 주요 포트폴리오 찾기
        max_sharpe_portfolio = max(results, key=lambda x: x["sharpe"])
        min_vol_portfolio = min(results, key=lambda x: x["volatility"])

        # 각 ETF의 개별 위험-수익 특성
        etf_points = [{
            "ticker": ticker,
            "name": etfs[i]["name"],
            "return": returns[i],
            "volatility": volatilities[i],
            "sharpe": (returns[i] - 0.03) / volatilities[i] if volatilities[i] > 0 else 0
        } for i, ticker in enumerate(tickers)]

        return {
            "portfolios": results,
            "max_sharpe": max_sharpe_portfolio,
            "min_volatility": min_vol_portfolio,
            "etf_points": etf_points
        }


# ====================================
# 3. 백테스트 및 성능 분석 모듈
# ====================================
class PortfolioAnalyzer:
    def __init__(self):
        pass

    def backtest_portfolio(self, portfolio, start_date="2018-01-01", end_date=None):
        """과거 데이터로 포트폴리오 성능 검증합니다."""
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")

        with st.spinner('백테스트 실행 중...'):
            # 백테스트 결과 생성 - 실제 데이터가 없는 경우 모의 데이터 사용
            results = self.generate_synthetic_backtest(
                [p["ticker"] for p in portfolio],
                [p["weight"] for p in portfolio],
                start_date, end_date
            )

        return results

    def generate_synthetic_backtest(self, tickers, weights, start_date, end_date):
        """모의 백테스트 데이터 생성합니다."""
        # 날짜 범위 생성
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        months = []
        current = start
        while current <= end:
            months.append(current.strftime("%Y-%m"))
            # 다음 달로 이동
            if current.month == 12:
                current = datetime(current.year + 1, 1, 1)
            else:
                current = datetime(current.year, current.month + 1, 1)

        # 시장 이벤트 정의 (재현성을 위한 주요 이벤트)
        market_events = {
            "2018-02": -0.04,  # 2018년 2월 급락
            "2018-10": -0.07,  # 2018년 10월 급락
            "2020-03": -0.20,  # 코로나 위기
            "2020-04": 0.10,  # 회복 시작
            "2020-05": 0.05,  # 회복 지속
            "2021-01": 0.05,  # 백신 보급 시작
            "2022-01": -0.05,  # 인플레이션 우려
            "2022-06": -0.08,  # 금리 인상 가속화
            "2023-03": -0.03,  # 은행 불안
            "2023-07": 0.05,  # AI 붐
        }

        # 자산 유형별 성과 특성
        category_events = {
            "DIV": {"2020-03": -0.15, "2022-01": 0.02},  # 배당주
            "CC": {"2020-03": -0.10, "2022-01": 0.03},  # 커버드콜
            "BND": {"2020-03": -0.05, "2022-01": -0.10},  # 채권
            "LC": {"2020-03": -0.20, "2022-01": -0.08},  # 대형주
            "GRO": {"2020-03": -0.25, "2022-01": -0.15, "2023-07": 0.10},  # 성장주
            "RE": {"2020-03": -0.30, "2022-01": -0.10},  # 리츠
            "INT": {"2020-03": -0.25, "2022-01": -0.05},  # 국제
            "COM": {"2020-03": -0.10, "2022-01": 0.10},  # 원자재
        }

        # 티커별 월간 수익률 생성
        ticker_returns = {}
        np.random.seed(42)  # 재현성을 위한 시드 설정

        # ETF 카테고리 할당
        ticker_categories = {}
        for i, ticker in enumerate(tickers):
            if "DIV" in ticker or "VYM" in ticker or "SCHD" in ticker:
                ticker_categories[ticker] = "DIV"
            elif "JEPI" in ticker or "QYLD" in ticker or "DIVO" in ticker:
                ticker_categories[ticker] = "CC"
            elif "BND" in ticker or "AGG" in ticker or "TIP" in ticker:
                ticker_categories[ticker] = "BND"
            elif "QQQ" in ticker or "ARKK" in ticker or "VUG" in ticker:
                ticker_categories[ticker] = "GRO"
            elif "VNQ" in ticker or "SCHH" in ticker:
                ticker_categories[ticker] = "RE"
            elif "VXUS" in ticker or "EFA" in ticker:
                ticker_categories[ticker] = "INT"
            elif "GLD" in ticker or "SLV" in ticker:
                ticker_categories[ticker] = "COM"
            else:
                ticker_categories[ticker] = "LC"  # 기본 카테고리

        for ticker in tickers:
            # 각 ETF의 카테고리와 기본 통계 가정
            category = ticker_categories.get(ticker, "LC")

            # 평균 수익률 및 변동성 가정
            base_return = {
                "DIV": 0.006, "CC": 0.005, "BND": 0.003, "LC": 0.007,
                "GRO": 0.01, "RE": 0.006, "INT": 0.006, "COM": 0.003
            }.get(category, 0.007)

            base_vol = {
                "DIV": 0.03, "CC": 0.025, "BND": 0.01, "LC": 0.04,
                "GRO": 0.06, "RE": 0.05, "INT": 0.045, "COM": 0.04
            }.get(category, 0.04)

            # ETF별 월간 수익률 생성
            monthly_returns = []

            for month in months:
                # 기본 수익률 (기본값 + 랜덤 변동)
                monthly_return = base_return + np.random.normal(0, base_vol)

                # 시장 이벤트 적용
                if month in market_events:
                    monthly_return += market_events[month]

                # 자산 유형별 특성 적용
                if month in category_events.get(category, {}):
                    monthly_return += category_events[category][month]

                monthly_returns.append(monthly_return)

            ticker_returns[ticker] = monthly_returns

        # 포트폴리오 성과 계산
        portfolio_returns = []
        for i in range(len(months)):
            # 월간 포트폴리오 수익률
            monthly_port_return = sum(weights[j] * ticker_returns[tickers[j]][i]
                                      for j in range(len(tickers)))
            portfolio_returns.append(monthly_port_return)

        # 누적 수익률 계산
        cumulative_returns = [1.0]
        for ret in portfolio_returns:
            cumulative_returns.append(cumulative_returns[-1] * (1 + ret))
        cumulative_returns = cumulative_returns[1:]  # 초기 값 제거

        # 성과 지표 계산
        total_return = cumulative_returns[-1] - 1.0
        years = len(months) / 12
        annualized_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0

        monthly_std = np.std(portfolio_returns)
        annualized_vol = monthly_std * np.sqrt(12)

        # 최대 낙폭 계산
        peak = cumulative_returns[0]
        max_drawdown = 0

        for value in cumulative_returns:
            if value > peak:
                peak = value
            dd = (peak - value) / peak
            if dd > max_drawdown:
                max_drawdown = dd

        # 샤프 비율
        risk_free_rate = 0.03  # 연 3% 가정
        monthly_rf = (1 + risk_free_rate) ** (1 / 12) - 1
        excess_returns = [r - monthly_rf for r in portfolio_returns]
        sharpe_ratio = np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(12)

        # 결과 구성
        return_series = [{"date": months[i], "return": portfolio_returns[i],
                          "cumulative": cumulative_returns[i]}
                         for i in range(len(months))]

        return {
            "return_series": return_series,
            "total_return": total_return,
            "annualized_return": annualized_return,
            "annualized_vol": annualized_vol,
            "max_drawdown": max_drawdown,
            "sharpe_ratio": sharpe_ratio
        }

    def stress_test_portfolio(self, portfolio, scenario='bear_market'):
        """다양한 시나리오에서 포트폴리오 성능 테스트합니다."""
        scenarios = {
            'bear_market': {  # 강한 하락장
                'name': '급격한 하락장 시나리오',
                'description': '주식 시장이 급격히 하락하는 상황 (예: 코로나19 위기)',
                'market_return': -0.30,  # 30% 하락
                'volatility_multiplier': 2.0,  # 변동성 2배
                'sector_impacts': {
                    'DIV': -0.05,  # 배당주 추가 5% 하락
                    'GRO': -0.25,  # 성장주 추가 25% 하락
                    'BND': 0.05,  # 채권 5% 상승
                    'CC': -0.10,  # 커버드콜 10% 하락
                    'RE': -0.20,  # 리츠 20% 하락
                    'COM': 0.10,  # 원자재 10% 상승
                }
            },
            'inflation': {  # 인플레이션
                'name': '높은 인플레이션 시나리오',
                'description': '급격한 인플레이션으로 금리 인상이 지속되는 상황',
                'market_return': -0.15,  # 15% 하락
                'volatility_multiplier': 1.5,  # 변동성 1.5배
                'sector_impacts': {
                    'DIV': -0.05,  # 배당주 추가 5% 하락
                    'GRO': -0.20,  # 성장주 추가 20% 하락
                    'BND': -0.10,  # 채권 10% 하락
                    'CC': -0.05,  # 커버드콜 5% 하락
                    'RE': -0.15,  # 리츠 15% 하락
                    'COM': 0.20,  # 원자재 20% 상승
                }
            },
            'tech_crash': {  # 기술주 붕괴
                'name': '기술주 급락 시나리오',
                'description': '기술주를 중심으로 한 성장주 급락 상황',
                'market_return': -0.20,  # 20% 하락
                'volatility_multiplier': 1.8,  # 변동성 1.8배
                'sector_impacts': {
                    'DIV': 0.05,  # 배당주 5% 상승
                    'GRO': -0.30,  # 성장주 추가 30% 하락
                    'BND': 0.10,  # 채권 10% 상승
                    'CC': -0.05,  # 커버드콜 5% 하락
                    'RE': 0.0,  # 리츠 변화 없음
                    'COM': 0.05,  # 원자재 5% 상승
                }
            },
            'fed_pivot': {  # 연준 피봇
                'name': '연준 금리 인하 시나리오',
                'description': '연준의 급격한 금리 인하로 자산 가격 상승',
                'market_return': 0.15,  # 15% 상승
                'volatility_multiplier': 0.7,  # 변동성 30% 감소
                'sector_impacts': {
                    'DIV': 0.05,  # 배당주 5% 상승
                    'GRO': 0.25,  # 성장주 25% 상승
                    'BND': 0.10,  # 채권 10% 상승
                    'CC': 0.05,  # 커버드콜 5% 상승
                    'RE': 0.15,  # 리츠 15% 상승
                    'COM': -0.05,  # 원자재 5% 하락
                }
            }
        }

        if scenario not in scenarios:
            return {'error': f'지원하지 않는 시나리오: {scenario}'}

        with st.spinner(f'{scenarios[scenario]["name"]} 테스트 중...'):
            scenario_params = scenarios[scenario]
            total_investment = sum(p['invest_amount'] for p in portfolio)

            # 포트폴리오 내 각 자산 영향 계산
            asset_impacts = []
            for p in portfolio:
                category = p['category']
                base_impact = scenario_params['market_return']

                # 섹터별 추가 영향
                sector_impact = scenario_params['sector_impacts'].get(category, 0)
                total_impact = base_impact + sector_impact

                # 변동성에 따른 영향 조정 (높은 변동성 = 더 큰 영향)
                vol_impact = 1.0
                if 'volatility' in p:
                    # 평균 변동성 대비 이 자산의 변동성이 높을수록 영향 증가
                    vol_impact = p['volatility'] / 0.15  # 0.15를 평균 변동성으로 가정

                # 최종 자산별 영향
                final_impact = total_impact * vol_impact * scenario_params['volatility_multiplier']
                value_change = p['invest_amount'] * final_impact

                asset_impacts.append({
                    'ticker': p['ticker'],
                    'name': p['name'],
                    'category': category,
                    'current_value': p['invest_amount'],
                    'impact': final_impact,
                    'value_change': value_change,
                    'new_value': p['invest_amount'] * (1 + final_impact)
                })

            # 포트폴리오 전체 영향
            total_value_change = sum(a['value_change'] for a in asset_impacts)
            portfolio_impact = total_value_change / total_investment
            new_portfolio_value = total_investment + total_value_change

        return {
            'scenario': scenario,
            'scenario_name': scenario_params['name'],
            'description': scenario_params['description'],
            'portfolio_impact': portfolio_impact,
            'total_investment': total_investment,
            'total_value_change': total_value_change,
            'new_portfolio_value': new_portfolio_value,
            'asset_impacts': asset_impacts
        }

    def monte_carlo_simulation(self, portfolio, n_sim=1000, years=10, alpha=0.05):
        """포트폴리오의 몬테카를로 시뮬레이션을 수행합니다."""
        total_invest = sum(p["invest_amount"] for p in portfolio)
        if total_invest <= 0:
            return None

        with st.spinner(f'몬테카를로 시뮬레이션 실행 중 ({n_sim}회, {years}년)...'):
            # 일일 수익률과 변동성 계산
            daily_returns_list = []
            weights = []
            for p in portfolio:
                # 연 수익률을 일일 수익률로 변환 (복리 가정)
                mean_daily = (1 + p.get("annual_return", 0.07)) ** (1 / 252) - 1
                annual_vol = p.get("volatility", 0.15)  # 연간 변동성
                daily_vol = annual_vol / np.sqrt(252)  # 일일 변동성
                daily_returns_list.append((mean_daily, daily_vol))
                w = p["invest_amount"] / total_invest
                weights.append(w)

            # 시뮬레이션 수행
            np.random.seed(42)  # 재현성을 위한 시드 설정
            annual_data = []

            for sim_idx in range(n_sim):
                # 누적 수익률 추적
                portfolio_value = 1.0  # 시작값 = 1

                # 년 단위로 누적
                for year in range(years):
                    # 1년(252 거래일) 수익률 계산
                    yearly_return = 1.0

                    for _ in range(252):  # 1년 영업일
                        # 일일 포트폴리오 수익률 계산
                        daily_return_port = 0.0
                        for (mu, sigma), w in zip(daily_returns_list, weights):
                            # 각 ETF의 일일 수익률 샘플링
                            sample_return = np.random.normal(mu, sigma)
                            daily_return_port += (sample_return * w)

                        # 일일 수익률 누적 (복리)
                        yearly_return *= (1 + daily_return_port)

                    # 이전 값에서 복리 적용
                    portfolio_value *= yearly_return

                # 최종 누적 수익률 (초기 투자 대비 수익률)
                final_return = portfolio_value - 1.0  # 수익률로 변환
                annual_data.append(final_return)

            # 수익률 데이터 배열로 변환
            annual_data = np.array(annual_data)

            # 시뮬레이션 결과 분석
            mean_return = np.mean(annual_data)
            std_dev = np.std(annual_data)

            # 백분위수 계산
            percentiles = {
                "5th": np.percentile(annual_data, 5),
                "25th": np.percentile(annual_data, 25),
                "50th": np.percentile(annual_data, 50),
                "75th": np.percentile(annual_data, 75),
                "95th": np.percentile(annual_data, 95)
            }

            # 투자 가치 계산
            percentile_values = {}
            for pct, value in percentiles.items():
                percentile_values[pct] = total_invest * (1 + value)

            # 월별 배당 계산
            monthly_dividend = 0
            for p in portfolio:
                monthly_dividend += p["weight"] * p.get("dividend_yield", 0) / 12
            expected_monthly_dividend = total_invest * monthly_dividend

        # 시뮬레이션 결과 반환
        return {
            "simulations": n_sim,
            "years": years,
            "initial_investment": total_invest,
            "mean_return": mean_return,
            "std_dev": std_dev,
            "percentiles": percentiles,
            "percentile_values": percentile_values,
            "expected_monthly_dividend": expected_monthly_dividend,
            "monthly_dividend_per_10m": expected_monthly_dividend * 10000000 / total_invest,
            "sim_returns": annual_data  # 시뮬레이션 원본 데이터 추가
        }

# ====================================
# 4. 시각화 모듈
# ====================================
# ====================================
# 4. 시각화 모듈 (영문 텍스트로 수정)
# ====================================
class PortfolioVisualizer:
    def __init__(self):
        pass

    def plot_portfolio_allocation(self, portfolio):
        """포트폴리오 자산 배분 그래프를 생성합니다."""
        # 폰트 설정
        plt.style.use('default')
        fig, ax = plt.subplots(figsize=(10, 6))

        # 자산 데이터 준비
        tickers = [f"{p['ticker']} ({p['weight'] * 100:.1f}%)" for p in portfolio]
        weights = [p['weight'] for p in portfolio]
        colors = plt.cm.tab10(np.arange(len(tickers)) % 10)

        # 원 그래프
        wedges, texts, autotexts = ax.pie(
            weights, labels=tickers, autopct='%1.1f%%', startangle=90, colors=colors,
            wedgeprops={'edgecolor': 'w', 'linewidth': 1}, textprops={'fontsize': 9}
        )

        # 그래프 설정
        ax.axis('equal')
        plt.setp(autotexts, size=9, weight="bold")
        ax.set_title('Portfolio Asset Allocation', fontsize=15, pad=20)

        return fig

    def plot_portfolio_categories(self, portfolio):
        """포트폴리오 카테고리 배분 그래프를 생성합니다."""
        # 카테고리별 배분 계산
        categories = {}
        for p in portfolio:
            cat = p['category']
            if cat not in categories:
                categories[cat] = 0
            categories[cat] += p['weight']

        # 카테고리별 색상 지정
        category_colors = {
            'DIV': '#4CAF50',  # 녹색
            'CC': '#2196F3',  # 파랑
            'BND': '#9E9E9E',  # 회색
            'LC': '#F44336',  # 빨강
            'GRO': '#FF9800',  # 주황
            'RE': '#E91E63',  # 분홍
            'INT': '#673AB7',  # 보라
            'COM': '#FFD700',  # 금색
        }

        # 카테고리 영문 이름
        category_names = {
            'DIV': 'Dividend-Focused ETF',
            'CC': 'Covered Call ETF',
            'BND': 'Bond ETF',
            'LC': 'Large-Cap ETF',
            'GRO': 'Growth ETF',
            'RE': 'Real Estate ETF',
            'INT': 'International ETF',
            'COM': 'Commodities ETF'
        }

        # 폰트 설정
        plt.style.use('default')
        fig, ax = plt.subplots(figsize=(10, 6))

        # 데이터 준비
        cat_labels = [f"{category_names.get(cat, cat)} ({weight * 100:.1f}%)" for cat, weight in categories.items()]
        cat_weights = list(categories.values())
        cat_colors = [category_colors.get(cat, '#999999') for cat in categories.keys()]

        # 원 그래프
        wedges, texts, autotexts = ax.pie(
            cat_weights, labels=cat_labels, autopct='%1.1f%%', startangle=90, colors=cat_colors,
            wedgeprops={'edgecolor': 'w', 'linewidth': 1}, textprops={'fontsize': 9}
        )

        # 그래프 설정
        ax.axis('equal')
        plt.setp(autotexts, size=9, weight="bold")
        ax.set_title('Portfolio Category Allocation', fontsize=15, pad=20)

        return fig

    def plot_efficient_frontier(self, ef_data, portfolio_return=None, portfolio_volatility=None):
        """효율적 프론티어 그래프를 생성합니다."""
        if not ef_data or 'portfolios' not in ef_data:
            return None

        # 그래프 준비
        plt.style.use('default')
        fig, ax = plt.subplots(figsize=(10, 6))

        # 효율적 프론티어 데이터
        returns = [p['return'] for p in ef_data['portfolios']]
        volatilities = [p['volatility'] for p in ef_data['portfolios']]
        sharpes = [p['sharpe'] for p in ef_data['portfolios']]

        # 산점도 그래프 (Sharpe ratio로 색상 구분)
        sc = ax.scatter(volatilities, returns, c=sharpes, cmap='viridis', s=10, alpha=0.5)
        cbar = fig.colorbar(sc, ax=ax)
        cbar.set_label('Sharpe Ratio')

        # 개별 ETF 표시
        if 'etf_points' in ef_data:
            for etf in ef_data['etf_points']:
                ax.scatter(etf['volatility'], etf['return'], marker='o', s=50,
                           label=etf['ticker'], alpha=0.7)

        # 최적 포트폴리오 표시
        if 'max_sharpe' in ef_data:
            ms = ef_data['max_sharpe']
            ax.scatter(ms['volatility'], ms['return'], marker='*', s=100, color='red',
                       label='Max Sharpe Portfolio')

        if 'min_volatility' in ef_data:
            mv = ef_data['min_volatility']
            ax.scatter(mv['volatility'], mv['return'], marker='*', s=100, color='green',
                       label='Min Volatility Portfolio')

        # 현재 포트폴리오 표시
        if portfolio_return is not None and portfolio_volatility is not None:
            ax.scatter(portfolio_volatility, portfolio_return, marker='X', s=100, color='blue',
                       label='Current Portfolio')

        # 그래프 꾸미기
        ax.set_title('Efficient Frontier', fontsize=15)
        ax.set_xlabel('Volatility (Annual Std Dev)', fontsize=12)
        ax.set_ylabel('Expected Return (Annual)', fontsize=12)
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8)

        # X축과 Y축 퍼센트로 표시
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.1%}'))
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y:.1%}'))

        return fig

    def plot_backtest_returns(self, backtest_results):
        """백테스트 결과 그래프를 생성합니다."""
        if not backtest_results or 'return_series' not in backtest_results:
            return None

        # 그래프 준비
        plt.style.use('default')
        fig, ax = plt.subplots(figsize=(12, 6))

        # 데이터 준비
        dates = [pd.to_datetime(r['date']) for r in backtest_results['return_series']]
        cumulative = [r['cumulative'] for r in backtest_results['return_series']]

        # 누적 수익률 그래프
        ax.plot(dates, cumulative, color='#2196F3', linewidth=2)
        ax.axhline(y=1.0, color='gray', linestyle='--', alpha=0.5)

        # 주요 지표 표시
        total_return = backtest_results['total_return']
        annual_return = backtest_results['annualized_return']
        max_dd = backtest_results['max_drawdown']
        sharpe = backtest_results['sharpe_ratio']

        ax.text(0.02, 0.95, f'Total Return: {total_return:.1%}', transform=ax.transAxes, fontsize=9)
        ax.text(0.02, 0.91, f'Annualized Return: {annual_return:.1%}', transform=ax.transAxes, fontsize=9)
        ax.text(0.02, 0.87, f'Max Drawdown: {max_dd:.1%}', transform=ax.transAxes, fontsize=9)
        ax.text(0.02, 0.83, f'Sharpe Ratio: {sharpe:.2f}', transform=ax.transAxes, fontsize=9)

        # 그래프 꾸미기
        ax.set_title('Portfolio Backtest Results (Cumulative Return)', fontsize=15)
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Cumulative Return', fontsize=12)
        ax.grid(True, alpha=0.3)

        # Y축 퍼센트로 표시
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y:.1f}x'))

        return fig

    def plot_monte_carlo_simulation(self, mc_results):
        """몬테카를로 시뮬레이션 결과 그래프를 생성합니다."""
        if not mc_results:
            return None

        # 그래프 준비
        plt.style.use('default')
        fig, ax = plt.subplots(figsize=(10, 6))

        # 히스토그램 데이터
        percentiles = mc_results['percentiles']
        mean_return = mc_results['mean_return']

        # 히스토그램 범위 계산
        min_val = percentiles['5th'] - 0.1
        max_val = percentiles['95th'] + 0.1

        # 히스토그램 X축 값 생성
        x = np.linspace(min_val, max_val, 100)

        # 히스토그램 그래프
        ax.hist([], bins=20, alpha=0.0)  # 더미 히스토그램으로 축 설정
        ax.axvline(x=mean_return, color='red', linestyle='-', linewidth=2, label=f'Mean Return: {mean_return:.1%}')
        ax.axvline(x=percentiles['5th'], color='orange', linestyle='--', linewidth=1.5,
                   label=f'5th Percentile: {percentiles["5th"]:.1%}')
        ax.axvline(x=percentiles['95th'], color='green', linestyle='--', linewidth=1.5,
                   label=f'95th Percentile: {percentiles["95th"]:.1%}')

        # 백분위수 영역 표시
        ax.axvspan(percentiles['5th'], percentiles['95th'], alpha=0.2, color='lightblue',
                   label='90% Confidence Interval')

        # 그래프 꾸미기
        ax.set_title(f'{mc_results["years"]}-Year Investment Simulation ({mc_results["simulations"]:,} runs)',
                     fontsize=15)
        ax.set_xlabel('Total Return', fontsize=12)
        ax.set_ylabel('Probability Distribution', fontsize=12)
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=9)

        # X축 퍼센트로 표시
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.0%}'))

        # 추가 투자 정보 표시
        info_text = (
            f'Initial Investment: {mc_results["initial_investment"]:,.0f} KRW\n'
            f'50% Probability Value: {mc_results["percentile_values"]["50th"]:,.0f} KRW\n'
            f'Expected Monthly Dividend: {mc_results["expected_monthly_dividend"]:,.0f} KRW\n'
            f'Monthly Dividend per 10M: {mc_results["monthly_dividend_per_10m"]:,.0f} KRW'
        )
        ax.annotate(info_text, xy=(0.02, 0.75), xycoords='axes fraction', fontsize=9,
                    bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.8))

        return fig


# ====================================
# 웹 애플리케이션 인터페이스
# ====================================

# 1. 사이드바 메뉴 설정
st.sidebar.header("메뉴")
page = st.sidebar.radio(
    "선택하세요",
    ["포트폴리오 최적화", "백테스트", "스트레스 테스트", "몬테카를로 시뮬레이션", "데이터 업데이트"]
)

# 초기화 - 세션 상태 관리
if 'data_manager' not in st.session_state:
    st.session_state.data_manager = ETFDataManager()

if 'optimizer' not in st.session_state:
    st.session_state.optimizer = PortfolioOptimizer(st.session_state.data_manager.etf_list)

if 'analyzer' not in st.session_state:
    st.session_state.analyzer = PortfolioAnalyzer()

if 'visualizer' not in st.session_state:
    st.session_state.visualizer = PortfolioVisualizer()

if 'portfolio' not in st.session_state:
    st.session_state.portfolio = None

# ETF 데이터 업데이트 페이지
if page == "데이터 업데이트":
    st.header("ETF 데이터 업데이트")
    st.markdown("ETF 데이터를 새로 가져옵니다. 실제 웹 서비스에서는 야후 파이낸스 API로부터 최신 데이터를 가져옵니다.")

    if st.button("데이터 업데이트", type="primary"):
        with st.spinner("ETF 데이터를 업데이트 중입니다..."):
            st.session_state.data_manager.etf_list = st.session_state.data_manager.load_etf_data(force_update=True)
            st.session_state.optimizer = PortfolioOptimizer(st.session_state.data_manager.etf_list)
            st.success("ETF 데이터가 성공적으로 업데이트되었습니다!")

    if os.path.exists(st.session_state.data_manager.csv_filename):
        modified_time = os.path.getmtime(st.session_state.data_manager.csv_filename)
        last_update = datetime.fromtimestamp(modified_time).strftime("%Y-%m-%d %H:%M:%S")
        st.info(f"마지막 업데이트: {last_update}")

        # ETF 데이터 테이블로 표시
        st.subheader("현재 ETF 데이터")
        df = pd.DataFrame(st.session_state.data_manager.etf_list)

        # 주요 컬럼만 선택
        if not df.empty:
            display_cols = ['ticker', 'name', 'category', 'dividend_yield', 'cagr_1y', 'risk_level']
            display_df = df[display_cols].copy()

            # 데이터 형식 변환
            display_df['dividend_yield'] = display_df['dividend_yield'].apply(lambda x: f"{x:.2%}")
            display_df['cagr_1y'] = display_df['cagr_1y'].apply(lambda x: f"{x:.2%}")

            # 컬럼명 변경
            display_df.columns = ['티커', '종목명', '카테고리', '배당률', '1년 수익률', '위험도']

            st.dataframe(display_df, use_container_width=True)

# 포트폴리오 최적화 페이지
elif page == "포트폴리오 최적화":
    st.header("ETF 포트폴리오 최적화")

    # 투자 기본 정보 입력
    col1, col2 = st.columns(2)

    with col1:
        seed_money = st.number_input(
            "투자 금액 (원)",
            min_value=1000000,
            max_value=10000000000,
            value=10000000,
            step=1000000,
            format="%d"
        )

        investment_focus = st.selectbox(
            "투자 초점",
            options=["dividend", "growth", "balanced"],
            format_func=lambda x: {
                "dividend": "배당 수입 (월 배당금 목표)",
                "growth": "자본 이득 (연 수익률 목표)",
                "balanced": "균형 접근 (배당 + 성장)"
            }.get(x, x)
        )

        if investment_focus == "dividend":
            target_value = st.number_input(
                "목표 월 배당금 (원)",
                min_value=1000,
                max_value=int(seed_money / 10),
                value=int(seed_money * 0.005),  # 기본값: 투자금의 0.5%/월
                step=1000,
                format="%d"
            )
        else:
            target_value = st.slider(
                "목표 연 수익률 (%)",
                min_value=1.0,
                max_value=20.0,
                value=8.0,
                step=0.5
            ) / 100

    with col2:
        risk_tolerance = st.select_slider(
            "위험 선호도",
            options=["conservative", "moderate", "aggressive"],
            value="moderate",
            format_func=lambda x: {
                "conservative": "보수적 (Conservative)",
                "moderate": "중립적 (Moderate)",
                "aggressive": "공격적 (Aggressive)"
            }.get(x, x)
        )

        investment_horizon = st.select_slider(
            "투자 기간",
            options=["short", "medium", "long"],
            value="medium",
            format_func=lambda x: {
                "short": "단기 (3년 이하)",
                "medium": "중기 (3~7년)",
                "long": "장기 (7년 이상)"
            }.get(x, x)
        )

        income_needs = st.select_slider(
            "배당 소득 필요성",
            options=["low", "medium", "high"],
            value="medium",
            format_func=lambda x: {
                "low": "낮음 (현재 소득 충분)",
                "medium": "중간 (부수입으로 활용)",
                "high": "높음 (생활비로 활용)"
            }.get(x, x)
        )

        optimization_method = st.selectbox(
            "최적화 방법",
            options=["sharpe", "risk_parity", "min_variance", "target_return"],
            format_func=lambda x: {
                "sharpe": "샤프 비율 최적화 (위험 대비 수익 최대화)",
                "risk_parity": "위험 패리티 (위험 균등 분배)",
                "min_variance": "최소 분산 (변동성 최소화)",
                "target_return": "목표 수익률/배당률 최적화"
            }.get(x, x)
        )

    # 포트폴리오 최적화 버튼
    if st.button("포트폴리오 최적화", type="primary"):
        investor_profile = {
            "risk_tolerance": risk_tolerance,
            "investment_horizon": investment_horizon,
            "income_needs": income_needs,
            "investment_focus": investment_focus
        }

        with st.spinner("포트폴리오 최적화 중..."):
            portfolio = st.session_state.optimizer.recommend_portfolio(
                investment_focus,
                seed_money,
                target_value,
                investor_profile,
                optimization_method
            )

            st.session_state.portfolio = portfolio

    # 포트폴리오 결과 표시
    if st.session_state.portfolio:
        portfolio = st.session_state.portfolio

        # 요약 정보
        total_investment = sum(p["invest_amount"] for p in portfolio)
        total_monthly_dividend = sum(p["expected_monthly_dividend"] for p in portfolio)
        weighted_annual_return = sum(p["annual_return"] * p["weight"] for p in portfolio)

        st.header("최적화된 ETF 포트폴리오")

        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
        with metric_col1:
            st.metric("총 투자 금액", f"{total_investment:,.0f}원")
        with metric_col2:
            st.metric("예상 월 배당금", f"{total_monthly_dividend:,.0f}원")
        with metric_col3:
            st.metric("예상 연 수익률", f"{weighted_annual_return:.2%}")
        with metric_col4:
            st.metric("1천만원당 월 배당", f"{total_monthly_dividend * 10000000 / total_investment:,.0f}원")

        # 포트폴리오 테이블
        st.subheader("포트폴리오 구성")

        portfolio_data = [{
            "티커": p["ticker"],
            "종목명": p["name"],
            "비중": f"{p['weight'] * 100:.1f}%",
            "투자금액": f"{p['invest_amount']:,.0f}원",
            "연 수익률": f"{p['annual_return']:.2%}",
            "배당 수익률": f"{p['dividend_yield']:.2%}",
            "월 배당금": f"{p['expected_monthly_dividend']:,.0f}원",
            "카테고리": p["category"]
        } for p in portfolio]

        st.table(pd.DataFrame(portfolio_data))

        # 시각화
        st.subheader("포트폴리오 시각화")

        viz_tab1, viz_tab2, viz_tab3 = st.tabs(["자산 배분", "카테고리 배분", "효율적 프론티어"])

        with viz_tab1:
            fig1 = st.session_state.visualizer.plot_portfolio_allocation(portfolio)
            st.pyplot(fig1)

        with viz_tab2:
            fig2 = st.session_state.visualizer.plot_portfolio_categories(portfolio)
            st.pyplot(fig2)

        with viz_tab3:
            ef_data = portfolio[0].get("efficient_frontier", None)
            if ef_data:
                weighted_return = sum(p["annual_return"] * p["weight"] for p in portfolio)
                weighted_vol = sum(p.get("volatility", 0.15) * p["weight"] for p in portfolio)

                fig3 = st.session_state.visualizer.plot_efficient_frontier(ef_data, weighted_return, weighted_vol)
                st.pyplot(fig3)
            else:
                st.info("효율적 프론티어 데이터를 생성할 수 없습니다.")

# 백테스트 페이지
elif page == "백테스트":
    st.header("포트폴리오 백테스트")

    if not st.session_state.portfolio:
        st.warning("먼저 포트폴리오 최적화를 실행해주세요.")
    else:
        # 백테스트 설정
        col1, col2 = st.columns(2)

        with col1:
            start_year = st.selectbox(
                "시작 연도",
                options=list(range(2010, datetime.now().year)),
                index=8  # 2018년 기본값
            )

        with col2:
            end_year = st.selectbox(
                "종료 연도",
                options=list(range(start_year, datetime.now().year + 1)),
                index=len(list(range(start_year, datetime.now().year + 1))) - 1  # 현재 연도 기본값
            )

        start_date = f"{start_year}-01-01"
        end_date = f"{end_year}-12-31"

        if st.button("백테스트 실행", type="primary"):
            backtest_results = st.session_state.analyzer.backtest_portfolio(
                st.session_state.portfolio,
                start_date,
                end_date
            )

            # 백테스트 결과 표시
            st.subheader("백테스트 결과")

            result_col1, result_col2, result_col3, result_col4 = st.columns(4)
            with result_col1:
                st.metric("총 수익률", f"{backtest_results['total_return']:.2%}")
            with result_col2:
                st.metric("연화 수익률", f"{backtest_results['annualized_return']:.2%}")
            with result_col3:
                st.metric("연화 변동성", f"{backtest_results['annualized_vol']:.2%}")
            with result_col4:
                st.metric("최대 낙폭", f"{backtest_results['max_drawdown']:.2%}")

            st.metric("샤프 비율", f"{backtest_results['sharpe_ratio']:.2f}")

            # 백테스트 차트
            st.subheader("누적 수익률 차트")
            backtest_fig = st.session_state.visualizer.plot_backtest_returns(backtest_results)
            st.pyplot(backtest_fig)

# 스트레스 테스트 페이지
elif page == "스트레스 테스트":
    st.header("포트폴리오 스트레스 테스트")

    if not st.session_state.portfolio:
        st.warning("먼저 포트폴리오 최적화를 실행해주세요.")
    else:
        # 스트레스 테스트 시나리오 선택
        scenario = st.selectbox(
            "스트레스 테스트 시나리오",
            options=["bear_market", "inflation", "tech_crash", "fed_pivot"],
            format_func=lambda x: {
                "bear_market": "급격한 하락장 시나리오 (베어마켓)",
                "inflation": "높은 인플레이션 시나리오",
                "tech_crash": "기술주 급락 시나리오",
                "fed_pivot": "연준 금리 인하 시나리오"
            }.get(x, x)
        )

        if st.button("스트레스 테스트 실행", type="primary"):
            stress_results = st.session_state.analyzer.stress_test_portfolio(
                st.session_state.portfolio,
                scenario
            )

            # 스트레스 테스트 결과 표시
            st.subheader(f"시나리오: {stress_results['scenario_name']}")
            st.markdown(f"**설명**: {stress_results['description']}")

            result_col1, result_col2, result_col3 = st.columns(3)
            with result_col1:
                st.metric("포트폴리오 영향", f"{stress_results['portfolio_impact']:.2%}")
            with result_col2:
                st.metric("초기 투자금", f"{stress_results['total_investment']:,.0f}원")
            with result_col3:
                value_change = stress_results['total_value_change']
                st.metric(
                    "가치 변화",
                    f"{value_change:,.0f}원",
                    delta=f"{value_change / stress_results['total_investment']:.1%}"
                )

            st.metric("예상 포트폴리오 가치", f"{stress_results['new_portfolio_value']:,.0f}원")

            # 자산별 영향 테이블
            st.subheader("자산별 영향")

            impact_data = [{
                "티커": asset["ticker"],
                "종목명": asset["name"],
                "카테고리": asset["category"],
                "현재가치": f"{asset['current_value']:,.0f}원",
                "영향률": f"{asset['impact']:.2%}",
                "변화액": f"{asset['value_change']:,.0f}원",
                "예상가치": f"{asset['new_value']:,.0f}원"
            } for asset in stress_results['asset_impacts']]

            st.table(pd.DataFrame(impact_data))

# 몬테카를로 시뮬레이션 페이지
elif page == "몬테카를로 시뮬레이션":
    st.header("포트폴리오 몬테카를로 시뮬레이션")

    if not st.session_state.portfolio:
        st.warning("먼저 포트폴리오 최적화를 실행해주세요.")
    else:
        # 시뮬레이션 설정
        col1, col2 = st.columns(2)

        with col1:
            n_sim = st.slider(
                "시뮬레이션 횟수",
                min_value=100,
                max_value=2000,
                value=1000,
                step=100
            )

        with col2:
            years = st.slider(
                "시뮬레이션 기간(년)",
                min_value=1,
                max_value=30,
                value=10,
                step=1
            )

        if st.button("몬테카를로 시뮬레이션 실행", type="primary"):
            mc_results = st.session_state.analyzer.monte_carlo_simulation(
                st.session_state.portfolio,
                n_sim,
                years
            )

            # 시뮬레이션 결과 표시
            st.subheader(f"몬테카를로 시뮬레이션 결과 ({n_sim}회, {years}년)")

            result_col1, result_col2, result_col3 = st.columns(3)
            with result_col1:
                st.metric("평균 수익률", f"{mc_results['mean_return']:.2%}")
            with result_col2:
                st.metric("표준 편차", f"{mc_results['std_dev']:.2%}")
            with result_col3:
                st.metric("월 예상 배당금", f"{mc_results['expected_monthly_dividend']:,.0f}원")

            # 백분위수 표시
            st.subheader("수익률 백분위수")

            percentiles = [
                {"구분": "5% 백분위수", "수익률": f"{mc_results['percentiles']['5th']:.2%}",
                 "예상 가치": f"{mc_results['percentile_values']['5th']:,.0f}원"},
                {"구분": "25% 백분위수", "수익률": f"{mc_results['percentiles']['25th']:.2%}",
                 "예상 가치": f"{mc_results['percentile_values']['25th']:,.0f}원"},
                {"구분": "50% 백분위수", "수익률": f"{mc_results['percentiles']['50th']:.2%}",
                 "예상 가치": f"{mc_results['percentile_values']['50th']:,.0f}원"},
                {"구분": "75% 백분위수", "수익률": f"{mc_results['percentiles']['75th']:.2%}",
                 "예상 가치": f"{mc_results['percentile_values']['75th']:,.0f}원"},
                {"구분": "95% 백분위수", "수익률": f"{mc_results['percentiles']['95th']:.2%}",
                 "예상 가치": f"{mc_results['percentile_values']['95th']:,.0f}원"}
            ]

            st.table(pd.DataFrame(percentiles))

            # 몬테카를로 차트
            st.subheader("수익률 분포 차트")
            mc_fig = st.session_state.visualizer.plot_monte_carlo_simulation(mc_results)
            st.pyplot(mc_fig)

# 앱 시작점
if __name__ == "__main__":
    pass
