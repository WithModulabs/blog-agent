# tools.py

import os
import requests
import streamlit as st
import urllib3
from bs4 import BeautifulSoup
from requests.exceptions import SSLError

from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic

# LLM 인스턴스를 안전하게 생성하는 헬퍼
def get_llm(temperature: float = 0.7):
    model_provider = st.session_state.get("model_provider", "OpenAI")
    
    if model_provider == "OpenAI":
        api_key = st.session_state.get("openai_api_key")
        if not api_key:
            st.error("OpenAI API Key가 설정되지 않았습니다.")
            return None
        os.environ["OPENAI_API_KEY"] = api_key
        try:
            return ChatOpenAI(model="gpt-5", temperature=temperature)
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
                model="gemini-1.5-flash-latest", 
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
                model="claude-sonnet-4-20250514",
                api_key=api_key,
                temperature=temperature,
            )
        except Exception as e:
            st.error(f"Claude LLM 초기화 실패: {e}")
            return None
    
    return None

def scrape_web_content(url: str) -> str:
    """지정된 URL의 웹 콘텐츠를 스크래핑하여 텍스트를 반환합니다."""
    
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0'})

    try:
        response = session.get(url, timeout=15)
        response.raise_for_status()

    except SSLError:
        print(f"⚠️ SSL 검증 실패. URL({url})에 대해 검증을 비활성화하여 재시도합니다.")
        response = session.get(url, verify=False, timeout=15)
        response.raise_for_status()

    except requests.RequestException as e:
        return f"URL 요청 중 오류 발생: {e}"
    
    except Exception as e:
        return f"콘텐츠 처리 중 오류 발생: {e}"

    try:
        soup = BeautifulSoup(response.content, 'html.parser')
        main_content = soup.find('main') or soup.find('article') or soup.body
        
        if main_content:
            for tag in main_content(['nav', 'footer', 'script', 'style', 'aside', 'form']):
                tag.decompose()
            text = main_content.get_text(separator='\n', strip=True)
            
            if not text:
                return "스크랩이 금지된 글이거나 텍스트 콘텐츠가 없습니다."
            return text
            
        return "콘텐츠를 추출할 수 없습니다."
    except Exception as e:
        return f"콘텐츠 스크래핑 중 오류 발생: {e}"