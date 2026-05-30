from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.state import MedicalState
from app.nodes.supervisor import supervisor_node, route_supervisor
from app.nodes.diagnostic_agent import diagnostic_agent_node
from app.nodes.physician_review import physician_review_node
from app.nodes.report_agent import report_agent_node


def build_graph():
    """
    Construit et compile le graphe LangGraph multi-agents medical.
    """
    builder = StateGraph(MedicalState)

    # Ajout des noeuds
    builder.add_node("supervisor", supervisor_node)
    builder.add_node("diagnostic_agent", diagnostic_agent_node)
    builder.add_node("physician_review", physician_review_node)
    builder.add_node("report_agent", report_agent_node)

    # Point d'entree
    builder.set_entry_point("supervisor")

    # Edges conditionnels depuis supervisor
    builder.add_conditional_edges(
        "supervisor",
        route_supervisor,
        {
            "diagnostic_agent": "diagnostic_agent",
            "physician_review": "physician_review",
            "report_agent": "report_agent",
            "FINISH": END
        }
    )

    # Apres chaque agent -> retour au supervisor
    builder.add_edge("diagnostic_agent", "supervisor")
    builder.add_edge("physician_review", "supervisor")
    builder.add_edge("report_agent", "supervisor")

    # Memoire persistante pour Human-in-the-Loop
    memory = MemorySaver()

    # Interruption avant physician_review (Human-in-the-Loop)
    graph = builder.compile(
        checkpointer=memory,
        interrupt_before=["physician_review"]
    )

    return graph


# Instance globale du graphe
medical_graph = build_graph()
