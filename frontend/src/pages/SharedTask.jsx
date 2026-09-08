import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import "./SharedTask.css";
import { API_URL } from "../config";


function ResultSection({
  title,
  content
}) {

  if (!content || !content.trim()) {
    return null;
  }

  return (
    <section className="shared-result-section">

      <div className="shared-result-header">
        {title}
      </div>

      <div className="shared-result-content">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>
          {content}
        </ReactMarkdown>
      </div>

    </section>
  );
}


function SharedTask() {

  const { token } = useParams();

  const [task, setTask] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");


  useEffect(() => {

    async function loadSharedTask() {

      if (!token) {

        setError(
          "Invalid shared task link."
        );

        setLoading(false);

        return;
      }

      try {

        const response = await fetch(
          `${API_URL}/share/${encodeURIComponent(token)}`
        );

        if (!response.ok) {

          if (response.status === 404) {

            throw new Error(
              "This shared task could not be found."
            );

          }

          throw new Error(
            "Unable to load the shared task."
          );
        }

        const data =
          await response.json();

        setTask(data);

      } catch (err) {

        setError(
          err.message ||
          "Unable to load the shared task."
        );

      } finally {

        setLoading(false);

      }
    }

    loadSharedTask();

  }, [token]);


  if (loading) {

    return (
      <div className="shared-page">

        <div className="shared-loading">
          Loading shared task...
        </div>

      </div>
    );
  }


  if (error) {

    return (
      <div className="shared-page">

        <div className="shared-error-card">

          <div className="shared-logo">

            <div className="shared-logo-mark">
              A
            </div>

            <span>
              AgentSwarm
            </span>

          </div>

          <h1>
            Shared task unavailable
          </h1>

          <p>
            {error}
          </p>

        </div>

      </div>
    );
  }


  return (
    <div className="shared-page">

      <header className="shared-header">

        <div className="shared-logo">

          <div className="shared-logo-mark">
            A
          </div>

          <span>
            AgentSwarm
          </span>

        </div>

        <div className="shared-badge">
          Shared result
        </div>

      </header>


      <main className="shared-main">

        <div className="shared-intro">

          <p className="shared-label">
            AGENTSWARM RESULT
          </p>

          <h1>
            {task.goal}
          </h1>

          <p className="shared-readonly">
            Read-only shared task
          </p>

        </div>


        <div className="shared-results">

          <ResultSection
            title="PLAN"
            content={task.plan}
          />

          <ResultSection
            title="RESEARCH"
            content={task.research}
          />

          <ResultSection
            title="CONTENT"
            content={task.content}
          />

          <ResultSection
            title="CODE"
            content={task.code}
          />

          <ResultSection
            title="REVIEW"
            content={task.evaluation}
          />

          <ResultSection
            title="FINAL RESULT"
            content={task.final_answer}
          />

        </div>

      </main>


      <footer className="shared-footer">

        Multi-agent task orchestration made simple.

      </footer>

    </div>
  );
}


export default SharedTask;