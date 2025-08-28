import streamlit as st
import json
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
import io
from PIL import Image, ImageDraw, ImageFont
import random

# --- CSS 스타일 ---
st.markdown("""
<style>
/* 질문 텍스트 박스 */
.question-box {
    min-height: 100px;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 1rem;
    border-radius: 10px;
    background-color: #f0f2f6;
    margin-bottom: 1rem;
}
.question-box h2 {
    text-align: center;
    font-size: 1.7rem;
    margin: 0;
}

/* 버튼들을 감싸는 Streamlit의 columns 컨테이너 자체를 중앙 정렬 */
div[data-testid="stHorizontalBlock"] {
    justify-content: center;
}

/* 개별 버튼 스타일 */
div[data-testid="stButton"] > button {
    width: 70px;
    height: 70px;
    font-size: 1.2rem;
    font-weight: bold;
    border: 1px solid #ccc;
    border-radius: 0; /* 기본적으로 모든 버튼은 직각 */
    border-left-width: 0; /* 왼쪽 테두리는 기본적으로 제거 (첫번째 버튼 제외) */
    margin: 0;
}

/* 첫 번째 버튼에만 특별한 스타일 적용 */
div[data-testid="stHorizontalBlock"] > div:first-child div[data-testid="stButton"] > button {
    border-top-left-radius: 8px;
    border-bottom-left-radius: 8px;
    border-left-width: 1px; /* 첫 번째 버튼에만 왼쪽 테두리 표시 */
}

/* 마지막 버튼에만 특별한 스타일 적용 */
div[data-testid="stHorizontalBlock"] > div:last-child div[data-testid="stButton"] > button {
    border-top-right-radius: 8px;
    border-bottom-right-radius: 8px;
}

div[data-testid="stButton"] > button:hover {
    border-color: #457B9D;
    color: #457B9D;
    background-color: #f0f2f6;
}

div[data-testid="stDownloadButton"] > button {
    width: 100%;
    height: 55px;
    font-size: 1.2rem;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)


# --- 폰트 경로 설정 ---
font_path = os.path.abspath('rgb-test/NanumGothic.ttf')
if os.path.exists(font_path):
    fm.fontManager.addfont(font_path)
    font_name = fm.FontProperties(fname=font_path).get_name()
    plt.rc('font', family=font_name)
    plt.rcParams['axes.unicode_minus'] = False
else:
    st.warning(f"한글 폰트 파일('{font_path}')을 찾을 수 없습니다. 그래프/이미지의 한글이 깨질 수 있습니다.")

# --- 다차원 결과용 이미지 생성 함수 ---
def generate_result_image(results, descriptions, font_path):
    img_width, img_height = 900, 2200
    img = Image.new("RGB", (img_width, img_height), color="#FDFDFD")
    draw = ImageDraw.Draw(img)

    try:
        title_font = ImageFont.truetype(font_path, 40)
        world_font = ImageFont.truetype(font_path, 32)
        text_font_bold = ImageFont.truetype(font_path, 20)
        text_font = ImageFont.truetype(font_path, 16)
    except IOError:
        title_font, world_font, text_font_bold, text_font = [ImageFont.load_default() for _ in range(4)]

    draw.text((img_width / 2, 60), "퍼스널컬러 심리검사 결과", font=title_font, fill="black", anchor="mm")

    y_cursor = 150

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
                draw.text((80, current_y), line, font=text_font, fill="#333333")
                current_y += text_font.size + 6
            current_y += 10
        return current_y

    for world_key, world_data in results.items():
        draw.text((50, y_cursor), world_data['title'], font=world_font, fill="#222222")
        y_cursor += 60

        draw.rectangle([80, y_cursor, 400, y_cursor + 120], fill=world_data['hex'], outline="gray", width=2)
        draw.text((240, y_cursor + 140), f"{world_data['hex']}", font=text_font_bold, fill="black", anchor="mm")

        bar_x_start = 450
        bar_y_start = y_cursor
        draw.text((bar_x_start, bar_y_start), f"진취형(R): {world_data['percentages']['R']}%", font=text_font, fill="black")
        draw.rectangle([bar_x_start, bar_y_start + 25, bar_x_start + (world_data['percentages']['R'] * 3.5), bar_y_start + 40], fill='#E63946')
        draw.text((bar_x_start, bar_y_start + 50), f"중재형(G): {world_data['percentages']['G']}%", font=text_font, fill="black")
        draw.rectangle([bar_x_start, bar_y_start + 75, bar_x_start + (world_data['percentages']['G'] * 3.5), bar_y_start + 90], fill='#7FB069')
        draw.text((bar_x_start, bar_y_start + 100), f"신중형(B): {world_data['percentages']['B']}%", font=text_font, fill="black")
        draw.rectangle([bar_x_start, bar_y_start + 125, bar_x_start + (world_data['percentages']['B'] * 3.5), bar_y_start + 140], fill='#457B9D')
        
        y_cursor += 180

        indices = world_data['indices']
        y_cursor = draw_multiline_text_by_bullet(descriptions['R'][indices['R']], y_cursor, img_width - 120)
        y_cursor = draw_multiline_text_by_bullet(descriptions['G'][indices['G']], y_cursor, img_width - 120)
        y_cursor = draw_multiline_text_by_bullet(descriptions['B'][indices['B']], y_cursor, img_width - 120)
        
        y_cursor += 30

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


# --- 데이터 로드 함수 ---
@st.cache_data
def load_data(file_name):
    try:
        file_path = os.path.join('rgb-test', file_name)
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"`rgb-test/{file_name}` 파일을 찾을 수 없습니다. 폴더 경로를 확인해주세요.")
        return None

# --- 질문리스트 균형 맞추기 ---
@st.cache_data
def get_balanced_questions(all_questions):
    if not all_questions: return []
    initial_question_list = all_questions.get('questions', [])
    typed_questions = { f"{main}{sub}{world}" : [] for main in "RGB" for sub in "PS" for world in "ias" }
    for q in initial_question_list:
        if q['type'] in typed_questions: typed_questions[q['type']].append(q)

    balanced_list = []
    for world in "ias":
        r_count = min(len(typed_questions[f'RP{world}']), len(typed_questions[f'RS{world}']))
        g_count = min(len(typed_questions[f'GP{world}']), len(typed_questions[f'GS{world}']))
        b_count = min(len(typed_questions[f'BP{world}']), len(typed_questions[f'BS{world}']))

        balanced_list.extend(typed_questions[f'RP{world}'][:r_count] + typed_questions[f'RS{world}'][:r_count])
        balanced_list.extend(typed_questions[f'GP{world}'][:g_count] + typed_questions[f'GS{world}'][:g_count])
        balanced_list.extend(typed_questions[f'BP{world}'][:b_count] + typed_questions[f'BS{world}'][:b_count])
    
    random.shuffle(balanced_list)
    for i, q in enumerate(balanced_list): q['id'] = i + 1
    return balanced_list

# --- 데이터 로드 ---
description_blocks = load_data('descriptions.json')
all_questions = load_data('questions.json')
question_list = get_balanced_questions(all_questions)

st.set_page_config(page_title="RGB 성격 심리 검사", layout="wide")

# --- [수정] SyntaxError를 해결한 함수 ---
def get_description_index(percentage):
    if percentage <= 10:
        return 0
    elif percentage <= 20:
        return 1
    elif percentage <= 30:
        return 2
    elif percentage <= 40:
        return 3
    elif percentage <= 50:
        return 4
    elif percentage <= 60:
        return 5
    elif percentage <= 70:
        return 6
    elif percentage <= 80:
        return 7
    elif percentage <= 90:
        return 8
    else:
        return 9

# --- 앱 실행 로직 ---
st.title("🧠 퍼스널컬러 심리검사")
st.markdown("---")

if question_list and description_blocks:
    total_questions = len(question_list)
    if 'responses' not in st.session_state: st.session_state.responses = {}
    
    next_question = next((q for q in question_list if q['id'] not in st.session_state.responses), None)

    progress = len(st.session_state.responses) / total_questions if total_questions > 0 else 0
    st.progress(progress, text=f"진행률: {len(st.session_state.responses)} / {total_questions}")

    if next_question:
        q = next_question
        st.markdown(f"<div class='question-box'><h2>Q{q['id']}. {q['text']}</h2></div>", unsafe_allow_html=True)
        
        label_cols = st.columns([1, 5, 1])
        with label_cols[0]: st.markdown("<p style='text-align: left; font-weight: bold; color: #555;'>⟵ 그렇지 않다</p>", unsafe_allow_html=True)
        with label_cols[2]: st.markdown("<p style='text-align: right; font-weight: bold; color: #555;'>그렇다 ⟶</p>", unsafe_allow_html=True)
        
        cols = st.columns(9)
        for i, val in enumerate(range(-4, 5)):
            with cols[i]:
                if st.button(str(val), key=f"q{q['id']}_val{val}"):
                    st.session_state.responses[q['id']] = val
                    st.rerun()
    
    elif len(st.session_state.responses) == total_questions and total_questions > 0:
        st.balloons()
        st.success("검사가 완료되었습니다! 아래에서 결과를 확인하세요. 🎉")
        st.markdown("---")
        
        scores = { f"{main}{sub}{world}" : 0 for main in "RGB" for sub in "PS" for world in "ias" }
        question_map = {q['id']: q for q in question_list}
        for q_id, value in st.session_state.responses.items():
            q_type = question_map[q_id]['type']
            scores[q_type] += value

        results = {}
        worlds = {'i': '내면 세계', 'a': '주변 세계', 's': '사회'}
        
        for world_code, world_title in worlds.items():
            final_scores = {
                'R': 128 + scores[f'RP{world_code}'] - scores[f'RS{world_code}'],
                'G': 128 + scores[f'GP{world_code}'] - scores[f'GS{world_code}'],
                'B': 128 + scores[f'BP{world_code}'] - scores[f'BS{world_code}']
            }
            absolute_scores = {k: max(v, 0) for k, v in final_scores.items()}
            percentages = {k: round((v / 256) * 100, 1) for k, v in absolute_scores.items()}
            hex_color = '#{:02X}{:02X}{:02X}'.format(min(absolute_scores.get('R', 0), 255), min(absolute_scores.get('G', 0), 255), min(absolute_scores.get('B', 0), 255))
            indices = { k: get_description_index(p) for k, p in percentages.items() }

            results[world_code] = {
                'title': world_title, 'percentages': percentages,
                'hex': hex_color, 'indices': indices
            }
        
        for world_code, world_data in results.items():
            st.header(f"📈 당신의 {world_data['title']} 분석 결과")
            col1, col2 = st.columns([1, 1])
            with col1:
                st.markdown("### 🎨 고유 성격 색상")
                st.markdown(f"<div style='width: 100%; height: 200px; background-color: {world_data['hex']}; border: 2px solid #ccc; border-radius: 12px;'></div>", unsafe_allow_html=True)
                st.markdown(f"<p style='text-align: center; font-size: 24px; font-weight: bold; margin-top: 10px;'>{world_data['hex']}</p>", unsafe_allow_html=True)
            with col2:
                fig, ax = plt.subplots(figsize=(10, 5))
                st.markdown("### ✨ 유형별 강도 시각화")
                y_labels = ["진취형 (R)", "중재형 (G)", "신중형 (B)"]
                values = [world_data['percentages'][k] for k in "RGB"]
                colors = ['#E63946', '#7FB069', '#457B9D']
                bars = ax.barh(y_labels, values, color=colors, height=0.6)
                ax.set_xlim(0, 115)
                ax.spines[['top', 'right', 'left', 'bottom']].set_visible(False)
                ax.xaxis.set_ticks_position('none'); ax.yaxis.set_ticks_position('none')
                ax.set_xticklabels([]); ax.set_yticklabels(y_labels, fontsize=14)
                for bar in bars:
                    width = bar.get_width()
                    ax.text(width + 2, bar.get_y() + bar.get_height() / 2, f'{width}%', ha='left', va='center', fontsize=12)
                st.pyplot(fig)
            
            st.markdown("#### 📜 상세 성격 분석")
            indices = world_data['indices']
            st.info(f"**🔴 진취형(R):** {description_blocks['R'][indices['R']]}")
            st.success(f"**🟢 중재형(G):** {description_blocks['G'][indices['G']]}")
            st.warning(f"**🔵 신중형(B):** {description_blocks['B'][indices['B']]}")
            st.markdown("---")

        image_buffer = generate_result_image(results, description_blocks, font_path)
        st.download_button(label="📥 종합 결과 이미지 저장하기", data=image_buffer, file_name="RGB_personality_result.png", mime="image/png")
        
        if st.button("다시 검사하기"):
            st.session_state.clear()
            st.rerun()
