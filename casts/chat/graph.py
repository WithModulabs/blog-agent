"""Entry point for the Chat graph.

Overview:
    * Extends :class:`BaseGraph` to build a LangGraph StateGraph.
    * Uses :class:`ChatState` as the underlying state container.
    * Ships with a minimal start → end path that you can extend.

Guidelines:
    1. Call ``builder.add_node()`` with custom node classes.
    2. Connect nodes via ``builder.add_edge()`` or ``builder.add_conditional_edges()`` when branching.
    3. Return the compiled graph to orchestrate LangGraph execution.

Official document URL:
    - Graph API: https://docs.langchain.com/oss/python/langgraph/graph-api
    - StateGraph: https://docs.langchain.com/oss/python/langgraph/graph-api#stategraph
    - Nodes: https://docs.langchain.com/oss/python/langgraph/graph-api#nodes
    - Edges: https://docs.langchain.com/oss/python/langgraph/graph-api#edges
    - Graph API Usage: https://docs.langchain.com/oss/python/langgraph/use-graph-api
"""

from langgraph.graph import END, START, StateGraph

from casts.base_graph import BaseGraph
from casts.chat.modules.nodes import SampleNode
from casts.chat.modules.state import InputState, OutputState, State


class ChatGraph(BaseGraph):
    """Graph definition for Chat.

    Attributes:
        input: Input schema for the graph.
        output: Output schema for the graph.
        state: State schema for the graph.
    """

    def __init__(self) -> None:
        super().__init__()
        self.input = InputState
        self.output = OutputState
        self.state = State

    def build(self):
        """Builds and compiles the graph graph.

        Returns:
            CompiledStateGraph: Compiled graph ready for execution.
        """
        builder = StateGraph(
            self.state, input_schema=self.input, output_schema=self.output
        )

        # Register node as an INSTANCE so it returns a dict update, not the class object
        builder.add_node("SampleNode", SampleNode())
        builder.add_edge(START, "SampleNode")
        builder.add_edge("SampleNode", END)

        graph = builder.compile()
        graph.name = self.name
        return graph


chat_graph = ChatGraph()
