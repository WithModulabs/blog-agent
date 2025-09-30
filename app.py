import os
import streamlit as st
from dotenv import load_dotenv, set_key, find_dotenv
from graph import build_graph, revise_with_feedback
import time

# --- 환경 설정 ---
# .env 파일에서 API 키 로드 (가장 먼저 실행되어야 함)
load_dotenv()

# LangSmith 추적 설정 (선택 사항) - 비활성화
# os.environ["LANGCHAIN_TRACING_V2"] = "true"
# os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")
# os.environ["LANGCHAIN_PROJECT"] = "Multi-Agent Blog Generator"

def show_fade_alert(message, alert_type="error"):
    """Fade out 효과가 있는 알람을 표시하는 함수"""
    placeholder = st.empty()
    
    # CSS 스타일 정의
    if alert_type == "error":
        bg_color = "#ffebee"
        border_color = "#f44336"
        text_color = "#c62828"
        icon = "❌"
    elif alert_type == "warning":
        bg_color = "#fff3e0"
        border_color = "#ff9800"
        text_color = "#f57c00"
        icon = "⚠️"
    else:  # info
        bg_color = "#e3f2fd"
        border_color = "#2196f3"
        text_color = "#1976d2"
        icon = "ℹ️"
    
    # 알람 표시
    placeholder.markdown(f"""
        <div id="fade-alert" style="
            background-color: {bg_color};
            border: 2px solid {border_color};
            color: {text_color};
            padding: 16px 20px;
            border-radius: 10px;
            margin: 15px 0;
            font-weight: 600;
            font-size: 16px;
            text-align: center;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            animation: fadeInOut 4.5s ease-in-out;
        ">
            {icon} {message}
        </div>
        <style>
        @keyframes fadeInOut {{
            0% {{ opacity: 0; transform: translateY(-20px) scale(0.95); }}
            15% {{ opacity: 1; transform: translateY(0) scale(1); }}
            85% {{ opacity: 1; transform: translateY(0) scale(1); }}
            100% {{ opacity: 0; transform: translateY(-20px) scale(0.95); }}
        }}
        </style>
    """, unsafe_allow_html=True)
    
    # 4.5초 후 알람 제거
    time.sleep(4.5)
    placeholder.empty()

def check_required_api_keys():
    """선택된 모델에 필요한 API 키가 있는지 확인"""
    model_provider = st.session_state.get("model_provider", "OpenAI")
    image_model_provider = st.session_state.get("image_model_provider", "DALL·E 3")
    
    missing_keys = []
    
    # 텍스트 모델용 API 키 확인
    if model_provider == "OpenAI" and not st.session_state.get("openai_api_key"):
        missing_keys.append("OpenAI API Key")
    elif model_provider == "Gemini" and not st.session_state.get("gemini_api_key"):
        missing_keys.append("Google API Key")
    elif model_provider == "Claude" and not st.session_state.get("anthropic_api_key"):
        missing_keys.append("Anthropic API Key")
    
    # 이미지 모델용 API 키 확인
    if image_model_provider == "DALL·E 3" and not st.session_state.get("openai_api_key"):
        if "OpenAI API Key" not in missing_keys:
            missing_keys.append("OpenAI API Key")
    # Pollinations.ai는 별도 API 키 불필요
    
    # Tavily API 키는 항상 필요
    if not st.session_state.get("tavily_api_key"):
        missing_keys.append("Tavily API Key")
    
    return missing_keys

def main():
    st.set_page_config(page_title="🤖 네이버 블로그 포스팅 자동 생성기", layout="wide", initial_sidebar_state="expanded")

    # 세션 상태 초기화 - .env 파일에서 자동 로드
    if "keys_initialized" not in st.session_state:
        st.session_state.keys_initialized = True
        # .env 파일에서 키 자동 로드
        if openai_key := os.getenv("OPENAI_API_KEY"):
            st.session_state.openai_api_key = openai_key
        if gemini_key := os.getenv("GEMINI_API_KEY"):
            st.session_state.gemini_api_key = gemini_key
        if anthropic_key := os.getenv("ANTHROPIC_API_KEY"):
            st.session_state.anthropic_api_key = anthropic_key
        if tavily_key := os.getenv("TAVILY_API_KEY"):
            st.session_state.tavily_api_key = tavily_key

    # --- 사이드바 UI ---
    with st.sidebar:
        st.header("⚙️ API 및 모델 설정")

        # 모델 선택
        model_provider = st.selectbox(
            "사용할 LLM 모델을 선택하세요",
            ("OpenAI", "Gemini", "Claude"),
            key="model_provider"
        )

        image_model_provider = st.selectbox(
            "이미지 생성에 사용할 모델을 선택하세요",
            ("DALL·E 3", "Pollinations.ai"),
            key="image_model_provider"
        )

        # 현재 저장된 키 상태 표시
        saved_keys_status = []
        if st.session_state.get("openai_api_key"):
            saved_keys_status.append("✅ OpenAI")
        if st.session_state.get("gemini_api_key"):
            saved_keys_status.append("✅ Gemini")
        if st.session_state.get("anthropic_api_key"):
            saved_keys_status.append("✅ Claude")
        if st.session_state.get("tavily_api_key"):
            saved_keys_status.append("✅ Tavily")

        if saved_keys_status:
            st.info(f"저장된 키: {', '.join(saved_keys_status)}")
        else:
            st.warning("⚠️ 저장된 API 키가 없습니다. 아래에서 키를 입력하고 저장해주세요.")

        # API 키 입력
        openai_key = st.text_input("OpenAI API Key", type="password", value=st.session_state.get("openai_api_key", ""))
        gemini_key = st.text_input("Google API Key", type="password", value=st.session_state.get("gemini_api_key", ""))
        anthropic_key = st.text_input("Anthropic API Key", type="password", value=st.session_state.get("anthropic_api_key", ""))
        tavily_key = st.text_input("Tavily API Key", type="password", value=st.session_state.get("tavily_api_key", ""))

        # 키가 변경되었는지 확인
        keys_changed = (
            openai_key != st.session_state.get("openai_api_key", "") or
            gemini_key != st.session_state.get("gemini_api_key", "") or
            anthropic_key != st.session_state.get("anthropic_api_key", "") or
            tavily_key != st.session_state.get("tavily_api_key", "")
        )

        # 키가 변경되었거나 저장된 키가 없는 경우에만 저장 버튼 강조
        if keys_changed or not saved_keys_status:
            button_type = "primary"
            button_help = "변경사항을 저장하려면 클릭하세요"
        else:
            button_type = "secondary"
            button_help = "모든 키가 이미 저장되어 있습니다"

        if st.button("💾 API Keys 저장", type=button_type, help=button_help):
            # .env 파일 경로 찾기 (없으면 생성)
            dotenv_path = find_dotenv() or ".env"

            # 키 저장 로직
            keys_to_save = {
                "OPENAI_API_KEY": openai_key,
                "GEMINI_API_KEY": gemini_key,
                "ANTHROPIC_API_KEY": anthropic_key,
                "TAVILY_API_KEY": tavily_key
            }
            saved_count = 0
            for key_name, key_value in keys_to_save.items():
                if key_value:
                    st.session_state[key_name.lower()] = key_value
                    set_key(dotenv_path, key_name, key_value)
                    saved_count += 1

            if saved_count > 0:
                st.success(f"✅ {saved_count}개의 API Key가 저장되었습니다!")
                # 저장 후 UI 컴포넌트에 즉시 반영되도록 스크립트 재실행
                st.rerun()
            else:
                st.warning("⚠️ 최소 하나의 API Key를 입력해주세요.")
    
    # --- 메인 페이지 UI ---
    st.title("🤖 네이버 블로그 포스팅 자동 생성기")
    st.markdown("참고할 기사나 블로그 글의 URL을 입력하면, AI 에이전트들이 협력하여 **네이버 SEO에 최적화된 블로그 포스트**를 자동으로 만들어 드립니다.")

    url = st.text_input("분석할 기사 또는 블로그 URL을 입력하세요:", placeholder="https://...")

    if st.button("🚀 블로그 글 생성 시작!"):
        if not url:
            show_fade_alert("URL을 입력해주세요.", "warning")
            return

        # 필수 API 키 확인
        missing_keys = check_required_api_keys()
        if missing_keys:
            missing_keys_str = ", ".join(missing_keys)
            show_fade_alert(f"{missing_keys_str}가 필요합니다! 사이드바에서 입력 후 저장해주세요.", "error")
            return

        with st.spinner("AI 멀티에이전트가 작업을 시작합니다..."):
            app = build_graph()
            initial_state = {"url": url}
            final_state = app.invoke(initial_state)
            
            # 결과를 세션 상태에 저장
            st.session_state.final_state = final_state

    # 세션 상태에서 결과 가져오기
    if 'final_state' in st.session_state:
        final_state = st.session_state.final_state
        
        # --- 결과 표시 ---
        # 1. 실패 시 여기서 실행 중단
        if "분석 실패:" in final_state.get('scraped_content', ''):
            st.error("생성 프로세스가 중단되었습니다. 위의 에러 메시지를 확인해주세요.")
            return # 더 이상 아래 UI를 그리지 않음

        # 2. 블로그 지수 확인 및 재작성 옵션
        blog_index = final_state.get('blog_index', 0)
        blog_details = final_state.get('blog_details', '')
        rewrite_count = final_state.get('rewrite_count', 0)
        
        if blog_index <= 60 and rewrite_count < 2:  # 최대 2회까지만 재작성 가능
            st.warning(f"📊 블로그 지수: {blog_index}점 (60점 이하)")
            st.info("💡 블로그 품질 향상을 위해 글을 재작성할 수 있습니다.")
            
            # 상세 평가 결과 표시
            if blog_details:
                with st.expander("📋 상세 평가 결과 보기"):
                    st.text(blog_details)
            
            # 재작성 선택 버튼
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 블로그 글 재작성하기", type="primary"):
                    with st.spinner("AI가 블로그 글을 재작성 중입니다..."):
                        # 재작성을 위한 새로운 그래프 실행
                        app = build_graph()
                        rewrite_state = final_state.copy()
                        rewrite_state["needs_rewrite"] = True
                        rewrite_state["rewrite_reason"] = blog_details
                        final_state = app.invoke(rewrite_state)
                        st.session_state.final_state = final_state
                        st.rerun()
            
            with col2:
                if st.button("✅ 현재 결과 사용하기"):
                    st.info("현재 결과를 사용하여 계속 진행합니다.")
        
        elif blog_index <= 60 and rewrite_count >= 2:
            st.warning(f"📊 블로그 지수: {blog_index}점 (60점 이하)")
            st.info(f"💡 이미 {rewrite_count}회 재작성을 시도했습니다. 현재 결과로 진행합니다.")
            if blog_details:
                with st.expander("📋 상세 평가 결과 보기"):
                    st.text(blog_details)

        # 3. 성공 시 최종 결과물 표시
        st.divider()
        st.header("✨ 최종 결과물 ✨")

        # 블로그 지수 표시
        st.subheader(f"📊 블로그 지수: {blog_index}점")
        if blog_details:
            with st.expander("📋 상세 평가 결과 보기"):
                st.text(blog_details)

        # 이미지 섹션
        st.subheader("🖼️ 생성된 이미지")
        
        # 메인 이미지와 부제목 이미지들을 모두 수집
        all_image_urls = []
        all_image_prompts = []
        image_keywords = final_state.get('image_keywords', ['키워드1', '키워드2'])
        keywords_str = '_'.join(image_keywords)

        if final_state.get("image_url"):
            all_image_urls.append(final_state["image_url"])
            all_image_prompts.append(final_state.get("image_prompt", ""))

        subtitle_urls = final_state.get("subtitle_image_urls", [])
        subtitle_prompts = final_state.get("subtitle_image_prompts", [])

        # 빈 문자열이 아닌 유효한 URL만 추가
        for url, prompt in zip(subtitle_urls, subtitle_prompts):
            if url:  # URL이 빈 문자열이 아닌 경우에만 추가
                all_image_urls.append(url)
                all_image_prompts.append(prompt)
        
        if all_image_urls:
            # 이미지 그리드로 표시
            cols = st.columns(2)
            for i, (url, prompt) in enumerate(zip(all_image_urls, all_image_prompts)):
                with cols[i % 2]:
                    st.image(url, caption=f"이미지 {i+1}: {prompt[:50]}...")
            
            # 일괄 다운로드 기능
            st.write("---")
            st.subheader("📥 이미지 다운로드")
            
            # ZIP 파일을 세션 상태에서 확인하거나 생성
            if f'zip_data_{keywords_str}' not in st.session_state:
                import requests
                import zipfile
                import io
                
                with st.spinner("ZIP 파일 준비 중..."):
                    # ZIP 파일 생성
                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                        for i, url in enumerate(all_image_urls, 1):
                            if not url:  # 빈 URL은 건너뜀
                                continue
                            try:
                                response = requests.get(url)
                                if response.status_code == 200:
                                    filename = f"{keywords_str}_{i}.png"
                                    zip_file.writestr(filename, response.content)
                            except Exception as e:
                                st.error(f"이미지 {i} 다운로드 실패: {e}")
                    
                    zip_buffer.seek(0)
                    st.session_state[f'zip_data_{keywords_str}'] = zip_buffer.getvalue()
                    st.success("✅ ZIP 파일 준비 완료!")
                
            # 다운로드 버튼
            st.download_button(
                label="📦 ZIP 파일로 모든 이미지 다운로드",
                data=st.session_state[f'zip_data_{keywords_str}'],
                file_name=f"{keywords_str}_images.zip",
                mime="application/zip",
                help="클릭하면 모든 이미지가 ZIP 파일로 다운로드됩니다."
            )
        else:
            st.warning("이미지를 생성하지 못했거나, 생성 과정이 생략되었습니다.")

        st.subheader("📝 추천 제목")
        st.code(final_state.get('final_title', '제목 생성 실패'), language=None)
        
        st.subheader("📋 네이버 SEO 최적화 부제목")
        subtitles = final_state.get('naver_seo_subtitles', [])
        if subtitles:
            # 부제목을 텍스트 영역에 한번에 표시
            all_subtitles = "\n".join([f"{i}. {subtitle}" for i, subtitle in enumerate(subtitles[:5], 1)])
            st.text_area("생성된 부제목 (전체 선택 후 복사)", value=all_subtitles, height=150, key="all_subtitles")
        else:
            st.info("부제목이 생성되지 않았습니다.")

        st.subheader("🔖 추천 태그")
        tags_str = ", ".join([f"#{tag}" for tag in final_state.get('seo_tags', []) if tag])
        st.code(tags_str, language=None)
        
        st.subheader("✍️ 완성된 블로그 포스트 (마크다운)")
        blog_content = final_state.get('draft_post', '포스트 생성 실패')
        
        # 복사 가능한 텍스트 영역으로 블로그 포스트 표시
        st.text_area(
            "전체 선택 후 복사하세요 (Ctrl+A → Ctrl+C)", 
            value=blog_content, 
            height=400,
            key="blog_post_copy"
        )
        
        # 마크다운 미리보기
        with st.expander("📖 마크다운 미리보기"):
            st.markdown(blog_content)

        with st.expander("🤖 에이전트 작업 상세 내용 보기"):
            st.write("**SEO 전문가 분석:**")
            st.text(final_state.get('seo_analysis', '분석 내용 없음'))

        # --- 채팅 인터페이스 ---
        st.divider()
        st.header("💬 작성가 에이전트와 대화하기")
        st.markdown("블로그 포스트를 더 개선하고 싶으신가요? 작성가 에이전트에게 수정 요청을 해보세요!")
        st.markdown("**예시:** '서론을 더 흥미롭게 만들어줘', '2번 섹션에 예시를 더 추가해줘', '전체적으로 더 간결하게 만들어줘'")

        # 채팅 히스토리 초기화
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []

        # 채팅 히스토리 표시
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # 채팅 입력
        if user_input := st.chat_input("수정 요청을 입력하세요..."):
            # 사용자 메시지 추가
            st.session_state.chat_history.append({"role": "user", "content": user_input})

            # 사용자 메시지 표시
            with st.chat_message("user"):
                st.markdown(user_input)

            # 에이전트 응답 생성
            with st.chat_message("assistant"):
                with st.spinner("작성가 에이전트가 블로그 포스트를 수정하고 있습니다..."):
                    revised_post = revise_with_feedback(
                        current_post=final_state.get('draft_post', ''),
                        user_feedback=user_input,
                        title=final_state.get('final_title', ''),
                        seo_analysis=final_state.get('seo_analysis', '')
                    )

                    # 수정된 포스트로 업데이트
                    st.session_state.final_state['draft_post'] = revised_post

                    response_message = "✅ 블로그 포스트가 수정되었습니다! 위의 '완성된 블로그 포스트' 섹션이 업데이트되었습니다."
                    st.markdown(response_message)

                    # 어시스턴트 응답 추가
                    st.session_state.chat_history.append({"role": "assistant", "content": response_message})

                    # 페이지 새로고침하여 업데이트된 포스트 표시
                    st.rerun()

if __name__ == "__main__":
    main()