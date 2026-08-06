"""The Copium pipeline graph."""

from langgraph.graph import START, END, StateGraph

from copium.nodes.classifier import classify_node
from copium.nodes.extractor import extract_node
from copium.nodes.research import research_node
from copium.nodes.roast import roast_node
from copium.state import PipelineState


def route_after_classify(state: PipelineState) -> str:
    """Send rejections onward. Everything else ends the run here.

    This is the early exit: acknowledgments, interview invites, and offers
    never reach extraction, so they never cost an LLM call or a search.
    """
    return "extract" if state.is_rejection else END


def build_graph():
    """Assemble and compile the pipeline."""
    builder = StateGraph(PipelineState)

    builder.add_node("classify", classify_node)
    builder.add_node("extract", extract_node)
    builder.add_node("research", research_node)
    builder.add_node("roast", roast_node)

    builder.add_edge(START, "classify")
    builder.add_conditional_edges(
        "classify",
        route_after_classify,
        {"extract": "extract", END: END},
    )
    builder.add_edge("extract", "research")
    builder.add_edge("research", "roast")
    builder.add_edge("roast", END)

    return builder.compile()


graph = build_graph()