import streamlit as st
import json
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os

font_path = os.path.abspath('rgb-test/NanumGothic.ttf')
if os.path.exists(font_path):
    fm.fontManager.addfont(font_path)
    font_name = fm.FontProperties(fname=font_path).get_name()
    plt.rc('font', family=font_name)
    plt.rcParams['axes.unicode_minus'] = False
else:
    st.warning(f"""
    한글 폰트 파일('{font_path}')을 찾을 수 없습니다. 
    그래프의 한글이 깨질 수 있습니다. 
    폰트 파일을 `streamlit_app.py`와 같은 폴더에 추가해주세요.
    """)


# --- [수정] 최종 '빌딩 블록' 설명 데이터 (객관적/현실적 톤) ---
description_blocks = {
    "R": [
        "당신은 위험을 감수하기보다 예측 가능하고 안정적인 환경을 매우 선호합니다. 새로운 일을 시작하기보다, 검증된 절차나 기존의 방식을 따르는 것에서 편안함을 느끼는 경향이 강합니다.",
        "당신은 변화를 주도하기보다, 주어진 환경과 규칙 안에서 자신의 역할을 안정적으로 수행하는 것을 중요하게 생각합니다. 급진적인 변화보다는 점진적인 개선 방식을 선호하는 편입니다.",
        "당신은 어떤 일을 할 때, 행동에 앞서 안전과 성공 가능성을 신중하게 점검하는 경향이 있습니다. 다른 사람들의 의견을 충분히 듣고, 위험이 적다고 판단될 때 움직이는 편입니다.",
        "당신은 안정을 중요하게 생각하지만, 필요하다면 변화를 수용할 수 있습니다. 행동하기 전에 여러 선택지의 장단점을 따져보며, 자신에게 이득이 되는 합리적인 방향으로 움직입니다.",
        "당신은 안정적인 상황을 선호하지만, 동시에 더 나은 가능성을 모색하기도 합니다. 무모한 도전은 피하지만, 현재에 안주하지 않고 점진적으로 발전하려는 경향을 보입니다.",
        "당신은 자신의 의견이나 아이디어가 있을 때, 이를 표현하고 사람들과 논의하는 것을 긍정적으로 생각합니다. 상황을 주도하기보다, 대화에 적극적으로 참여하여 영향력을 발휘하는 편입니다.",
        "당신은 목표가 생기면 이를 달성하기 위해 적극적으로 행동에 나서는 경향이 있습니다. 필요하다면 팀을 이끌고 방향을 제시하며, 다른 사람들에게 동기를 부여하는 역할을 맡기도 합니다.",
        "당신은 목표를 성취하려는 의지가 강하며, 그 과정에서 나타나는 어려움을 극복의 대상으로 여깁니다. 자신의 열정과 에너지를 목표 달성을 위해 집중적으로 사용하는 편입니다.",
        "당신은 복잡하고 어려운 문제에 직면했을 때, 이를 회피하기보다 책임감을 갖고 해결하려는 성향이 매우 강합니다. 명확한 판단력으로 결정을 내리고, 실질적인 결과를 만들어내는 데 집중합니다.",
        "당신은 기존의 방식에 의문을 제기하고, 더 나은 대안을 찾아내려는 성향이 극대화되어 있습니다. 높은 수준의 목표를 설정하고, 이를 달성하기 위해 대담한 시도와 결정을 내리는 것을 두려워하지 않습니다."
    ],
    "G": [
        "당신은 공동체의 조화나 관계보다는, 개인의 독립적인 목표와 원칙을 훨씬 더 중요하게 생각하는 경향이 있습니다. 다른 사람의 감정에 크게 영향을 받지 않으며, 혼자 일하는 것을 가장 편안하게 느낍니다.",
        "당신은 감정적인 교류보다는, 사실과 논리에 기반한 객관적인 소통을 선호합니다. 공과 사를 명확히 구분하며, 관계보다는 주어진 과업의 효율적인 완수를 우선시하는 경향이 있습니다.",
        "당신은 다른 사람들과 협력할 때도 개인의 독립적인 공간과 생각을 유지하는 것이 중요합니다. 팀의 목표에 기여하면서도, 감정적으로 깊이 얽매이는 것은 불편하게 느끼는 편입니다.",
        "당신은 대부분의 사람들과 원만한 관계를 유지하려고 노력하며, 주변 분위기를 긍정적으로 만들고자 합니다. 상대방의 입장을 이해하려고 하지만, 최종 결정은 합리성에 근거하여 내립니다.",
        "당신은 다른 사람의 감정을 존중하고, 신뢰를 바탕으로 한 관계를 중요하게 생각합니다. 도움이 필요한 사람에게 손을 내밀 줄 알며, 정서적인 교감을 통해 안정감을 얻는 편입니다.",
        "당신은 다른 사람의 이야기를 잘 들어주는 편이며, 주변 사람들이 당신에게 종종 고민을 털어놓습니다. 상대방의 마음을 편안하게 해주는 능력으로 긍정적인 관계를 형성합니다.",
        "당신은 다른 사람의 감정 변화에 민감하며, 공동체의 화합을 위해 적극적으로 노력하는 경향이 있습니다. 갈등이 발생했을 때, 이를 해결하고 조화로운 분위기를 만들기 위해 중재에 나서기도 합니다.",
        "당신은 다른 사람의 성장을 돕고 지원하는 것에서 상당한 보람과 만족감을 느낍니다. 자신이 속한 조직이나 그룹 전체가 좋은 방향으로 나아가는 데 기여하려는 마음이 강합니다.",
        "당신은 대부분의 상황에서 자신보다 타인이나 공동체의 입장을 먼저 고려하는 성향이 매우 강합니다. 사람들이 서로 신뢰하고 도울 수 있는 환경을 만드는 데 많은 시간과 에너지를 사용합니다.",
        "당신은 타인의 성공과 행복을 자신의 것처럼 기뻐하며, 이를 위해 헌신하는 것에서 삶의 큰 의미를 찾습니다. 주변 사람과 사회에 긍정적인 영향을 미치려는 이타적인 동기가 매우 강하게 나타납니다."
    ],
    "B": [
        "당신은 계획을 세우고 따르기보다, 매 순간의 느낌과 직관에 따라 즉흥적으로 행동하는 것을 매우 선호합니다. 정해진 틀을 답답하게 느끼며, 자유로운 상황에서 가장 편안함을 느낍니다.",
        "당신은 상세한 분석보다는 과거의 경험이나 직감에 의존하여 빠르게 판단하는 경향이 있습니다. 이론보다는 실제 부딪히며 배우는 것을 선호하며, 변화하는 상황에 대한 적응이 빠릅니다.",
        "당신은 큰 방향만 설정하고, 세부적인 계획 없이 유연하게 일을 처리하는 편입니다. 지나치게 꼼꼼한 계획은 오히려 속도를 늦춘다고 생각하며, 빠른 실행과 수정을 선호합니다.",
        "당신은 직관적으로 빠른 판단을 내리면서도, 현실적인 감각을 잃지 않습니다. 불필요한 분석으로 시간을 낭비하기보다, 핵심을 파악하고 즉시 실행에 옮기는 실용적인 면모를 보입니다.",
        "당신은 직관적으로 떠오른 생각을 논리적으로 한번 더 검토해보는, 균형 잡힌 사고를 하려고 노력합니다. 빠른 판단력과 신중한 분석력 사이에서 적절한 결정을 내리고자 합니다.",
        "당신은 어떤 일을 시작하기 전에, 예상되는 결과와 과정을 미리 생각하고 체계적으로 정리하는 것을 선호합니다. 계획에 따라 일이 진행될 때 안정감을 느끼며, 효율적으로 업무를 처리합니다.",
        "당신은 어떤 현상을 접했을 때, 그 이면에 있는 데이터나 논리적인 원리를 파악하려는 경향이 있습니다. 감정이나 직관보다는 객관적인 사실을 바탕으로 상황을 해석하고 판단합니다.",
        "당신은 복잡한 상황 속에서도 핵심적인 변수들을 파악하고, 장기적인 관점에서 최적의 계획을 세우려는 경향이 있습니다. 발생 가능한 위험을 미리 예측하고 대비하는 전략적인 모습을 보입니다.",
        "당신은 단편적인 사실들을 종합하여 전체적인 구조나 시스템을 이해하려는 지적 욕구가 강합니다. 견고하고 지속 가능한 해결책을 찾기 위해, 다양한 변수들을 고려하여 체계적으로 접근합니다.",
        "당신은 한 분야에 대해 깊이 파고들어, 본질적인 원리를 완전히 이해하려는 성향이 극대화되어 있습니다. 매우 높은 수준의 논리적 사고와 분석력을 바탕으로, 복잡한 문제에 대한 최적의 해결책을 제시합니다."
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
import os

def load_questions():
    try:
        file_path = os.path.join('rgb-test', 'questions.json')
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("`rgb-test/questions.json` 파일을 찾을 수 없습니다. 폴더 경로를 확인해주세요.")
        return None
questions = load_questions()

st.title("🧠 퍼스널컬러 심리검사")
st.markdown("---")

if questions:
    total_questions = len(questions)

    if 'responses' not in st.session_state:
        st.session_state.responses = {}
    
    next_question = None
    for q in questions:
        if q['id'] not in st.session_state.responses:
            next_question = q
            break

    progress = len(st.session_state.responses) / total_questions
    st.progress(progress, text=f"진행률: {len(st.session_state.responses)} / {total_questions}")

    if next_question:
        q = next_question
        st.subheader(f"Q{q['id']}. {q['text']}")
        
        cols = st.columns(9)
        for i, val in enumerate(range(-4, 5)):
            if cols[i].button(str(val), key=f"q{q['id']}_val{val}"):
                st.session_state.responses[q['id']] = {'type': q['type'], 'value': val}
                st.rerun()
    
    elif len(st.session_state.responses) == total_questions:
        st.balloons()
        st.success("검사가 완료되었습니다! 아래에서 결과를 확인하세요. 🎉")
        st.markdown("---")
        
        final_scores = {'R': 0, 'G': 0, 'B': 0}
        for q_id, resp in st.session_state.responses.items():
            final_scores[resp['type']] += resp['value']

        absolute_scores = {
            k: max(128 + v, 0) for k, v in final_scores.items()
        }
        
        percentages = {
            k: round((v / 256) * 100, 1) for k, v in absolute_scores.items()
        }

        rgb_for_color = {
            k: min(v, 255) for k, v in absolute_scores.items()
        }
        rgb_tuple = (
            rgb_for_color.get('R', 0),
            rgb_for_color.get('G', 0),
            rgb_for_color.get('B', 0)
        )
        hex_color = '#{:02X}{:02X}{:02X}'.format(*rgb_tuple)

        st.header("📈 당신의 성격 분석 결과")
        
        col1, col2 = st.columns([1, 1])

        with col1:
            st.markdown("### 🎨 당신의 고유 성격 색상")
            st.markdown(
                f"""
                <div style='
                    width: 100%; 
                    height: 200px; 
                    background-color: {hex_color};
                    border: 2px solid #ccc;
                    border-radius: 12px;
                '></div>
                """,
                unsafe_allow_html=True
            )
            st.markdown(f"<p style='text-align: center; font-size: 24px; font-weight: bold; margin-top: 10px;'>{hex_color}</p>", unsafe_allow_html=True)
            
        with col2:
            st.markdown("### ✨ 유형별 강도 시각화")
            
            y_labels = ["진취형 (R)", "중재형 (G)", "신중형 (B)"]
            values = [percentages.get('R', 0), percentages.get('G', 0), percentages.get('B', 0)]
            colors = ['#E63946', '#7FB069', '#457B9D']

            fig, ax = plt.subplots(figsize=(10, 5))
            bars = ax.barh(y_labels, values, color=colors, height=0.6)

            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_visible(False)
            ax.spines['bottom'].set_visible(False)
            ax.xaxis.set_ticks_position('none')
            ax.yaxis.set_ticks_position('none')
            ax.set_xticklabels([])
            ax.set_yticklabels(y_labels, fontsize=14) 
            ax.set_xlim(0, 115)

            for bar in bars:
                width = bar.get_width()
                ax.text(width + 2,
                        bar.get_y() + bar.get_height() / 2,
                        f'{width}%',
                        ha='left', va='center',
                        fontsize=12)
            st.pyplot(fig)
        
        st.markdown("---")
        
        st.header("📜 상세 성격 분석")

        r_index = get_description_index(percentages.get('R', 0))
        g_index = get_description_index(percentages.get('G', 0))
        b_index = get_description_index(percentages.get('B', 0))

        st.markdown("### 🔴 진취형(R)에 대하여")
        st.info(description_blocks['R'][r_index])

        st.markdown("### 🟢 중재형(G)에 대하여")
        st.success(description_blocks['G'][g_index])
        
        st.markdown("### 🔵 신중형(B)에 대하여")
        st.warning(description_blocks['B'][b_index])

        if st.button("다시 검사하기"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
