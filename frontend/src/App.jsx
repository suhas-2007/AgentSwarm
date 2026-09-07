import {
  BrowserRouter,
  Routes,
  Route,
  Link,
  Navigate
} from "react-router-dom";

import Login from "./pages/Login";
import Signup from "./pages/Signup";
import ForgotPassword from "./pages/ForgotPassword";
import ResetPassword from "./pages/ResetPassword";
import Dashboard from "./pages/Dashboard";
import SharedTask from "./pages/SharedTask";

import "./index.css";


function ProtectedRoute({ children }) {

  const accessToken = localStorage.getItem(
    "access_token"
  );

  if (!accessToken) {
    return <Navigate to="/login" replace />;
  }

  return children;
}


function LandingPage() {

  return (
    <div className="app">

      {/* Navigation */}

      <header className="navbar">

        <div className="logo">

          <div className="logo-mark">
            A
          </div>

          <span>
            AgentSwarm
          </span>

        </div>


        <nav className="nav-links">

          <a href="#how-it-works">
            How it works
          </a>

          <Link
            to="/login"
            className="login-button"
          >
            Sign in
          </Link>

          <Link
            to="/signup"
            className="signup-button"
          >
            Get started
          </Link>

        </nav>

      </header>


      <main>

        {/* Hero */}

        <section className="hero">

          <div className="hero-content">

            <div className="badge">

              <span className="badge-dot"></span>

              Your AI team for getting things done

            </div>


            <h1>

              Tell us what you want.

              <span>
                {" "}We'll handle the work.
              </span>

            </h1>


            <p className="hero-description">

              AgentSwarm turns your idea into a finished solution.
              It plans the work, finds useful information, builds the
              solution, checks it, and lets you approve the result.

            </p>


            <div className="hero-actions">

              <Link
                to="/signup"
                className="primary-button"
              >
                Get started
                <span>→</span>
              </Link>


              <a
                href="#how-it-works"
                className="secondary-button"
              >
                See how it works
              </a>

            </div>


            <p className="hero-note">
              No technical knowledge required.
            </p>

          </div>


          {/* Workflow Card */}

          <div className="workflow-card">

            <div className="workflow-header">

              <div>

                <p className="workflow-label">
                  AGENTSWARM
                </p>

                <h2>
                  How your request gets done
                </h2>

              </div>


              <div className="status-pill">

                <span></span>

                Ready

              </div>

            </div>


            <div className="workflow">

              <WorkflowStep
                number="1"
                title="Understand"
                description="Your request is broken into clear steps."
                icon="✦"
              />

              <div className="workflow-line"></div>

              <WorkflowStep
                number="2"
                title="Research"
                description="Useful information is gathered."
                icon="⌕"
              />

              <div className="workflow-line"></div>

              <WorkflowStep
                number="3"
                title="Build"
                description="The solution is created."
                icon="◆"
              />

              <div className="workflow-line"></div>

              <WorkflowStep
                number="4"
                title="Check"
                description="The result is reviewed for problems."
                icon="✓"
              />

              <div className="workflow-line"></div>

              <WorkflowStep
                number="5"
                title="You approve"
                description="You stay in control of the final result."
                icon="→"
              />

            </div>

          </div>

        </section>


        {/* Simple explanation */}

        <section className="simple-section">

          <div className="section-heading">

            <p className="section-label">
              MADE SIMPLE
            </p>

            <h2>

              You don't need to know

              <span>
                {" "}how it works.
              </span>

            </h2>


            <p>

              Just describe what you need in your own words.
              AgentSwarm takes care of the complicated steps behind
              the scenes.

            </p>

          </div>


          <div className="example-card">

            <div className="example-label">
              FOR EXAMPLE
            </div>


            <div className="example-request">

              "Create a Python program that analyzes student marks
              and shows the results."

            </div>


            <div className="example-arrow">
              ↓
            </div>


            <div className="example-result">

              <div className="result-check">
                ✓
              </div>


              <div>

                <strong>
                  AgentSwarm handles the work
                </strong>

                <p>
                  Plans → researches → builds → checks → asks you
                  for approval
                </p>

              </div>

            </div>

          </div>

        </section>


        {/* How it works */}

        <section
          id="how-it-works"
          className="how-section"
        >

          <div className="section-heading centered">

            <p className="section-label">
              HOW IT WORKS
            </p>


            <h2>

              From an idea to a

              <span>
                {" "}finished result.
              </span>

            </h2>


            <p>
              Everything happens step by step, and you stay in
              control.
            </p>

          </div>


          <div className="steps-grid">

            <SimpleStep
              number="01"
              title="Tell us"
              description="Describe what you want to accomplish. Use normal language."
            />

            <SimpleStep
              number="02"
              title="We plan"
              description="AgentSwarm figures out the smaller tasks needed to reach your goal."
            />

            <SimpleStep
              number="03"
              title="We build"
              description="Different AI agents work on research, implementation, and checking."
            />

            <SimpleStep
              number="04"
              title="You decide"
              description="Review the result and approve it or ask for improvements."
            />

          </div>

        </section>


        {/* CTA */}

        <section className="cta-section">

          <div className="cta-card">

            <p className="section-label">
              READY?
            </p>


            <h2>

              Start with an idea.

              <span>
                {" "}End with a solution.
              </span>

            </h2>


            <p>

              Tell AgentSwarm what you want to build and let your
              AI team take it from there.

            </p>


            <Link
              to="/signup"
              className="primary-button"
            >
              Get started
              <span>→</span>
            </Link>

          </div>

        </section>

      </main>


      <footer className="footer">

        <div className="logo">

          <div className="logo-mark">
            A
          </div>

          <span>
            AgentSwarm
          </span>

        </div>


        <p>
          Multi-agent task orchestration made simple.
        </p>

      </footer>

    </div>
  );
}


function WorkflowStep({
  number,
  title,
  description,
  icon
}) {

  return (
    <div className="workflow-step">

      <div className="step-icon">
        <span>{icon}</span>
      </div>

      <div className="step-number">
        {number}
      </div>

      <div className="step-content">

        <h3>
          {title}
        </h3>

        <p>
          {description}
        </p>

      </div>

    </div>
  );
}


function SimpleStep({
  number,
  title,
  description
}) {

  return (
    <div className="simple-step">

      <div className="simple-step-number">
        {number}
      </div>

      <h3>
        {title}
      </h3>

      <p>
        {description}
      </p>

    </div>
  );
}


function App() {

  return (
    <BrowserRouter>

      <Routes>

        <Route
          path="/"
          element={<LandingPage />}
        />

        <Route
          path="/login"
          element={<Login />}
        />

        <Route
          path="/signup"
          element={<Signup />}
        />

        <Route
          path="/forgot-password"
          element={<ForgotPassword />}
        />

        <Route
          path="/reset-password"
          element={<ResetPassword />}
        />

        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />

        {/* Public shared task */}

        <Route
          path="/share/:token"
          element={<SharedTask />}
        />

      </Routes>

    </BrowserRouter>
  );
}


export default App;