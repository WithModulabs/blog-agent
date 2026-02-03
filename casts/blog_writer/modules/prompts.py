"""Prompt templates for Blog Writer cast.

Contains all prompts used by the LLM nodes.
"""

ANALYZE_CONTENT_PROMPT = """당신은 웹 콘텐츠 분석 전문가입니다.

다음 웹페이지 콘텐츠를 분석하여 JSON 형식으로 핵심 정보를 추출해주세요:

<web_content>
{raw_content}
</web_content>

다음 정보를 추출하세요:
1. title: 페이지 제목
2. main_topic: 핵심 주제 (1-2문장)
3. key_points: 핵심 포인트들 (리스트, 최대 5개)
4. summary: 전체 요약 (3-5문장)
5. tone: 콘텐츠 톤 (formal/casual/technical 등)

JSON 형식으로만 응답하세요."""


SUGGEST_KEYWORDS_PROMPT = """당신은 SEO 키워드 전문가입니다.

다음 콘텐츠 분석 결과를 바탕으로 블로그 글에 적합한 키워드를 최대 30개까지 제안해주세요:

<analyzed_content>
제목: {title}
주제: {main_topic}
핵심 포인트: {key_points}
요약: {summary}
</analyzed_content>

{user_keywords_section}

요구사항:
- SEO에 효과적인 키워드
- 검색량이 높을 것으로 예상되는 키워드
- 콘텐츠 주제와 밀접하게 관련된 키워드
- 반드시 한글 키워드로 제안 (영문 브랜드명/기술명은 그대로 사용 가능)

JSON 형식으로 키워드를 리스트로 반환하세요 (최대 30개):
{{"keywords": ["키워드1", "키워드2", ...]}}"""


WRITE_BLOG_PROMPT = """당신은 전문 블로그 작성자입니다.

다음 정보를 바탕으로 매력적인 블로그 글을 마크다운 형식으로 작성해주세요:

<source_content>
제목: {title}
주제: {main_topic}
핵심 포인트: {key_points}
요약: {summary}
</source_content>

<keywords>
{selected_keywords}
</keywords>

요구사항:
1. 제목(H1)으로 시작
2. 서론/본론/결론 구조
3. 키워드를 자연스럽게 포함
4. 소제목(H2, H3) 활용
5. 이미지 삽입 위치를 [IMAGE: 설명] 형식으로 표시
6. 독자 친화적인 톤
7. 1000-2000자 분량

마크다운 형식으로만 응답하세요."""


OPTIMIZE_SEO_PROMPT = """당신은 SEO 전문가입니다.

다음 블로그 글과 키워드를 바탕으로 SEO 메타 정보를 생성해주세요:

<blog_content>
{blog_markdown}
</blog_content>

<keywords>
{selected_keywords}
</keywords>

JSON 형식으로 응답하세요:
{{
    "title": "SEO 최적화된 페이지 제목 (50-60자)",
    "description": "메타 설명 (150-160자)"
}}"""


GENERATE_IMAGE_PROMPT = """당신은 이미지 프롬프트 전문가입니다.

다음 블로그 콘텐츠에 어울리는 이미지 생성 프롬프트를 만들어주세요:

<content>
주제: {main_topic}
핵심 포인트: {key_points}
</content>

요구사항:
- 블로그 메인 이미지에 적합
- 전문적이고 시각적으로 매력적인 스타일
- 영어로 작성

이미지 생성 프롬프트만 응답하세요 (따옴표 없이)."""
