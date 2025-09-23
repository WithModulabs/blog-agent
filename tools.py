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
                model="gemini-2.5-flash", 
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
                model="claude-4-sonnet",
                api_key=api_key,
                temperature=temperature,
            )
        except Exception as e:
            st.error(f"Claude LLM 초기화 실패: {e}")
            return None
    
    return None


def generate_image_with_gemini(prompt: str, api_key: str):
    """Pollinations.ai를 사용하여 이미지 생성

    무료 AI 이미지 생성 서비스인 Pollinations.ai를 사용합니다.
    API 키가 필요 없으며, URL을 통해 직접 이미지를 생성합니다.
    """
    try:
        import urllib.parse
        import time

        # Pollinations.ai API 사용 (무료, API 키 불필요)
        # 프롬프트를 URL 인코딩
        encoded_prompt = urllib.parse.quote(prompt)

        # Pollinations.ai 이미지 생성 URL
        # seed를 추가하여 매번 다른 이미지 생성
        seed = int(time.time())
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?seed={seed}&width=1024&height=1024&nologo=true"

        # Pollinations.ai는 첫 요청 시 이미지를 생성하므로 시간이 걸림
        # HEAD 요청 대신 직접 URL을 반환 (브라우저가 이미지를 가져올 때 생성됨)
        st.info("🎨 Pollinations.ai를 통해 이미지를 생성 중... (첫 로딩 시 10-20초 소요)")

        # 이미지 생성을 트리거하기 위해 GET 요청을 보내되,
        # 타임아웃이 발생해도 URL은 유효하므로 반환
        try:
            # 이미지 생성 트리거 (최대 40초 대기)
            response = requests.get(image_url, timeout=40, stream=True)
            if response.status_code == 200:
                st.success("✅ 이미지 생성 완료!")
                return image_url
        except requests.Timeout:
            # 타임아웃이 발생해도 URL은 유효함
            st.warning("⏳ 이미지 생성 중... URL은 유효하며 잠시 후 표시됩니다.")
            return image_url
        except Exception:
            # 다른 오류가 발생해도 URL 자체는 유효할 수 있음
            return image_url

        return image_url

    except Exception as e:
        st.error(f"이미지 URL 생성 실패: {e}")
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