from functools import partial
from . import core


def build_graph(llm):
    from langgraph.graph import END, StateGraph
    g = StateGraph(core.State)
    g.add_node("gate", core.n_gate)
    g.add_node("draft", partial(core.n_draft, llm=llm))
    g.add_node("check", core.n_check)
    g.add_node("revise", partial(core.n_revise, llm=llm))
    g.add_node("finalize", core.n_finalize)
    g.set_entry_point("gate")
    g.add_conditional_edges("gate", core.route_gate, {"draft": "draft", "finalize": "finalize"})
    g.add_edge("draft", "check")
    g.add_conditional_edges("check", core.route_check, {"revise": "revise", "finalize": "finalize"})
    g.add_edge("revise", "check")
    g.add_edge("finalize", END)
    return g.compile()