import os
import requests
import streamlit as st
from bs4 import BeautifulSoup
from requests.exceptions import SSLError, RequestException

from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic
import trafilatura
from urllib.parse import urlparse, urljoin, parse_qs


def get_llm(temperature: float = 0.7):
    model_provider = st.session_state.get("model_provider", "OpenAI")
    
    if model_provider == "OpenAI":
        api_key = st.session_state.get("openai_api_key")
        if not api_key:
            st.error("OpenAI API Key가 설정되지 않았습니다.")
            return None
        os.environ["OPENAI_API_KEY"] = api_key
        try:
            return ChatOpenAI(model="gpt-4o", temperature=temperature)
        except Exception as e:
            st.error(f"OpenAI LLM 초기화 실패: {e}")
            return None
            
    elif model_provider == "Gemini":
        api_key = st.session_state.get("gemini_api_key")
        if not api_key:
            st.error("Google API Key가 설정되지 않았습니다.")
            return None
        try:
            return ChatGoogleGenerativeAI(
                model="gemini-2.0-flash-exp", 
                google_api_key=api_key,
                temperature=temperature,
                convert_system_message_to_human=True
            )
        except Exception as e:
            st.error(f"Gemini LLM 초기화 실패: {e}")
            return None

    elif model_provider == "Claude":
        api_key = st.session_state.get("anthropic_api_key")
        if not api_key:
            st.error("Anthropic API Key가 설정되지 않았습니다.")
            return None
        try:
            return ChatAnthropic(
                model="claude-3-5-sonnet-20241022",
                api_key=api_key,
                temperature=temperature,
            )
        except Exception as e:
            st.error(f"Claude LLM 초기화 실패: {e}")
            return None
    
    return None


def generate_image_with_gemini(prompt: str, api_key: str):
    """Gemini를 사용하여 이미지 생성"""
    try:
        import google.generativeai as genai
        
        genai.configure(api_key=api_key)
        
        # Gemini 2.0 Flash의 이미지 생성 기능 사용
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # 이미지 생성 요청
        response = model.generate_content([
            "Generate an image based on this description: " + prompt,
            "Please create a high-quality, detailed image that matches the description."
        ])
        
        # 응답에서 이미지 URL 추출 (실제 구현은 Gemini API 응답 형식에 따라 조정 필요)
        if hasattr(response, 'images') and response.images:
            return response.images[0].url
        else:
            # Gemini 이미지 생성이 지원되지 않는 경우 대체 로직
            st.warning("Gemini 이미지 생성 기능을 사용할 수 없습니다. 텍스트 설명으로 대체합니다.")
            return None
            
    except Exception as e:
        st.error(f"Gemini 이미지 생성 실패: {e}")
        return None


def _session():
    s = requests.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    })
    return s

def _scrape_naver_blog(url: str):
    s = _session()
    try:
        r = s.get(url, timeout=20)
        r.raise_for_status()
    except RequestException as e:
        return "", f"URL 요청 중 오류 발생: {e}"

    soup = BeautifulSoup(r.content, "html.parser")

    frame = soup.find("iframe", {"id": "mainFrame"}) or soup.find("frame", {"id": "mainFrame"})
    if not frame or not frame.get("src"):
        return "", "콘텐츠를 추출할 수 없습니다."

    inner_url = urljoin("https://blog.naver.com", frame.get("src"))
    try:
        r2 = s.get(inner_url, timeout=20)
        r2.raise_for_status()
    except RequestException as e:
        return "", f"URL 요청 중 오류 발생: {e}"

    inner = BeautifulSoup(r2.content, "html.parser")

    title_candidates = [
        ".se-title-text", ".se_title_text", "h3.se_textarea", "#title_1", "h3#postTitleText"
    ]
    title = ""
    for sel in title_candidates:
        el = inner.select_one(sel)
        if el and el.get_text(strip=True):
            title = el.get_text(strip=True)
            break
    if not title:
        title = inner.title.get_text(strip=True) if inner.title else ""

    container = inner.select_one(".se-main-container") or inner.select_one("#postViewArea")
    if container:
        for tag in container(["script","style","nav","footer","aside","form"]):
            tag.decompose()
        text = container.get_text(separator="\n", strip=True)
        return title, text if text else "콘텐츠를 추출할 수 없습니다."

    extracted = trafilatura.extract(r2.text)
    if extracted:
        return title, extracted

    return title, "콘텐츠를 추출할 수 없습니다."

def scrape_web_content(url: str):
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    if "blog.naver.com" in host or "m.blog.naver.com" in host:
        return _scrape_naver_blog(url)

    s = _session()
    try:
        r = s.get(url, timeout=20)
        r.raise_for_status()
    except SSLError:
        r = s.get(url, timeout=20, verify=False)
        r.raise_for_status()
    except RequestException as e:
        return "", f"URL 요청 중 오류 발생: {e}"

    title = ""
    try:
        soup = BeautifulSoup(r.content, "html.parser")
        title = soup.title.get_text(strip=True) if soup.title else ""
    except Exception:
        pass

    extracted = trafilatura.extract(r.text)
    if extracted:
        return title, extracted
    return title, "콘텐츠를 추출할 수 없습니다."