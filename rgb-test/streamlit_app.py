# streamlit_app.py (최종 수정본)
import streamlit as st
import json
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
import io
from PIL import Image, ImageDraw, ImageFont
import random
import math

# -------------------------
# ✅ 경로 자동 탐색 (rgb-test 중복 문제 완전 해결)
# -------------------------
current_dir = os.path.dirname(os.path.abspath(__file__))

# 만약 현재 디렉토리가 rgb-test라면 그대로 사용,
# 아니라면 rgb-test 폴더를 찾아 들어감
if os.path.basename(current_dir) == "rgb-test":
    resources_dir = current_dir
else:
    resources_dir = os.path.join(current_dir, "rgb-test")

# -------------------------
# 디버그용 정보 출력 (Streamlit에 표시됨)
# -------------------------
st.write("📁 현재 리소스 경로:", resources_dir)
st.write("📄 폰트 파일 존재 여부:", os.path.exists(os.path.join(resources_dir, "NanumGothic.ttf")))
st.write("📄 질문 파일 존재 여부:", os.path.exists(os.path.join(resources_dir, "questions.json")))
st.write("📄 설명 파일 존재 여부:", os.path.exists(os.path.join(resources_dir, "descriptions.json")))

# -------------------------
# CSS: 버튼 / 질문 박스 스타일
# -------------------------
st.markdown("""
<style>
.question-box { 
    min-height: 100px; 
    display: flex; 
    align-items: center; 
    justify-content: center; 
    padding: 1rem; 
    border-radius: 14px; 
    background-color: #f0f2f6; 
    margin-bottom: 1rem; 
}
.question-box h2 { text-align: center; font-size: 1.7rem; margin: 0; }

.intro-box { text-align: center; padding: 2rem; }
.intro-box h1 { font-size: 2.5rem; margin-bottom: 10px; }
.intro-box h2 { font-size: 1.2rem; color: #555; margin-bottom: 15px; }

div[data-testid="stButton"] > button {
    width: 160px;
    height: 70px;
    font-size: 1.25rem;
    font-weight: bold;
    border-radius: 14px;
    border: 2px solid #e0e0e0;
    background-color: #ffffff;
}
div[data-testid="stButton"] > button:hover {
    border-color: #457B9D; 
    color: #457B9D; 
}
div[data-testid="stDownloadButton"] > button {
    width: 300px; 
    height: 60px; 
    font-size: 1.15rem; 
    border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)

# -------------------------
# ✅ 폰트 설정
# -------------------------
font_path = os.path.join(resources_dir, "NanumGothic.ttf")

if os.path.exists(font_path):
    try:
        fm.fontManager.addfont(font_path)
        font_name = fm.FontProperties(fname=font_path).get_name()
        plt.rc("font", family=font_name)
        plt.rcParams["axes.unicode_minus"] = False
    except Exception as e:
        st.warning(f"폰트 등록 중 오류: {e}")
else:
    st.warning(f"⚠️ 폰트 파일을 찾을 수 없습니다: {font_path}")

# -------------------------
# 결과 이미지 생성 함수
# -------------------------
def generate_result_image(comprehensive_result, font_path):
    img_width = 900
    try:
        title_font = ImageFont.truetype(font_path, 40)
        text_font_bold = ImageFont.truetype(font_path, 22)
        text_font = ImageFont.truetype(font_path, 18)
    except Exception:
        title_font = text_font_bold = text_font = ImageFont.load_default()

    img_height = 1600
    img = Image.new("RGB", (img_width, img_height), color="#FDFDFD")
    draw = ImageDraw.Draw(img)

    draw.text((img_width/2, 60), "퍼스널컬러 심리검사 종합 결과", font=title_font, fill="black", anchor="mm")

    hex_color = comprehensive_result['hex']
    draw.rectangle([100, 120, 800, 270], fill=hex_color, outline="gray", width=2)
    draw.text((img_width/2, 300), f"나의 종합 성격 색상: {hex_color}", font=text_font_bold, fill="black", anchor="mm")

    y = 380
    p = comprehensive_result['percentages']
    draw.text((100, y), f"진취형(R): {p['R']}%", font=text_font_bold, fill="black")
    draw.rectangle([100, y+35, 100 + (p['R'] * 7), y+55], fill='#E63946')
    y += 80
    draw.text((100, y), f"중재형(G): {p['G']}%", font=text_font_bold, fill="black")
    draw.rectangle([100, y+35, 100 + (p['G'] * 7), y+55], fill='#7FB069')
    y += 80
    draw.text((100, y), f"신중형(B): {p['B']}%", font=text_font_bold, fill="black")
    draw.rectangle([100, y+35, 100 + (p['B'] * 7), y+55], fill='#457B9D')

    y += 150
    draw.text((50, y), "상세 성격 분석", font=title_font, fill="black")
    y += 80

    for key, color in zip(['R', 'G', 'B'], ['#E63946', '#7FB069', '#457B9D']):
        text = comprehensive_result['descriptions'][key]
        lines = text.split('•')
        for line in lines:
            if line.strip():
                draw.text((80, y), f"• {line.strip()}", font=text_font, fill="#333333")
                y += text_font.size + 8
        y += 10

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()

# -------------------------
# 데이터 로드 함수
# -------------------------
@st.cache_data
def load_data(filename):
    path = os.path.join(resources_dir, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# -------------------------
# 질문 그룹화
# -------------------------
@st.cache_data
def get_balanced_questions_grouped(all_data):
    if not all_data:
        return []
    qs = all_data.get("questions", [])
    typed = {}
    for q in qs:
        t = q.get("type")
        if t:
            typed.setdefault(t, []).append(q)

    r_count = min(len(typed.get("RP", [])), len(typed.get("RS", [])))
    g_count = min(len(typed.get("GP", [])), len(typed.get("GS", [])))
    b_count = min(len(typed.get("BP", [])), len(typed.get("BS", [])))

    balanced = (
        typed.get("RP", [])[:r_count] + typed.get("RS", [])[:r_count] +
        typed.get("GP", [])[:g_count] + typed.get("GS", [])[:g_count] +
        typed.get("BP", [])[:b_count] + typed.get("BS", [])[:b_count]
    )
    random.shuffle(balanced)
    for i, q in enumerate(balanced):
        q["id"] = i + 1
    return balanced

# -------------------------
# Streamlit 앱 실행
# -------------------------
st.set_page_config(page_title="RGB 성격 심리 검사", layout="wide")
st.title("🧠 퍼스널컬러 심리검사")
st.markdown("---")

try:
    descriptions = load_data("descriptions.json")
    questions_all = load_data("questions.json")
except FileNotFoundError as e:
    st.error(f"데이터 파일을 찾을 수 없습니다: {e}")
    st.stop()

questions = get_balanced_questions_grouped(questions_all)
total_questions = len(questions)

if "responses" not in st.session_state:
    st.session_state["responses"] = {}
if "stage" not in st.session_state:
    st.session_state["stage"] = -1  # -1: 시작 전

if total_questions == 0:
    st.warning("불러온 질문이 없습니다. questions.json을 확인하세요.")
else:
    if st.session_state["stage"] == -1:
        st.markdown("<div class='intro-box'><h1>테스트 시작</h1><h2>아래 버튼을 눌러 시작하세요.</h2></div>", unsafe_allow_html=True)
        cols = st.columns([1.5, 1.2, 1])
        with cols[2]:
            if st.button("시작하기"):
                st.session_state["stage"] = 0
                st.rerun()
    elif st.session_state["stage"] < total_questions:
        cur = st.session_state["stage"]
        q = questions[cur]
        st.markdown(f"<div class='question-box'><h2>Q{q['id']}. {q['text']}</h2></div>", unsafe_allow_html=True)
        label_cols = st.columns([1, 5, 1])
        with label_cols[0]:
            st.markdown("<p style='text-align:left; font-weight:bold; color:#555;'>⟵ 그렇지 않다</p>", unsafe_allow_html=True)
        with label_cols[2]:
            st.markdown("<p style='text-align:right; font-weight:bold; color:#555;'>그렇다 ⟶</p>", unsafe_allow_html=True)
        cols_btn = st.columns(9)
        for i, val in enumerate(range(-4, 5)):
            with cols_btn[i]:
                if st.button(str(val), key=f"q{q['id']}_val{val}"):
                    st.session_state["responses"][q["id"]] = {"type": q["type"], "value": val}
                    st.session_state["stage"] += 1
                    st.rerun()
    else:
        st.balloons()
        st.success("검사가 완료되었습니다! 🎉")
        st.markdown("---")

        scores = {"RP": 0, "RS": 0, "GP": 0, "GS": 0, "BP": 0, "BS": 0}
        for _, r in st.session_state["responses"].items():
            if r["type"] in scores:
                scores[r["type"]] += r["value"]

        final = {
            "R": 128 + scores["RP"] - scores["RS"],
            "G": 128 + scores["GP"] - scores["GS"],
            "B": 128 + scores["BP"] - scores["BS"],
        }
        abs_scores = {k: max(v, 0) for k, v in final.items()}
        perc = {k: round((v / 256) * 100, 1) for k, v in abs_scores.items()}
        hex_color = "#{:02X}{:02X}{:02X}".format(int(min(abs_scores["R"], 255)), int(min(abs_scores["G"], 255)), int(min(abs_scores["B"], 255)))

        st.header("📈 당신의 성격 분석 결과")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 🎨 당신의 고유 성격 색상")
            st.markdown(f"<div style='width:100%; height:200px; background-color:{hex_color}; border-radius:12px; border:2px solid #ccc;'></div>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align:center; font-size:24px; font-weight:bold;'>{hex_color}</p>", unsafe_allow_html=True)
        with col2:
            st.markdown("### ✨ 유형별 강도 시각화")
            fig, ax = plt.subplots(figsize=(8,4))
            y_labels = ["진취형 (R)", "중재형 (G)", "신중형 (B)"]
            vals = [perc["R"], perc["G"], perc["B"]]
            colors = ["#E63946", "#7FB069", "#457B9D"]
            bars = ax.barh(y_labels, vals, color=colors, height=0.6)
            ax.set_xlim(0,115)
            ax.spines[['top','right','left','bottom']].set_visible(False)
            for b in bars:
                w = b.get_width()
                ax.text(w+2, b.get_y()+b.get_height()/2, f"{w}%", va='center', fontsize=11)
            st.pyplot(fig)

        # 상세 설명
        st.header("📜 상세 성격 분석")
        def get_idx(p):
            return min(int(p // 10), 9)
        r_idx, g_idx, b_idx = get_idx(perc["R"]), get_idx(perc["G"]), get_idx(perc["B"])

        descs = descriptions
        r_text = descs["R"][r_idx] if isinstance(descs.get("R"), list) else descs.get("R", "")
        g_text = descs["G"][g_idx] if isinstance(descs.get("G"), list) else descs.get("G", "")
        b_text = descs["B"][b_idx] if isinstance(descs.get("B"), list) else descs.get("B", "")

        st.info(f"**🔴 진취형(R):** {r_text}")
        st.success(f"**🟢 중재형(G):** {g_text}")
        st.warning(f"**🔵 신중형(B):** {b_text}")

        # 이미지 다운로드
        comp_res = {"hex": hex_color, "percentages": perc, "descriptions": {"R": r_text, "G": g_text, "B": b_text}}
        img_buf = generate_result_image(comp_res, font_path)
        st.download_button("📥 결과 이미지 저장", img_buf, "RGB_personality_result.png", "image/png")

        if st.button("다시 검사하기"):
            st.session_state.clear()
            st.rerun()
