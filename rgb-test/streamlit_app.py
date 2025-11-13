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
# 설정: 현재 스크립트 위치 기준 (중요: 여기서 리소스 폴더 중복 참조를 제거)
# -------------------------
current_dir = os.path.dirname(os.path.abspath(__file__))  # streamlit_app.py가 있는 폴더
resources_dir = current_dir  # 질문/설명/폰트 파일이 같은 폴더에 있다고 가정

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
/* [수정] 9개 버튼 크기 조정 */
div[data-testid="stButton"] > button {
    width: 100%;   /* 버튼 가로 크기 (컬럼에 꽉 차게) */
    height: 70px;   /* 버튼 세로 크기 조정 */
    font-size: 1.25rem;
    font-weight: bold;
    border-radius: 14px;
    border: 2px solid #e0e0e0;
    background-color: #ffffff;
}

/* [수정] 시작하기 버튼은 별도로 식별이 어려우므로 CSS로 크게 만들기보다, st.columns 비율로 조절 */

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
</style>
""", unsafe_allow_html=True)

# -------------------------
# 폰트 파일 경로 (이미지 생성 + matplotlib 한글 폰트)
# -------------------------
font_filename = 'NanumGothic.ttf'  # 실제 파일명 (예: NanumGothic.ttf)
font_path = os.path.join(resources_dir, 'rgb-test', font_filename) # [수정] rgb-test 폴더 안에 있는 것으로 경로 수정

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
# [수정] 폰트 크기 계산 방식 변경 (getsize -> textbbox/textlength)
# -------------------------
def generate_result_image(comprehensive_result, font_path):
    img_width = 900

    # 폰트 로드 (PIL용)
    try:
        title_font = ImageFont.truetype(font_path, 40)
        text_font_bold = ImageFont.truetype(font_path, 22)
        text_font = ImageFont.truetype(font_path, 18)
    except Exception:
        title_font = ImageFont.load_default()
        text_font_bold = ImageFont.load_default()
        text_font = ImageFont.load_default()

    # 1. 높이 계산 (텍스트 양에 따라 자동 확장)
    temp_img = Image.new("RGB", (img_width, 100), color="#FDFDFD")
    temp_draw = ImageDraw.Draw(temp_img)
    y = 60
    title_text = "퍼스널컬러 심리검사 종합 결과"
    title_h = temp_draw.textbbox((0,0), title_text, font=title_font)[3] - temp_draw.textbbox((0,0), title_text, font=title_font)[1]
    y += title_h + 40

    y += 150 + 20  # 색상 박스 높이 + 여백
    
    color_info_text = f"나의 종합 성격 색상: {comprehensive_result['hex']}"
    color_info_h = temp_draw.textbbox((0,0), color_info_text, font=text_font_bold)[3] - temp_draw.textbbox((0,0), color_info_text, font=text_font_bold)[1]
    y += color_info_h + 30

    percentages = comprehensive_result['percentages']
    # 각 바 영역
    y += 80  # R (텍스트 높이 포함)
    y += 80  # G
    y += 80 + 40 # B + 여백

    detail_title_text = "상세 성격 분석"
    detail_title_h = temp_draw.textbbox((0,0), detail_title_text, font=title_font)[3] - temp_draw.textbbox((0,0), detail_title_text, font=title_font)[1]
    y += detail_title_h + 30  # 상세 제목 여백

    # 상세 텍스트 길이(대략)
    def estimate_text_block_height(txt, font, draw_obj, width_limit):
        pts = [p.strip() for p in txt.split('•') if p.strip()]
        h = 0
        for p in pts:
            line_with_bullet = "• " + p
            words = line_with_bullet.split(' ')
            line = ""
            lines_count = 1
            for w in words:
                if draw_obj.textlength(line + w, font=font) < (width_limit - 160): # 80 + 80 여백
                    line += w + " "
                else:
                    lines_count += 1
                    line = w + " "
            h += lines_count * (font.size + 6) + 10 # 줄간격 + 불릿간격
        return h

    desc = comprehensive_result['descriptions']
    y += estimate_text_block_height(desc['R'], text_font, temp_draw, img_width)
    y += estimate_text_block_height(desc['G'], text_font, temp_draw, img_width)
    y += estimate_text_block_height(desc['B'], text_font, temp_draw, img_width)

    final_height = int(y + 100) # 하단 여백

    # 2. 실제 이미지 생성
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
    draw.text((img_width/2, cursor), color_info_text, font=text_font_bold, fill="black", anchor="mm")
    cursor += color_info_h + 30

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
    draw.text((50, cursor), detail_title_text, font=title_font, fill="black")
    cursor += detail_title_h + 30

    # 상세 텍스트 그리기 (줄바꿈 처리)
    def draw_multiline_by_bullet(text, ystart):
        cur = ystart
        pts = [p.strip() for p in text.split('•') if p.strip()]
        for p in pts:
            line_with_bullet = "• " + p
            words = line_with_bullet.split(' ')
            line = ""
            for w in words:
                if draw.textlength(line + w, font=text_font) < (img_width - 160): # 양쪽 여백 80씩
                    line += w + " "
                else:
                    draw.text((80, cur), line, font=text_font, fill="#333333")
                    cur += text_font.size + 6
                    line = w + " "
            if line: # 마지막 줄 그리기
                draw.text((80, cur), line, font=text_font, fill="#333333")
                cur += text_font.size + 6
            cur += 10 # 불릿 사이 간격
        return cur

    cursor = draw_multiline_by_bullet(desc['R'], cursor)
    cursor = draw_multiline_by_bullet(desc['G'], cursor)
    cursor = draw_multiline_by_bullet(desc['B'], cursor)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()

# -------------------------
# 데이터 로드 함수 (resources_dir 기준으로 안전하게 읽기)
# [수정] rgb-test 폴더를 경로에 포함
# -------------------------
@st.cache_data
def load_data(filename):
    path = os.path.join(resources_dir, 'rgb-test', filename)
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

# -------------------------
# [변경] 질문 그룹화 함수 -> 'i', 'a', 's' 제거 (단순화된 JSON 구조 반영)
# -------------------------
@st.cache_data
def get_balanced_questions_grouped(all_questions_data):
    if not all_questions_data:
        return {}
    initial_question_list = all_questions_data.get('questions', [])
    
    # [수정] typed_questions를 RP/RS, GP/GS, BP/BS만 보도록 단순화
    typed_questions = { f"{main}{sub}":[] for main in "RGB" for sub in "PS" }
    
    for q in initial_question_list:
        t = q.get('type')
        # [수정] 'i', 'a', 's' 접미사를 제거하고 기본 타입만 봅니다.
        base_type = t[:2] if t else None 
        if base_type in typed_questions:
            typed_questions[base_type].append(q)

    # RP/RS, GP/GS, BP/BS 균형 맞추기
    r_count = min(len(typed_questions.get('RP', [])), len(typed_questions.get('RS', [])))
    g_count = min(len(typed_questions.get('GP', [])), len(typed_questions.get('GS', [])))
    b_count = min(len(typed_questions.get('BP', [])), len(typed_questions.get('BS', [])))

    balanced = []
    balanced += typed_questions.get('RP', [])[:r_count] + typed_questions.get('RS', [])[:r_count]
    balanced += typed_questions.get('GP', [])[:g_count] + typed_questions.get('GS', [])[:g_count]
    balanced += typed_questions.get('BP', [])[:b_count] + typed_questions.get('BS', [])[:b_count]

    random.shuffle(balanced)
    
    # ID 재부여
    for i, q in enumerate(balanced):
        q['id'] = i + 1
        
    return balanced

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
    st.stop()

# 질문을 원하는 방식으로 그룹화/균형화 (단순화된 로직 적용)
question_list = get_balanced_questions_grouped(questions_all)
total_questions = len(question_list)

if 'responses' not in st.session_state:
    st.session_state['responses'] = {}

# [변경] stage 로직 수정 (intro / quiz / results)
if 'stage' not in st.session_state:
    st.session_state['stage'] = 'intro'
if 'current_question_index' not in st.session_state:
    st.session_state['current_question_index'] = 0


# --- Intro 화면 ---
if st.session_state['stage'] == 'intro':
    st.markdown("<div class='intro-box'><h1>테스트 시작</h1><h2>아래 버튼을 눌러 시작하세요.</h2></div>", unsafe_allow_html=True)
    # [수정] 버튼을 중앙에 배치하고 크기를 조절하기 위해 CSS 대신 컬럼 비율 사용
    cols = st.columns([1.5, 1, 1.5]) 
    with cols[1]: # 중앙 컬럼
        # [수정] CSS 대신 Streamlit의 use_container_width=True 사용
        if st.button("시작하기", key="start", use_container_width=True):
            st.session_state['stage'] = 'quiz'
            st.session_state['current_question_index'] = 0
            st.session_state['responses'] = {}
            st.rerun()

# --- 검사 진행 ---
elif st.session_state['stage'] == 'quiz':
    if total_questions == 0:
        st.warning("불러온 질문이 없습니다. questions.json을 확인하세요.")
        st.stop()

    cur_idx = st.session_state['current_question_index']
    
    # 진행률 표시
    progress = (cur_idx / total_questions) if total_questions > 0 else 0
    st.progress(progress, text=f"진행률: {cur_idx} / {total_questions}")

    if cur_idx < total_questions:
        q = question_list[cur_idx]
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
                # [수정] use_container_width=True로 버튼이 컬럼에 꽉 차도록 함
                if st.button(str(val), key=f"q{q['id']}_val{val}", use_container_width=True):
                    # [수정] 'i', 'a', 's' 없는 기본 타입 저장
                    st.session_state['responses'][q['id']] = {'type': q['type'][:2], 'value': val}
                    st.session_state['current_question_index'] = cur_idx + 1
                    
                    # 마지막 질문이면 결과 페이지로
                    if st.session_state['current_question_index'] == total_questions:
                        st.session_state['stage'] = 'results'
                    
                    st.rerun()
    else:
        # 이 블록은 'quiz' 스테이지이지만 cur_idx >= total_questions일 때 도달 (사실상 위에서 처리됨)
        st.session_state['stage'] = 'results'
        st.rerun()

# --- 결과 화면 ---
elif st.session_state['stage'] == 'results':
    st.balloons()
    st.success("검사가 완료되었습니다! 결과를 확인하세요.")
    st.markdown("---")

    # [변경] 점수 합산 (i, a, s 구분 없음)
    scores = {'RP': 0, 'RS': 0, 'GP': 0, 'GS': 0, 'BP': 0, 'BS': 0}
    for qid, resp in st.session_state['responses'].items():
        t = resp['type'] # 이미 'RP', 'RS' 등으로 저장됨
        v = resp['value']
        if t in scores:
            scores[t] += v

    # [변경] 점수 계산 (i, a, s 구분 없음)
    final_scores = {
        'R': 128 + (scores['RP'] - scores['RS']) * 2, # [수정] 기존 로직(i,a,s 3배) 대신 2배로 조정 (필요시 배율 조정)
        'G': 128 + (scores['GP'] - scores['GS']) * 2,
        'B': 128 + (scores['BP'] - scores['BS']) * 2
    }
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

    # [변경] description 파일 포맷에 맞게 조정 (comprehensive 키 사용)
    try:
        descs = descriptions['comprehensive'] # 'comprehensive' 키가 있다고 가정
        r_text = descs['R'][r_idx]
        g_text = descs['G'][g_idx]
        b_text = descs['B'][b_idx]
    except Exception as e:
        r_text = g_text = b_text = f"상세 설명을 불러오는 중 오류가 발생했습니다. (descriptions.json 구조 확인 필요: {e})"

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
    
    # [수정] 다운로드 버튼과 다시하기 버튼을 컬럼으로 분리
    btn_cols = st.columns([1, 1])
    with btn_cols[0]:
        st.download_button(
            label="📥 종합 결과 이미지 저장하기", 
            data=image_buf, 
            file_name="RGB_personality_result.png", 
            mime="image/png",
            use_container_width=True # 버튼을 꽉 채움
        )
    with btn_cols[1]:
        if st.button("다시 검사하기", use_container_width=True):
            st.session_state.clear()
            st.session_state['stage'] = 'intro' # [수정] 초기 화면으로 이동
            st.rerun()
