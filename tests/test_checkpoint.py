from graph.workflow import app


def test_workflow_has_checkpointer():

    assert app is not None

    assert app.checkpointer is not None