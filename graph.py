import os
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from state import FraudState
from agents.intake_agent import intake_node
from agents.vision_agent import vision_node
from agents.decision_agent import decision_node


def route_intake(state: FraudState) -> str:
    if state.next_step == "vision_agent":
        if state.image_path and os.path.exists(state.image_path):
            return "vision_agent"
        else:
            return END
    return END


def route_vision(state: FraudState) -> str:
    if state.next_step == "decision_agent":
        return "decision_agent"
    return END


def route_decision(state: FraudState) -> str:
    return END


def build_graph():
    graph = StateGraph(FraudState)

    graph.add_node("intake_agent", intake_node)
    graph.add_node("vision_agent", vision_node)
    graph.add_node("decision_agent", decision_node)

    graph.set_entry_point("intake_agent")

    graph.add_conditional_edges(
        "intake_agent",
        route_intake,
        {
            "vision_agent": "vision_agent",
            END: END,
        }
    )

    graph.add_conditional_edges(
        "vision_agent",
        route_vision,
        {
            "decision_agent": "decision_agent",
            END: END,
        }
    )

    graph.add_conditional_edges(
        "decision_agent",
        route_decision,
        {
            END: END,
        }
    )

    memory = MemorySaver()

    return graph.compile(
        checkpointer=memory,
        interrupt_before=["decision_agent"],
    )


fraud_graph = build_graph()