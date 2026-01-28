# Act: Blog Agent

웹사이트 링크 기반 블로그 포스트 자동 작성 시스템

## 개요

사용자가 제공한 URL의 웹 콘텐츠를 분석하여 SEO 최적화된 블로그 포스트(HTML)를 자동으로 생성합니다.

## 주요 기능

- 웹 콘텐츠 수집 및 분석
- 키워드 제안 및 사용자 선택
- 블로그 글 자동 작성
- SEO 메타 정보 생성
- 이미지 생성/수집

## Casts

| Cast | 설명 | 상태 |
|------|------|------|
| [chat](casts/chat/CLAUDE.md) | 기본 채팅 cast | 기존 |
| [blog_writer](casts/blog_writer/CLAUDE.md) | 블로그 자동 작성 | 신규 |

## 기술 스택

### LLM 제공자 (사용자 설정)
- OpenAI (GPT-4, GPT-4o)
- Anthropic (Claude)
- Google (Gemini)

### 이미지 생성 (사용자 설정)
- OpenAI DALL-E
- Stability AI
- Unsplash API
- Pexels API

### 웹 스크래핑
- BeautifulSoup + requests
- Playwright (JS 렌더링)

## 환경 변수

```bash
# LLM API Keys (사용자 선택에 따라)
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GOOGLE_API_KEY=

# Image API Keys
STABILITY_API_KEY=
UNSPLASH_ACCESS_KEY=
PEXELS_API_KEY=
```
