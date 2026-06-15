import json
import re

import streamlit as st
from anthropic import Anthropic

st.set_page_config(page_title="나의 꿈 신문 - 내용 추천", page_icon="📰", layout="centered")

# ----------------------------------------------------------------------------
# Styling (가볍게 macOS 느낌 살리기)
# ----------------------------------------------------------------------------
st.markdown(
    """
    <style>
      .stApp {
        background: linear-gradient(135deg, #aeccff 0%, #d6c4ff 100%);
      }
      .block-container {
        max-width: 640px;
        background: rgba(255,255,255,0.72);
        backdrop-filter: blur(20px);
        border-radius: 18px;
        padding: 2rem 2rem 2.5rem;
        margin-top: 1.5rem;
        box-shadow: 0 24px 60px rgba(30,30,60,0.15);
      }
      .brand-badge {
        display:inline-block;
        font-weight:700;
        background: rgba(255,255,255,0.85);
        border-radius: 999px;
        padding: 6px 18px;
        margin-bottom: 1rem;
        font-size: 0.9rem;
      }
      .rec-card {
        background: rgba(255,255,255,0.85);
        border-radius: 12px;
        padding: 12px 16px;
        margin-bottom: 10px;
        border: 1px solid rgba(255,255,255,0.6);
      }
      .rec-title { font-weight:700; font-size: 1rem; margin-bottom: 2px; }
      .rec-reason { color:#6e6e73; font-size: 0.9rem; margin-bottom: 6px; }
      .rec-hint {
        display:inline-block;
        background: rgba(10,132,255,0.10);
        border-radius: 8px;
        padding: 6px 10px;
        font-size: 0.85rem;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------------
# Anthropic client
# ----------------------------------------------------------------------------
client = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
MODEL = "claude-sonnet-4-6"


def build_prompt(target: str, topic: str, knowledge: str, interest: str) -> str:
    return f"""중학교 1학년 학생이 '나의 꿈 신문'(자신의 꿈과 관련된 직업을 설명하는 글)을 쓰기 위해 자료를 조사하려고 합니다. 아래 정보를 참고하여 신문에 담을 수 있는 내용 아이디어를 4가지 추천해주세요.

- 설명 대상(꿈과 관련된 직업): {target}
- 글의 주제(말하고 싶은 것): {topic}
- 예상 독자의 배경지식·수준: {knowledge}
- 예상 독자의 관심사·흥미: {interest}

조건:
1. '꿈 소개', '직업 소개', '되는 방법', '대표 인물', '추천 도서나 영화', '미래의 하루를 담은 만화', '다짐'처럼 학생들이 흔히 떠올리는 항목 중 이 학생에게 잘 맞는 것 1~2개와, 독자의 관심사·흥미를 활용한 새롭고 구체적인 아이디어 2~3개를 합쳐 총 4개를 추천해주세요. 흔한 항목이라도 이 학생의 설명 대상·주제·독자에 맞게 구체적으로 다시 표현해주세요.
2. 각 아이디어는 학생이 실제로 자료를 찾을 때 어떤 키워드, 자료 형태(영상/기사/통계/인터뷰/책 등), 어디서 찾으면 좋을지 구체적인 힌트를 포함해야 합니다.
3. 중학생이 이해할 수 있는 쉬운 표현을 쓰고, 최대한 간결하게 작성하세요. title은 8자 이내, reason과 hint는 각각 25자 이내의 짧은 한 문장으로 작성하세요.

다음 JSON 형식으로만, 공백·줄바꿈 없이 간결하게 응답하세요. 다른 설명, 인사말, 마크다운 기호는 절대 포함하지 마세요:
{{"recommendations":[{{"title":"...","reason":"...","hint":"..."}}]}}"""


def parse_recommendations(text: str):
    clean = re.sub(r"```json|```", "", text).strip()

    try:
        parsed = json.loads(clean)
        recs = parsed.get("recommendations")
        if isinstance(recs, list) and recs:
            return recs
    except json.JSONDecodeError:
        pass

    # recover whatever complete {title, reason, hint} objects exist,
    # even if the overall JSON got truncated
    pattern = re.compile(
        r'\{\s*"title"\s*:\s*"((?:[^"\\]|\\.)*)"\s*,\s*"reason"\s*:\s*"((?:[^"\\]|\\.)*)"\s*,\s*"hint"\s*:\s*"((?:[^"\\]|\\.)*)"\s*\}'
    )
    items = []
    for m in pattern.finditer(clean):
        items.append(
            {
                "title": re.sub(r"\\(.)", r"\1", m.group(1)),
                "reason": re.sub(r"\\(.)", r"\1", m.group(2)),
                "hint": re.sub(r"\\(.)", r"\1", m.group(3)),
            }
        )
    return items


def get_recommendations(target: str, topic: str, knowledge: str, interest: str):
    response = client.messages.create(
        model=MODEL,
        max_tokens=1000,
        messages=[{"role": "user", "content": build_prompt(target, topic, knowledge, interest)}],
    )
    text = "".join(block.text for block in response.content if block.type == "text")
    return parse_recommendations(text)


# ----------------------------------------------------------------------------
# UI
# ----------------------------------------------------------------------------
st.markdown('<div class="brand-badge">🍞 빵쌤과 함께하는 국어 수업</div>', unsafe_allow_html=True)
st.title("🔎 어떤 내용을 신문에 담을까?")
st.caption("수행평가지에 적은 내용을 참고해서 입력해보세요. 입력이 끝나면 신문에 담을 만한 내용을 추천해드려요.")

with st.form("plan_form"):
    target = st.text_input("💼 설명 대상 — 나의 꿈과 관련된 직업", placeholder="예) 파티시에")
    topic = st.text_area(
        "✏️ 글의 주제 — 이 글에서 말하고 싶은 것",
        placeholder="예) 파티시에가 되는 방법과 필요한 자격, 하루 일과를 중심으로 소개하고 싶다.",
        height=80,
    )
    knowledge = st.selectbox(
        "📚 예상 독자의 배경지식 · 수준",
        [
            "이 직업에 대해 거의 모른다",
            "이름만 들어봤지 자세히는 모른다",
            "어느 정도 알고 있지만 자세한 정보는 모른다",
            "꽤 잘 알고 있는 편이다",
        ],
    )
    interest = st.text_input(
        "❤️ 예상 독자의 관심사 · 흥미",
        placeholder="예) 먹는 것, 유튜브 영상, 카페 디저트, 손으로 만드는 것",
    )
    submitted = st.form_submit_button("✨ 내용 추천받기", use_container_width=True)

if submitted:
    if not target.strip() or not topic.strip():
        st.error("설명 대상과 글의 주제는 꼭 입력해주세요.")
    else:
        with st.spinner("추천 아이디어를 정리하는 중..."):
            try:
                items = get_recommendations(
                    target.strip(),
                    topic.strip(),
                    knowledge,
                    interest.strip() or "특별히 알려진 것은 없음",
                )
            except Exception:
                items = []

        if not items:
            st.error("추천을 가져오는 데 문제가 생겼어요. 잠시 후 다시 시도해주세요.")
        else:
            st.subheader("이런 내용을 다뤄보면 어떨까요?")
            for item in items:
                st.markdown(
                    f"""
                    <div class="rec-card">
                      <div class="rec-title">{item.get('title','')}</div>
                      <div class="rec-reason">{item.get('reason','')}</div>
                      <div class="rec-hint">🔍 {item.get('hint','')}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

st.caption("💡 추천은 참고용 아이디어예요. 실제 자료는 아이북으로 직접 찾고, 출처를 꼭 확인해서 수행평가지에 정리하세요!")
