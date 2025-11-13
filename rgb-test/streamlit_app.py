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
# 설정: 현재 스크립트 위치 기준
# (중요: app.py가 Mental-Personal-Color-Test 폴더에 있고, rgb-test 폴더가 그 안에 있을 때의 경로 설정)
# -------------------------
current_dir = os.path.dirname(os.path.abspath(__file__))  # app.py가 있는 폴더 (예: .../Mental-Personal-Color-Test)
# resources_dir은 이제 직접적으로 사용하지 않고, current_dir에 'rgb-test'를 붙여 사용합니다.
# resources_dir = current_dir # 이 줄은 이제 의미상 제거됩니다.

# -------------------------
# CSS: 버튼 크기, 모양, 질문 박스 등
# -------------------------
st.markdown("""
<style>
/* 전체 질문 박스 모서리 둥글게, 중앙 정렬 */
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

/* 질문 텍스트(글씨 크기 변경 시 여기 수정) */
.question-box h2 {
    text-align: center;
    font-size: 1.7rem;
    margin: 0;
}

/* intro 박스 */
.intro-box { text-align: center; padding: 2rem; }
.intro-box h1 { font-size: 2.5rem; margin: 0 0 8px 0; }
.intro-box h2 { font-size: 1.2rem; color: #555; margin: 0 0 12px 0; }

/* 스택에서 제공하는 버튼 스타일 조정 (모서리 둥글게, 크기 확대) */
div[data-testid="stButton"] > button {
    width: 160px;   /* 버튼 가로 크기 조정 */
    height: 70px;   /* 버튼 세로 크기 조정 */
    font-size: 1.25rem;
    font-weight: bold;
    border-radius: 14px;
    border: 2px solid #e0e0e0;
    background-color: #ffffff;
}

/* hover 효과 */
div[data-testid="stButton"] > button:hover {
    border-color: #457B9D;
    color: #457B9D;
}

/* 다운로드 버튼 스타일 (크게) */
div[data-testid="stDownloadButton"] > button {
    width: 300px;
    height: 60px;
    font-size: 1.15rem;
    border-radius: 12px;
}

/* 9개 버튼을 묶는 가상 컨테이너 (스트림릿 레이아웃과 혼합되어 동작) */
.button-row {
    display:flex;
    justify-content:center;
    gap:6px; /* 버튼 사이 간격을 작게 */
    align-items:center;
}
</style>
""", unsafe_allow_html=True)

# -------------------------
# 폰트 파일 경로 (이미지 생성 + matplotlib 한글 폰트)
# [수정 시작]
# -------------------------
font_filename = 'NanumGothic.ttf'  # 실제 파일명
font_path = os.path.join(current_dir, 'rgb-test', font_filename) # 'rgb-test' 폴더를 경로에 추가

if os.path.exists(font_path):
    try:
        fm.fontManager.addfont(font_path)
        font_name = fm.FontProperties(fname=font_path).get_name()
        plt.rc('font', family=font_name)
        plt.rcParams['axes.unicode_minus'] = False
    except Exception as e:
        st.warning(f"폰트 추가 중 문제 발생: {e}")
else:
    st.warning(f"한글 폰트 파일('{font_path}')을 찾을 수 없습니다. 그래프/이미지의 한글이 깨질 수 있습니다.")

# -------------------------
# 결과 이미지 생성 함수 (동적 높이 + 폰트 적용)
# (이 함수는 경로 수정 외에는 변경 없음)
# -------------------------
def generate_result_image(comprehensive_result, font_path):
    # comprehensive_result: {'hex':..., 'percentages': {'R':..,'G':..,'B':..}, 'descriptions': {'R':..,'G':..,'B':..}}
    img_width = 900

    # 폰트 로드 (PIL용)
    try:
        title_font = ImageFont.truetype(font_path, 40)
        text_font_bold = ImageFont.truetype(font_path, 22)
        text_font = ImageFont.truetype(font_path, 18)
    except Exception:
        # 폰트 없으면 기본 폰트 사용
        title_font = ImageFont.load_default()
        text_font_bold = ImageFont.load_default()
        text_font = ImageFont.load_default()

    # 간단히 높이 계산 (텍스트 양에 따라 자동 확장)
    temp_img = Image.new("RGB", (img_width, 100), color="#FDFDFD")
    temp_draw = ImageDraw.Draw(temp_img)
    y = 60
    title_text = "퍼스널컬러 심리검사 종합 결과"
    title_h = temp_draw.textbbox((0,0), title_text, font=title_font)[3]
    y += title_h + 40

    y += 150 + 40  # 색상 박스 높이 + 여백

    percentages = comprehensive_result['percentages']
    # 각 바 영역
    y += (text_font_bold.size + 6) + (25 + 20)  # R
    y += (text_font_bold.size + 6) + (25 + 20)  # G
    y += (text_font_bold.size + 6) + (25 + 20)  # B

    y += 60  # 상세 제목 여백

    # 상세 텍스트 길이(대략)
    def estimate_text_block_height(txt, font, draw_obj, width_limit):
        pts = [p.strip() for p in txt.split('•') if p.strip()]
        h = 0
        for p in pts:
            # 한 포인트의 대략 줄수 계산
            words = p.split(' ')
            line = ""
            lines = 1
            for w in words:
                if draw_obj.textlength(line + w, font=font) < (width_limit - 120):
                    line += w + " "
                else:
                    lines += 1
                    line = w + " "
            h += lines * (font.size + 6) + 10
        return h

    desc = comprehensive_result['descriptions']
    y += estimate_text_block_height(desc['R'], text_font, temp_draw, img_width)
    y += estimate_text_block_height(desc['G'], text_font, temp_draw, img_width)
    y += estimate_text_block_height(desc['B'], text_font, temp_draw, img_width)

    final_height = int(y + 100)

    # 실제 이미지 생성
    img = Image.new("RGB", (img_width, final_height), color="#FDFDFD")
    draw = ImageDraw.Draw(img)
    cursor = 60

    # 제목
    draw.text((img_width/2, cursor), title_text, font=title_font, fill="black", anchor="mm")
    cursor += title_h + 40

    # 색상 박스
    hex_color = comprehensive_result['hex']
    draw.rectangle([100, cursor, img_width-100, cursor+150], fill=hex_color, outline="gray", width=2)
    cursor += 150 + 20

    # 색상 코드
    color_info_text = f"나의 종합 성격 색상: {hex_color}"
    draw.text((img_width/2, cursor), color_info_text, font=text_font_bold, fill="black", anchor="mm")
    cursor += text_font_bold.getsize(color_info_text)[1] + 30

    # 퍼센티지 바들
    draw.text((100, cursor), f"진취형(R): {percentages['R']}%", font=text_font_bold, fill="black")
    draw.rectangle([100, cursor+35, 100 + (percentages['R'] * 7), cursor + 55], fill='#E63946')
    cursor += 80

    draw.text((100, cursor), f"중재형(G): {percentages['G']}%", font=text_font_bold, fill="black")
    draw.rectangle([100, cursor+35, 100 + (percentages['G'] * 7), cursor + 55], fill='#7FB069')
    cursor += 80

    draw.text((100, cursor), f"신중형(B): {percentages['B']}%", font=text_font_bold, fill="black")
    draw.rectangle([100, cursor+35, 100 + (percentages['B'] * 7), cursor + 55], fill='#457B9D')
    cursor += 80 + 40

    # 상세 섹션
    draw.text((50, cursor), "상세 성격 분석", font=title_font, fill="black")
    cursor += title_font.getsize("상세 성격 분석")[1] + 30

    # 상세 텍스트 그리기 (줄바꿈 처리)
    def draw_multiline_by_bullet(text, ystart):
        cur = ystart
        pts = [p.strip() for p in text.split('•') if p.strip()]
        for p in pts:
            line_with_bullet = "• " + p
            words = line_with_bullet.split(' ')
            line = ""
            for w in words:
                if draw.textlength(line + w, font=text_font) < (img_width - 160):
                    line += w + " "
                else:
                    draw.text((80, cur), line, font=text_font, fill="#333333")
                    cur += text_font.size + 6
                    line = w + " "
            if line:
                draw.text((80, cur), line, font=text_font, fill="#333333")
                cur += text_font.size + 6
            cur += 10
        return cur

    cursor = draw_multiline_by_bullet(desc['R'], cursor)
    cursor = draw_multiline_by_bullet(desc['G'], cursor)
    cursor = draw_multiline_by_bullet(desc['B'], cursor)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()

# -------------------------
# 데이터 로드 함수 (current_dir 기준으로 'rgb-test' 폴더 안에서 찾도록 수정)
# [수정 시작]
# -------------------------
@st.cache_data
def load_data(filename):
    # current_dir은 Mental-Personal-Color-Test 폴더를 가리키고,
    # 데이터 파일은 그 안의 rgb-test 폴더에 있습니다.
    path = os.path.join(current_dir, 'rgb-test', filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {path}") # 더 명확한 오류 메시지
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)
# [수정 끝]

# -------------------------
# 질문 그룹화 함수 (questions.json 구조에 맞춰 수정)
# (이 부분이 '불러온 질문이 없습니다' 에러의 주 원인일 수 있습니다)
# [수정 시작]
# -------------------------
@st.cache_data
def get_balanced_questions_grouped(all_questions_data):
    if not all_questions_data:
        st.error("questions.json 데이터가 비어있거나 올바르지 않습니다.") # 추가 오류 메시지
        return [] # 빈 리스트 반환

    initial_question_list = all_questions_data.get('questions', []) # 'questions' 키가 없으면 빈 리스트 반환
    if not initial_question_list:
        st.error("questions.json 파일에 'questions' 키가 없거나 질문 목록이 비어 있습니다.") # 추가 오류 메시지
        return []

    # 'RP', 'RS', 'GP', 'GS', 'BP', 'BS'와 같은 기본 타입으로 그룹화
    typed_questions = { f"{main}{sub}":[] for main in "RGB" for sub in "PS" }

    for q in initial_question_list:
        q_type = q.get('type')
        # questions.json의 type이 'RPi', 'RSa' 처럼 뒤에 i/a/s가 붙어있다고 가정
        # 그래서 앞 두 글자만 추출하여 기본 타입으로 사용합니다.
        base_type = q_type[:2] if q_type and len(q_type) >= 2 else None

        if base_type in typed_questions:
            typed_questions[base_type].append(q)
        else:
            # 예상치 못한 타입이 있을 경우 경고 (디버깅용)
            if q_type:
                st.warning(f"예상치 못한 질문 타입 발견: {q_type}. 이 질문은 검사에 포함되지 않습니다.")


    # RP/RS, GP/GS, BP/BS 각 쌍의 질문 수를 맞춰 균형을 맞춥니다.
    # 각 타입에서 사용할 수 있는 질문의 최소 개수를 찾습니다.
    r_count = min(len(typed_questions.get('RP', [])), len(typed_questions.get('RS', [])))
    g_count = min(len(typed_questions.get('GP', [])), len(typed_questions.get('GS', [])))
    b_count = min(len(typed_questions.get('BP', [])), len(typed_questions.get('BS', [])))

    balanced = []
    # min_count만큼 질문을 가져와 추가합니다.
    balanced.extend(typed_questions.get('RP', [])[:r_count])
    balanced.extend(typed_questions.get('RS', [])[:r_count])
    balanced.extend(typed_questions.get('GP', [])[:g_count])
    balanced.extend(typed_questions.get('GS', [])[:g_count])
    balanced.extend(typed_questions.get('BP', [])[:b_count])
    balanced.extend(typed_questions.get('BS', [])[:b_count])

    random.shuffle(balanced) # 질문 순서 섞기

    # 질문 ID 재부여 (1부터 시작)
    for i, q in enumerate(balanced):
        q['id'] = i + 1

    return balanced
# [수정 끝]

# -------------------------
# 실제 앱 흐름
# -------------------------
st.set_page_config(page_title="RGB 성격 심리 검사", layout="wide")
st.title("🧠 퍼스널컬러 심리검사")
st.markdown("---")

# 데이터 로드 (예외 메시지를 사용자에게 명확히)
try:
    descriptions = load_data('descriptions.json')
    questions_all = load_data('questions.json')
except FileNotFoundError as e:
    st.error(f"데이터 파일을 찾을 수 없습니다: {e}")
    st.stop() # 파일이 없으면 앱 실행 중단

# 질문을 원하는 방식으로 그룹화/균형화
question_list = get_balanced_questions_grouped(questions_all)
total_questions = len(question_list)

if 'responses' not in st.session_state:
    st.session_state['responses'] = {}

# --- Intro 화면: 시작 버튼을 우측으로 이동시키고 크게 함 ---
# total_questions가 0이면 시작 버튼을 보여주지 않고 에러 메시지만 남김
if total_questions == 0:
    st.error("질문 목록을 불러오지 못했습니다. `questions.json` 파일의 내용을 확인해주세요.")
else:
    st.markdown("<div class='intro-box'><h1>테스트 시작</h1><h2>아래 버튼을 눌러 시작하세요.</h2></div>", unsafe_allow_html=True)
    cols = st.columns([1.5, 1.2, 1])
    with cols[2]:
        if st.button("시작하기", key="start"):
            st.session_state['stage'] = 0
            st.rerun()

# 검사 진행
if total_questions > 0: # 질문 목록이 있을 때만 검사 진행 로직 실행
    # stage 인덱스(현재 문항)
    if 'stage' not in st.session_state:
        st.session_state['stage'] = 0

    cur = st.session_state['stage']
    if cur < total_questions:
        q = question_list[cur]
        st.markdown(f"<div class='question-box'><h2>Q{q['id']}. {q['text']}</h2></div>", unsafe_allow_html=True)
        # 좌/우 레이블
        label_cols = st.columns([1, 5, 1])
        with label_cols[0]:
            st.markdown("<p style='text-align:left; font-weight:bold; color:#555;'>⟵ 그렇지 않다</p>", unsafe_allow_html=True)
        with label_cols[2]:
            st.markdown("<p style='text-align:right; font-weight:bold; color:#555;'>그렇다 ⟶</p>", unsafe_allow_html=True)

        # 9개 버튼 한 줄로 중앙 정렬
        cols_buttons = st.columns(9, gap="small")
        for i, val in enumerate(range(-4, 5)):
            with cols_buttons[i]:
                if st.button(str(val), key=f"q{q['id']}_val{val}"):
                    # [수정 시작] q['type']에서 'i/a/s' 접미사 제거
                    st.session_state['responses'][q['id']] = {'type': q['type'][:2], 'value': val}
                    # [수정 끝]
                    st.session_state['stage'] = cur + 1
                    st.rerun()
    else:
        # 결과 계산
        st.balloons()
        st.success("검사가 완료되었습니다! 결과를 확인하세요.")
        st.markdown("---")

        # 점수 합산
        # [수정 시작] scores 딕셔너리 키를 'RP', 'RS' 등 기본 타입으로 변경
        scores = {'RP': 0, 'RS': 0, 'GP': 0, 'GS': 0, 'BP': 0, 'BS': 0}
        # [수정 끝]
        for qid, resp in st.session_state['responses'].items():
            t = resp['type']
            v = resp['value']
            if t in scores:
                scores[t] += v

        # [수정 시작] final_scores 계산 로직 변경 (이전 3배 대신 2배로 조정)
        final_scores = {
            'R': 128 + (scores['RP'] - scores['RS']) * 2,
            'G': 128 + (scores['GP'] - scores['GS']) * 2,
            'B': 128 + (scores['BP'] - scores['BS']) * 2
        }
        # [수정 끝]
        absolute_scores = {k: max(v, 0) for k, v in final_scores.items()}
        percentages = {k: round((v / 256) * 100, 1) for k, v in absolute_scores.items()}
        hex_color = '#{:02X}{:02X}{:02X}'.format(min(absolute_scores['R'], 255), min(absolute_scores['G'], 255), min(absolute_scores['B'], 255))

        st.header("📈 당신의 성격 분석 결과")
        col1, col2 = st.columns([1,1])
        with col1:
            st.markdown("### 🎨 당신의 고유 성격 색상")
            st.markdown(f"<div style='width:100%; height:200px; background-color:{hex_color}; border-radius:12px; border:2px solid #ccc;'></div>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align:center; font-size:24px; font-weight:bold; margin-top:10px;'>{hex_color}</p>", unsafe_allow_html=True)
        with col2:
            st.markdown("### ✨ 유형별 강도 시각화")
            fig, ax = plt.subplots(figsize=(8,4))
            y_labels = ["진취형 (R)", "중재형 (G)", "신중형 (B)"]
            vals = [percentages['R'], percentages['G'], percentages['B']]
            colors = ['#E63946', '#7FB069', '#457B9D']
            bars = ax.barh(y_labels, vals, color=colors, height=0.6)
            ax.set_xlim(0,115)
            ax.spines[['top','right','left','bottom']].set_visible(False)
            ax.xaxis.set_ticks_position('none'); ax.yaxis.set_ticks_position('none')
            ax.set_xticklabels([]); ax.set_yticklabels(y_labels, fontsize=12)
            for b in bars:
                w = b.get_width()
                ax.text(w+2, b.get_y()+b.get_height()/2, f"{w}%", va='center', fontsize=11)
            st.pyplot(fig)

        st.markdown("---")

        # description index 선택 (단순 재사용)
        def get_index(p):
            if p <= 10: return 0
            if p <= 20: return 1
            if p <= 30: return 2
            if p <= 40: return 3
            if p <= 50: return 4
            if p <= 60: return 5
            if p <= 70: return 6
            if p <= 80: return 7
            if p <= 90: return 8
            return 9

        r_idx = get_index(percentages['R'])
        g_idx = get_index(percentages['G'])
        b_idx = get_index(percentages['B'])

        # description 파일 포맷에 맞게 조정해서 사용
        try:
            descs = descriptions
            # [수정 시작] descriptions.json 파일 구조를 'comprehensive' 키를 포함하는 형태로 가정
            # 예: descriptions['comprehensive']['R'][r_idx]
            r_text = descs['comprehensive']['R'][r_idx] if isinstance(descs.get('comprehensive', {}).get('R'), list) else descs.get('R', '')
            g_text = descs['comprehensive']['G'][g_idx] if isinstance(descs.get('comprehensive', {}).get('G'), list) else descs.get('G', '')
            b_text = descs['comprehensive']['B'][b_idx] if isinstance(descs.get('comprehensive', {}).get('B'), list) else descs.get('B', '')
            # [수정 끝]
        except Exception as e:
            r_text = g_text = b_text = f"상세 설명을 불러오는 중 오류가 발생했습니다. descriptions.json 파일 구조를 확인해주세요. 오류: {e}"

        st.header("📜 상세 성격 분석")
        st.markdown("### 🔴 진취형(R)에 대하여")
        st.info(r_text)
        st.markdown("### 🟢 중재형(G)에 대하여")
        st.success(g_text)
        st.markdown("### 🔵 신중형(B)에 대하여")
        st.warning(b_text)

        # 종합 이미지 생성 및 다운로드
        comp_res = {'hex': hex_color, 'percentages': percentages, 'descriptions': {'R': r_text, 'G': g_text, 'B': b_text}}
        image_buf = generate_result_image(comp_res, font_path)
        st.download_button(label="📥 종합 결과 이미지 저장하기", data=image_buf, file_name="RGB_personality_result.png", mime="image/png")

        if st.button("다시 검사하기"):
            st.session_state.clear()
            st.rerun()


