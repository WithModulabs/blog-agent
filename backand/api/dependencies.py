"""FastAPI dependencies for graph instances and shared resources."""

from functools import lru_cache

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from casts.blog_writer.modules.nodes import (
    AnalyzeContent,
    ConvertToHTML,
    FetchContent,
    GenerateImages,
    HumanSelectKeywords,
    OptimizeSEO,
    SuggestKeywords,
    WriteBlog,
)
from casts.blog_writer.modules.state import BlogState, InputState, OutputState
from casts.chat.modules.nodes import SampleNode
from casts.chat.modules.state import InputState as ChatInputState
from casts.chat.modules.state import OutputState as ChatOutputState
from casts.chat.modules.state import State as ChatState


@lru_cache(maxsize=1)
def get_checkpointer() -> MemorySaver:
    """Get shared in-memory checkpointer singleton.

    Note: Use Redis/PostgreSQL checkpointer in production for persistence.
    """
    return MemorySaver()


@lru_cache(maxsize=1)
def get_blog_writer_graph():
    """Get compiled blog writer graph with checkpointer.

    Builds the graph with proper checkpointer for state persistence
    required by interrupt_before functionality.
    """
    checkpointer = get_checkpointer()

    builder = StateGraph(BlogState, input_schema=InputState, output_schema=OutputState)

    # Register nodes
    builder.add_node("fetch_content", FetchContent())
    builder.add_node("analyze_content", AnalyzeContent())
    builder.add_node("suggest_keywords", SuggestKeywords())
    builder.add_node("human_select_keywords", HumanSelectKeywords())
    builder.add_node("write_blog", WriteBlog())
    builder.add_node("optimize_seo", OptimizeSEO())
    builder.add_node("generate_images", GenerateImages())
    builder.add_node("convert_to_html", ConvertToHTML())

    # Connect edges
    builder.add_edge(START, "fetch_content")
    builder.add_edge("fetch_content", "analyze_content")
    builder.add_edge("analyze_content", "suggest_keywords")
    builder.add_edge("suggest_keywords", "human_select_keywords")
    builder.add_edge("human_select_keywords", "write_blog")
    builder.add_edge("write_blog", "optimize_seo")
    builder.add_edge("optimize_seo", "generate_images")
    builder.add_edge("generate_images", "convert_to_html")
    builder.add_edge("convert_to_html", END)

    # Compile with checkpointer and interrupt
    graph = builder.compile(
        checkpointer=checkpointer,
        interrupt_before=["human_select_keywords"],
    )
    graph.name = "BlogWriterGraph"
    return graph


@lru_cache(maxsize=1)
def get_chat_graph():
    """Get compiled chat graph with checkpointer."""
    checkpointer = get_checkpointer()

    builder = StateGraph(
        ChatState, input_schema=ChatInputState, output_schema=ChatOutputState
    )

    builder.add_node("SampleNode", SampleNode())
    builder.add_edge(START, "SampleNode")
    builder.add_edge("SampleNode", END)

    graph = builder.compile(checkpointer=checkpointer)
    graph.name = "ChatGraph"
    return graph
