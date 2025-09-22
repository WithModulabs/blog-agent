import json

import streamlit as st
from typing import List, TypedDict

from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_tavily import TavilySearch
from langgraph.graph import StateGraph, END
from openai import OpenAI

from tools import get_llm, scrape_web_content, generate_image_with_gemini


class AgentState(TypedDict):
    url: str
    scraped_content: str
    seo_analysis: str
    seo_tags: List[str]
    draft_post: str
    final_title: str
    final_subheadings: List[str]
    naver_seo_subtitles: List[str]
    image_prompt: str
    image_url: str
    blog_index: int
    blog_details: str
    subtitle_image_prompts: List[str]
    subtitle_image_urls: List[str]
    image_keywords: List[str]
    needs_rewrite: bool
    rewrite_reason: str
    rewrite_count: int  # 재작성 횟수 추가
    messages: List[BaseMessage]


def researcher_node(state: AgentState):
    st.write("▶️ 리서처 에이전트: URL 콘텐츠 분석 시작...")
    url = state['url']
    title, text = scrape_web_content(url)
    scraped_content = (title or "") + (text or "")
    failure_keywords = ["오류 발생", "추출할 수 없습니다", "스크랩이 금지된 글"] 
    if any(k in scraped_content for k in failure_keywords):
        st.error(f"⚠️ {scraped_content}")
        return {"scraped_content": f"분석 실패: {scraped_content}"}
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
        tavily = TavilySearch(max_results=3, tavily_api_key=tavily_api_key)
        results = tavily.invoke({"query": search_query})
        seo_trends = ""
        if results and "results" in results:
            for r in results["results"]:
                seo_trends += f"제목: {r.get('title','')}\n내용: {r.get('content','')}\n\n"
        else:
            seo_trends = "검색 결과를 찾을 수 없습니다."
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
         "**분석할 원본 콘텐츠:**\n{scraped_content}")
    ])

    llm = get_llm()
    if llm is None:
        return {"scraping_status": "Failure", "seo_analysis": "LLM 없음", "seo_tags": []}

    chain = prompt | llm
    resp = chain.invoke({"seo_trends": seo_trends, "scraped_content": scraped_content[:4000]})
    analysis_text = resp.content
    try:
        tags_part = analysis_text.split("[추천 태그]")[1].strip()
        tags = [t.strip() for t in tags_part.split(",") if t.strip()]
    except IndexError:
        tags = []

    st.success("✅ SEO 전문가 에이전트: 전략 분석 및 태그 생성 완료!")
    return {"seo_analysis": analysis_text, "seo_tags": tags}


def writer_node(state: AgentState):
    # 재작성 여부 확인
    is_rewrite = state.get("needs_rewrite", False)
    rewrite_count = state.get("rewrite_count", 0)
    
    if is_rewrite:
        st.write(f"▶️ 작성가 에이전트: 블로그 포스트 재작성 중... ({rewrite_count + 1}회차)")
    else:
        st.write("▶️ 작성가 에이전트: 블로그 포스트 초안 작성 중...")
    
    scraped_content = state['scraped_content']
    seo_analysis = state['seo_analysis']
    rewrite_reason = state.get('rewrite_reason', '')

    title_prompt = ChatPromptTemplate.from_template(
        "주어진 SEO 분석과 원본 콘텐츠를 바탕으로, 네이버 검색에 최적화된 매력적인 블로그 제목 1개만 생성해주세요. (추가 설명 없이 제목만 출력)\n\n"
        "**SEO 분석:**\n{seo_analysis}\n\n"
        "**원본 콘텐츠:**\n{scraped_content}"
    )
    llm = get_llm()
    if llm is None:
        return {"draft_post": "LLM 없음", "final_title": "", "final_subheadings": [], "naver_seo_subtitles": []}

    title_chain = title_prompt | llm
    main_title = title_chain.invoke({
        "seo_analysis": seo_analysis,
        "scraped_content": scraped_content[:2000]
    }).content.strip().replace('"', '')

    subtitle_prompt = ChatPromptTemplate.from_template(
        """다음 블로그 제목과 SEO 분석을 바탕으로, 네이버 블로그 SEO에 최적화된 부제목 5개를 생성해주세요.
        
        **네이버 블로그 부제목 작성 가이드:**
        - 검색 키워드 자연스러운 포함
        - 클릭을 유도하는 문구
        - 숫자/시간 표현 활용
        - 감정적/호기심 유발 요소
        - 20-30자 내외
        - 서로 다른 관점

        각 부제목은 한 줄씩 번호 없이 출력하세요.
        
        **메인 제목:** {main_title}
        
        **SEO 분석:**
        {seo_analysis}"""
    )
    subtitle_chain = subtitle_prompt | llm
    subtitle_resp = subtitle_chain.invoke({"main_title": main_title, "seo_analysis": seo_analysis}).content
    naver_seo_subtitles = [ln.strip() for ln in subtitle_resp.split("\n") if ln.strip() and not ln.strip().startswith("**")]

    # 재작성일 경우 개선사항을 반영한 프롬프트 사용
    if is_rewrite and rewrite_reason:
        draft_prompt = ChatPromptTemplate.from_messages([
            ("system", 
             """당신은 전문 블로그 작가입니다. 이전에 작성한 블로그 포스트의 품질이 낮아서 재작성을 진행합니다. 60점 이상의 점수를 받도록 글을 재작성해주세요.
             
             다음 개선사항들을 반영하여 고품질의 네이버 블로그 포스트를 마크다운 형식으로 작성해주세요:
             - 이모지를 적절히 활용하여 친근한 어조 유지
             - 서론, 본론(소제목 ## 사용), 결론으로 구성
             - 독자 공감 포인트와 실제 경험담 포함
             - 검색 최적화를 위한 키워드 자연스럽게 배치
             - 목록과 번호를 활용하여 가독성 강화
             - CTA(Call to Action) 삽입하여 독자 참여 유도
             
             **개선해야 할 부분:**
             {rewrite_reason}"""),
            ("human", "**제목:** {main_title}\n\n**SEO 분석:**\n{seo_analysis}\n\n**원본 콘텐츠:**\n{scraped_content}")
        ])
    else:
        draft_prompt = ChatPromptTemplate.from_messages([
            ("system", "당신은 전문 블로그 작가입니다. 주어진 제목, SEO 분석, 원본 콘텐츠를 바탕으로 이모지를 활용하여 친근한 어조의 매력적인 네이버 블로그 포스트를 마크다운 형식으로 작성해주세요. 내용은 서론, 본론(소제목 ## 사용), 결론으로 구성해주세요."),
            ("human", "**제목:** {main_title}\n\n**SEO 분석:**\n{seo_analysis}\n\n**원본 콘텐츠:**\n{scraped_content}")
        ])

    draft_chain = draft_prompt | llm
    draft_context = {
        "main_title": main_title,
        "seo_analysis": seo_analysis,
        "scraped_content": scraped_content[:4000]
    }
    if is_rewrite and rewrite_reason:
        draft_context["rewrite_reason"] = rewrite_reason

    draft_post = draft_chain.invoke(draft_context).content

    subheadings = [ln.replace("## ", "").strip() for ln in draft_post.split("\n") if ln.startswith("## ")]

    # 재작성 상태 업데이트
    result = {
        "draft_post": draft_post,
        "final_title": main_title,
        "final_subheadings": subheadings,
        "naver_seo_subtitles": naver_seo_subtitles,
        "needs_rewrite": False,  # 재작성 플래그 초기화
        "rewrite_reason": ""  # 재작성 이유 초기화
    }
    
    if is_rewrite:
        result["rewrite_count"] = rewrite_count + 1
        st.success("✅ 작성가 에이전트: 포스트 재작성 완료!")
    else:
        result["rewrite_count"] = 0
        st.success("✅ 작성가 에이전트: 포스트 초안 작성 완료!")
    
    return result


def blog_indexer_node(state: AgentState):
    """블로그 지수를 계산하는 에이전트"""
    st.write("▶️ 블로그 지수 에이전트")
    st.success("✅ 블로그 지수 계산 중...")

    draft_post = state["draft_post"]

    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 블로그 콘텐츠 전문가입니다. 주어진 블로그 게시물을 분석하여 블로그 지수(Blog Index)를 계산해주세요.

다음 10개 항목을 각각 0-10점으로 평가하여 총 100점 만점으로 채점하고, 각 항목별 평가 근거와 개선점을 제시해주세요.

## 평가 기준

### 1. 검색 최적화 제목 작성 
- 핵심 키워드가 앞부분에 위치하는가? 
- 숫자, 시간, 지역명을 활용했는가? 
- 클릭을 유도하는 감정 단어가 포함되어 있는가? 

### 2. 첫 문단에서 핵심 요약 
- 3줄 이내에 글 전체를 이해할 수 있도록 정리되었는가? 
- 질문형으로 시작하여 호기심을 자극하는가? 

### 3. 독자 공감 포인트 확보 
- 실제 사례, 경험담, 에피소드가 포함되어 있는가? 
- "저도 처음엔 몰랐는데…" 같은 톤으로 신뢰감을 형성하는가? 

### 4. 본문 구조화 
- 소제목에 키워드가 포함되어 있는가? 
- 목록/번호를 활용하여 가독성을 강화했는가? 
- 긴 문장을 2~3줄로 끊어 썼는가? 

### 5. 꾸준한 구독자 유입을 위한 시리즈화 
- 단발성이 아닌 연재 시리즈로 구성되었는가? 
- 예: "초보자를 위한 ○○ 1편", "실전 응용 2편"

### 6. 내부 링크 & 외부 링크 전략 
- 블로그 내 다른 글로 자연스럽게 연결되어 있는가? 
- 신뢰할 수 있는 외부 출처 1~2개 인용

### 7. 이미지 활용법 
- 글당 최소 3장 이상의 이미지를 사용했는가? 
- 핵심 키워드를 포함한 그림 파일명을 작성했는가? 
- ALT 텍스트에 설명을 추가했는가? 

### 8. CTA(Call To Action) 삽입 
- 공감/구독/이웃추가를 유도하는 문구가 있는가? 
- 댓글을 유도하는 질문이 포함되어 있는가? 

### 9. 메타데이터와 태그 최적화 
- 글의 카테고리, 해시태그가 키워드와 일치하는가? 
- 불필요한 태그 남발은 피하고 핵심 키워드 3~5개만 집중하여 태그를 설정했는가?

### 10. 콘텐츠 차별화 요소 추가 
- 직접 촬영한 사진, 인포그래픽, 표, 차트를 활용했는가? 
- 단순 요약형이 아닌 경험+인사이트를 담아 독창성을 강화했는가? 

## 출력 형식
다음 형식으로 출력해주세요:

평가 기준 1: [점수]/10 - [평가 이유]
평가 기준 2: [점수]/10 - [평가 이유]
...
평가 기준 10: [점수]/10 - [평가 이유]
총점: [총점]/100

위의 평가 기준에 따라 주어진 블로그 게시물을 분석하고, 각 항목별로 상세한 평가를 제공해주세요."""),
        ("human", "다음 블로그 게시물의 블로그 지수를 분석해주세요:\n\n{draft_post}")
    ])

    llm = get_llm()
    if llm is None:
        return {"blog_index": 0, "blog_details": "LLM 초기화 실패"}

    try:
        chain = prompt | llm
        response = chain.invoke({"draft_post": draft_post})
        
        content = response.content
        
        # 총점 추출
        total_score = 0
        if "총점:" in content:
            total_part = content.split("총점:")[1].split("/")[0].strip()
            try:
                total_score = int(total_part)
            except:
                total_score = 0

        st.success(f"✅ 블로그 지수 계산 완료. {total_score}점")
        return {
            "blog_index": total_score,
            "blog_details": content
        }

    except Exception as e:
        st.error(f"❌ 블로그 지수 계산에 실패했습니다: {e}")
        return {"blog_index": 0, "blog_details": f"계산 실패: {str(e)}"}


def art_director_node(state: AgentState):
    st.write("▶️ 아트 디렉터 에이전트: 이미지 생성 중...")
    title = state['final_title']
    subtitles = state.get('naver_seo_subtitles', [])
    image_model_provider = st.session_state.get("image_model_provider", "DALL·E 3")

    # 모델별 API 키 확인
    if image_model_provider == "DALL·E 3" and not st.session_state.get("openai_api_key"):
        st.warning("⚠️ DALL·E 3 이미지 생성을 위해서는 OpenAI API Key가 필요합니다.")
        return {"image_prompt": "", "image_url": "", "subtitle_image_prompts": [], "subtitle_image_urls": [], "image_keywords": []}
    elif image_model_provider == "Gemini 2.5 Flash Image" and not st.session_state.get("gemini_api_key"):
        st.warning("⚠️ Gemini 이미지 생성을 위해서는 Google API Key가 필요합니다.")
        return {"image_prompt": "", "image_url": "", "subtitle_image_prompts": [], "subtitle_image_urls": [], "image_keywords": []}

    prompt_llm = get_llm()
    if prompt_llm is None:
        return {"image_prompt": "", "image_url": "", "subtitle_image_prompts": [], "subtitle_image_urls": [], "image_keywords": []}

    keyword_t = ChatPromptTemplate.from_template(
        "다음 블로그 제목에서 핵심 키워드 2개를 추출해주세요. 언더스코어(_)로 연결해서 출력하세요.\n예: '맛집_후기' 또는 '여행_팁'\n제목: {title}"
    )
    kw_chain = keyword_t | prompt_llm
    kw_resp = kw_chain.invoke({"title": title}).content.strip()
    image_keywords = [k.strip() for k in kw_resp.split("_")[:2]]

    try:
        st.write("  📸 메인 이미지 생성 중...")
        main_t = ChatPromptTemplate.from_template("블로그 제목 '{title}'에 어울리는 이미지 생성용 영어 프롬프트를 한 문장으로 만들어줘.")
        main_chain = main_t | prompt_llm
        main_prompt = main_chain.invoke({"title": title}).content

        # 이미지 생성 (모델별 분기)
        main_url = ""
        if image_model_provider == "DALL·E 3":
            client = OpenAI(api_key=st.session_state.get("openai_api_key"))
            main_res = client.images.generate(model="dall-e-3", prompt=main_prompt, size="1024x1024", quality="standard", n=1)
            main_url = main_res.data[0].url

        st.write("  🎨 부제목 기반 이미지 3개 생성 중...")
        sub_prompts, sub_urls = [], []
        for i, sub in enumerate(subtitles[:3], 1):
            st.write(f"    • 이미지 {i+1} 생성 중...")
            sub_t = ChatPromptTemplate.from_template("블로그 부제목 '{subtitle}'에 어울리는 이미지 생성용 영어 프롬프트를 한 문장으로 만들어줘.")
            sub_chain = sub_t | prompt_llm
            sub_prompt = sub_chain.invoke({"subtitle": sub}).content
            sub_prompts.append(sub_prompt)
            
            # 부제목 이미지 생성 (모델별 분기)
            sub_url = ""
            if image_model_provider == "DALL·E 3":
                sub_res = client.images.generate(model="dall-e-3", prompt=sub_prompt, size="1024x1024", quality="standard", n=1)
                sub_url = sub_res.data[0].url
            
            sub_urls.append(sub_url)

        generated_count = sum(1 for url in [main_url] + sub_urls if url)
        st.success(f"✅ 아트 디렉터 에이전트: {generated_count}개 이미지 생성 완료!")
        return {
            "image_prompt": main_prompt,
            "image_url": main_url,
            "subtitle_image_prompts": sub_prompts,
            "subtitle_image_urls": sub_urls,
            "image_keywords": image_keywords
        }

    except Exception as e:
        st.error(f"이미지 생성 실패: {e}")
        return {
            "image_prompt": locals().get("main_prompt", ""),
            "image_url": "",
            "subtitle_image_prompts": [],
            "subtitle_image_urls": [],
            "image_keywords": image_keywords
        }


def should_continue_from_researcher(state: AgentState):
    """리서처 노드 이후 분기"""
    if "분석 실패:" in state.get('scraped_content', ''):
        return "end_process"
    else:
        return "continue_to_seo"


def should_continue_from_indexer(state: AgentState):
    """블로그 지수 노드 이후 분기"""
    blog_index = state.get("blog_index", 0)
    rewrite_count = state.get("rewrite_count", 0)
    
    # 재작성 요청이 있고, 재작성 횟수가 2회 미만이고, 점수가 60점 이하인 경우
    if (state.get("needs_rewrite", False) and 
        rewrite_count < 2 and  # 최대 2회까지만 재작성
        blog_index <= 60):
        return "rewrite_post"
    
    # 그 외의 경우는 아트 디렉터로 진행
    return "continue_to_art"


def build_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("seo_specialist", seo_specialist_node)
    workflow.add_node("writer", writer_node)
    workflow.add_node("art_director", art_director_node)
    workflow.add_node("blog_indexer", blog_indexer_node)
    
    workflow.set_entry_point("researcher")
    
    # 리서처 이후 조건부 분기
    workflow.add_conditional_edges(
        "researcher",
        should_continue_from_researcher,
        {"continue_to_seo": "seo_specialist", "end_process": END}
    )
    
    workflow.add_edge("seo_specialist", "writer")
    workflow.add_edge("writer", "blog_indexer")
    
    # 블로그 지수 이후 조건부 분기 - 재작성 시 writer로 돌아가고, 아니면 art_director로
    workflow.add_conditional_edges(
        "blog_indexer",
        should_continue_from_indexer,
        {
            "rewrite_post": "writer",  # 재작성 시 writer로 돌아가기
            "continue_to_art": "art_director"  # 정상 진행 시 art_director로
        }
    )
    
    workflow.add_edge("art_director", END)
    
    return workflow.compile()