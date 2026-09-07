from graph.workflow import app


def test_workflow_is_compiled():

    assert app is not None


def test_workflow_contains_expected_nodes():

    expected_nodes = {
        "planner",
        "prepare_next_task",
        "researcher",
        "coder",
        "evaluator",
        "mark_current_task_complete",
        "human",
        "prepare_evaluator_revision",
        "prepare_human_revision",
        "finalizer"
    }

    actual_nodes = set(
        app.get_graph().nodes.keys()
    )

    assert expected_nodes.issubset(
        actual_nodes
    )


def test_workflow_has_start_and_end():

    graph = app.get_graph()

    node_names = set(
        graph.nodes.keys()
    )

    assert "__start__" in node_names
    assert "__end__" in node_names