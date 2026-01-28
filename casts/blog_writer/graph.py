"""Entry point for the Blog Writer graph.

Assembles 8 nodes into a Sequential + Human-in-the-loop graph:
START → FetchContent → AnalyzeContent → SuggestKeywords →
HumanSelectKeywords (interrupt) → WriteBlog → OptimizeSEO →
GenerateImages → ConvertToHTML → END
"""

from langgraph.graph import END, START, StateGraph

from casts.base_graph import BaseGraph
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


class BlogWriterGraph(BaseGraph):
    """Graph definition for Blog Writer.

    Attributes:
        input: Input schema for the graph.
        output: Output schema for the graph.
        state: State schema for the graph.
    """

    def __init__(self) -> None:
        super().__init__()
        self.input = InputState
        self.output = OutputState
        self.state = BlogState

    def build(self):
        """Builds and compiles the Blog Writer graph.

        Returns:
            CompiledStateGraph: Compiled graph ready for execution.
        """
        builder = StateGraph(
            self.state, input_schema=self.input, output_schema=self.output
        )

        # Register nodes (as instances)
        builder.add_node("fetch_content", FetchContent())
        builder.add_node("analyze_content", AnalyzeContent())
        builder.add_node("suggest_keywords", SuggestKeywords())
        builder.add_node("human_select_keywords", HumanSelectKeywords())
        builder.add_node("write_blog", WriteBlog())
        builder.add_node("optimize_seo", OptimizeSEO())
        builder.add_node("generate_images", GenerateImages())
        builder.add_node("convert_to_html", ConvertToHTML())

        # Connect edges (Sequential flow)
        builder.add_edge(START, "fetch_content")
        builder.add_edge("fetch_content", "analyze_content")
        builder.add_edge("analyze_content", "suggest_keywords")
        builder.add_edge("suggest_keywords", "human_select_keywords")
        builder.add_edge("human_select_keywords", "write_blog")
        builder.add_edge("write_blog", "optimize_seo")
        builder.add_edge("optimize_seo", "generate_images")
        builder.add_edge("generate_images", "convert_to_html")
        builder.add_edge("convert_to_html", END)

        # Compile with interrupt at keyword selection
        graph = builder.compile(interrupt_before=["human_select_keywords"])
        graph.name = self.name
        return graph


blog_writer_graph = BlogWriterGraph()
