import streamlit as st
import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from typing import List, TypedDict

from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.graph import StateGraph, END

# --- 1. 환경 설정 ---
# .env 파일에서 API 키 로드
load_dotenv()

# LangSmith 추적 설정 (선택 사항) - 비활성화
# os.environ["LANGCHAIN_TRACING_V2"] = "true"
# os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")
# os.environ["LANGCHAIN_PROJECT"] = "Multi-Agent Blog Generator"

# --- 2. 도구 정의 ---
# Tavily를 사용한 웹 검색 도구
tavily_tool = TavilySearchResults(max_results=5)

# URL 콘텐츠 스크래핑 도구
def scrape_web_content(url: str) -> str:
    """지정된 URL의 웹 콘텐츠를 스크래핑하여 텍스트를 반환합니다."""
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()  # HTTP 오류 발생 시 예외 발생
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 본문 콘텐츠 위주로 추출 (article, main 태그 등)
        main_content = soup.find('main') or soup.find('article') or soup.body
        if main_content:
            # 불필요한 태그 제거 (nav, footer, script, style 등)
            for tag in main_content(['nav', 'footer', 'script', 'style', 'aside', 'form']):
                tag.decompose()
            text = main_content.get_text(separator='\n', strip=True)
            return text
        return "콘텐츠를 추출할 수 없습니다."
    except requests.RequestException as e:
        return f"URL 요청 중 오류 발생: {e}"
    except Exception as e:
        return f"콘텐츠 스크래핑 중 오류 발생: {e}"

# --- 3. 에이전트 상태 정의 ---
class AgentState(TypedDict):
    url: str
    scraped_content: str
    seo_analysis: str
    seo_tags: List[str]
    draft_post: str
    final_title: str
    final_subheadings: List[str]
    final_post: str
    image_prompt: str
    image_url: str
    messages: List[BaseMessage]

# --- 4. 에이전트 및 노드 정의 ---
# LLM 모델 초기화
llm = ChatOpenAI(model="gpt-5", temperature=0.7)

# 4.1. 리서처 에이전트 (URL 스크래핑)
def researcher_node(state: AgentState):
    """
    입력된 URL의 콘텐츠를 스크래핑하여 다음 단계로 전달합니다.
    """
    st.write("▶️ 리서처 에이전트: URL 콘텐츠 분석 시작...")
    url = state['url']
    scraped_content = scrape_web_content(url)
    
    if "오류 발생" in scraped_content or "추출할 수 없습니다" in scraped_content:
        st.error(f"콘텐츠를 가져오는 데 실패했습니다: {scraped_content}")
        return {
            "scraped_content": f"분석 실패: {scraped_content}",
            "messages": [HumanMessage(content=f"URL 스크래핑 실패: {url}")]
        }
        
    st.success("✅ 리서처 에이전트: 콘텐츠 분석 완료!")
    return {
        "scraped_content": scraped_content,
        "messages": [HumanMessage(content=f"URL '{url}'의 콘텐츠 분석 완료.")]
    }

# 4.2. SEO 전문가 에이전트
def seo_specialist_node(state: AgentState):
    """
    스크랩된 콘텐츠를 기반으로 네이버 SEO 전략을 분석하고 태그를 생성합니다.
    """
    st.write("▶️ SEO 전문가 에이전트: 네이버 SEO 전략 분석 중...")
    scraped_content = state['scraped_content']
    
    # 네이버 SEO 트렌드 검색
    search_query = "2025년 네이버 블로그 SEO 최적화 전략"
    seo_trends = tavily_tool.invoke({"query": search_query})

    prompt = ChatPromptTemplate.from_messages([
        ("system", 
         """당신은 15년 경력의 네이버 블로그 SEO 전문가입니다. 
         당신의 목표는 주어진 원본 콘텐츠와 최신 SEO 트렌드 정보를 바탕으로, 네이버 검색에 최적화된 블로그 포스트 전략을 수립하는 것입니다.
         
         지침:
         1. 원본 콘텐츠의 핵심 주제와 주요 키워드를 파악합니다.
         2. 최신 네이버 SEO 트렌드를 참고하여, 어떤 키워드와 주제를 강조해야 할지 결정합니다.
         3. 사용자들이 검색할 만한 매력적이고 구체적인 롱테일 키워드를 포함한 제목과 소제목 아이디어를 제안합니다.
         4. 네이버 블로그에 사용될 SEO에 가장 효과적인 태그 30개를 정확히 추출하여 리스트 형태로 제공합니다.
         5. 모든 결과물은 한국어로 작성해야 합니다.
         
         결과는 다음 형식으로 정리해주세요:
         
         [분석 및 전략]
         - (여기에 콘텐츠를 기반으로 한 SEO 전략과 키워드 분석 내용을 서술)
         
         [추천 태그]
         태그1, 태그2, 태그3, 태그4, 태그5, 태그6, 태그7, 태그8, 태그9, 태그10,
         태그11, 태그12, 태그13, 태그14, 태그15, 태그16, 태그17, 태그18, 태그19, 태그20,
         태그21, 태그22, 태그23, 태그24, 태그25, 태그26, 태그27, 태그28, 태그29, 태그30,
         """),
        ("human", 
         "**최신 네이버 SEO 트렌드:**\n{seo_trends}\n\n"
         "**분석할 원본 콘텐츠:**\n{scraped_content}"),
    ])
    
    chain = prompt | llm
    # Pass variables to the prompt template
    response = chain.invoke({
        "seo_trends": seo_trends,
        "scraped_content": scraped_content[:4000]
    })
    
    # 결과 파싱
    analysis_text = response.content
    tags_part = analysis_text.split("[추천 태그]")[1].strip()
    tags = [tag.strip() for tag in tags_part.split(", ")]
    
    st.success("✅ SEO 전문가 에이전트: 전략 분석 및 태그 생성 완료!")
    return {
        "seo_analysis": analysis_text,
        "seo_tags": tags
    }

# 4.3. 작성가 에이전트
def writer_node(state: AgentState):
    """
    SEO 분석 결과를 바탕으로 실제 블로그 포스트 초안을 작성합니다.
    """
    st.write("▶️ 작성가 에이전트: 블로그 포스트 초안 작성 중...")
    scraped_content = state['scraped_content']
    seo_analysis = state['seo_analysis']
    
    # 1개의 추천 제목을 생성
    title_prompt = ChatPromptTemplate.from_messages([
        ("system", 
         """당신은 네이버 블로그 SEO 전문가입니다. 주어진 콘텐츠와 SEO 분석을 바탕으로 클릭을 유도하는 매력적인 제목을 만드는 것이 임무입니다.
         
         요구사항:
         - SEO 키워드를 자연스럽게 포함
         - 호기심을 자극하는 표현 사용
         - 네이버 검색에 최적화된 길이 (30-40자)
         - 매력적이고 클릭률이 높은 하나의 제목 제안
         
         결과는 제목만 출력하세요 (추가 설명 없이).
         """),
        ("human", 
         "**SEO 전문가 분석 및 전략:**\n{seo_analysis}\n\n"
         "**참고할 원본 콘텐츠:**\n{scraped_content}"),
    ])
    
    title_chain = title_prompt | llm
    main_title = title_chain.invoke({
        "seo_analysis": seo_analysis,
        "scraped_content": scraped_content[:4000]
    }).content.strip()
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", 
         """당신은 사람들의 시선을 사로잡는 글을 쓰는 전문 블로그 작가입니다. 네이버 블로그 플랫폼의 특성을 잘 이해하고 있습니다.
         당신의 임무는 주어진 제목과 SEO 전문가의 분석 자료를 바탕으로, 독자들이 쉽게 읽고 공감할 수 있는 매력적인 블로그 포스트를 마크다운 형식으로 작성하는 것입니다.
         
         작성 가이드라인:
         1. **제목:** 주어진 제목을 `#`으로 시작하여 사용하세요.
         2. **소개:** 독자의 흥미를 유발하고 글을 계속 읽고 싶게 만드는 도입부를 작성하세요.
         3. **본문:** SEO 전문가가 제안한 소제목 아이디어를 활용하여 여러 개의 소제목(`##`)으로 문단을 나누세요. 각 문단은 원본 콘텐츠의 내용을 바탕으로 하되, 더 친근하고 이해하기 쉬운 문체로 재구성합니다. 이모지를 적절히 사용하여 가독성을 높여주세요.
         4. **결론:** 글의 내용을 요약하고, 독자에게 행동을 유도하거나 긍정적인 메시지를 전달하며 마무리하세요.
         5. **스타일:** 전체적으로 친근하고 대화하는 듯한 톤앤매너를 유지하고, 각 토픽은 500자 이상 1000자 이하로 작성해주새요
         """),
        ("human", 
         "**사용할 제목:**\n{title}\n\n"
         "**SEO 전문가 분석 및 전략:**\n{seo_analysis}\n\n"
         "**참고할 원본 콘텐츠:**\n{scraped_content}"),
    ])
    
    chain = prompt | llm
    draft_post = chain.invoke({
        "title": main_title,
        "seo_analysis": seo_analysis,
        "scraped_content": scraped_content[:4000]
    }).content
    
    # 소제목 추출 (기존 로직 유지)
    lines = draft_post.split('\n')
    subheadings = []
    for line in lines:
        if line.startswith('## '):
            subheadings.append(line.replace('## ', '').strip())
            
    st.success("✅ 작성가 에이전트: 포스트 초안 작성 완료!")
    return {
        "draft_post": draft_post,
        "final_title": main_title,
        "final_subheadings": subheadings
    }

# 4.4. 아트 디렉터 에이전트
def art_director_node(state: AgentState):
    """
    블로그 제목과 내용을 기반으로 DALL-E를 사용하여 이미지를 생성합니다.
    """
    st.write("▶️ 아트 디렉터 에이전트: 대표 이미지 생성 중...")
    title = state['final_title']
    draft_post = state['draft_post']

    # DALL-E 프롬프트 생성
    prompt_generator_llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", "당신은 창의적인 아트 디렉터입니다. 블로그 포스트의 제목과 내용을 바탕으로, DALL-E 3가 이미지를 생성할 수 있는 가장 효과적이고 상세한 영어 프롬프트를 한 문장으로 생성해야 합니다."),
        ("human", f"블로그 제목: {title}\n\n블로그 내용 요약:\n{draft_post[:500]}\n\n위 내용을 대표할 수 있는 이미지 프롬프트를 영어로 만들어주세요.")
    ])
    
    chain = prompt_template | prompt_generator_llm
    # No variables needed since we use f-strings in the template
    image_prompt = chain.invoke({}).content

    # 이미지 생성 클라이언트
    from openai import OpenAI
    client = OpenAI()

    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=image_prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        image_url = response.data[0].url
        st.success("✅ 아트 디렉터 에이전트: 이미지 생성 완료!")
        return {"image_prompt": image_prompt, "image_url": image_url}
    except Exception as e:
        st.error(f"이미지 생성에 실패했습니다: {e}")
        return {"image_prompt": image_prompt, "image_url": "이미지 생성 실패"}

# --- 5. 그래프 빌드 ---
def build_graph():
    workflow = StateGraph(AgentState)
    
    # 노드 추가
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("seo_specialist", seo_specialist_node)
    workflow.add_node("writer", writer_node)
    workflow.add_node("art_director", art_director_node)
    
    # 엣지 연결 (순차적 실행)
    workflow.set_entry_point("researcher")
    workflow.add_edge("researcher", "seo_specialist")
    workflow.add_edge("seo_specialist", "writer")
    workflow.add_edge("writer", "art_director")
    workflow.add_edge("art_director", END)
    
    return workflow.compile()

# --- 6. 스트림릿 UI ---
def main():
    st.set_page_config(page_title="🤖 네이버 블로그 포스팅 자동 생성기", layout="wide")
    st.title("🤖 네이버 블로그 포스팅 자동 생성기")
    st.markdown("""
    **참고할 기사나 블로그 글의 URL을 입력**하면, AI 에이전트들이 협력하여 **네이버 SEO에 최적화된 블로그 포스트**를 자동으로 만들어 드립니다. 
    이 도구는 **콘텐츠 제작 시간을 단축**하고 **검색 노출을 증대**시키는 것을 목표로 합니다.
    """)

    url = st.text_input("분석할 기사 또는 블로그 URL을 입력하세요:", placeholder="https://...")

    if st.button("🚀 블로그 글 생성 시작!"):
        if not url:
            st.warning("URL을 입력해주세요.")
            return

        with st.spinner("AI 멀티에이전트가 작업을 시작합니다... 잠시만 기다려주세요."):
            app = build_graph()
            
            # 초기 상태 설정
            initial_state = {"url": url, "messages": []}
            
            # 그래프 실행
            final_state = app.invoke(initial_state)

        st.divider()
        st.header("✨ 최종 결과물 ✨")

        # 1. 생성된 이미지 표시
        if final_state.get("image_url") and final_state["image_url"] != "이미지 생성 실패":
            st.image(final_state["image_url"], caption=f"DALL-E Prompt: {final_state.get('image_prompt', 'N/A')}")
        else:
            st.warning("대표 이미지를 생성하지 못했습니다.")

        # 2. 추천 제목 및 태그 표시
        st.subheader("📝 추천 제목")
        st.code(final_state.get('final_title', '제목 생성 실패'), language=None)

        st.subheader("🔖 추천 태그 (복사해서 사용하세요)")
        tags_str = ", ".join([f"#{tag}" for tag in final_state.get('seo_tags', [])])
        st.code(tags_str, language=None)
        
        # 3. 완성된 블로그 글 표시
        st.subheader("✍️ 완성된 블로그 포스트 (마크다운)")
        st.markdown(final_state.get('draft_post', '포스트 생성 실패'))

        # 4. 상세 분석 내용 (디버깅/참고용)
        with st.expander("🤖 에이전트 작업 상세 내용 보기"):
            st.write("**SEO 전문가 분석:**")
            st.text(final_state.get('seo_analysis', '분석 내용 없음'))

if __name__ == "__main__":
    main()