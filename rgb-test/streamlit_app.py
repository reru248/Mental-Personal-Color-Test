import streamlit as st
import json
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
import io
from PIL import Image, ImageDraw, ImageFont
import random
import math

# --- CSS 스타일 ---
st.markdown("""
<style>
.question-box { min-height: 100px; display: flex; align-items: center; justify-content: center; padding: 1rem; border-radius: 10px; background-color: #f0f2f6; margin-bottom: 1rem; }
.question-box h2 { text-align: center; font-size: 1.7rem; margin: 0; }
.intro-box { text-align: center; padding: 2rem; }
.intro-box h1 { font-size: 2.5rem; }
.intro-box h2 { font-size: 1.5rem; color: #555; margin-bottom: 2rem; }
div[data-testid="stButton"] > button { width: 120px; height: 55px; font-size: 1.2rem; font-weight: bold; border-radius: 8px; border: 2px solid #e0e0e0; }
div[data-testid="stButton"] > button:hover { border-color: #457B9D; color: #457B9D; }
div[data-testid="stDownloadButton"] > button { width: 250px; height: 55px; font-size: 1.2rem; font-weight: bold; }
</style>
""", unsafe_allow_html=True)


# --- 폰트 경로 설정 ---
# 스크립트 파일이 위치한 디렉토리의 절대 경로를 얻습니다.
# 이 방법은 Streamlit 앱이 어느 디렉토리에서 실행되든 항상 정확한 스크립트 디렉토리를 참조합니다.
current_dir = os.path.dirname(os.path.abspath(__file__))
# 'rgb-test' 폴더는 current_dir 바로 아래에 있다고 가정합니다.
font_path = os.path.join(current_dir, 'rgb-test', 'NanumGothic.ttf')

if os.path.exists(font_path):
    fm.fontManager.addfont(font_path)
    font_name = fm.FontProperties(fname=font_path).get_name()
    plt.rc('font', family=font_name)
    plt.rcParams['axes.unicode_minus'] = False
else:
    st.warning(f"한글 폰트 파일('{font_path}')을 찾을 수 없습니다. 그래프/이미지의 한글이 깨질 수 있습니다.")
    
# --- 종합 결과 이미지 생성 함수 (동적 높이 조절 적용) ---
def generate_result_image(comprehensive_result, font_path):
    # --- 1. 초기 설정 및 폰트 로드 ---
    img_width = 900 # 이미지 폭은 고정 (내용이 옆으로 넘치지 않도록 충분히 넓게)
    
    # 폰트 로드 시도
    try:
        title_font = ImageFont.truetype(font_path, 40)
        text_font_bold = ImageFont.truetype(font_path, 22)
        text_font = ImageFont.truetype(font_path, 18)
    except IOError:
        st.warning(f"폰트 파일 '{font_path}'을(를) 찾을 수 없습니다. 이미지 생성에 기본 폰트를 사용합니다.")
        title_font, text_font_bold, text_font = ImageFont.load_default(), ImageFont.load_default(), ImageFont.load_default()

    # --- 2. 이미지 높이 계산을 위한 첫 번째 렌더링 (가상) ---
    temp_img = Image.new("RGB", (img_width, 100), color="#FDFDFD") # 임시 이미지
    temp_draw = ImageDraw.Draw(temp_img) # 임시 draw 객체

    # 텍스트 그리기 시작 Y 좌표 (높이 계산용)
    calculated_y_for_height = 60

    # 2-1. 제목 "퍼스널컬러 심리검사 종합 결과"
    title_text = "퍼스널컬러 심리검사 종합 결과"
    title_bbox = temp_draw.textbbox((0, 0), title_text, font=title_font)
    title_height = title_bbox[3] - title_bbox[1]
    calculated_y_for_height += title_height / 2 
    calculated_y_for_height += title_height / 2 + 40 

    # 2-2. 색상 바 및 "나의 종합 성격 색상" 텍스트
    hex_color = comprehensive_result['hex']
    
    calculated_y_for_height += 10 # 여백 (사각형 위)
    calculated_y_for_height += 150 + 20 # 사각형 자체의 높이 + 사각형 아래 여백
    
    text_color_info = f"나의 종합 성격 색상: {hex_color}"
    color_info_bbox = temp_draw.textbbox((0, 0), text_color_info, font=text_font_bold)
    color_info_height = color_info_bbox[3] - color_info_bbox[1]
    calculated_y_for_height += color_info_height + 40 

    # 2-3. 퍼센티지 바 섹션
    percentages = comprehensive_result['percentages']
    
    # R 바
    calculated_y_for_height += (text_font_bold.size + 6)
    calculated_y_for_height += (20 + 25)
    
    # G 바
    calculated_y_for_height += (text_font_bold.size + 6)
    calculated_y_for_height += (20 + 25)
    
    # B 바
    calculated_y_for_height += (text_font_bold.size + 6)
    calculated_y_for_height += (20 + 25)
    
    calculated_y_for_height += 40 # 퍼센티지 바 섹션 아래 여백

    # 2-4. "상세 성격 분석" 제목
    detail_title_text = "상세 성격 분석"
    detail_title_bbox = temp_draw.textbbox((0, 0), detail_title_text, font=title_font)
    detail_title_height = detail_title_bbox[3] - detail_title_bbox[1]
    calculated_y_for_height += detail_title_height + 80 

    # 2-5. 상세 설명 (descriptions)의 높이 계산
    descriptions = comprehensive_result['descriptions']
    
    def calculate_multiline_text_block_height(text, font, width_limit, draw_obj):
        total_block_height = 0
        bullet_points = [p.strip() for p in text.split('•') if p.strip()]
        
        for point in bullet_points:
            line_with_bullet = "• " + point
            lines = []
            words = line_with_bullet.split(' ')
            line_buffer = ""
            
            available_width = width_limit - 80 

            for word in words:
                if draw_obj.textlength(line_buffer + word, font=font) < available_width:
                    line_buffer += word + " "
                else:
                    lines.append(line_buffer)
                    line_buffer = word + " "
            lines.append(line_buffer)
            
            for _ in lines:
                total_block_height += font.size + 6 
            total_block_height += 10 
        return total_block_height

    calculated_y_for_height += calculate_multiline_text_block_height(descriptions['R'], text_font, img_width, temp_draw)
    calculated_y_for_height += calculate_multiline_text_block_height(descriptions['G'], text_font, img_width, temp_draw)
    calculated_y_for_height += calculate_multiline_text_block_height(descriptions['B'], text_font, img_width, temp_draw)
    
    final_img_height = int(calculated_y_for_height) + 100 

    # --- 3. 실제 이미지 생성 및 그리기 ---
    img = Image.new("RGB", (img_width, final_img_height), color="#FDFDFD")
    draw = ImageDraw.Draw(img)

    y_cursor = 60 
    
    # 3-1. 제목 "퍼스널컬러 심리검사 종합 결과"
    draw.text((img_width / 2, y_cursor), title_text, font=title_font, fill="black", anchor="mm")
    y_cursor += title_height + 40 

    # 3-2. 색상 바 및 "나의 종합 성격 색상" 텍스트
    draw.rectangle([100, y_cursor, 800, y_cursor + 150], fill=hex_color, outline="gray", width=2)
    y_cursor += 150 + 20 

    draw.text((img_width / 2, y_cursor), text_color_info, font=text_font_bold, fill="black", anchor="mm")
    y_cursor += color_info_height + 40 

    # 3-3. 퍼센티지 바 섹션
    draw.text((100, y_cursor), f"진취형(R): {percentages['R']}%", font=text_font_bold, fill="black")
    draw.rectangle([100, y_cursor + 35, 100 + (percentages['R'] * 7), y_cursor + 55], fill='#E63946')
    y_cursor += 80 

    draw.text((100, y_cursor), f"중재형(G): {percentages['G']}%", font=text_font_bold, fill="black")
    draw.rectangle([100, y_cursor + 35, 100 + (percentages['G'] * 7), y_cursor + 55], fill='#7FB069')
    y_cursor += 80 

    draw.text((100, y_cursor), f"신중형(B): {percentages['B']}%", font=text_font_bold, fill="black")
    draw.rectangle([100, y_cursor + 35, 100 + (percentages['B'] * 7), y_cursor + 55], fill='#457B9D')
    y_cursor += 80 + 40 

    # 3-4. "상세 성격 분석" 제목
    draw.text((50, y_cursor), "상세 성격 분석", font=title_font, fill="black")
    y_cursor += detail_title_height + 80 

    # 3-5. 상세 설명 (descriptions) 그리기
    def draw_multiline_text_by_bullet_actual(text, y_start, width_limit, draw_obj, font_obj):
        bullet_points = [p.strip() for p in text.split('•') if p.strip()]
        current_y_local = y_start 
        
        for point in bullet_points:
            line_with_bullet = "• " + point
            lines = []
            words = line_with_bullet.split(' ')
            line_buffer = ""
            
            available_width = width_limit - 80 

            for word in words:
                if draw_obj.textlength(line_buffer + word, font=font_obj) < available_width: 
                    line_buffer += word + " "
                else:
                    lines.append(line_buffer)
                    line_buffer = word + " "
            lines.append(line_buffer)
            
            for line in lines:
                draw_obj.text((80, current_y_local), line, font=font_obj, fill="#333333")
                current_y_local += font_obj.size + 6 
            current_y_local += 10 
        return current_y_local 

    y_cursor = draw_multiline_text_by_bullet_actual(descriptions['R'], y_cursor, img_width, draw, text_font)
    y_cursor = draw_multiline_text_by_bullet_actual(descriptions['G'], y_cursor, img_width, draw, text_font)
    y_cursor = draw_multiline_text_by_bullet_actual(descriptions['B'], y_cursor, img_width, draw, text_font)
    
    # --- 4. 최종 이미지 저장 및 반환 ---
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


# --- 데이터 로드 함수 ---
@st.cache_data
def load_data(file_name):
    try:
        # 파일 경로도 폰트 경로와 동일하게 current_dir을 기준으로 'rgb-test' 폴더 안에 있는 것으로 설정
        file_path = os.path.join(current_dir, 'rgb-test', file_name)
        with open(file_path, 'r', encoding='utf-8') as f: return json.load(f)
    except FileNotFoundError:
        st.error(f"데이터 파일 '{file_path}'을(를) 찾을 수 없습니다. 폴더 경로를 확인해주세요."); return None

# --- 질문리스트 그룹화 함수 ---
@st.cache_data
def get_balanced_questions_grouped(all_questions_data):
    if not all_questions_data: return {}
    initial_question_list = all_questions_data.get('questions', [])
    typed_questions = { f"{main}{sub}{world}":[] for main in "RGB" for sub in "PS" for world in "ias" }
    for q in initial_question_list:
        if q['type'] in typed_questions: typed_questions[q['type']].append(q)
    
    question_groups = {}
    for world in ['i', 'a', 's']:
        world_list = []
        r_count = min(len(typed_questions.get(f'RP{world}',[])), len(typed_questions.get(f'RS{world}',[])))
        g_count = min(len(typed_questions.get(f'GP{world}',[])), len(typed_questions.get(f'GS{world}',[])))
        b_count = min(len(typed_questions.get(f'BP{world}',[])), len(typed_questions.get(f'BS{world}',[])))
        world_list.extend(typed_questions.get(f'RP{world}',[])[:r_count] + typed_questions.get(f'RS{world}',[])[:r_count])
        world_list.extend(typed_questions.get(f'GP{world}',[])[:g_count] + typed_questions.get(f'GS{world}',[])[:g_count])
        world_list.extend(typed_questions.get(f'BP{world}',[])[:b_count] + typed_questions.get(f'BS{world}',[])[:b_count])
        random.shuffle(world_list)
        question_groups[world] = world_list
        
    current_id = 1
    for world in ['i', 'a', 's']:
        for question in question_groups[world]:
            question['id'] = current_id; current_id += 1
            
    return question_groups

# --- 데이터 로드 ---
description_blocks = load_data('descriptions.json')
all_questions_data = load_data('questions.json')
question_lists = get_balanced_questions_grouped(all_questions_data)

st.set_page_config(page_title="RGB 성격 심리 검사", layout="wide")

# --- 인덱스 계산 함수 ---
def get_comprehensive_index(percentage):
    if percentage <= 10: return 0
    elif percentage <= 20: return 1
    elif percentage <= 30: return 2
    elif percentage <= 40: return 3
    elif percentage <= 50: return 4
    elif percentage <= 60: return 5
    elif percentage <= 70: return 6
    elif percentage <= 80: return 7
    elif percentage <= 90: return 8
    else: return 9

def get_world_description_index(score, world_type):
    if world_type == 'i':
        index = math.floor((score + 48) / 9.7)
    else:
        index = math.floor((score + 40) / 8.1)
    return min(max(index, 0), 9)

# --- 앱 실행 로직 ---
st.title("🧠 퍼스널컬러 심리검사")
st.markdown("---")

if 'stage' not in st.session_state: st.session_state.stage = 'intro_i'
if 'responses' not in st.session_state: st.session_state.responses = {}

if question_lists and description_blocks: # 데이터 로드가 성공했을 때만 앱 로직 실행
    all_questions_flat = question_lists['i'] + question_lists['a'] + question_lists['s']
    total_questions = len(all_questions_flat)
    current_stage = st.session_state.stage

    if 'intro' in current_stage:
        world_code = current_stage.split('_')[1]
        worlds_info = {
            'i': ("내면 세계", len(question_lists['i'])),
            'a': ("주변 세계 (가족, 친구)", len(question_lists['a'])),
            's': ("사회 (업무, 공적 관계)", len(question_lists['s']))
        }
        title, num_questions = worlds_info[world_code]
        st.markdown(f"<div class='intro-box'><h1>{title}</h1><h2>지금부터 {title}에 관한 {num_questions}개의 질문이 시작됩니다.</h2></div>", unsafe_allow_html=True)
        cols = st.columns([1.55, 1, 1])
        with cols[1]:
            if st.button("시작하기", key=f"start_{world_code}"):
                st.session_state.stage = f"quiz_{world_code}"
                st.rerun()

    elif 'quiz' in current_stage:
        progress = len(st.session_state.responses) / total_questions
        st.progress(progress, text=f"전체 진행률: {len(st.session_state.responses)} / {total_questions}")
        world_code = current_stage.split('_')[1]
        current_question_list = question_lists[world_code]
        next_question = next((q for q in current_question_list if q['id'] not in st.session_state.responses), None)

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
        else:
            if world_code == 'i': st.session_state.stage = 'intro_a'
            elif world_code == 'a': st.session_state.stage = 'intro_s'
            elif world_code == 's': st.session_state.stage = 'results'
            st.rerun()
            
    elif current_stage == 'results':
        st.balloons()
        st.success("검사가 완료되었습니다! 아래에서 결과를 확인하세요. 🎉")
        st.markdown("---")
        
        scores = { f"{main}{sub}{world}":0 for main in "RGB" for sub in "PS" for world in "ias" }
        question_map = {q['id']: q for q in all_questions_flat}
        for q_id, value in st.session_state.responses.items():
            q_type = question_map[q_id]['type']
            if q_type in scores: scores[q_type] += value

        total_score_R = (scores['RPi']+scores['RPa']+scores['RPs']) - (scores['RSi']+scores['RSa']+scores['RSs'])
        total_score_G = (scores['GPi']+scores['GPa']+scores['GPs']) - (scores['GSi']+scores['GSa']+scores['GSs'])
        total_score_B = (scores['BPi']+scores['BPa']+scores['BPs']) - (scores['BSi']+scores['BSa']+scores['BSs'])
        comp_final = {'R': 128 + total_score_R*2, 'G': 128 + total_score_G*2, 'B': 128 + total_score_B*2}
        comp_abs = {k: max(v, 0) for k, v in comp_final.items()}
        comp_perc = {k: round((v / 256) * 100, 1) for k, v in comp_abs.items()}
        comp_hex = '#{:02X}{:02X}{:02X}'.format(int(min(comp_abs.get('R',0),255)), int(min(comp_abs.get('G',0),255)), int(min(comp_abs.get('B',0),255)))
        comp_indices = { k: get_comprehensive_index(p) for k, p in comp_perc.items() }
        comprehensive_result = {
            'title': '종합', 'percentages': comp_perc, 'hex': comp_hex,
            'descriptions': { k: description_blocks['comprehensive'][k][comp_indices[k]] for k in "RGB" }
        }

        world_results = {}; worlds_map = {'i': '내면 세계', 'a': '주변 세계', 's': '사회'}; world_key_map = {'i': 'inner', 'a': 'relationships', 's': 'social'}
        for code, data in worlds_map.items():
            world_key = world_key_map[code]
            score_R = scores[f'RP{code}'] - scores[f'RS{code}']
            score_G = scores[f'GP{code}'] - scores[f'GS{code}']
            score_B = scores[f'BP{code}'] - scores[f'BS{code}']
            index_R = get_world_description_index(score_R, code)
            index_G = get_world_description_index(score_G, code)
            index_B = get_world_description_index(score_B, code)
            world_results[code] = {
                'title': title,
                'description_R': description_blocks[world_key]['R'][index_R],
                'description_G': description_blocks[world_key]['G'][index_G],
                'description_B': description_blocks[world_key]['B'][index_B],
            }

        st.header(f"📈 당신의 종합 분석 결과")
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown("### 🎨 종합 성격 색상")
            st.markdown(f"<div style='width: 100%; height: 200px; background-color: {comp_hex}; border: 2px solid #ccc; border-radius: 12px;'></div>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align: center; font-size: 24px; font-weight: bold; margin-top: 10px;'>{comp_hex}</p>", unsafe_allow_html=True)
        with col2:
            fig, ax = plt.subplots(figsize=(10, 5))
            st.markdown("### ✨ 유형별 강도 시각화")
            y_labels = ["진취형 (R)", "중재형 (G)", "신중형 (B)"]
            values = [comp_perc[k] for k in "RGB"]
            colors = ['#E63946', '#7FB069', '#457B9D']
            bars = ax.barh(y_labels, values, color=colors, height=0.6)
            ax.set_xlim(0, 115)
            ax.spines[['top', 'right', 'left', 'bottom']].set_visible(False)
            ax.xaxis.set_ticks_position('none')
            ax.yaxis.set_ticks_position('none')
            ax.set_xticklabels([])
            ax.set_yticklabels(y_labels, fontsize=14)
            for bar in bars:
                width = bar.get_width()
                ax.text(width + 2, bar.get_y() + bar.get_height() / 2, f'{width}%', ha='left', va='center', fontsize=12)
            st.pyplot(fig)
            
        st.markdown("#### 📜 상세 성격 분석")
        st.info(f"**🔴 진취형(R):** {comprehensive_result['descriptions']['R']}")
        st.success(f"**🟢 중재형(G):** {comprehensive_result['descriptions']['G']}")
        st.warning(f"**🔵 신중형(B):** {comprehensive_result['descriptions']['B']}")
        st.markdown("---")

        st.header("📑 세계별 요약 분석")
        for code, data in world_results.items():
            with st.expander(f"**당신의 {data['title']}에서는...**"):
                st.markdown(f"**🔴 (추진력/결정/리더십):** {data['description_R']}")
                st.markdown(f"**🟢 (인간관계/협력/의사소통):** {data['description_G']}")
                st.markdown(f"**🔵 (사고방식/계획/판단):** {data['description_B']}")
        st.markdown("---")
        
        image_buffer = generate_result_image(comprehensive_result, font_path)
        st.download_button(label="📥 종합 결과 이미지 저장하기", data=image_buffer, file_name="RGB_personality_result.png", mime="image/png")
        
        if st.button("다시 검사하기"):
            st.session_state.clear()
            st.rerun()
