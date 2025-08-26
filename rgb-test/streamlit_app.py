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
        flex-direction: column;
        text-align: center; /* 질문 텍스트 중앙 정렬 */
    }
    .question-box h2 {
        margin: 0; /* h2 기본 마진 제거 */
        font-size: 1.7rem;
    }

    /* 버튼 그룹 전체를 감싸는 컨테이너 */
    .button-group {
        display: flex;
        justify-content: center; /* 중앙 정렬 */
        margin-top: 15px;
        margin-bottom: 20px;
        /* 그룹 전체에 둥근 모서리 적용 (개별 버튼은 직각 유지) */
        border-radius: 8px; 
        overflow: hidden; /* 자식 요소가 부모의 둥근 모서리를 침범하지 않도록 */
        border: 1px solid #ccc; /* 그룹 전체의 테두리 (버튼 테두리와 일치시키거나 없앨 수 있음) */
        width: fit-content; /* 내용물에 맞춰 너비 조정 */
        margin-left: auto;
        margin-right: auto;
    }

    /* 개별 Streamlit 버튼 스타일 */
    div[data-testid*="stButton"] > button { /* 'stButton'으로 시작하는 모든 testid에 적용 */
        width: 70px;  
        height: 70px;
        font-size: 1.2rem;
        font-weight: bold;
        border: none; /* 개별 버튼의 테두리 제거. 그룹 테두리로 대체 */
        border-radius: 0; /* 각 버튼을 직사각형으로 유지 */
        margin: 0; /* 버튼 간 마진 제거 */
        /* 버튼 사이에 구분선 추가 (선택 사항) */
        border-right: 1px solid #ddd; 
    }
    /* 마지막 버튼의 오른쪽 구분선 제거 */
    div[data-testid*="stButton"]:last-of-type > button {
        border-right: none;
    }

    /* 호버 시 스타일 */
    div[data-testid*="stButton"] > button:hover {
        background-color: #e0e0e0; /* 호버 시 배경색 변경 */
        color: #457B9D;
        cursor: pointer;
    }

    /* 다운로드 버튼 스타일 (기존 유지) */
    div[data-testid="stDownloadButton"] > button {
        width: 100%; 
        height: 55px; 
        font-size: 1.2rem; 
        font-weight: bold;
        border-radius: 8px;
        border: 2px solid #e0e0e0;
    }

    /* 기타 라벨 정렬 */
    .st-emotion-cache-1pxazr7 { /* Streamlit 컬럼 내부의 p 태그 스타일, Streamlit 버전에 따라 변경될 수 있음 */
        display: flex;
        justify-content: space-between;
        width: 100%;
    }
    .st-emotion-cache-1pxazr7 p {
        margin-top: 0;
        margin-bottom: 0;
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

# --- [핵심 수정] 3개의 세계 결과를 모두 담는 이미지 생성 함수 ---
def generate_result_image(results, descriptions, font_path):
    img_width, img_height = 900, 2000 # 이미지 크기 확장
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
    
    # 3개의 세계(내면, 주변, 사회)를 순회하며 이미지에 그리기
    for world_key, world_data in results.items():
        draw.text((50, y_cursor), world_data['title'], font=world_font, fill="#222222")
        y_cursor += 60

        # 색상 상자
        draw.rectangle([80, y_cursor, 400, y_cursor + 120], fill=world_data['hex'], outline="gray", width=2)
        draw.text((240, y_cursor + 140), f"{world_data['hex']}", font=text_font_bold, fill="black", anchor="mm")

        # 막대 그래프
        bar_x_start = 450
        bar_y_start = y_cursor
        draw.text((bar_x_start, bar_y_start), f"R: {world_data['percentages']['R']}%", font=text_font, fill="black")
        draw.rectangle([bar_x_start, bar_y_start + 25, bar_x_start + (world_data['percentages']['R'] * 3.5), bar_y_start + 40], fill='#E63946')
        
        draw.text((bar_x_start, bar_y_start + 50), f"G: {world_data['percentages']['G']}%", font=text_font, fill="black")
        draw.rectangle([bar_x_start, bar_y_start + 75, bar_x_start + (world_data['percentages']['G'] * 3.5), bar_y_start + 90], fill='#7FB069')

        draw.text((bar_x_start, bar_y_start + 100), f"B: {world_data['percentages']['B']}%", font=text_font, fill="black")
        draw.rectangle([bar_x_start, bar_y_start + 125, bar_x_start + (world_data['percentages']['B'] * 3.5), bar_y_start + 140], fill='#457B9D')
        
        y_cursor += 180
        
        # 상세 설명
        # 각 세계별 설명 (R, G, B 모두 포함하도록 수정)
        
        # R 설명
        draw.text((50, y_cursor), "🔴 진취형(R)에 대하여", font=text_font_bold, fill="#E63946")
        y_cursor += text_font_bold.size + 10
        current_desc_y = y_cursor
        
        bullet_points_R = [p.strip() for p in descriptions['R'][world_data['indices']['R']].split('•') if p.strip()]
        for point in bullet_points_R:
            line_with_bullet = "• " + point
            lines = []
            words = line_with_bullet.split(' ')
            line_buffer = ""
            for word in words:
                if draw.textlength(line_buffer + word, font=text_font) < img_width - 120:
                    line_buffer += word + " "
                else:
                    lines.append(line_buffer)
                    line_buffer = word + " "
            lines.append(line_buffer)
            for line in lines:
                draw.text((60, current_desc_y), line, font=text_font, fill="#333333")
                current_desc_y += text_font.size + 6
            current_desc_y += 5
        y_cursor = current_desc_y + 10

        # G 설명
        draw.text((50, y_cursor), "🟢 중재형(G)에 대하여", font=text_font_bold, fill="#7FB069")
        y_cursor += text_font_bold.size + 10
        current_desc_y = y_cursor
        
        bullet_points_G = [p.strip() for p in descriptions['G'][world_data['indices']['G']].split('•') if p.strip()]
        for point in bullet_points_G:
            line_with_bullet = "• " + point
            lines = []
            words = line_with_bullet.split(' ')
            line_buffer = ""
            for word in words:
                if draw.textlength(line_buffer + word, font=text_font) < img_width - 120:
                    line_buffer += word + " "
                else:
                    lines.append(line_buffer)
                    line_buffer = word + " "
            lines.append(line_buffer)
            for line in lines:
                draw.text((60, current_desc_y), line, font=text_font, fill="#333333")
                current_desc_y += text_font.size + 6
            current_desc_y += 5
        y_cursor = current_desc_y + 10

        # B 설명
        draw.text((50, y_cursor), "🔵 신중형(B)에 대하여", font=text_font_bold, fill="#457B9D")
        y_cursor += text_font_bold.size + 10
        current_desc_y = y_cursor

        bullet_points_B = [p.strip() for p in descriptions['B'][world_data['indices']['B']].split('•') if p.strip()]
        for point in bullet_points_B:
            line_with_bullet = "• " + point
            lines = []
            words = line_with_bullet.split(' ')
            line_buffer = ""
            for word in words:
                if draw.textlength(line_buffer + word, font=text_font) < img_width - 120:
                    line_buffer += word + " "
                else:
                    lines.append(line_buffer)
                    line_buffer = word + " "
            lines.append(line_buffer)
            for line in lines:
                draw.text((60, current_desc_y), line, font=text_font, fill="#333333")
                current_desc_y += text_font.size + 6
            current_desc_y += 5
        y_cursor = current_desc_y + 50 # 각 세계 섹션 사이의 여백

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
def get_balanced_questions(all_questions):
    if not all_questions:
        return []
        
    initial_question_list = all_questions.get('questions', [])
    
    # 세분화된 18개 유형을 모두 담을 딕셔너리
    typed_questions = { f"{main}{sub}{world}" : [] for main in "RGB" for sub in "PS" for world in "ias" }
    
    for q in initial_question_list:
        if q['type'] in typed_questions:
            typed_questions[q['type']].append(q)

    balanced_list = []
    # 각 세계(i, a, s)별로 문항 수 균형 맞추기
    for world in "ias":
        r_count = min(len(typed_questions[f'RP{world}']), len(typed_questions[f'RS{world}']))
        g_count = min(len(typed_questions[f'GP{world}']), len(typed_questions[f'GS{world}']))
        b_count = min(len(typed_questions[f'BP{world}']), len(typed_questions[f'BS{world}']))

        balanced_list.extend(typed_questions[f'RP{world}'][:r_count] + typed_questions[f'RS{world}'][:r_count])
        balanced_list.extend(typed_questions[f'GP{world}'][:g_count] + typed_questions[f'GS{world}'][:g_count])
        balanced_list.extend(typed_questions[f'BP{world}'][:b_count] + typed_questions[f'BS{world}'][:b_count])
    
    random.shuffle(balanced_list)
    for i, q in enumerate(balanced_list):
        q['id'] = i + 1
        
    return balanced_list

# --- 데이터 로드 ---
description_blocks = load_data('descriptions.json')
all_questions = load_data('questions.json')
question_list = get_balanced_questions(all_questions)

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

# --- 앱 실행 로직 ---
st.title("🧠 퍼스널컬러 심리검사")
st.markdown("---")

if question_list and description_blocks:
    total_questions = len(question_list)

    if 'responses' not in st.session_state:
        st.session_state.responses = {}
    
    next_question = next((q for q in question_list if q['id'] not in st.session_state.responses), None)

    progress = len(st.session_state.responses) / total_questions if total_questions > 0 else 0
    st.progress(progress, text=f"진행률: {len(st.session_state.responses)} / {total_questions}")

    if next_question:
        q = next_question
        st.markdown(f"<div class='question-box'><h2>Q{q['id']}. {q['text']}</h2></div>", unsafe_allow_html=True)
        
        # '그렇지 않다'와 '그렇다' 텍스트를 버튼 그룹 위아래로 배치
        st.markdown(
            "<div style='display: flex; justify-content: space-between; width: fit-content; margin: 0 auto; padding: 0 10px;'>"
            "<p style='text-align: left; font-weight: bold; color: #555; margin-right: 20px;'>⟵ 그렇지 않다</p>"
            "<p style='text-align: right; font-weight: bold; color: #555; margin-left: 20px;'>그렇다 ⟶</p>"
            "</div>", unsafe_allow_html=True
        )

        st.markdown('<div class="button-group">', unsafe_allow_html=True)
        cols = st.columns(9) # Streamlit의 컬럼 기능을 활용하여 버튼을 가로로 배열
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
        
        # --- [핵심 수정] 18개 유형에 대한 점수 집계 ---
        scores = { f"{main}{sub}{world}" : 0 for main in "RGB" for sub in "PS" for world in "ias" }
        question_map = {q['id']: q for q in question_list}
        for q_id, value in st.session_state.responses.items():
            q_type = question_map[q_id]['type']
            scores[q_type] += value

        # --- [핵심 수정] 각 세계별로 점수, 퍼센트, 색상 계산 ---
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
                'title': world_title,
                'percentages': percentages,
                'hex': hex_color,
                'indices': indices
            }
        
        # --- [핵심 수정] 3개의 세계 결과를 화면에 각각 표시 ---
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
                # (그래프 세부 설정은 기존과 유사)
                ax.spines[['top', 'right', 'left', 'bottom']].set_visible(False)
                ax.xaxis.set_ticks_position('none'); ax.yaxis.set_ticks_position('none')
                ax.set_xticklabels([]); ax.set_yticklabels(y_labels, fontsize=14)
                for bar in bars:
                    width = bar.get_width()
                    ax.text(width + 2, bar.get_y() + bar.get_height() / 2, f'{width}%', ha='left', va='center', fontsize=12)
                st.pyplot(fig)
            
            st.markdown("#### 📜 상세 성격 분석")
            st.info(f"**🔴 진취형(R):** {description_blocks['R'][world_data['indices']['R']]}")
            st.success(f"**🟢 중재형(G):** {description_blocks['G'][world_data['indices']['G']]}")
            st.warning(f"**🔵 신중형(B):** {description_blocks['B'][world_data['indices']['B']]}")
            st.markdown("---")

        # 다운로드 버튼 (새로운 이미지 생성 함수 호출)
        image_buffer = generate_result_image(results, description_blocks, font_path)
        st.download_button(label="📥 종합 결과 이미지 저장하기", data=image_buffer, file_name="RGB_personality_result.png", mime="image/png")
        
        if st.button("다시 검사하기"):
            st.session_state.clear()
            st.rerun()
