import streamlit as st
import json
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
import io
from PIL import Image, ImageDraw, ImageFont
import random

# --- 스타일 CSS ---
st.markdown(
    """
    <style>
    .question-box { 
        min-height: 100px; 
        display: flex; 
        align-items: center; 
        justify-content: center; 
        padding: 1rem; 
        border-radius: 10px; 
        background-color: #f0f2f6; 
        margin-bottom: 1rem; 
        flex-direction: column;
        font-size: 1rem;
    }
    .button-group {
        display: flex;
        justify-content: center;   /* 중앙 정렬 */
        margin-top: 15px;
        margin-bottom: 20px;
    }
    div[data-testid="stButton"] > button {
        width: 70px; 
        height: 70px;
        font-size: 1.2rem;
        font-weight: bold;
        border: 1px solid #ccc;
        border-radius: 0;   /* 각 버튼을 직사각형으로 */
        margin: 0;
    }
    div[data-testid="stButton"] > button:hover {
        border-color: #457B9D;
        color: #457B9D;
    }
    </style>
    """, 
    unsafe_allow_html=True
)

# --- 폰트 경로 설정 ---
font_path = os.path.abspath('rgb-test/NanumGothic.ttf')
if os.path.exists(font_path):
    fm.fontManager.addfont(font_path)
    font_name = fm.FontProperties(fname=font_path).get_name()
    plt.rc('font', family=font_name)
    plt.rcParams['axes.unicode_minus'] = False
else:
    st.warning(f"한글 폰트 파일('{font_path}')을 찾을 수 없습니다. 그래프/이미지의 한글이 깨질 수 있습니다.")

# --- 종합 결과 이미지 생성 함수 ---
def generate_result_image(hex_color, percentages, descriptions, font_path):
    img_width, img_height = 800, 1600
    img = Image.new("RGB", (img_width, img_height), color="#FDFDFD")
    draw = ImageDraw.Draw(img)
    try:
        title_font = ImageFont.truetype(font_path, 36)
        text_font_bold = ImageFont.truetype(font_path, 22)
        text_font = ImageFont.truetype(font_path, 18)
    except IOError:
        title_font, text_font_bold, text_font = ImageFont.load_default(), ImageFont.load_default(), ImageFont.load_default()
    
    draw.text((400, 50), "퍼스널컬러 심리검사 결과", font=title_font, fill="black", anchor="mm")
    draw.rectangle([100, 100, 700, 250], fill=hex_color, outline="gray", width=2)
    draw.text((400, 280), f"나의 고유 성격 색상: {hex_color}", font=text_font_bold, fill="black", anchor="mm")
    
    y_start_bars = 350
    draw.text((100, y_start_bars), f"진취형(R): {percentages['R']}%", font=text_font_bold, fill="black")
    draw.rectangle([100, y_start_bars + 35, 100 + (percentages['R'] * 6), y_start_bars + 55], fill='#E63946')
    draw.text((100, y_start_bars + 70), f"중재형(G): {percentages['G']}%", font=text_font_bold, fill="black")
    draw.rectangle([100, y_start_bars + 105, 100 + (percentages['G'] * 6), y_start_bars + 125], fill='#7FB069')
    draw.text((100, y_start_bars + 140), f"신중형(B): {percentages['B']}%", font=text_font_bold, fill="black")
    draw.rectangle([100, y_start_bars + 175, 100 + (percentages['B'] * 6), y_start_bars + 200], fill='#457B9D')
    
    y_start_desc = 580
    draw.text((50, y_start_desc), "상세 성격 분석", font=title_font, fill="black")

    def draw_multiline_text_by_bullet(text, y_start, width_limit):
        bullet_points = [p.strip() for p in text.split('•') if p.strip()]
        current_y = y_start
        for point in bullet_points:
            line_with_bullet = "• " + point
            lines = []
            words = line_with_bullet.split(' ')
            line_buffer = ""
            for word in words:
                if draw.textlength(line_buffer + word, font=text_font) < width_limit:
                    line_buffer += word + " "
                else:
                    lines.append(line_buffer)
                    line_buffer = word + " "
            lines.append(line_buffer)
            for line in lines:
                draw.text((60, current_y), line, font=text_font, fill="#333333")
                current_y += text_font.size + 6
            current_y += 10
        return current_y

    current_y = y_start_desc + 70
    draw.text((60, current_y), "진취형(R)에 대하여", font=text_font_bold, fill="#E63946")
    current_y = draw_multiline_text_by_bullet(descriptions['R'], current_y + 40, img_width - 120)
    draw.text((60, current_y), "중재형(G)에 대하여", font=text_font_bold, fill="#7FB069")
    current_y = draw_multiline_text_by_bullet(descriptions['G'], current_y + 50, img_width - 120)
    draw.text((60, current_y), "신중형(B)에 대하여", font=text_font_bold, fill="#457B9D")
    draw_multiline_text_by_bullet(descriptions['B'], current_y + 50, img_width - 120)

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()

# --- descriptions 로드 ---
@st.cache_data
def load_descriptions():
    try:
        file_path = os.path.join('rgb-test', 'descriptions.json')
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("`rgb-test/descriptions.json` 파일을 찾을 수 없습니다. 폴더 경로를 확인해주세요.")
        return None

description_blocks = load_descriptions()

st.set_page_config(page_title="RGB 성격 심리 검사", layout="wide")

def get_description_index(percentage):
    if percentage <= 10: return 0
    if percentage <= 20: return 1
    if percentage <= 30: return 2
    if percentage <= 40: return 3
    if percentage <= 50: return 4
    if percentage <= 60: return 5
    if percentage <= 70: return 6
    if percentage <= 80: return 7
    if percentage <= 90: return 8
    return 9

@st.cache_data
def load_and_balance_questions():
    try:
        file_path = os.path.join('rgb-test', 'questions.json')
        with open(file_path, 'r', encoding='utf-8') as f:
            questions_data = json.load(f)
    except FileNotFoundError:
        st.error("`rgb-test/questions.json` 파일을 찾을 수 없습니다. 폴더 경로를 확인해주세요.")
        return None

    initial_question_list = []
    if isinstance(questions_data, dict) and 'questions' in questions_data:
        initial_question_list = questions_data['questions']
    elif isinstance(questions_data, list):
        initial_question_list = questions_data
    else:
        st.error("questions.json 파일의 형식이 올바르지 않습니다.")
        return None

    typed_questions = {'RP': [], 'RS': [], 'GP': [], 'GS': [], 'BP': [], 'BS': []}
    for q in initial_question_list:
        if q['type'] in typed_questions:
            typed_questions[q['type']].append(q)

    r_count = min(len(typed_questions['RP']), len(typed_questions['RS']))
    g_count = min(len(typed_questions['GP']), len(typed_questions['GS']))
    b_count = min(len(typed_questions['BP']), len(typed_questions['BS']))

    balanced_list = (
        typed_questions['RP'][:r_count] + typed_questions['RS'][:r_count] +
        typed_questions['GP'][:g_count] + typed_questions['GS'][:g_count] +
        typed_questions['BP'][:b_count] + typed_questions['BS'][:b_count]
    )
    
    random.shuffle(balanced_list)
    
    for i, q in enumerate(balanced_list):
        q['id'] = i + 1
        
    return balanced_list

# --- 앱 실행 로직 ---
question_list = load_and_balance_questions()

st.title("🧠 퍼스널컬러 심리검사")
st.markdown("---")

if question_list and description_blocks:
    total_questions = len(question_list)

    if 'responses' not in st.session_state:
        st.session_state.responses = {}
    
    next_question = None
    for q in question_list:
        if q['id'] not in st.session_state.responses:
            next_question = q
            break

    progress = len(st.session_state.responses) / total_questions if total_questions > 0 else 0
    st.progress(progress, text=f"진행률: {len(st.session_state.responses)} / {total_questions}")

    if next_question:
        q = next_question
        st.markdown(f"<div class='question-box'><h2>Q{q['id']}. {q['text']}</h2></div>", unsafe_allow_html=True)
        
        label_cols = st.columns([1, 5, 1])
        with label_cols[0]:
            st.markdown("<p style='text-align: left; font-weight: bold; color: #555;'>⟵ 그렇지 않다</p>", unsafe_allow_html=True)
        with label_cols[2]:
            st.markdown("<p style='text-align: right; font-weight: bold; color: #555;'>그렇다 ⟶</p>", unsafe_allow_html=True)

        # --- [수정된 버튼 영역] ---
        st.markdown('<div class="button-group">', unsafe_allow_html=True)
        cols = st.columns(9)
        for i, val in enumerate(range(-4, 5)):
            with cols[i]:
                if st.button(str(val), key=f"q{q['id']}_val{val}"):
                    st.session_state.responses[q['id']] = val
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    elif len(st.session_state.responses) == total_questions and total_questions > 0:
        st.balloons()
        st.success("검사가 완료되었습니다! 아래에서 결과를 확인하세요. 🎉")
        st.markdown("---")
        
        scores = {'RP': 0, 'RS': 0, 'GP': 0, 'GS': 0, 'BP': 0, 'BS': 0}
        
        question_map = {q['id']: q for q in question_list}
        for q_id, value in st.session_state.responses.items():
            q_type = question_map[q_id]['type']
            scores[q_type] += value

        final_scores = {
            'R': 128 + scores['RP'] - scores['RS'],
            'G': 128 + scores['GP'] - scores['GS'],
            'B': 128 + scores['BP'] - scores['BS']
        }
        
        absolute_scores = {k: max(v, 0) for k, v in final_scores.items()}
        percentages = {k: round((v / 256) * 100, 1) for k, v in absolute_scores.items()}
        hex_color = '#{:02X}{:02X}{:02X}'.format(min(absolute_scores.get('R', 0), 255), min(absolute_scores.get('G', 0), 255), min(absolute_scores.get('B', 0), 255))

        st.header("📈 당신의 성격 분석 결과")
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("### 🎨 당신의 고유 성격 색상")
            st.markdown(f"<div style='width: 100%; height: 200px; background-color: {hex_color}; border: 2px solid #ccc; border-radius: 12px;'></div>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align: center; font-size: 24px; font-weight: bold; margin-top: 10px;'>{hex_color}</p>", unsafe_allow_html=True)
            
        with col2:
            fig, ax = plt.subplots(figsize=(10, 5))
            st.markdown("### ✨ 유형별 강도 시각화")
            y_labels, values = ["진취형 (R)", "중재형 (G)", "신중형 (B)"], [percentages.get('R', 0), percentages.get('G', 0), percentages.get('B', 0)]
            colors = ['#E63946', '#7FB069', '#457B9D']
            bars = ax.barh(y_labels, values, color=colors, height=0.6)
            ax.spines[['top', 'right', 'left', 'bottom']].set_visible(False)
            ax.xaxis.set_ticks_position('none'); ax.yaxis.set_ticks_position('none')
            ax.set_xticklabels([]); ax.set_yticklabels(y_labels, fontsize=14); ax.set_xlim(0, 115)
            for bar in bars:
                width = bar.get_width()
                ax.text(width + 2, bar.get_y() + bar.get_height() / 2, f'{width}%', ha='left', va='center', fontsize=12)
            st.pyplot(fig)
        
        st.markdown("---")

        r_index = get_description_index(percentages.get('R', 0))
        g_index = get_description_index(percentages.get('G', 0))
        b_index = get_description_index(percentages.get('B', 0))

        description_texts = {
            'R': description_blocks['R'][r_index],
            'G': description_blocks['G'][g_index],
            'B': description_blocks['B'][b_index],
        }

        image_buffer = generate_result_image(hex_color, percentages, description_texts, font_path)
        
        st.download_button(label="📥 종합 결과 이미지 저장하기", data=image_buffer, file_name="RGB_personality_result.png", mime="image/png")
        
        st.header("📜 상세 성격 분석")
        st.markdown("### 🔴 진취형(R)에 대하여")
        st.info(description_blocks['R'][r_index])
        st.markdown("### 🟢 중재형(G)에 대하여")
        st.success(description_blocks['G'][g_index])
        st.markdown("### 🔵 신중형(B)에 대하여")
        st.warning(description_blocks['B'][b_index])

        if st.button("다시 검사하기"):
            st.session_state.clear()
            st.rerun()



