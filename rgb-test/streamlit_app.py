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
# 기본 디렉토리 설정
# -------------------------
current_dir = os.path.dirname(os.path.abspath(__file__))  # streamlit_app.py가 있는 폴더
resources_dir = current_dir  # 같은 폴더 안에 json, 폰트 등이 있음

# -------------------------
# CSS 스타일 (버튼, 질문 박스 등)
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
.question-box h2 { 
    text-align: center; 
    font-size: 1.7rem; 
    margin: 0; 
}
.intro-box { text-align: center; padding: 2rem; }
.intro-box h1 { font-size: 2.5rem; margin: 0 0 8px 0; }
.intro-box h2 { font-size: 1.2rem; color: #555; margin: 0 0 12px 0; }
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
.button-row {
    display:flex;
    justify-content:center;
    gap:6px;
    align-items:center;
}
</style>
""", unsafe_allow_html=True)

# -------------------------
# 폰트 설정 (NanumGothic.ttf)
# -------------------------
font_filename = 'NanumGothic.ttf'
font_path = os.path.join(resources_dir, font_filename)
font_exists = os.path.exists(font_path)

if font_exists:
    fm.fontManager.addfont(font_path)
    font_name = fm.FontProperties(fname=font_path).get_name()
    plt.rc('font', family=font_name)
    plt.rcParams['axes.unicode_minus'] = False
else:
    font_path = None  # 폰트가 없을 경우 None 처리

# -------------------------
# JSON 파일 로드 함수
# -------------------------
@st.cache_data
def load_data(filename):
    path = os.path.join(resources_dir, filename)
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

# -------------------------
# 결과 이미지 생성
# -------------------------
def generate_result_image(comprehensive_result, font_path=None):
    img_width = 900
    try:
        title_font = ImageFont.truetype(font_path, 40) if font_path else ImageFont.load_default()
        bold_font = ImageFont.truetype(font_path, 22) if font_path else ImageFont.load_default()
        text_font = ImageFont.truetype(font_path, 18) if font_path else ImageFont.load_default()
    except Exception:
        title_font = bold_font = text_font = ImageFont.load_default()

    img = Image.new("RGB", (900, 1200), "#FFFFFF")
    draw = ImageDraw.Draw(img)
    y = 60
    draw.text((450, y), "퍼스널컬러 심리검사 종합 결과", font=title_font, fill="black", anchor="mm")
    y += 100
    hex_color = comprehensive_result['hex']
    draw.rectangle([100, y, 800, y+150], fill=hex_color, outline="gray", width=2)
    y += 180
    draw.text((450, y), f"나의 종합 성격 색상: {hex_color}", font=bold_font, fill="black", anchor="mm")
    y += 60
    perc = comprehensive_result['percentages']
    colors = {'R': '#E63946', 'G': '#7FB069', 'B': '#457B9D'}
    labels = {'R': '진취형(R)', 'G': '중재형(G)', 'B': '신중형(B)'}
    for k in ['R', 'G', 'B']:
        draw.text((100, y), f"{labels[k]}: {perc[k]}%", font=bold_font, fill="black")
        draw.rectangle([100, y+35, 100 + perc[k]*7, y+55], fill=colors[k])
        y += 80
    y += 30
    draw.text((50, y), "상세 성격 분석", font=title_font, fill="black")
    y += 60
    for k in ['R', 'G', 'B']:
        draw.text((80, y), f"• {comprehensive_result['descriptions'][k]}", font=text_font, fill="#333333")
        y += 60

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()

# -------------------------
# 질문 그룹화 함수 (정상 동작)
# -------------------------
@st.cache_data
def get_balanced_questions_grouped(all_questions_data):
    initial = all_questions_data.get('questions', [])
    grouped = {}
    for q in initial:
        grouped.setdefault(q['type'], []).append(q)
    all_questions = []
    for v in grouped.values():
        all_questions.extend(v)
    random.shuffle(all_questions)
    for i, q in enumerate(all_questions):
        q['id'] = i + 1
    return all_questions

# -------------------------
# 앱 실행
# -------------------------
st.set_page_config(page_title="RGB 성격 심리 검사", layout="wide")
st.title("🧠 퍼스널컬러 심리검사")
st.markdown("---")

try:
    questions_all = load_data("questions.json")
    descriptions = load_data("descriptions.json")
    question_list = get_balanced_questions_grouped(questions_all)
except Exception as e:
    st.error("데이터 파일을 불러오지 못했습니다. questions.json 및 descriptions.json 파일을 확인하세요.")
    st.stop()

if len(question_list) == 0:
    st.warning("질문 데이터가 비어 있습니다. questions.json 파일을 확인하세요.")
    st.stop()

if 'stage' not in st.session_state:
    st.session_state.stage = 0
if 'responses' not in st.session_state:
    st.session_state.responses = {}

if st.session_state.stage == 0:
    st.markdown("<div class='intro-box'><h1>테스트 시작</h1><h2>아래 버튼을 눌러 시작하세요.</h2></div>", unsafe_allow_html=True)
    cols = st.columns([1.5, 1.2, 1])
    with cols[2]:
        if st.button("시작하기", key="start"):
            st.session_state.stage = 1
            st.rerun()
else:
    cur = st.session_state.stage
    total = len(question_list)
    if cur <= total:
        q = question_list[cur-1]
        st.markdown(f"<div class='question-box'><h2>Q{q['id']}. {q['text']}</h2></div>", unsafe_allow_html=True)
        cols = st.columns(9, gap="small")
        for i, val in enumerate(range(-4, 5)):
            with cols[i]:
                if st.button(str(val), key=f"q{q['id']}_val{val}"):
                    st.session_state.responses[q['id']] = {'type': q['type'], 'value': val}
                    st.session_state.stage += 1
                    st.rerun()
    else:
        # 결과 계산
        st.success("검사가 완료되었습니다!")
        scores = {'RP':0,'RS':0,'GP':0,'GS':0,'BP':0,'BS':0}
        for _, resp in st.session_state.responses.items():
            t = resp['type'][:-1]  # 예: RPi -> RP
            if t in scores:
                scores[t] += resp['value']
        final = {
            'R': 128 + scores['RP'] - scores['RS'],
            'G': 128 + scores['GP'] - scores['GS'],
            'B': 128 + scores['BP'] - scores['BS']
        }
        perc = {k: round((max(v,0)/256)*100, 1) for k,v in final.items()}
        hex_color = '#{:02X}{:02X}{:02X}'.format(min(final['R'],255),min(final['G'],255),min(final['B'],255))
        st.markdown(f"### 🎨 당신의 색상 코드: `{hex_color}`")
        comp_res = {'hex': hex_color, 'percentages': perc, 'descriptions': {'R': '진취형 설명', 'G': '중재형 설명', 'B': '신중형 설명'}}
        buf = generate_result_image(comp_res, font_path)
        st.download_button("📥 결과 이미지 저장", data=buf, file_name="RGB_result.png", mime="image/png")
