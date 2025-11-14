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
current_dir = os.path.dirname(os.path.abspath(__file__))
font_path = os.path.join(current_dir, 'NanumGothic.ttf')

if os.path.exists(font_path):
    fm.fontManager.addfont(font_path)
    font_name = fm.FontProperties(fname=font_path).get_name()
    plt.rc('font', family=font_name)
    plt.rcParams['axes.unicode_minus'] = False
else:
    pass 
    
# --- 텍스트 길이 측정 도우미 함수 (안정성 강화) ---
def safe_text_width(draw_obj, text, font):
    """PIL의 textlength 대신 textbbox를 사용하여 텍스트 너비를 안전하게 측정합니다."""
    if not text:
        return 0
    try:
        bbox = draw_obj.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0]
    except Exception:
        return len(text) * font.size 


# --- 종합 결과 이미지 생성 함수 (스타일 및 겹침 문제 해결 반영) ---
def generate_result_image(comprehensive_result, world_results, font_path):
    # --- 1. 초기 설정 및 폰트 로드 ---
    img_width = 1200  # 이미지 너비 증가 (1200px)
    padding_x = 20    # 좌우 여백 유지
    
    title_font, section_title_font, sub_section_title_font, text_font_bold, text_font, hex_font = [ImageFont.load_default()] * 6
    try:
        title_font = ImageFont.truetype(font_path, 36)
        section_title_font = ImageFont.truetype(font_path, 28)
        sub_section_title_font = ImageFont.truetype(font_path, 24)
        text_font_bold = ImageFont.truetype(font_path, 20)
        text_font = ImageFont.truetype(font_path, 16)
        hex_font = ImageFont.truetype(font_path, 24)
    except IOError:
        pass 

    # --- 2. 이미지 높이 계산을 위한 첫 번째 렌더링 (가상) ---
    temp_img = Image.new("RGB", (img_width, 100), color="#FDFDFD")
    temp_draw = ImageDraw.Draw(temp_img)
    
    # 2-1. 공통 너비 설정
    # 좌우 상세/세계별 분석 섹션의 유효 너비 (570px)
    main_section_width = (img_width / 2) - (1.5 * padding_x) 

    calculated_y_for_height = 60
    calculated_y_for_height += title_font.size + 30
    calculated_y_for_height += section_title_font.size + 20 
    
    color_box_height = 150 + hex_font.size + 30
    bar_section_height = (text_font_bold.size + 30) * 3 + 20 
    calculated_y_for_height += max(color_box_height, bar_section_height) + 40 

    # --- 2-2. 상세 분석 및 세계별 분석 섹션 높이 계산 ---
    
    # 줄바꿈을 계산하고 높이를 반환하는 도우미 함수 (간격 조정 반영)
    def calculate_multiline_text_block_height(text, font, width_limit, draw_obj, title_font_obj, is_world_section=False):
        total_block_height = 0
        total_block_height += title_font_obj.size + 15 # 제목 높이
        
        lines = []
        words = text.split(' ')
        line_buffer = ""
        available_width = width_limit - (padding_x * 2)

        for word in words:
            if safe_text_width(draw_obj, line_buffer + word, font=font) < available_width:
                line_buffer += word + " "
            else:
                lines.append(line_buffer)
                line_buffer = word + " "
        lines.append(line_buffer)
        
        for _ in lines:
            total_block_height += font.size + (5 if is_world_section else 15) # 줄 간격 조정 (세계별 분석 5px)
            
        total_block_height += (30 if is_world_section else 60) # 문단 간격 조정 (세계별 분석 30px, 종합 60px)
        return total_block_height

    # 왼쪽 (종합 상세 분석) 높이 계산 (width_limit = main_section_width)
    y_left = section_title_font.size + 40 # 상세 성격 분석 제목 높이
    descriptions = comprehensive_result['descriptions']
    y_left += calculate_multiline_text_block_height(descriptions['R'], text_font, main_section_width, temp_draw, text_font_bold, is_world_section=False)
    y_left += calculate_multiline_text_block_height(descriptions['G'], text_font, main_section_width, temp_draw, text_font_bold, is_world_section=False)
    y_left += calculate_multiline_text_block_height(descriptions['B'], text_font, main_section_width, temp_draw, text_font_bold, is_world_section=False)
    
    # 오른쪽 (세계별 요약 분석) 높이 계산 (width_limit = main_section_width)
    y_right = section_title_font.size + 40 # 세계별 요약 분석 제목 높이
    for code, data in world_results.items():
        y_right += sub_section_title_font.size + 20 # 세계별 소제목 높이
        y_right += calculate_multiline_text_block_height(data['description_R'], text_font, main_section_width, temp_draw, text_font_bold, is_world_section=True)
        y_right += calculate_multiline_text_block_height(data['description_G'], text_font, main_section_width, temp_draw, text_font_bold, is_world_section=True)
        y_right += calculate_multiline_text_block_height(data['description_B'], text_font, main_section_width, temp_draw, text_font_bold, is_world_section=True)


    final_img_height = int(calculated_y_for_height) + max(y_left, y_right) + 50

    # --- 3. 실제 이미지 생성 및 그리기 ---
    img = Image.new("RGB", (img_width, final_img_height), color="#FFFFFF")
    draw = ImageDraw.Draw(img)

    y_cursor = 60 
    
    # 3-1. 제목 "당신의 종합 분석 결과"
    draw.text((padding_x, y_cursor), "당신의 종합 분석 결과", font=title_font, fill="#333333")
    y_cursor += title_font.size + 30 
    
    # 3-2. 섹션 제목 (좌우)
    # 왼쪽 (종합 색상)
    draw.text((padding_x, y_cursor), "종합 성격 색상", font=section_title_font, fill="#333333")
    # 오른쪽 (그래프) - 위치 조정: (img_width / 2 + padding_x)
    draw.text((img_width / 2 + padding_x, y_cursor), "유형별 강도 시각화", font=section_title_font, fill="#333333") 
    y_cursor += section_title_font.size + 20

    # --- 3-3. 왼쪽 상단: 종합 성격 색상 ---
    hex_color = comprehensive_result['hex']
    color_box_y_start = y_cursor
    color_box_y_end = color_box_y_start + 150
    color_box_x_end = img_width / 2 - (1.5 * padding_x)
    draw.rectangle([padding_x, color_box_y_start, color_box_x_end, color_box_y_end], fill=hex_color, outline="#CCCCCC", width=1)
    
    draw.text((padding_x + (color_box_x_end - padding_x) / 2, color_box_y_end + 10), 
              hex_color, font=hex_font, fill="#333333", anchor="mt")
    
    y_cursor_after_color_box = color_box_y_end + hex_font.size + 30

    # --- 3-4. 오른쪽 상단: 퍼센티지 바 섹션 ---
    percentages = comprehensive_result['percentages']
    
    bar_y_start = y_cursor + 20 
    bar_x_start = img_width / 2 + padding_x # X 시작 위치
    
    section_width = img_width - bar_x_start - padding_x 
    text_buffer_width = 80  # 수치 텍스트 공간
    bar_width = section_width - text_buffer_width # 막대 길이
    
    colors = {'R': '#E63946', 'G': '#7FB069', 'B': '#457B9D'}
    labels = {'R': '진취형 (R)', 'G': '중재형 (G)', 'B': '신중형 (B)'}
    
    for k in ['B', 'G', 'R']:
        bar_height = 20
        perc = percentages[k]
        
        draw.text((bar_x_start, bar_y_start), labels[k], font=text_font_bold, fill="#333333")
        
        perc_text_x = bar_x_start + bar_width + 10
        draw.text((perc_text_x, bar_y_start), f"{perc}%", font=text_font_bold, fill="#333333")
        
        draw.rectangle([bar_x_start, bar_y_start + 30, bar_x_start + bar_width, bar_y_start + 30 + bar_height], fill='#E0E0E0', outline="#CCCCCC", width=1)
        
        actual_bar_length = int(bar_width * (perc / 100))
        draw.rectangle([bar_x_start, bar_y_start + 30, bar_x_start + actual_bar_length, bar_y_start + 30 + bar_height], fill=colors[k])
        
        bar_y_start += (bar_height + 40)
        
    y_cursor = max(y_cursor_after_color_box, bar_y_start + 20) 

    # --- 3-5. 상세 분석 & 세계별 분석 2단 배치 ---

    # 왼쪽 섹션의 X 시작/끝 좌표
    left_x_start = padding_x
    left_section_width = color_box_x_end 

    # 오른쪽 섹션의 X 시작/끝 좌표
    right_x_start = img_width / 2 + padding_x # 오른쪽 시작 지점
    right_section_width = img_width - right_x_start - padding_x # 오른쪽 유효 너비
    
    # y_cursor는 두 섹션의 시작 Y 좌표
    start_y_for_two_cols = y_cursor

    # 3-6. 왼쪽: 상세 성격 분석
    current_y_left = start_y_for_two_cols
    draw.text((left_x_start, current_y_left), "상세 성격 분석", font=section_title_font, fill="#333333")
    current_y_left += section_title_font.size + 40 

    def draw_description_block(title_text, description, color_code, y_start, x_start, width_limit, draw_obj, title_font_obj, text_font_obj, is_world_section=False):
        current_y_local = y_start 
        
        color_fill_map = {'R': '#E63946', 'G': '#7FB069', 'B': '#457B9D', 
                          'default_r': '#E63946', 'default_g': '#7FB069', 'default_b': '#457B9D'} 

        title_color = color_fill_map.get(color_code, '#333333')
        
        draw_obj.text((x_start, current_y_local), title_text, font=title_font_obj, fill=title_color) 
        current_y_local += title_font_obj.size + 15

        lines = []
        words = description.split(' ')
        line_buffer = ""
        available_width = width_limit - (x_start - (x_start if x_start == padding_x else x_start - padding_x)) # 패딩 고려

        for word in words:
            if safe_text_width(draw_obj, line_buffer + word, font=text_font_obj) < width_limit - (x_start + padding_x): 
                line_buffer += word + " "
            else:
                lines.append(line_buffer)
                line_buffer = word + " "
        lines.append(line_buffer)
        
        for line in lines:
            draw_obj.text((x_start, current_y_local), line, font=text_font_obj, fill="#555555")
            current_y_local += text_font_obj.size + (5 if is_world_section else 15) # 줄 간격 조정
            
        current_y_local += (30 if is_world_section else 60) # 문단 간격 조정
        return current_y_local

    # 종합 상세 분석 (왼쪽 열)
    current_y_left = draw_description_block("진취형(R) 성향 분석", descriptions['R'], 'R', current_y_left, left_x_start, left_section_width, draw, text_font_bold, text_font, is_world_section=False)
    current_y_left = draw_description_block("중재형(G) 성향 분석", descriptions['G'], 'G', current_y_left, left_x_start, left_section_width, draw, text_font_bold, text_font, is_world_section=False)
    current_y_left = draw_description_block("신중형(B) 성향 분석", descriptions['B'], 'B', current_y_left, left_x_start, left_section_width, draw, text_font_bold, text_font, is_world_section=False)
    
    # 3-7. 오른쪽: 세계별 요약 분석
    current_y_right = start_y_for_two_cols
    draw.text((right_x_start, current_y_right), "세계별 요약 분석", font=section_title_font, fill="#333333") 
    current_y_right += section_title_font.size + 40 

    worlds_map = {'i': '내면 세계', 'a': '주변 세계', 's': '사회'}
    for code, data in world_results.items():
        draw.text((right_x_start, current_y_right), f"'{worlds_map[code]}'에서는...", font=sub_section_title_font, fill="#333333")
        current_y_right += sub_section_title_font.size + 20

        # 세계별 R, G, B 설명 (is_world_section=True)
        current_y_right = draw_description_block("추진력/결정/리더십", data['description_R'], 'default_r', current_y_right, right_x_start, right_section_width, draw, text_font_bold, text_font, is_world_section=True)
        current_y_right = draw_description_block("인간관계/협력/의사소통", data['description_G'], 'default_g', current_y_right, right_x_start, right_section_width, draw, text_font_bold, text_font, is_world_section=True)
        current_y_right = draw_description_block("사고방식/계획/판단", data['description_B'], 'default_b', current_y_right, right_x_start, right_section_width, draw, text_font_bold, text_font, is_world_section=True)

    # --- 4. 최종 이미지 저장 및 반환 ---
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


# --- 데이터 로드 함수 (이하 동일) ---
current_dir = os.path.dirname(os.path.abspath(__file__)) 

@st.cache_data
def load_data(file_name):
    try:
        file_path = os.path.join(current_dir, file_name)
        with open(file_path, 'r', encoding='utf-8') as f: return json.load(f)
    except FileNotFoundError:
        st.error(f"데이터 파일 '{file_path}'을(를) 찾을 수 없습니다. 폴더 경로를 확인해주세요."); return None

# --- 질문리스트 그룹화 함수 (이하 동일) ---
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
description_blocks = None
all_questions_data = None

try:
    description_blocks = load_data('descriptions.json')
    all_questions_data = load_data('questions.json')
    question_lists = get_balanced_questions_grouped(all_questions_data)
except Exception as e:
    st.error(f"초기 데이터 로드 중 오류가 발생했습니다: {e}. 앱 실행 불가.")
    question_lists = {}

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

# 데이터 로드가 성공적으로 되었을 때만 앱 로직 실행
if question_lists and description_blocks: 
    all_questions_flat = []
    for world_key in ['i', 'a', 's']:
        if world_key in question_lists:
            all_questions_flat.extend(question_lists[world_key])
    
    total_questions = len(all_questions_flat)
    current_stage = st.session_state.stage

    if 'intro' in current_stage:
        world_code = current_stage.split('_')[1]
        worlds_info = {
            'i': ("내면 세계", len(question_lists.get('i', []))),
            'a': ("주변 세계 (가족, 친구)", len(question_lists.get('a', []))),
            's': ("사회 (업무, 공적 관계)", len(question_lists.get('s', [])))
        }
        title, num_questions = worlds_info[world_code]
        st.markdown(f"<div class='intro-box'><h1>{title}</h1><h2>지금부터 {title}에 관한 {num_questions}개의 질문이 시작됩니다.</h2></div>", unsafe_allow_html=True)
        cols = st.columns([1.55, 1, 1])
        with cols[1]:
            if st.button("시작하기", key=f"start_{world_code}"):
                st.session_state.stage = f"quiz_{world_code}"
                st.rerun()

    elif 'quiz' in current_stage:
        progress = len(st.session_state.responses) / total_questions if total_questions > 0 else 0
        st.progress(progress, text=f"전체 진행률: {len(st.session_state.responses)} / {total_questions}")
        world_code = current_stage.split('_')[1]
        current_question_list = question_lists.get(world_code, [])

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
        
        comp_abs = {k: min(max(v, 0), 255) for k, v in comp_final.items()}
        
        comp_perc = {k: round((v / 256.0) * 100, 1) for k, v in comp_abs.items()}
        
        comp_hex = '#{:02X}{:02X}{:02X}'.format(int(comp_abs['R']), int(comp_abs['G']), int(comp_abs['B']))
        
        comp_indices = { k: get_comprehensive_index(p) for k, p in comp_perc.items() }
        comprehensive_result = {
            'title': '종합', 'percentages': comp_perc, 'hex': comp_hex,
            'descriptions': { k: description_blocks['comprehensive'][k][comp_indices[k]] for k in "RGB" }
        }

        world_results_data = {}; worlds_map = {'i': '내면 세계', 'a': '주변 세계', 's': '사회'}; world_key_map = {'i': 'inner', 'a': 'relationships', 's': 'social'}
        for code, data in worlds_map.items():
            world_key = world_key_map[code]
            score_R = scores[f'RP{code}'] - scores[f'RS{code}']
            score_G = scores[f'GP{code}'] - scores[f'GS{code}']
            score_B = scores[f'BP{code}'] - scores[f'BS{code}']
            index_R = get_world_description_index(score_R, code)
            index_G = get_world_description_index(score_G, code)
            index_B = get_world_description_index(score_B, code)
            world_results_data[code] = {
                'title': data,
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
        for code, data in world_results_data.items():
            with st.expander(f"**당신의 {data['title']}에서는...**"):
                # 세계별 결과 섹션에는 이모지를 유지하여 텍스트로 구분
                st.markdown(f"**🔴 (추진력/결정/리더십):** {data['description_R']}")
                st.markdown(f"**🟢 (인간관계/협력/의사소통):** {data['description_G']}")
                st.markdown(f"**🔵 (사고방식/계획/판단):** {data['description_B']}")
        st.markdown("---")
        
        # 이미지 생성 시 world_results_data를 인자로 전달
        image_buffer = generate_result_image(comprehensive_result, world_results_data, font_path)
        st.download_button(label="📥 종합 결과 이미지 저장하기", data=image_buffer, file_name="RGB_personality_result.png", mime="image/png")
        
        if st.button("다시 검사하기"):
            st.session_state.clear()
            st.rerun()
else:
    st.error("초기 데이터 로드에 실패하여 앱을 시작할 수 없습니다. 파일 경로 및 파일 내용을 확인해주세요.")
