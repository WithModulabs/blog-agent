import os
import streamlit as st
from dotenv import load_dotenv, set_key, find_dotenv
from graph import build_graph

load_dotenv()

def main():
    st.set_page_config(page_title="🤖 네이버 블로그 포스팅 자동 생성기", layout="wide", initial_sidebar_state="expanded")
    
    with st.sidebar:
        st.header("⚙️ API 및 모델 설정")
        model_provider = st.selectbox("사용할 LLM 모델을 선택하세요", ("OpenAI", "Gemini", "Claude"), key="model_provider")
        openai_key = st.text_input("OpenAI API Key", type="password", value=st.session_state.get("openai_api_key", os.getenv("OPENAI_API_KEY") or ""))
        gemini_key = st.text_input("Google API Key", type="password", value=st.session_state.get("gemini_api_key", os.getenv("GEMINI_API_KEY") or ""))
        anthropic_key = st.text_input("Anthropic API Key", type="password", value=st.session_state.get("anthropic_api_key", os.getenv("ANTHROPIC_API_KEY") or ""))
        tavily_key = st.text_input("Tavily API Key", type="password", value=st.session_state.get("tavily_api_key", os.getenv("TAVILY_API_KEY") or ""))
        if st.button("💾 API Keys 저장"):
            dotenv_path = find_dotenv() or ".env"
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
                st.rerun()
            else:
                st.warning("⚠️ 최소 하나의 API Key를 입력해주세요.")
    
    st.title("🤖 네이버 블로그 포스팅 자동 생성기")
    st.markdown("참고할 기사나 블로그 글의 URL을 입력하면, AI 에이전트들이 협력하여 **네이버 SEO에 최적화된 블로그 포스트**를 자동으로 만들어 드립니다.")

    url = st.text_input("분석할 기사 또는 블로그 URL을 입력하세요:", placeholder="https://...")

    if st.button("🚀 블로그 글 생성 시작!"):
        if not url:
            st.warning("URL을 입력해주세요.")
            return
        required_key = "openai_api_key" if st.session_state.model_provider == "OpenAI" else ("gemini_api_key" if st.session_state.model_provider == "Gemini" else "anthropic_api_key")
        if not st.session_state.get(required_key):
            st.error(f"❌ {st.session_state.model_provider} API Key가 필요합니다. 사이드바에서 입력 후 저장해주세요.")
            return
        if not st.session_state.get("tavily_api_key"):
            st.error("❌ Tavily API Key가 필요합니다. 사이드바에서 입력 후 저장해주세요.")
            return

        with st.spinner("AI 멀티에이전트가 작업을 시작합니다..."):
            app = build_graph()
            initial_state = {"url": url}
            final_state = app.invoke(initial_state)
            st.session_state.final_state = final_state

    if 'final_state' in st.session_state:
        final_state = st.session_state.final_state
        if "분석 실패:" in final_state.get('scraped_content', ''):
            st.error("생성 프로세스가 중단되었습니다. 위의 에러 메시지를 확인해주세요.")
            return

        st.divider()
        st.header("✨ 최종 결과물 ✨")

        st.subheader("🖼️ 생성된 이미지")
        all_image_urls = []
        all_image_prompts = []
        image_keywords = final_state.get('image_keywords', ['키워드1', '키워드2'])
        keywords_str = '_'.join(image_keywords)
        
        if final_state.get("image_url"):
            all_image_urls.append(final_state["image_url"])
            all_image_prompts.append(final_state.get("image_prompt", ""))
        
        subtitle_urls = final_state.get("subtitle_image_urls", [])
        subtitle_prompts = final_state.get("subtitle_image_prompts", [])
        all_image_urls.extend(subtitle_urls)
        all_image_prompts.extend(subtitle_prompts)
        
        if all_image_urls:
            cols = st.columns(2)
            for i, (u, prompt) in enumerate(zip(all_image_urls, all_image_prompts)):
                with cols[i % 2]:
                    st.image(u, caption=f"이미지 {i+1}: {prompt[:50]}...")
            st.write("---")
            st.subheader("📥 이미지 다운로드")
            if f'zip_data_{keywords_str}' not in st.session_state:
                import requests, zipfile, io
                with st.spinner("ZIP 파일 준비 중..."):
                    buf = io.BytesIO()
                    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
                        for i, u in enumerate(all_image_urls, 1):
                            try:
                                r = requests.get(u)
                                if r.status_code == 200:
                                    zf.writestr(f"{keywords_str}_{i}.png", r.content)
                            except Exception as e:
                                st.error(f"이미지 {i} 다운로드 실패: {e}")
                    buf.seek(0)
                    st.session_state[f'zip_data_{keywords_str}'] = buf.getvalue()
                    st.success("✅ ZIP 파일 준비 완료!")
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
            all_subtitles = "\n".join([f"{i}. {subtitle}" for i, subtitle in enumerate(subtitles[:5], 1)])
            st.text_area("생성된 부제목 (전체 선택 후 복사)", value=all_subtitles, height=150, key="all_subtitles")
        else:
            st.info("부제목이 생성되지 않았습니다.")

        st.subheader("🔖 추천 태그")
        tags_str = ", ".join([f"#{tag}" for tag in final_state.get('seo_tags', []) if tag])
        st.code(tags_str, language=None)
        
        st.subheader("✍️ 완성된 블로그 포스트 (마크다운)")
        blog_content = final_state.get('draft_post', '포스트 생성 실패')
        st.text_area("전체 선택 후 복사하세요 (Ctrl+A → Ctrl+C)", value=blog_content, height=400, key="blog_post_copy")
        with st.expander("📖 마크다운 미리보기"):
            st.markdown(blog_content)
        with st.expander("🤖 에이전트 작업 상세 내용 보기"):
            st.write("**SEO 전문가 분석:**")
            st.text(final_state.get('seo_analysis', '분석 내용 없음'))

if __name__ == "__main__":
    main()