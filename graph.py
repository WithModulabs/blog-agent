import streamlit as st
from typing import List, TypedDict

from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.graph import StateGraph, END
from openai import OpenAI

# tools.py에서 함수 임포트
from tools import get_llm, scrape_web_content

# --- 에이전트 상태 정의 ---
class AgentState(TypedDict):
    url: str
    scraped_content: str
    seo_analysis: str
    seo_tags: List[str]
    draft_post: str
    final_title: str
    final_subheadings: List[str]
    image_prompt: str
    image_url: str
    messages: List[BaseMessage]

# --- 에이전트 및 노드 정의 ---
def researcher_node(state: AgentState):
    st.write("▶️ 리서처 에이전트: URL 콘텐츠 분석 시작...")
    url = state['url']
    scraped_content = scrape_web_content(url)
    
    failure_keywords = ["오류 발생", "추출할 수 없습니다", "스크랩이 금지된 글"] 
    
    if any(keyword in scraped_content for keyword in failure_keywords):
        st.error(f"⚠️ {scraped_content}")
        return {
            "scraped_content": f"분석 실패: {scraped_content}",
        }
        
    st.success("✅ 리서처 에이전트: 콘텐츠 분석 완료!")
    return {
        "scraped_content": scraped_content,
        "messages": [HumanMessage(content=f"URL '{url}'의 콘텐츠 분석 완료.")]
    }

def seo_specialist_node(state: AgentState):
    st.write("▶️ SEO 전문가 에이전트: 네이버 SEO 전략 분석 중...")
    scraped_content = state['scraped_content']
    search_query = "2025년 네이버 블로그 SEO 최적화 전략"
    tavily_api_key = st.session_state.get("tavily_api_key")

    if not tavily_api_key:
        st.error("❌ Tavily API Key가 설정되어 있지 않습니다.")
        return {"scraping_status": "Failure", "seo_analysis": "Tavily API Key 없음", "seo_tags": []}

    try:
        tavily_tool = TavilySearchResults(max_results=3, tavily_api_key=tavily_api_key)
        seo_trends = tavily_tool.invoke({"query": search_query})
    except Exception as e:
        st.error(f"Tavily 검색 오류: {e}")
        seo_trends = ""

    prompt = ChatPromptTemplate.from_messages([
         ("system", 
         """당신은 15년 경력의 네이버 블로그 SEO 전문가입니다. 
         주어진 원본 콘텐츠와 최신 SEO 트렌드 정보를 바탕으로, 네이버 검색에 최적화된 블로그 포스트 전략을 수립해야 합니다.
         결과는 다음 형식으로 정리해주세요:
         [분석 및 전략]
         - (여기에 콘텐츠 기반 SEO 전략과 키워드 분석 내용을 서술)
         
         [추천 태그]
         태그1, 태그2, 태그3, ... (쉼표로 구분된 30개의 태그)"""),
        ("human", 
         "**최신 네이버 SEO 트렌드:**\n{seo_trends}\n\n"
         "**분석할 원본 콘텐츠:**\n{scraped_content}"),
    ])
    
    llm = get_llm()
    if llm is None:
        return {"scraping_status": "Failure", "seo_analysis": "LLM 없음", "seo_tags": []}

    chain = prompt | llm
    response = chain.invoke({
        "seo_trends": seo_trends,
        "scraped_content": scraped_content[:4000]
    })
    
    analysis_text = response.content
    try:
        tags_part = analysis_text.split("[추천 태그]")[1].strip()
        tags = [tag.strip() for tag in tags_part.split(",") if tag.strip()]
    except IndexError:
        tags = []
    
    st.success("✅ SEO 전문가 에이전트: 전략 분석 및 태그 생성 완료!")
    return {"seo_analysis": analysis_text, "seo_tags": tags}

def writer_node(state: AgentState):
    st.write("▶️ 작성가 에이전트: 블로그 포스트 초안 작성 중...")
    scraped_content = state['scraped_content']
    seo_analysis = state['seo_analysis']
    
    title_prompt = ChatPromptTemplate.from_template(
        "주어진 SEO 분석과 원본 콘텐츠를 바탕으로, 네이버 검색에 최적화된 매력적인 블로그 제목 1개만 생성해주세요. (추가 설명 없이 제목만 출력)\n\n"
        "**SEO 분석:**\n{seo_analysis}\n\n"
        "**원본 콘텐츠:**\n{scraped_content}"
    )
    
    llm = get_llm()
    if llm is None:
        return {"draft_post": "LLM 없음", "final_title": "", "final_subheadings": []}

    title_chain = title_prompt | llm
    main_title = title_chain.invoke({
        "seo_analysis": seo_analysis,
        "scraped_content": scraped_content[:2000]
    }).content.strip().replace('"', '')

    draft_prompt = ChatPromptTemplate.from_messages([
        ("system", "당신은 전문 블로그 작가입니다. 주어진 제목, SEO 분석, 원본 콘텐츠를 바탕으로 이모지를 활용하여 친근한 어조의 매력적인 네이버 블로그 포스트를 마크다운 형식으로 작성해주세요. 내용은 서론, 본론(소제목 ## 사용), 결론으로 구성해주세요."),
        ("human", f"**제목:** {main_title}\n\n**SEO 분석:**\n{seo_analysis}\n\n**원본 콘텐츠:**\n{scraped_content[:4000]}"),
    ])
    
    draft_chain = draft_prompt | llm
    draft_post = draft_chain.invoke({}).content
    
    subheadings = [line.replace('## ', '').strip() for line in draft_post.split('\n') if line.startswith('## ')]
            
    st.success("✅ 작성가 에이전트: 포스트 초안 작성 완료!")
    return {"draft_post": draft_post, "final_title": main_title, "final_subheadings": subheadings}

def art_director_node(state: AgentState):
    st.write("▶️ 아트 디렉터 에이전트: 대표 이미지 생성 중...")
    title = state['final_title']
    
    # 이미지 생성을 위해서는 OpenAI 키가 반드시 필요
    if not st.session_state.get("openai_api_key"):
        st.warning("⚠️ 이미지 생성(DALL-E)을 위해서는 OpenAI API Key가 필요합니다.")
        return {"image_prompt": "", "image_url": ""}

    # 이미지 프롬프트 생성은 사용자가 선택한 LLM 사용
    prompt_generator_llm = get_llm()
    if prompt_generator_llm is None:
        return {"image_prompt": "", "image_url": ""}
        
    prompt_template = ChatPromptTemplate.from_template("블로그 제목 '{title}'에 어울리는 DALL-E 3 이미지 생성용 영어 프롬프트를 한 문장으로 만들어줘.")
    chain = prompt_template | prompt_generator_llm
    image_prompt = chain.invoke({"title": title}).content

    try:
        # 이미지 생성은 OpenAI 클라이언트 직접 사용
        client = OpenAI(api_key=st.session_state.get("openai_api_key"))
        response = client.images.generate(
            model="dall-e-3", prompt=image_prompt, size="1024x1024", quality="standard", n=1,
        )
        image_url = response.data[0].url
        st.success("✅ 아트 디렉터 에이전트: 이미지 생성 완료!")
        return {"image_prompt": image_prompt, "image_url": image_url}
    except Exception as e:
        st.error(f"이미지 생성 실패: {e}")
        return {"image_prompt": image_prompt, "image_url": ""}

# --- 그래프 빌드 ---
def should_continue(state: AgentState):
    if "분석 실패:" in state.get('scraped_content', ''):
        return "end_process"
    else:
        return "continue_to_seo"

def build_graph():
    workflow = StateGraph(AgentState)
    
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("seo_specialist", seo_specialist_node)
    workflow.add_node("writer", writer_node)
    workflow.add_node("art_director", art_director_node)
    
    workflow.set_entry_point("researcher")
    workflow.add_conditional_edges(
        "researcher",
        should_continue,
        {"continue_to_seo": "seo_specialist", "end_process": END}
    )
    workflow.add_edge("seo_specialist", "writer")
    workflow.add_edge("writer", "art_director")
    workflow.add_edge("art_director", END)
    
    return workflow.compile()