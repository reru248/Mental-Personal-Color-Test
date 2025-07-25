import streamlit as st
import json
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
import io
from PIL import Image, ImageDraw, ImageFont
import random

# --- UI 개선을 위한 CSS 스타일 ---
st.markdown("""
<style>
/* (스타일 코드는 기존과 동일) */
.question-box { min-height: 100px; display: flex; align-items: center; justify-content: center; padding: 1rem; border-radius: 10px; background-color: #f0f2f6; margin-bottom: 1rem; }
.question-box h2 { text-align: center; font-size: 1.7rem; }
div[data-testid="stButton"] > button { width: 100%; height: 55px; font-size: 1.2rem; font-weight: bold; border-radius: 8px; border: 2px solid #e0e0e0; }
div[data-testid="stButton"] > button:hover { border-color: #457B9D; color: #457B9D; }
div[data-testid="stDownloadButton"] > button { width: 100%; height: 55px; font-size: 1.2rem; font-weight: bold; }
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

# --- [핵심 수정 2] 이미지 생성 함수 로직 개선 ---
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
        """
        • 기호를 기준으로 문단을 나누고, 각 문단별로 자동 줄바꿈을 적용하는 함수
        """
        # 1. '•' 기호를 기준으로 설명 항목들을 분리합니다.
        #    (앞의 '•'는 제거하고, 공백이나 개행문자를 정리합니다)
        bullet_points = [p.strip() for p in text.split('•') if p.strip()]
        
        current_y = y_start
        
        # 2. 분리된 각 항목을 순회합니다.
        for point in bullet_points:
            # 3. 각 항목 앞에 '•'를 다시 붙여줍니다.
            line_with_bullet = "• " + point
            
            lines = []
            words = line_with_bullet.split(' ')
            line_buffer = ""
            
            # 4. 각 항목별로 자동 줄바꿈 로직을 적용합니다.
            for word in words:
                if draw.textlength(line_buffer + word, font=text_font) < width_limit:
                    line_buffer += word + " "
                else:
                    lines.append(line_buffer)
                    line_buffer = word + " "
            lines.append(line_buffer)
            
            # 5. 완성된 줄들을 이미지에 그립니다.
            for line in lines:
                draw.text((60, current_y), line, font=text_font, fill="#333333")
                current_y += text_font.size + 6
            
            # 6. 각 항목 사이에 추가적인 여백을 주어 가독성을 높입니다.
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


# --- [핵심 수정 1] '빌딩 블록' 설명 데이터 줄바꿈 방식 변경 ---
# 모든 \n 을 공백 2개 + \n (  \n)으로 변경하여 마크다운 줄바꿈을 강제합니다.
description_blocks = {
    "R": [
        "• 주도성: 리더 역할을 맡기보다, 명확하게 주어진 지시를 따르는 것을 훨씬 편안하게 느낍니다.  \n• 도전정신: 검증되지 않은 새로운 방식보다는, 예측 가능하고 안정성이 확보된 방법을 따르려는 경향이 매우 강합니다.  \n• 결단력: 스스로 결정을 내리기보다, 다른 사람이나 그룹의 의견에 따르는 것을 선호합니다.  \n• 목표지향성: 뚜렷한 개인적 목표를 설정하고 추진하기보다, 조직의 목표나 현재의 과업에 집중합니다.  \n• 적극성: 자신의 의견을 강하게 주장하기보다, 주로 듣고 관망하는 역할을 맡습니다.",
        "• 주도성: 대부분의 경우, 지시를 따르는 역할을 편안하게 느끼지만, 익숙한 분야에서는 의견을 낼 수 있습니다.  \n• 도전정신: 위험을 감수하는 것을 꺼리며, 되도록 안정적인 선택을 하려고 합니다.  \n• 결단력: 중요한 결정은 다른 사람에게 의존하는 경향이 있으며, 결정을 내리는 데 시간이 걸립니다.  \n• 목표지향성: 개인의 야망보다는, 팀이나 조직의 안정적인 성과에 기여하는 데 만족감을 느낍니다.  \n• 적극성: 조용하고 차분한 태도를 유지하며, 꼭 필요한 경우에만 발언합니다.",
        "• 주도성: 다른 사람을 이끌기보다, 신뢰하는 리더를 보좌하고 지원하는 역할에서 능력을 발휘합니다.  \n• 도전정신: 성공이 보장된 확실한 목표에 대해서만 도전하려는 경향이 있습니다.  \n• 결단력: 다른 사람들과 충분히 상의한 후 결정을 내리며, 독단적인 판단을 피합니다.  \n• 목표지향성: 목표를 향해 나아가지만, 과정에서 안정성을 해치지 않는 것을 중요하게 생각합니다.  \n• 적극성: 자신의 의견을 내세우기보다, 전체적인 분위기와 흐름을 맞추는 데 집중합니다.",
        "• 주도성: 필요하다면 의견을 제시하지만, 전면에 나서서 그룹을 이끄는 것은 부담스러워합니다.  \n• 도전정신: 새로운 시도를 할 때, 위험 요소를 먼저 분석하고 대비책을 마련해두어야 안심합니다.  \n• 결단력: 여러 선택지를 신중하게 비교한 후에야 결정을 내리며, 빠른 판단을 요구받으면 스트레스를 느낍니다.  \n• 목표지향성: 현실적으로 달성 가능한 목표를 설정하고, 꾸준히 나아가는 것을 선호합니다.  \n• 적극성: 논리적인 근거가 있을 때 자신의 의견을 표현하지만, 감정적인 주장은 피합니다.",
        "• 주도성: 익숙한 환경에서는 리더십을 발휘할 수 있지만, 낯선 상황에서는 관찰하는 쪽을 택합니다.  \n• 도전정신: 안정을 선호하지만, 충분한 정보가 있다면 새로운 기회를 탐색해 볼 의향이 있습니다.  \n• 결단력: 자신의 판단을 믿지만, 중요한 결정 전에는 주변의 조언을 반드시 구합니다.  \n• 목표지향성: 목표 달성도 중요하지만, 그 과정에서 발생하는 갈등이나 무리한 진행은 피하려고 합니다.  \n• 적극성: 상황에 따라 적극적으로 나서기도 하고, 때로는 뒤로 물러서기도 하는 유연한 태도를 보입니다.",
        "• 주도성: 그룹 활동에서 자연스럽게 의견을 제시하고 토론을 이끌며, 주도적인 역할을 즐깁니다.  \n• 도전정신: 현재에 안주하기보다, 새로운 기술이나 방법을 배우고 시도하는 것에서 즐거움을 느낍니다.  \n• 결단력: 합리적인 근거가 있다면, 다른 사람의 반대에도 불구하고 결정을 내릴 수 있습니다.  \n• 목표지향성: 한번 목표를 설정하면, 상당한 에너지를 쏟아부어 꾸준히 추진해 나갑니다.  \n• 적극성: 자신의 생각이나 아이디어를 다른 사람에게 명확하게 전달하고 설득하는 데 능숙합니다.",
        "• 주도성: 팀이나 프로젝트의 방향을 제시하고, 다른 사람들이 따를 수 있도록 이끄는 리더십을 발휘합니다.  \n• 도전정신: 약간의 위험이 따르더라도, 더 큰 성과를 얻을 수 있는 도전적인 과제를 선호합니다.  \n• 결단력: 정보가 부족한 상황에서도, 자신의 직관과 경험을 믿고 신속하게 판단을 내립니다.  \n• 목표지향성: 목표 달성을 위해 장애물을 만나더라도, 쉽게 포기하지 않고 해결책을 찾아냅니다.  \n• 적극성: 정체된 분위기를 싫어하며, 역동적이고 빠르게 진행되는 환경에서 더 큰 활력을 느낍니다.",
        "• 주도성: 자신이 속한 조직이나 그룹에서 리더 역할을 맡는 경우가 많으며, 이를 통해 책임감을 느낍니다.  \n• 도전정신: 실패를 두려워하기보다, 도전하지 않는 것을 더 후회하는 경향이 강합니다.  \n• 결단력: 복잡한 상황에서도 핵심을 파악하고, 단호하게 결정을 내리는 능력이 있습니다.  \n• 목표지향성: 자신의 성과를 명확하게 증명할 수 있는 목표를 선호하며, 성취를 통해 만족감을 얻습니다.  \n• 적극성: 자신의 의견을 관철시키기 위해, 논쟁이나 경쟁을 마다하지 않습니다.",
        "• 주도성: 위기 상황에서 방향을 제시하고 사람들을 결집시키는 등 강력한 리더십을 발휘합니다.  \n• 도전정신: 불확실성이 높은 환경을 두려워하지 않으며, 오히려 새로운 기회를 찾는 계기로 삼습니다.  \n• 결단력: 한번 내린 결정에 대해서는 강한 책임감을 느끼며, 결과에 대해 변명하지 않습니다.  \n• 목표지향성: 매우 높은 수준의 목표를 설정하고, 이를 달성하기 위해 자신을 끊임없이 채찍질합니다.  \n• 적극성: 자신의 존재감과 영향력을 분명하게 드러내며, 조직 전체의 변화를 주도합니다.",
        "• 주도성: 단순히 팀을 이끄는 것을 넘어, 새로운 규칙이나 시장의 판도를 만드는 역할을 합니다.  \n• 도전정신: 아무도 가지 않은 길을 개척하는 것에서 가장 큰 동기를 얻으며, 실패 가능성은 거의 고려하지 않습니다.  \n• 결단력: 거의 모든 상황에서 즉각적이고 본능적인 판단을 내리며, 자신의 결정에 대한 확신이 매우 강합니다.  \n• 목표지향성: 개인의 성공을 넘어, 자신이 속한 분야나 사회에 큰 족적을 남기려는 야망을 가집니다.  \n• 적극성: 자신의 비전을 실현하기 위해 모든 자원을 동원하며, 주변의 그 어떤 반대에도 흔들리지 않습니다."
    ],
    "G": [
        "• 공감능력: 다른 사람의 감정에 거의 영향을 받지 않으며, 객관적인 사실에만 집중합니다.  \n• 조화추구: 그룹의 분위기나 관계보다, 개인의 원칙이나 과업의 효율성을 훨씬 중요하게 생각합니다.  \n• 협력지향: 혼자 일하는 것이 가장 편안하며, 다른 사람과 협력하는 것을 불필요하다고 느낄 때가 많습니다.  \n• 지지/배려: 다른 사람의 실수에 대해 관용을 베풀기보다, 규칙에 따라 처리하는 것을 선호합니다.  \n• 관계중심: 소수의 깊은 관계보다는, 필요에 따른 기능적인 인간관계로도 충분하다고 생각합니다.",
        "• 공감능력: 감정적인 이야기보다는, 사실에 기반한 논리적인 대화를 더 편안하게 느낍니다.  \n• 조화추구: 불필요한 논쟁을 피하려고 하지만, 자신의 원칙이 침해당하면 단호하게 대응합니다.  \n• 협력지향: 독립적으로 일하는 것을 선호하지만, 목표 달성을 위해 필요하다면 협력할 수 있습니다.  \n• 지지/배려: 다른 사람을 돕기보다, 각자 자신의 일을 책임지는 것이 합리적이라고 생각합니다.  \n• 관계중심: 넓고 얕은 인간관계보다는, 명확한 목적을 가진 소수의 관계를 유지합니다.",
        "• 공감능력: 친한 사람의 감정은 이해하려고 노력하지만, 모르는 사람의 감정에는 크게 신경 쓰지 않습니다.  \n• 조화추구: 대부분의 경우 조화를 추구하지만, 비효율적인 상황은 참기 어려워하며 직접적으로 지적하기도 합니다.  \n• 협력지향: 팀으로 일할 때, 감정적인 교류보다 각자의 역할을 명확히 하는 것을 더 중요하게 생각합니다.  \n• 지지/배려: 상대방에게 직접적인 도움보다, 문제를 스스로 해결할 수 있도록 원칙적인 조언을 하는 편입니다.  \n• 관계중심: 개인적인 삶과 일의 경계를 명확히 하며, 사적인 관계가 일에 영향을 미치는 것을 꺼립니다.",
        "• 공감능력: 상대방의 감정을 인지하고 이해하지만, 거기에 깊이 동화되지는 않고 거리를 유지합니다.  \n• 조화추구: 논쟁을 즐기지는 않지만, 문제 해결을 위해 필요하다면 기꺼이 토론에 참여합니다.  \n• 협력지향: 혼자서도 일을 잘하지만, 팀워크를 통해 더 나은 결과를 낼 수 있다는 점을 인정합니다.  \n• 지지/배려: 도움이 필요한 사람을 외면하지 않으며, 자신이 할 수 있는 범위 내에서 기꺼이 돕습니다.  \n• 관계중심: 새로운 사람들과도 잘 어울리지만, 소수의 친구와 깊은 관계를 맺는 것을 더 중요하게 생각합니다.",
        "• 공감능력: 다른 사람의 입장에서 생각하려고 노력하며, 감정적인 대화에도 편안함을 느낍니다.  \n• 조화추구: 가능한 한 갈등을 피하고, 평화로운 분위기를 만들기 위해 노력합니다.  \n• 협력지향: 혼자 일하기보다, 다른 사람과 함께 아이디어를 나누고 협력하는 과정에서 즐거움을 느낍니다.  \n• 지지/배려: 다른 사람의 실수를 너그럽게 이해해주려고 하며, 성장을 기다려줄 줄 압니다.  \n• 관계중심: 주변 사람들과 유대감을 형성하고, 안정적인 관계를 유지하는 것을 중요하게 생각합니다.",
        "• 공감능력: 다른 사람의 감정 변화를 민감하게 알아차리고, 그에 맞춰 세심하게 행동합니다.  \n• 조화추구: 그룹 내에 불편한 기류가 흐르면, 이를 해소하기 위해 적극적으로 나서서 분위기를 전환합니다.  \n• 협력지향: 팀의 공동 목표 달성을 위해, 자신의 공을 기꺼이 다른 사람에게 양보할 수 있습니다.  \n• 지지/배려: 상대방이 무엇을 필요로 하는지 먼저 파악하고, 실질적인 도움을 주려고 노력합니다.  \n• 관계중심: 한번 맺은 인연을 소중하게 생각하며, 꾸준히 연락하며 관계를 유지합니다.",
        "• 공감능력: 영화나 소설을 보며 주인공의 감정에 깊이 몰입하며, 눈물을 흘릴 때도 많습니다.  \n• 조화추구: 의견 대립이 생겼을 때, 양쪽의 입장을 모두 듣고 합리적인 중재안을 제시하는 데 능숙합니다.  \n• 협력지향: 경쟁적인 분위기보다, 서로 돕고 지지하는 협력적인 분위기에서 최고의 능력을 발휘합니다.  \n• 지지/배려: 다른 사람이 성장하고 성공하는 모습을 보는 것에서 큰 기쁨과 보람을 느낍니다.  \n• 관계중심: 내가 속한 공동체 구성원 모두가 소외되지 않고 잘 어울리는 것에 큰 책임감을 느낍니다.",
        "• 공감능력: 상대방의 표정이나 말투만으로도 그 사람의 기분이나 생각을 상당 부분 짐작할 수 있습니다.  \n• 조화추구: 자신에게 손해가 되더라도, 그룹 전체의 평화와 화합을 깨뜨리는 선택은 거의 하지 않습니다.  \n• 협력지향: '나'의 성공보다 '우리'의 성공을 훨씬 더 중요하게 생각하며, 이를 위해 헌신합니다.  \n• 지지/배려: 상대방이 힘든 상황에 부닥쳤을 때, 마치 자신의 일처럼 여기며 진심으로 위로하고 돕습니다.  \n• 관계중심: 주변 사람들을 챙기고, 그들의 기념일을 기억하는 등 관계 유지를 위해 많은 노력을 기울입니다.",
        "• 공감능력: 다른 사람의 고통이나 슬픔을 접하면, 그 감정이 직접적으로 전해져와 함께 아파합니다.  \n• 조화추구: 어떤 상황에서든 갈등을 예방하고, 모든 사람이 만족할 수 있는 해결책을 찾으려고 합니다.  \n• 협력지향: 팀의 성공을 위해서라면, 자신의 역할이나 공이 드러나지 않아도 전혀 개의치 않습니다.  \n• 지지/배려: 타인의 성장을 돕는 것을 자신의 사명처럼 여기며, 이를 위해 시간과 자원을 아낌없이 투자합니다.  \n• 관계중심: 자신이 속한 공동체에 대한 강한 소속감과 애정을 느끼며, 구성원들을 가족처럼 여깁니다.",
        "• 공감능력: 개별적인 사람을 넘어, 사회나 인류 전체가 겪는 문제에 깊이 공감하고 안타까워합니다.  \n• 조화추구: 세상의 모든 갈등과 대립이 사라지고, 평화로운 상태가 되기를 진심으로 바랍니다.  \n• 협력지향: 경쟁이라는 개념 자체를 불편하게 느끼며, 모든 것이 상호 협력을 통해 이루어져야 한다고 믿습니다.  \n• 지지/배려: 자신을 희생해서라도, 어려움에 부닥친 사람이나 사회적 약자를 돕는 것이 당연하다고 생각합니다.  \n• 관계중심: 주변 사람들과의 관계를 넘어, 모든 생명체와의 연결과 유대감을 중요하게 생각합니다."
    ],
    "B": [
        "• 분석력: 데이터를 보기보다, 순간적인 느낌이나 직관에 의존하여 판단하는 것을 매우 선호합니다.  \n• 계획성: 계획을 세우는 것 자체가 답답하고, 모든 것을 즉흥적으로 결정하는 데서 자유로움을 느낍니다.  \n• 신중함: 위험을 따져보기보다, 일단 행동으로 옮기고 문제를 해결해나가는 방식을 선호합니다.  \n• 객관성: 논리적인 타당성보다, 자신의 경험에서 비롯된 주관적인 확신을 더 신뢰합니다.  \n• 체계성: 정해진 규칙이나 절차를 따르는 것을 싫어하며, 자신만의 방식으로 일하는 것을 좋아합니다.",
        "• 분석력: 세부적인 데이터를 분석하기보다, 전체적인 흐름과 핵심을 빠르게 파악하는 데 더 능숙합니다.  \n• 계획성: 장기적인 계획보다, 단기적인 목표를 세우고 유연하게 대응하는 것을 선호합니다.  \n• 신중함: 약간의 위험은 감수할 수 있으며, 빠른 실행을 위해 완벽함을 포기할 수 있습니다.  \n• 객관성: 감정이나 직관이 결정에 큰 영향을 미치며, 이를 자연스럽게 받아들입니다.  \n• 체계성: 복잡한 이론이나 시스템을 배우기보다, 직접 경험하며 배우는 것을 선호합니다.",
        "• 분석력: 중요한 데이터는 확인하지만, 모든 것을 분석에만 의존하지는 않고 직관을 함께 활용합니다.  \n• 계획성: 대략적인 계획만 세우고, 구체적인 내용은 상황에 따라 즉흥적으로 결정하는 편입니다.  \n• 신중함: 결정을 내리기 전에 빠르게 정보를 수집하지만, 너무 오래 고민하지는 않습니다.  \n• 객관성: 객관적인 사실을 존중하지만, 사람들의 감정이나 분위기 같은 비논리적인 요소도 중요하게 고려합니다.  \n• 체계성: 기존의 틀에 얽매이지 않으며, 필요하다면 규칙을 바꾸거나 무시하는 유연성을 보입니다.",
        "• 분석력: 논리적 분석의 중요성을 알지만, 때로는 자신의 직관이 더 정확하다고 느낄 때가 있습니다.  \n• 계획성: 계획을 세우지만, 상황이 바뀌면 언제든지 계획을 수정하거나 폐기할 준비가 되어 있습니다.  \n• 신중함: 위험을 인지하고 관리하려고 하지만, 기회가 왔을 때는 과감하게 행동할 줄도 압니다.  \n• 객관성: 자신의 주관적인 판단이 들어갈 수 있음을 인정하고, 이를 보완하기 위해 다른 사람의 의견을 구합니다.  \n• 체계성: 정해진 절차를 따르면서도, 더 효율적인 방법이 있다면 과감히 방식을 바꾸는 실용적인 태도를 보입니다.",
        "• 분석력: 직관적으로 내린 결론을 논리적인 데이터로 다시 한번 검증해보는 균형 잡힌 접근을 합니다.  \n• 계획성: 계획의 필요성을 충분히 인지하고, 실행 과정에서 발생할 수 있는 변수들을 고려합니다.  \n• 신중함: 행동하기 전에 충분히 정보를 검토하지만, 정보 수집에만 너무 많은 시간을 쓰지는 않습니다.  \n• 객관성: 가능한 한 객관적인 판단을 내리려고 노력하며, 감정적인 편향을 경계합니다.  \n• 체계성: 자신만의 효율적인 작업 방식과 체계를 가지고 있으며, 이를 꾸준히 개선해나갑니다.",
        "• 분석력: 어떤 현상을 보면, 그 원인이 무엇인지 논리적으로 따져보고 분석하는 습관이 있습니다.  \n• 계획성: 일을 시작하기 전에, 목표, 과정, 필요한 자원 등을 미리 정리하고 계획을 세웁니다.  \n• 신중함: 결정을 내리기 전에, 발생할 수 있는 긍정적, 부정적 결과를 미리 시뮬레이션해 봅니다.  \n• 객관성: 개인적인 감정이나 친분이 공적인 판단에 영향을 미치지 않도록 의식적으로 노력합니다.  \n• 체계성: 복잡한 문제를 작은 단위로 나누어, 단계별로 체계적으로 해결하는 것을 선호합니다.",
        "• 분석력: 데이터 속에서 다른 사람들이 보지 못하는 패턴이나 인사이트를 찾아내는 데 능숙합니다.  \n• 계획성: 만약을 대비한 '플랜 B'를 항상 준비해두며, 계획의 완성도를 매우 중요하게 생각합니다.  \n• 신중함: 행동으로 옮기기 전에, 관련된 정보를 거의 완벽하게 수집하고 검토해야만 안심합니다.  \n• 객관성: 모든 주장에 대해 '왜?'라는 질문을 던지며, 논리적인 근거나 데이터가 없으면 잘 믿지 않습니다.  \n• 체계성: 일관된 원칙과 기준을 가지고 있으며, 모든 것을 이 체계에 맞춰 정리하고 판단합니다.",
        "• 분석력: 복잡하게 얽힌 문제의 핵심을 정확히 꿰뚫어 보고, 가장 효율적인 해결책을 설계합니다.  \n• 계획성: 단기적인 성과보다, 장기적인 관점에서 최적의 결과를 가져올 수 있는 큰 그림을 그립니다.  \n• 신중함: 아주 작은 리스크도 놓치지 않으려 하며, 의사결정의 모든 과정을 기록하고 검토합니다.  \n• 객관성: 자신의 전문 분야에 대해서는, 감정이나 편견을 거의 완벽하게 배제하고 판단할 수 있습니다.  \n• 체계성: 자신만의 정교한 지식 체계를 가지고 있으며, 새로운 정보도 이 체계 속에서 재구성하여 이해합니다.",
        "• 분석력: 방대한 데이터를 종합하여 미래를 예측하거나, 복잡한 시스템의 동작 원리를 정확히 모델링합니다.  \n• 계획성: 거의 모든 변수를 고려한 완벽에 가까운 계획을 세우며, 계획과 실제의 오차를 최소화합니다.  \n• 신중함: 정보가 100% 확실하지 않다면, 섣불리 결론을 내리거나 행동하지 않는 완벽주의적 성향을 보입니다.  \n• 객관성: 자신의 판단이 틀릴 수 있다는 가능성을 항상 열어두고, 끊임없이 자신의 지식을 의심하고 검증합니다.  \n• 체계성: 자신만의 확고한 논리 체계와 원칙을 바탕으로, 일관성 있고 오류 없는 판단을 내립니다.",
        "• 분석력: 한 분야의 모든 지식과 원리를 통달하여, 누구도 생각하지 못한 새로운 통찰을 이끌어냅니다.  \n• 계획성: 미래에 일어날 여러 시나리오를 예측하고, 각각에 대한 최적의 대응 전략을 미리 설계해 둡니다.  \n• 신중함: 모든 정보의 신뢰도를 교차 검증하며, 단 하나의 불확실성도 용납하지 않으려는 경향이 있습니다.  \n• 객관성: 개인적인 감정을 완벽하게 배제하고, 오직 데이터와 논리에만 근거하여 최적의 결정을 내립니다.  \n• 체계성: 세상의 복잡한 현상을 자신만의 깊이 있는 이론과 체계로 설명하고 예측할 수 있는 수준에 이르렀습니다."
    ]
}


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

if question_list:
    total_questions = len(question_list)

    if 'responses' not in st.session_state:
        st.session_state.responses = {}
    
    next_question = None
    # ID를 직접 순회하는 대신, question_list를 순회합니다.
    for i in range(total_questions):
        q_id = question_list[i]['id']
        if q_id not in st.session_state.responses:
            next_question = question_list[i]
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

        button_cols = st.columns(9)
        for i, val in enumerate(range(-4, 5)):
            if button_cols[i].button(str(val), key=f"q{q['id']}_val{val}"):
                # 이제 응답에 타입을 저장할 필요가 없습니다. ID만으로 충분합니다.
                st.session_state.responses[q['id']] = val
                st.rerun()
    
    elif len(st.session_state.responses) == total_questions and total_questions > 0:
        st.balloons()
        st.success("검사가 완료되었습니다! 아래에서 결과를 확인하세요. 🎉")
        st.markdown("---")
        
        scores = {'RP': 0, 'RS': 0, 'GP': 0, 'GS': 0, 'BP': 0, 'BS': 0}
        
        # ID를 키로 사용하여 점수를 계산합니다.
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
            y_labels = ["진취형 (R)", "중재형 (G)", "신중형 (B)"]
            values = [percentages.get('R', 0), percentages.get('G', 0), percentages.get('B', 0)]
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
