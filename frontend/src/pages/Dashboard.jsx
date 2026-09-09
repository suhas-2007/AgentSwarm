import { useEffect, useState } from "react";
import {
    Link,
    useNavigate
} from "react-router-dom";
import {
    MoreHorizontal,
    Share2,
    Trash2,
    Download,
    Key,
    Pencil
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import "./Dashboard.css";
import { API_URL } from "../config";
import ApiKeysModal from "../components/ApiKeysModal";
import NamePromptModal from "../components/NamePromptModal";


function Dashboard() {

    const navigate = useNavigate();

    const [task, setTask] = useState("");
    const [taskState, setTaskState] = useState(null);
    const [loading, setLoading] = useState(false);
    const [feedback, setFeedback] = useState("");
    const [error, setError] = useState("");

    const [recentTasks, setRecentTasks] = useState([]);
    const [historyLoading, setHistoryLoading] = useState(true);
    const [showAllTasks, setShowAllTasks] = useState(false);
    const [openingTaskId, setOpeningTaskId] = useState(null);

    const [stoppingTask, setStoppingTask] = useState(false);
    const [deletingTaskId, setDeletingTaskId] = useState(null);

    const [deleteAccount, setDeleteAccount] = useState(false);
    const [deleteLoading, setDeleteLoading] = useState(false);

    const [artifacts, setArtifacts] = useState([]);
    const [artifactsLoading, setArtifactsLoading] = useState(false);
    const [downloadingArtifact, setDownloadingArtifact] = useState(null);

    const [showApiKeysModal, setShowApiKeysModal] = useState(false);
    const [showNameModal, setShowNameModal] = useState(false);

    const userEmail = localStorage.getItem("user_email") || "";
    const [userName, setUserName] = useState(
        localStorage.getItem("user_name") || ""
    );
    const userAvatar = localStorage.getItem("user_avatar");


    const exampleTasks = [
        "Build a Python calculator",
        "Analyze a CSV dataset",
        "Create a REST API",
        "Explain a programming concept"
    ];


    const getAccessToken = () => {

        return localStorage.getItem(
            "access_token"
        );

    };


    // =====================================================
    // LOAD TASK ARTIFACTS
    // =====================================================

    const loadArtifacts = async (taskId) => {

        if (!taskId) {

            return;

        }


        const accessToken =
            getAccessToken();


        if (!accessToken) {

            return;

        }


        setArtifactsLoading(true);


        try {

            const response = await fetch(
                `${API_URL}/tasks/${taskId}/artifacts`,
                {
                    method: "GET",

                    headers: {
                        "Authorization": `Bearer ${accessToken}`
                    }
                }
            );


            if (response.status === 401) {

                localStorage.removeItem(
                    "access_token"
                );

                navigate(
                    "/login",
                    {
                        replace: true
                    }
                );

                return;

            }


            if (!response.ok) {

                throw new Error(
                    "Unable to load task artifacts."
                );

            }


            const data =
                await response.json();

            const artifactsList = Array.isArray(data)
                ? data
                : (Array.isArray(data?.artifacts) ? data.artifacts : []);

            setArtifacts(
                artifactsList
            );


        } catch (err) {

            console.error(
                "Artifact loading failed:",
                err
            );

            setArtifacts([]);


        } finally {

            setArtifactsLoading(false);

        }

    };


    // =====================================================
    // DOWNLOAD TASK ARTIFACT
    // =====================================================

    const handleDownloadArtifact = async (
        taskId,
        filename
    ) => {

        if (!taskId || !filename) {

            return;

        }


        const accessToken =
            getAccessToken();


        if (!accessToken) {

            navigate(
                "/login",
                {
                    replace: true
                }
            );

            return;

        }


        const downloadKey =
            `${taskId}:${filename}`;


        setDownloadingArtifact(
            downloadKey
        );

        setError("");


        try {

            const response = await fetch(
                `${API_URL}/tasks/${taskId}/artifacts/${encodeURIComponent(filename)}`,
                {
                    method: "GET",

                    headers: {
                        "Authorization": `Bearer ${accessToken}`
                    }
                }
            );


            if (response.status === 401) {

                localStorage.removeItem(
                    "access_token"
                );

                navigate(
                    "/login",
                    {
                        replace: true
                    }
                );

                return;

            }


            if (!response.ok) {

                let message =
                    "Unable to download this artifact.";


                try {

                    const data =
                        await response.json();


                    message =
                        data.detail ||
                        message;

                } catch {

                    // Keep default message.

                }


                throw new Error(
                    message
                );

            }


            const blob =
                await response.blob();


            const blobUrl =
                window.URL.createObjectURL(
                    blob
                );


            const link =
                document.createElement(
                    "a"
                );


            link.href =
                blobUrl;

            link.download =
                filename;


            document.body.appendChild(
                link
            );


            link.click();


            link.remove();


            window.URL.revokeObjectURL(
                blobUrl
            );


        } catch (err) {

            console.error(
                "Artifact download failed:",
                err
            );


            setError(
                err.message ||
                "Unable to download this artifact."
            );

        } finally {

            setDownloadingArtifact(
                null
            );

        }

    };


    // =====================================================
    // LOAD TASK HISTORY
    // =====================================================

    const loadTaskHistory = async () => {

        const accessToken =
            getAccessToken();


        if (!accessToken) {

            navigate(
                "/login",
                {
                    replace: true
                }
            );

            return;

        }


        setHistoryLoading(true);


        try {

            const response = await fetch(
                `${API_URL}/tasks`,
                {
                    method: "GET",

                    headers: {
                        "Authorization": `Bearer ${accessToken}`
                    }
                }
            );


            if (response.status === 401) {

                localStorage.removeItem(
                    "access_token"
                );


                navigate(
                    "/login",
                    {
                        replace: true
                    }
                );


                return;

            }


            if (!response.ok) {

                throw new Error(
                    "Unable to load task history."
                );

            }


            const data =
                await response.json();

            const tasksList = Array.isArray(data)
                ? data
                : (Array.isArray(data?.tasks) ? data.tasks : []);

            setRecentTasks(
                tasksList
            );


        } catch (err) {

            console.error(err);


            setError(
                "Unable to load your task history."
            );


        } finally {

            setHistoryLoading(false);

        }

    };


    useEffect(() => {

        loadTaskHistory();

        const accessToken = getAccessToken();
        if (accessToken) {
            fetch(`${API_URL}/auth/me`, {
                headers: {
                    Authorization: `Bearer ${accessToken}`
                }
            })
                .then(async (res) => {
                    if (!res.ok) return null;
                    return res.json();
                })
                .then((data) => {
                    if (data?.name) {
                        setUserName(data.name);
                        localStorage.setItem("user_name", data.name);
                    } else if (!localStorage.getItem("user_name")) {
                        setShowNameModal(true);
                    }
                })
                .catch(() => {});
        }

    }, []);


    // =====================================================
    // POLL CURRENT TASK STATUS
    // =====================================================

    useEffect(() => {

        if (!taskState?.task_id) {

            return;

        }


        const terminalStatuses = [
            "WAITING_FOR_HUMAN",
            "COMPLETED",
            "FAILED",
            "STOPPED",
            "EVALUATION_UNAVAILABLE"
        ];


        if (
            terminalStatuses.includes(
                taskState.status
            )
        ) {

            return;

        }


        const accessToken =
            getAccessToken();


        if (!accessToken) {

            return;

        }


        let cancelled = false;


        const pollTask = async () => {

            try {

                const response = await fetch(
                    `${API_URL}/tasks/${taskState.task_id}`,
                    {
                        method: "GET",

                        headers: {
                            "Authorization": `Bearer ${accessToken}`
                        }
                    }
                );


                if (cancelled) {

                    return;

                }


                if (response.status === 401) {

                    localStorage.removeItem(
                        "access_token"
                    );


                    navigate(
                        "/login",
                        {
                            replace: true
                        }
                    );


                    return;

                }


                if (!response.ok) {

                    return;

                }


                const data =
                    await response.json();


                setTaskState(data);


                if (
                    data.status === "COMPLETED" ||
                    data.status === "FAILED" ||
                    data.status === "WAITING_FOR_HUMAN" ||
                    data.status === "STOPPED" ||
                    data.status === "EVALUATION_UNAVAILABLE"
                ) {

                    await loadTaskHistory();


                    await loadArtifacts(
                        data.task_id
                    );

                }


            } catch (err) {

                if (!cancelled) {

                    console.error(
                        "Task polling failed:",
                        err
                    );

                }

            }

        };


        const intervalId =
            setInterval(
                pollTask,
                2000
            );


        return () => {

            cancelled = true;

            clearInterval(
                intervalId
            );

        };

    }, [
        taskState?.task_id,
        taskState?.status
    ]);


    // =====================================================
    // OPEN A PREVIOUS TASK
    // =====================================================

    const handleOpenTask = async (
        taskId
    ) => {

        const accessToken =
            getAccessToken();


        if (!accessToken) {

            navigate(
                "/login",
                {
                    replace: true
                }
            );

            return;

        }


        setOpeningTaskId(taskId);
        setError("");


        try {

            const response = await fetch(
                `${API_URL}/tasks/${taskId}`,
                {
                    method: "GET",

                    headers: {
                        "Authorization": `Bearer ${accessToken}`
                    }
                }
            );


            if (response.status === 401) {

                localStorage.removeItem(
                    "access_token"
                );


                navigate(
                    "/login",
                    {
                        replace: true
                    }
                );


                return;

            }


            if (response.status === 404) {

                setRecentTasks(
                    (previous) =>
                        previous.filter(
                            (recentTask) =>
                                recentTask.task_id !==
                                taskId
                        )
                );


                if (
                    taskState?.task_id ===
                    taskId
                ) {

                    setTaskState(null);

                    setFeedback("");

                    setArtifacts([]);

                }


                await loadTaskHistory();


                setError(
                    "This task is no longer available. It may have been deleted."
                );


                return;

            }


            if (!response.ok) {

                throw new Error(
                    "Unable to open this task."
                );

            }


            const data =
                await response.json();


            setTaskState(data);

            setFeedback("");


            await loadArtifacts(
                data.task_id
            );


            setTimeout(() => {

                const element =
                    document.getElementById("task-result") ||
                    document.querySelector(".workflow-card");

                element?.scrollIntoView({
                    behavior: "smooth",
                    block: "start"
                });

            }, 120);


        } catch (err) {

            console.error(err);


            setError(
                err.message ||
                "Unable to open this task."
            );


        } finally {

            setOpeningTaskId(null);

        }

    };


    // =====================================================
    // SHARE TASK
    // =====================================================

    const handleShareTask = async (
        taskId,
        title,
        description
    ) => {

        setError("");


        const accessToken =
            getAccessToken();


        if (!accessToken) {

            navigate(
                "/login",
                {
                    replace: true
                }
            );

            return;

        }


        try {

            const response = await fetch(
                `${API_URL}/tasks/${taskId}/share`,
                {
                    method: "POST",

                    headers: {
                        "Authorization": `Bearer ${accessToken}`
                    }
                }
            );


            if (response.status === 401) {

                localStorage.removeItem(
                    "access_token"
                );


                navigate(
                    "/login",
                    {
                        replace: true
                    }
                );


                return;

            }


            const data =
                await response.json();


            if (!response.ok) {

                throw new Error(
                    data.detail ||
                    "Unable to create a share link."
                );

            }


            const shareUrl =
                `${window.location.origin}${data.share_url}`;


            const shareData = {

                title:
                    title ||
                    `AgentSwarm Task #${taskId}`,

                text:
                    description ||
                    `AgentSwarm Task #${taskId}`,

                url:
                    shareUrl

            };


            if (
                navigator.share &&
                typeof navigator.share ===
                "function"
            ) {

                await navigator.share(
                    shareData
                );

                return;

            }


            if (
                navigator.clipboard &&
                typeof navigator.clipboard.writeText ===
                "function"
            ) {

                await navigator.clipboard.writeText(
                    `${shareData.text}\n\n${shareData.url}`
                );


                window.alert(
                    "Public task link copied to your clipboard."
                );


                return;

            }


            window.prompt(
                "Copy this public task link:",
                shareUrl
            );


        } catch (err) {

            if (
                err?.name ===
                "AbortError"
            ) {

                return;

            }


            console.error(
                "Task sharing failed:",
                err
            );


            setError(
                err.message ||
                "Unable to share this task."
            );

        }

    };


    // =====================================================
    // STOP TASK
    // =====================================================

    const handleStopTask = async (
        taskId
    ) => {

        if (!taskId) {

            return;

        }


        const confirmed =
            window.confirm(
                "Stop this task? The current agent may finish its current operation before AgentSwarm stops the workflow."
            );


        if (!confirmed) {

            return;

        }


        const accessToken =
            getAccessToken();


        if (!accessToken) {

            navigate(
                "/login",
                {
                    replace: true
                }
            );

            return;

        }


        setStoppingTask(true);
        setError("");


        try {

            const response = await fetch(
                `${API_URL}/tasks/${taskId}/stop`,
                {
                    method: "POST",

                    headers: {
                        "Authorization": `Bearer ${accessToken}`
                    }
                }
            );


            if (response.status === 401) {

                localStorage.removeItem(
                    "access_token"
                );


                navigate(
                    "/login",
                    {
                        replace: true
                    }
                );


                return;

            }


            const data =
                await response.json();


            if (!response.ok) {

                throw new Error(
                    data.detail ||
                    "Unable to stop this task."
                );

            }


            setTaskState(
                (previous) => {

                    if (
                        !previous ||
                        previous.task_id !==
                        taskId
                    ) {

                        return previous;

                    }


                    return {
                        ...previous,
                        ...data,
                        status: "STOPPED"
                    };

                }
            );


            await loadArtifacts(
                taskId
            );


            await loadTaskHistory();


        } catch (err) {

            console.error(err);


            setError(
                err.message ||
                "Unable to stop this task."
            );


        } finally {

            setStoppingTask(false);

        }

    };


    // =====================================================
    // DELETE TASK
    // =====================================================

    const handleDeleteTask = async (
        taskId
    ) => {

        if (!taskId) {

            return;

        }


        const confirmed =
            window.confirm(
                "Delete this task permanently? This action cannot be undone."
            );


        if (!confirmed) {

            return;

        }


        const accessToken =
            getAccessToken();


        if (!accessToken) {

            navigate(
                "/login",
                {
                    replace: true
                }
            );

            return;

        }


        setDeletingTaskId(taskId);
        setError("");


        try {

            const response = await fetch(
                `${API_URL}/tasks/${taskId}`,
                {
                    method: "DELETE",

                    headers: {
                        "Authorization": `Bearer ${accessToken}`
                    }
                }
            );


            if (response.status === 401) {

                localStorage.removeItem(
                    "access_token"
                );


                navigate(
                    "/login",
                    {
                        replace: true
                    }
                );


                return;

            }


            const data =
                await response.json();


            if (!response.ok) {

                throw new Error(
                    data.detail ||
                    "Unable to delete this task."
                );

            }


            setRecentTasks(
                (previous) =>
                    previous.filter(
                        (recentTask) =>
                            recentTask.task_id !==
                            taskId
                    )
            );


            if (
                taskState?.task_id ===
                taskId
            ) {

                setTaskState(null);

                setFeedback("");

                setArtifacts([]);

            }


        } catch (err) {

            console.error(err);


            setError(
                err.message ||
                "Unable to delete this task."
            );


        } finally {

            setDeletingTaskId(null);

        }

    };


    // =====================================================
    // EXAMPLE TASK
    // =====================================================

    const handleExampleClick = (
        example
    ) => {

        setTask(example);

        setError("");

    };

    const handleRetryTask = (goal) => {
        if (goal) {
            setTask(goal);
            setError("");
            const formEl = document.querySelector(".task-form textarea");
            if (formEl) {
                formEl.focus();
                formEl.scrollIntoView({
                    behavior: "smooth",
                    block: "center"
                });
            }
        }
    };


    // =====================================================
    // CREATE NEW TASK
    // =====================================================

    const handleSubmit = async (
        event
    ) => {

        event.preventDefault();


        if (!task.trim()) {

            setError(
                "Please describe what you want AgentSwarm to do."
            );

            return;

        }


        const accessToken =
            getAccessToken();


        if (!accessToken) {

            navigate(
                "/login",
                {
                    replace: true
                }
            );

            return;

        }


        setLoading(true);
        setError("");
        setTaskState(null);
        setArtifacts([]);


        try {

            const response = await fetch(
                `${API_URL}/tasks`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json",

                        "Authorization":
                            `Bearer ${accessToken}`
                    },

                    body: JSON.stringify({
                        goal: task.trim()
                    })
                }
            );


            if (response.status === 401) {

                localStorage.removeItem(
                    "access_token"
                );


                navigate(
                    "/login",
                    {
                        replace: true
                    }
                );


                return;

            }


            if (!response.ok) {

                const message =
                    await response.text();


                throw new Error(
                    message ||
                    "Failed to create task."
                );

            }


            const data =
                await response.json();


            setTaskState(data);


            await loadTaskHistory();


        } catch (err) {

            console.error(err);


            setError(
                "Unable to connect to AgentSwarm. Make sure the FastAPI server is running."
            );


        } finally {

            setLoading(false);

        }

    };


    // =====================================================
    // HUMAN APPROVAL
    // =====================================================

    const handleApproval = async (
        approved
    ) => {

        if (!taskState?.task_id) {

            return;

        }


        if (
            !approved &&
            !feedback.trim()
        ) {

            setError(
                "Please tell AgentSwarm what should be improved."
            );

            return;

        }


        const accessToken =
            getAccessToken();


        if (!accessToken) {

            navigate(
                "/login",
                {
                    replace: true
                }
            );

            return;

        }


        setLoading(true);
        setError("");


        try {

            const response = await fetch(
                `${API_URL}/tasks/${taskState.task_id}/approval`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json",

                        "Authorization":
                            `Bearer ${accessToken}`
                    },

                    body: JSON.stringify({
                        approved,

                        feedback:
                            approved
                                ? ""
                                : feedback.trim()
                    })
                }
            );


            if (response.status === 401) {

                localStorage.removeItem(
                    "access_token"
                );


                navigate(
                    "/login",
                    {
                        replace: true
                    }
                );


                return;

            }


            if (!response.ok) {

                const message =
                    await response.text();


                throw new Error(
                    message ||
                    "Unable to submit approval."
                );

            }


            const data =
                await response.json();


            setTaskState(
                (previous) => ({
                    ...previous,
                    ...data
                })
            );


            setFeedback("");


            await loadTaskHistory();


        } catch (err) {

            console.error(err);


            setError(
                "Unable to submit your decision. Please make sure the backend is running."
            );


        } finally {

            setLoading(false);

        }

    };


    // =====================================================
    // DELETE ACCOUNT
    // =====================================================

    const handleDeleteAccount = async () => {

        setDeleteLoading(true);
        setError("");


        try {

            const accessToken =
                getAccessToken();


            if (!accessToken) {

                navigate(
                    "/login",
                    {
                        replace: true
                    }
                );

                return;

            }


            const response = await fetch(
                `${API_URL}/auth/account`,
                {
                    method: "DELETE",

                    headers: {
                        "Authorization":
                            `Bearer ${accessToken}`
                    }
                }
            );


            const data =
                await response.json();


            if (!response.ok) {

                throw new Error(
                    data.detail ||
                    "Unable to delete your account."
                );

            }


            localStorage.removeItem(
                "access_token"
            );


            navigate(
                "/login",
                {
                    replace: true
                }
            );


        } catch (err) {

            console.error(err);


            setError(
                err.message ||
                "Unable to delete your account."
            );


        } finally {

            setDeleteLoading(false);

        }

    };


    // =====================================================
    // TASKS TO DISPLAY
    // =====================================================

    const displayedTasks =
        showAllTasks
            ? recentTasks
            : recentTasks.slice(0, 3);


    return (

        <div className="dashboard">

            <aside className="dashboard-sidebar">

                <Link
                    to="/dashboard"
                    className="brand"
                >

                    <div className="brand-mark">
                        A
                    </div>


                    <div className="brand-name">
                        Agent<span>Swarm</span>
                    </div>

                </Link>


                <nav className="sidebar-nav">

                    <div className="nav-heading">
                        WORKSPACE
                    </div>


                    <Link
                        to="/dashboard"
                        className="nav-item active"
                    >

                        <span className="nav-icon">

                            <svg viewBox="0 0 24 24">
                                <path d="M4 13h6V4H4v9Zm0 7h6v-5H4v5Zm10 0h6v-9h-6v9Zm0-16v4h6V4h-6Z" />
                            </svg>

                        </span>

                        Dashboard

                    </Link>


                    <button
                        className="nav-item"
                        type="button"
                        onClick={() =>
                            document
                                .getElementById(
                                    "recent-tasks"
                                )
                                ?.scrollIntoView({
                                    behavior: "smooth"
                                })
                        }
                    >

                        <span className="nav-icon">

                            <svg viewBox="0 0 24 24">
                                <path d="M6 3h12a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Zm2 4v2h8V7H8Zm0 4v2h8v-2H8Zm0 4v2h5v-2H8Z" />
                            </svg>

                        </span>

                        Task history

                    </button>


                    <div className="nav-heading team-heading">
                        YOUR AI TEAM
                    </div>


                    <TeamMember
                        icon="✦"
                        title="Planner"
                        description="Understands your goal"
                        active={getTeamStatus(
                            taskState?.status,
                            "planner"
                        )}
                    />


                    <TeamMember
                        icon="⌕"
                        title="Researcher"
                        description="Finds useful information"
                        active={getTeamStatus(
                            taskState?.status,
                            "researcher"
                        )}
                    />


                    <TeamMember
                        icon="◆"
                        title="Builder"
                        description="Creates the solution"
                        active={getTeamStatus(
                            taskState?.status,
                            "coder"
                        )}
                    />


                    <TeamMember
                        icon="✓"
                        title="Reviewer"
                        description="Checks the result"
                        active={getTeamStatus(
                            taskState?.status,
                            "evaluator"
                        )}
                    />

                </nav>


                <div className="sidebar-bottom">

                    <button
                        type="button"
                        className="api-keys-btn"
                        onClick={() => setShowApiKeysModal(true)}
                    >
                        <span className="nav-icon">
                            <Key size={16} />
                        </span>
                        API Keys & Credits
                    </button>

                    <div className="account-card">

                        <div className="account-avatar">
                            {userAvatar ? (
                                <img
                                    src={userAvatar}
                                    alt={userName}
                                    className="account-avatar-img"
                                />
                            ) : (
                                (userName || userEmail || "U")[0].toUpperCase()
                            )}
                        </div>

                        <div className="account-details">

                            <strong>
                                {userName || "User"}
                            </strong>

                            <span title={userEmail}>
                                {userEmail ? (userEmail.length > 18 ? userEmail.slice(0, 16) + "..." : userEmail) : "Personal Account"}
                            </span>

                        </div>

                    </div>

                    <Link
                        to="/"
                        className="logout-button"
                        onClick={() => {
                            localStorage.removeItem("access_token");
                            localStorage.removeItem("user_id");
                            localStorage.removeItem("user_email");
                            localStorage.removeItem("user_name");
                            localStorage.removeItem("user_avatar");
                        }}
                    >

                        <span>
                            ↪
                        </span>

                        Log out

                    </Link>


                    {!deleteAccount ? (

                        <button
                            type="button"
                            className="delete-account-button"
                            onClick={() =>
                                setDeleteAccount(true)
                            }
                        >

                            <span>
                                ×
                            </span>

                            Delete account

                        </button>

                    ) : (

                        <div className="delete-confirmation">

                            <p>
                                Delete your account permanently?
                            </p>


                            <span>
                                Your account and associated tasks
                                will be deleted.
                            </span>


                            <div className="delete-actions">

                                <button
                                    type="button"
                                    className="delete-cancel-button"
                                    disabled={
                                        deleteLoading
                                    }
                                    onClick={() =>
                                        setDeleteAccount(
                                            false
                                        )
                                    }
                                >
                                    Cancel
                                </button>


                                <button
                                    type="button"
                                    className="delete-confirm-button"
                                    disabled={
                                        deleteLoading
                                    }
                                    onClick={
                                        handleDeleteAccount
                                    }
                                >

                                    {deleteLoading
                                        ? "Deleting..."
                                        : "Delete permanently"
                                    }

                                </button>

                            </div>

                        </div>

                    )}

                </div>

            </aside>


            <main className="dashboard-content">

                <header className="topbar">

                    <div>

                        <div className="small-label">
                            WORKSPACE
                        </div>

                        <div className="workspace-title-row">

                            <h1>
                                Good to see you, {userName || (userEmail ? userEmail.split("@")[0] : "there")}.
                            </h1>

                            <button
                                type="button"
                                className="edit-name-button"
                                title="Change display name"
                                aria-label="Change display name"
                                onClick={() => setShowNameModal(true)}
                            >
                                <Pencil size={15} />
                            </button>

                        </div>

                    </div>


                    <div className="system-status">

                        <span className="status-dot"></span>

                        AI team ready

                    </div>

                </header>


                <section className="workspace-grid">

                    <div className="composer-card">

                        <div className="composer-top">

                            <div className="eyebrow-pill">

                                <span>
                                    ✦
                                </span>

                                AI WORKSPACE

                            </div>

                        </div>


                        <h2>

                            What do you want

                            <br />

                            <span>
                                to accomplish?
                            </span>

                        </h2>


                        <p className="composer-description">

                            Tell AgentSwarm what you want in your own words.
                            Your AI team will plan, research, build and review it.

                        </p>


                        <form
                            className="task-form"
                            onSubmit={handleSubmit}
                        >

                            <textarea
                                value={task}
                                onChange={(event) =>
                                    setTask(
                                        event.target.value
                                    )
                                }
                                placeholder="Describe your task..."
                                disabled={loading}
                            />


                            <div className="composer-actions">

                                <span className="composer-tip">
                                    Be as simple or detailed as you like.
                                </span>


                                <button
                                    type="submit"
                                    className="start-button"
                                    disabled={loading}
                                >

                                    {loading
                                        ? "Working..."
                                        : "Start task"
                                    }

                                    <span>
                                        →
                                    </span>

                                </button>

                            </div>

                        </form>


                        {error && (

                            <div className="error-message">
                                {error}
                            </div>

                        )}


                        <div className="examples-section">

                            <div className="examples-title">
                                TRY AN EXAMPLE
                            </div>


                            <div className="example-list">

                                {exampleTasks.map(
                                    (example) => (

                                        <button
                                            key={example}
                                            type="button"
                                            className="example-button"
                                            onClick={() =>
                                                handleExampleClick(
                                                    example
                                                )
                                            }
                                        >

                                            {example}

                                        </button>

                                    )
                                )}

                            </div>

                        </div>

                    </div>


                    <div className="workflow-card">

                        <div className="workflow-header">

                            <div>

                                <div className="workflow-label">
                                    LIVE WORKFLOW
                                </div>


                                <h3>
                                    Your AI team
                                </h3>

                            </div>


                            <div
                                className={`workflow-badge ${getWorkflowBadgeClass(
                                    taskState?.status
                                )}`}
                            >

                                {getWorkflowBadge(
                                    taskState?.status
                                )}

                            </div>

                        </div>


                        <div className="workflow-list">

                            {/* Step 1: Planner */}
                            <WorkflowStep
                                number="01"
                                icon="✦"
                                title="Planner"
                                description="Decomposes goal into execution graph"
                                status={getWorkflowStepStatus(
                                    taskState?.status,
                                    "planner"
                                )}
                            />

                            <WorkflowLine
                                status={getWorkflowLineStatus(
                                    taskState?.status,
                                    "planner"
                                )}
                            />

                            {/* Step 2: Multi-Agent Worker Tier (Branching) */}
                            <div className="workflow-branch-tier">
                                <div className="workflow-branch-header">
                                    <span className="workflow-branch-label">
                                        02 · WORKERS
                                    </span>
                                    <span className="workflow-branch-sub">
                                        Researcher / Coder / Content
                                    </span>
                                </div>

                                <div className="workflow-worker-grid">
                                    <div
                                        className={`worker-pill ${getWorkerPillClass(
                                            taskState,
                                            "researcher"
                                        )}`}
                                    >
                                        <span className="worker-pill-icon">⌕</span>
                                        <div className="worker-pill-info">
                                            <strong>Researcher</strong>
                                            <span>
                                                {getWorkerPillStatusText(
                                                    taskState,
                                                    "researcher"
                                                )}
                                            </span>
                                        </div>
                                    </div>

                                    <div
                                        className={`worker-pill ${getWorkerPillClass(
                                            taskState,
                                            "coder"
                                        )}`}
                                    >
                                        <span className="worker-pill-icon">◆</span>
                                        <div className="worker-pill-info">
                                            <strong>Coder</strong>
                                            <span>
                                                {getWorkerPillStatusText(
                                                    taskState,
                                                    "coder"
                                                )}
                                            </span>
                                        </div>
                                    </div>

                                    <div
                                        className={`worker-pill ${getWorkerPillClass(
                                            taskState,
                                            "content"
                                        )}`}
                                    >
                                        <span className="worker-pill-icon">✎</span>
                                        <div className="worker-pill-info">
                                            <strong>Content</strong>
                                            <span>
                                                {getWorkerPillStatusText(
                                                    taskState,
                                                    "content"
                                                )}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <WorkflowLine
                                status={getWorkflowLineStatus(
                                    taskState?.status,
                                    "coder"
                                )}
                            />

                            {/* Step 3: Evaluator */}
                            <WorkflowStep
                                number="03"
                                icon="✓"
                                title="Evaluator"
                                description="RAG verification & quality verdict"
                                status={getWorkflowStepStatus(
                                    taskState?.status,
                                    "evaluator"
                                )}
                            />

                            <WorkflowLine
                                status={getWorkflowLineStatus(
                                    taskState?.status,
                                    "evaluator"
                                )}
                            />

                            {/* Step 4: Human Review */}
                            <WorkflowStep
                                number="04"
                                icon="◉"
                                title="Human Review"
                                description="Approve or request changes"
                                status={getWorkflowStepStatus(
                                    taskState?.status,
                                    "human"
                                )}
                            />

                            <WorkflowLine
                                status={getWorkflowLineStatus(
                                    taskState?.status,
                                    "human"
                                )}
                            />

                            {/* Step 5: Revision OR Finalizer Branch */}
                            <div className="workflow-decision-tier">
                                <div
                                    className={`decision-branch ${getDecisionBranchClass(
                                        taskState,
                                        "revision"
                                    )}`}
                                >
                                    <div className="decision-branch-header">
                                        <span className="decision-icon">↻</span>
                                        <strong>Revision</strong>
                                    </div>
                                    <span className="decision-sub">
                                        Loops back to Evaluator
                                    </span>
                                    {taskState?.revision_count > 0 && (
                                        <span className="decision-badge rev">
                                            Rev {taskState.revision_count}/2
                                        </span>
                                    )}
                                </div>

                                <div className="decision-or">
                                    OR
                                </div>

                                <div
                                    className={`decision-branch ${getDecisionBranchClass(
                                        taskState,
                                        "finalizer"
                                    )}`}
                                >
                                    <div className="decision-branch-header">
                                        <span className="decision-icon">→</span>
                                        <strong>Finalizer</strong>
                                    </div>
                                    <span className="decision-sub">
                                        Assembles final answer
                                    </span>
                                    {taskState?.status === "COMPLETED" && (
                                        <span className="decision-badge done">
                                            Done
                                        </span>
                                    )}
                                </div>
                            </div>

                        </div>


                        <div className="workflow-footer">

                            <span
                                className={`workflow-dot ${getWorkflowDotClass(
                                    taskState?.status
                                )}`}
                            ></span>


                            {taskState
                                ? formatStatus(
                                    taskState.status
                                )
                                : "Waiting for your next task"
                            }

                            {taskState?.status === "FAILED" && (
                                <span className="workflow-failure-hint">
                                    — see error details below
                                </span>
                            )}

                        </div>

                    </div>

                </section>


                {taskState && (

                    <TaskResult
                        taskState={taskState}
                        artifacts={artifacts}
                        artifactsLoading={artifactsLoading}
                        downloadingArtifact={
                            downloadingArtifact
                        }
                        onDownloadArtifact={
                            handleDownloadArtifact
                        }
                        feedback={feedback}
                        setFeedback={setFeedback}
                        onApproval={handleApproval}
                        onStop={handleStopTask}
                        stoppingTask={stoppingTask}
                        onDelete={handleDeleteTask}
                        deletingTaskId={
                            deletingTaskId
                        }
                        onRetry={handleRetryTask}
                        loading={
                            loading ||
                            Boolean(openingTaskId)
                        }
                    />

                )}


                <section
                    className="recent-section"
                    id="recent-tasks"
                >

                    <div className="section-header">

                        <div>

                            <div className="small-label">
                                WORKSPACE
                            </div>


                            <h2>
                                Recent tasks
                            </h2>

                        </div>


                        {recentTasks.length > 3 && (

                            <button
                                className="view-all-button"
                                type="button"
                                onClick={() =>
                                    setShowAllTasks(
                                        (previous) =>
                                            !previous
                                    )
                                }
                            >

                                {showAllTasks
                                    ? "Show less ↑"
                                    : "View all →"
                                }

                            </button>

                        )}

                    </div>


                    {historyLoading ? (

                        <div className="recent-grid">

                            <div className="recent-card">

                                <p>
                                    Loading your tasks...
                                </p>

                            </div>

                        </div>

                    ) : recentTasks.length === 0 ? (

                        <div className="recent-grid">

                            <div className="recent-card">

                                <div className="recent-top">

                                    <div className="recent-icon">
                                        ✦
                                    </div>

                                </div>


                                <h3>
                                    No tasks yet
                                </h3>


                                <p>
                                    Start your first AgentSwarm task
                                    and it will appear here.
                                </p>

                            </div>

                        </div>

                    ) : (

                        <div className="recent-grid">

                            {displayedTasks.map(
                                (recentTask) => (

                                    <RecentTask
                                        key={
                                            recentTask.task_id
                                        }

                                        icon={
                                            getTaskIcon(
                                                recentTask.status
                                            )
                                        }

                                        title={
                                            getTaskTitle(
                                                recentTask.goal
                                            )
                                        }

                                        description={
                                            recentTask.goal
                                        }

                                        status={
                                            formatStatus(
                                                recentTask.status
                                            )
                                        }

                                        statusType={
                                            getStatusType(
                                                recentTask.status
                                            )
                                        }

                                        time={
                                            formatTaskTime(
                                                recentTask.created_at
                                            )
                                        }

                                        taskId={
                                            recentTask.task_id
                                        }

                                        onOpen={
                                            handleOpenTask
                                        }

                                        onShare={
                                            handleShareTask
                                        }

                                        onDelete={
                                            handleDeleteTask
                                        }

                                        openingTaskId={
                                            openingTaskId
                                        }

                                        deletingTaskId={
                                            deletingTaskId
                                        }

                                    />

                                )
                            )}

                        </div>

                    )}

                </section>


                <footer className="dashboard-footer">

                    <span>
                        AgentSwarm
                    </span>


                    <span>
                        Multi-agent task orchestration
                    </span>

                </footer>

            </main>

            <ApiKeysModal
                isOpen={showApiKeysModal}
                onClose={() => setShowApiKeysModal(false)}
            />

            <NamePromptModal
                isOpen={showNameModal}
                onClose={() => setShowNameModal(false)}
                currentName={userName}
                onSaveSuccess={(newName) => setUserName(newName)}
            />

        </div>

    );

}


// =========================================================
// TEAM MEMBER
// =========================================================

function TeamMember({
    icon,
    title,
    description,
    active
}) {

    return (

        <div
            className={`team-member ${active === "active"
                    ? "team-member-active"
                    : active === "completed"
                        ? "team-member-completed"
                        : ""
                }`}
        >

            <div className="team-icon">
                {icon}
            </div>


            <div className="team-text">

                <strong>
                    {title}
                </strong>


                <span>
                    {description}
                </span>

            </div>


            {active === "active" && (

                <span className="team-status">
                    WORKING
                </span>

            )}


            {active === "completed" && (

                <span className="team-status completed">
                    DONE
                </span>

            )}

        </div>

    );

}


// =========================================================
// WORKFLOW STEP
// =========================================================

function WorkflowStep({
    number,
    icon,
    title,
    description,
    status
}) {

    return (

        <div
            className={`workflow-step ${status === "active"
                    ? "workflow-step-active"
                    : status === "completed"
                        ? "workflow-step-completed"
                        : status === "waiting"
                            ? "workflow-step-waiting"
                            : ""
                }`}
        >

            <div className="workflow-number">
                {number}
            </div>


            <div className="workflow-icon">

                {status === "completed"
                    ? "✓"
                    : icon
                }

            </div>


            <div className="workflow-step-text">

                <strong>
                    {title}
                </strong>


                <span>
                    {description}
                </span>

            </div>


            {status === "active" && (

                <span className="workflow-step-status">
                    ACTIVE
                </span>

            )}


            {status === "completed" && (

                <span className="workflow-step-status completed">
                    DONE
                </span>

            )}


            {status === "waiting" && (

                <span className="workflow-step-status waiting">
                    WAITING
                </span>

            )}

        </div>

    );

}


// =========================================================
// WORKFLOW LINE
// =========================================================

function WorkflowLine({
    status
}) {

    return (

        <div
            className={`workflow-line ${status === "completed"
                    ? "workflow-line-completed"
                    : ""
                }`}
        >

            <span></span>

        </div>

    );

}


// =========================================================
// TASK RESULT
// =========================================================

function TaskResult({
    taskState,
    artifacts,
    artifactsLoading,
    downloadingArtifact,
    onDownloadArtifact,
    feedback,
    setFeedback,
    onApproval,
    onStop,
    stoppingTask,
    onDelete,
    deletingTaskId,
    onRetry,
    loading
}) {

    const waitingForHuman =
        taskState.status ===
        "WAITING_FOR_HUMAN";


    const completed =
        taskState.status ===
        "COMPLETED";


    const stopped =
        taskState.status ===
        "STOPPED";


    const failed =
        taskState.status ===
        "FAILED";


    const evaluationUnavailable =
        taskState.status ===
        "EVALUATION_UNAVAILABLE";


    const canStop =
        !waitingForHuman &&
        !completed &&
        !stopped &&
        !failed &&
        !evaluationUnavailable;


    const canDelete =
        completed ||
        stopped ||
        failed;


    return (

        <section
            className="result-section"
            id="task-result"
        >

            <div className="result-header">

                <div>

                    <div className="small-label">
                        TASK STATUS
                    </div>


                    <h2>

                        {completed

                            ? "Task completed"

                            : stopped

                                ? "Task stopped"

                                : failed

                                    ? "Task failed"

                                    : evaluationUnavailable

                                        ? "Evaluation temporarily unavailable"

                                        : waitingForHuman

                                            ? "Your review is needed"

                                            : "AgentSwarm is working"

                        }

                    </h2>

                </div>


                <div className="task-status-pill">

                    <span></span>


                    {formatStatus(
                        taskState.status
                    )}

                </div>

            </div>


            <div className="task-meta">

                <div>

                    <span>
                        Task ID
                    </span>


                    <strong>
                        {taskState.task_id}
                    </strong>

                </div>


                <div>

                    <span>
                        Revisions
                    </span>


                    <strong>
                        {taskState.revision_count}
                    </strong>

                </div>

            </div>


            <div className="result-grid">

                <div className="result-card">

                    <div className="result-card-title">

                        <span>
                            01
                        </span>

                        PLAN

                    </div>


                    <div className="result-content">

                        {taskState.plan

                            ? (

                                <pre>
                                    {taskState.plan}
                                </pre>

                            )

                            : failed
                                ? "Did not run (task failed)"
                                : "Planning in progress..."}

                    </div>

                </div>


                <div className="result-card">

                    <div className="result-card-title">

                        <span>
                            02
                        </span>

                        RESEARCH

                    </div>


                    <div className="result-content">

                        {taskState.research

                            ? (

                                <pre>
                                    {taskState.research}
                                </pre>

                            )

                            : failed
                                ? "Did not run (task failed)"
                                : "Research in progress..."}

                    </div>

                </div>


                <div className="result-card">

                    <div className="result-card-title">

                        <span>
                            03
                        </span>

                        CONTENT

                    </div>


                    <div className="result-content">

                        {taskState.content

                            ? (

                                <pre>
                                    {taskState.content}
                                </pre>

                            )

                            : failed
                                ? "Did not run (task failed)"
                                : "Content generation in progress..."}

                    </div>

                </div>


                <div className="result-card">

                    <div className="result-card-title">

                        <span>
                            04
                        </span>

                        CODE

                    </div>


                    <div className="result-content">

                        {taskState.code

                            ? (

                                <pre>
                                    {taskState.code}
                                </pre>

                            )

                            : failed
                                ? "Did not run (task failed)"
                                : "Code generation not required or in progress..."}

                    </div>

                </div>


                <div className="result-card">

                    <div className="result-card-title">

                        <span>
                            05
                        </span>

                        REVIEW

                    </div>


                    <div className="result-content">

                        {taskState.evaluation

                            ? (

                                <pre>
                                    {taskState.evaluation}
                                </pre>

                            )

                            : evaluationUnavailable

                                ? (

                                    <div>

                                        Evaluation temporarily unavailable
                                        because the Gemini evaluator quota has
                                        been exhausted. The worker output was
                                        generated but could not be verified.

                                    </div>

                                )

                                : failed
                                    ? "Did not run (task failed)"
                                    : "Review in progress..."}

                    </div>

                </div>

            </div>


            {/* =================================================
                GENERATED ARTIFACTS
            ================================================= */}

            {(artifactsLoading ||
                artifacts.length > 0) && (

                    <div className="artifacts-panel">

                        <div className="artifacts-header">

                            <div>

                                <div className="small-label">
                                    ARTIFACTS
                                </div>


                                <h3>
                                    Generated files
                                </h3>

                            </div>


                            {!artifactsLoading && (

                                <span>

                                    {artifacts.length}
                                    {" "}
                                    {artifacts.length === 1
                                        ? "file"
                                        : "files"
                                    }

                                </span>

                            )}

                        </div>


                        {artifactsLoading ? (

                            <div className="artifacts-loading">
                                Loading generated files...
                            </div>

                        ) : (

                            <div className="artifacts-list">

                                {artifacts.map(
                                    (artifact) => {

                                        const downloadKey =
                                            `${taskState.task_id}:${artifact.filename}`;


                                        const isDownloading =
                                            downloadingArtifact ===
                                            downloadKey;


                                        return (

                                            <div
                                                className="artifact-item"
                                                key={
                                                    artifact.filename
                                                }
                                            >

                                                <div className="artifact-icon">
                                                    ▣
                                                </div>


                                                <div className="artifact-details">

                                                    <strong>
                                                        {artifact.filename}
                                                    </strong>


                                                    <span>
                                                        {formatArtifactSize(
                                                            artifact.size_bytes
                                                        )}
                                                    </span>

                                                </div>


                                                <button
                                                    type="button"
                                                    className="artifact-download-button"
                                                    disabled={
                                                        isDownloading
                                                    }
                                                    onClick={() =>
                                                        onDownloadArtifact(
                                                            taskState.task_id,
                                                            artifact.filename
                                                        )
                                                    }
                                                    title="Download artifact"
                                                    aria-label={`Download ${artifact.filename}`}
                                                >

                                                    {isDownloading ? (

                                                        <span>
                                                            Downloading...
                                                        </span>

                                                    ) : (

                                                        <>

                                                            <Download
                                                                size={15}
                                                                strokeWidth={1.8}
                                                            />

                                                            <span>
                                                                Download
                                                            </span>

                                                        </>

                                                    )}

                                                </button>

                                            </div>

                                        );

                                    }
                                )}

                            </div>

                        )}

                    </div>

                )}


            {evaluationUnavailable && (

                <div className="task-control-panel">

                    <div>

                        <strong>
                            Evaluation temporarily unavailable
                        </strong>


                        <p>
                            The worker output was generated, but the Gemini
                            Evaluator could not verify it because the API
                            quota is currently exhausted. AgentSwarm did not
                            treat the result as approved.
                        </p>

                    </div>

                </div>

            )}


            {canStop && (

                <div className="task-control-panel">

                    <div>

                        <strong>
                            Stop this task?
                        </strong>


                        <p>
                            AgentSwarm will stop the workflow at the next safe point.
                        </p>

                    </div>


                    <button
                        type="button"
                        className="stop-task-button"
                        disabled={
                            stoppingTask ||
                            loading
                        }
                        onClick={() =>
                            onStop(
                                taskState.task_id
                            )
                        }
                    >

                        {stoppingTask
                            ? "Stopping..."
                            : "Stop task"
                        }

                    </button>

                </div>

            )}


            {canDelete && (

                <div className="task-control-panel">

                    <div>

                        <strong>
                            Task management
                        </strong>


                        <p>
                            {failed
                                ? "This task did not complete. You can retry it with the same goal or remove it."
                                : "This task is no longer running and can be removed from your history."
                            }
                        </p>

                    </div>


                    <div className="task-control-actions">

                        {failed && onRetry && (
                            <button
                                type="button"
                                className="retry-task-button"
                                onClick={() =>
                                    onRetry(taskState.goal)
                                }
                                title="Load goal and retry"
                            >
                                ↺ Retry task
                            </button>
                        )}

                        <button
                            type="button"
                            className="delete-task-button"
                            disabled={
                                deletingTaskId ===
                                taskState.task_id
                            }
                            onClick={() =>
                                onDelete(
                                    taskState.task_id
                                )
                            }
                        >

                            {deletingTaskId ===
                                taskState.task_id
                                ? "Deleting..."
                                : "Delete task"
                            }

                        </button>

                    </div>

                </div>

            )}


            {waitingForHuman && (

                <div className="approval-panel">

                    <div className="approval-icon">
                        ✓
                    </div>


                    <div className="approval-content">

                        <div className="approval-label">
                            YOUR DECISION
                        </div>


                        <h3>
                            AgentSwarm needs your approval
                        </h3>


                        <p>

                            The AI team has finished reviewing the
                            implementation. Take a look at the result
                            and decide whether to finalize it or ask
                            the team to improve it.

                        </p>


                        <div className="approval-actions">

                            <button
                                type="button"
                                className="approve-button"
                                disabled={loading}
                                onClick={() =>
                                    onApproval(true)
                                }
                            >

                                {loading
                                    ? "Processing..."
                                    : "Approve & finalize"
                                }


                                <span>
                                    ✓
                                </span>

                            </button>

                        </div>


                        <div className="revision-box">

                            <label>
                                Want something changed?
                            </label>


                            <textarea
                                value={feedback}
                                onChange={(event) =>
                                    setFeedback(
                                        event.target.value
                                    )
                                }
                                placeholder="Tell the AI team what you'd like them to improve..."
                                disabled={loading}
                            />


                            <button
                                type="button"
                                className="revision-button"
                                disabled={loading}
                                onClick={() =>
                                    onApproval(false)
                                }
                            >

                                Ask for improvements

                                <span>
                                    ↻
                                </span>

                            </button>

                        </div>

                    </div>

                </div>

            )}


            {completed &&
                taskState.final_answer && (

                    <div className="final-answer">

                        <div className="final-answer-header">

                            <div className="final-check">
                                ✓
                            </div>


                            <div>

                                <div className="small-label">
                                    FINAL RESULT
                                </div>


                                <h3>
                                    Your task is complete
                                </h3>

                            </div>

                        </div>


                        <div className="final-answer-content">

                            <ReactMarkdown
                                remarkPlugins={[
                                    remarkGfm
                                ]}
                            >
                                {taskState.final_answer}
                            </ReactMarkdown>

                        </div>

                    </div>

                )}

            {failed && (

                <div className="task-failure-panel">

                    <div className="task-failure-header">

                        <div className="failure-icon">
                            ⚠️
                        </div>

                        <div>

                            <div className="small-label" style={{ color: "#ef4444" }}>
                                ERROR DETAILS
                            </div>

                            <h3>
                                Why this task failed
                            </h3>

                        </div>

                    </div>

                    <div className="task-failure-content">

                        {taskState.final_answer ? (
                            <ReactMarkdown
                                remarkPlugins={[
                                    remarkGfm
                                ]}
                            >
                                {taskState.final_answer}
                            </ReactMarkdown>
                        ) : (
                            <p>
                                An error occurred while executing this workflow. Check your API keys and configuration in the left sidebar, or click Retry above.
                            </p>
                        )}

                    </div>

                </div>

            )}

        </section>

    );

}


// =========================================================
// RECENT TASK
// =========================================================

function RecentTask({
    icon,
    title,
    description,
    status,
    statusType,
    time,
    taskId,
    onOpen,
    onShare,
    onDelete,
    openingTaskId,
    deletingTaskId
}) {

    const [menuOpen, setMenuOpen] =
        useState(false);

    const isOpening =
        openingTaskId === taskId;

    const isDeleting =
        deletingTaskId === taskId;


    const canDelete =
        statusType === "completed" ||
        statusType === "failed" ||
        statusType === "stopped";


    useEffect(() => {

        if (!menuOpen) {

            return;

        }


        const handleOutsideClick =
            (event) => {

                if (
                    !event.target.closest(
                        ".recent-actions"
                    )
                ) {

                    setMenuOpen(false);

                }

            };


        document.addEventListener(
            "mousedown",
            handleOutsideClick
        );


        return () => {

            document.removeEventListener(
                "mousedown",
                handleOutsideClick
            );

        };

    }, [
        menuOpen
    ]);


    const handleShare = async (e) => {

        e?.stopPropagation?.();

        setMenuOpen(false);


        await onShare(
            taskId,
            title,
            description
        );

    };


    const handleDelete = (e) => {

        e?.stopPropagation?.();

        setMenuOpen(false);


        onDelete(
            taskId
        );

    };


    return (

        <div
            className="recent-card recent-card-interactive"
            onClick={(e) => {
                if (!e.target.closest(".recent-actions")) {
                    onOpen(taskId);
                }
            }}
            onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                    if (!e.target.closest(".recent-actions")) {
                        e.preventDefault();
                        onOpen(taskId);
                    }
                }
            }}
            role="button"
            tabIndex={0}
            title="Click to open task"
        >

            <div className="recent-top">

                <div className="recent-icon">
                    {icon}
                </div>


                <div
                    className={`recent-status ${statusType}`}
                >

                    <span></span>

                    {status}

                </div>

            </div>


            <h3>
                {title}
            </h3>


            <p>
                {description}
            </p>


            <div className="recent-bottom">

                <span>
                    {time}
                </span>


                <div className="recent-actions">

                    <button
                        type="button"
                        className="recent-open-button"
                        disabled={isOpening}
                        onClick={(e) => {
                            e.stopPropagation();
                            onOpen(taskId);
                        }}
                    >

                        {isOpening
                            ? "Opening..."
                            : "Open"
                        }

                    </button>


                    <div className="recent-menu-wrapper">

                        <button
                            type="button"
                            className={`recent-menu-button ${menuOpen
                                    ? "recent-menu-button-open"
                                    : ""
                                }`}
                            onClick={(e) => {
                                e.stopPropagation();
                                setMenuOpen(
                                    (previous) =>
                                        !previous
                                );
                            }}
                            title="More options"
                            aria-label="More options"
                            aria-expanded={
                                menuOpen
                            }
                        >

                            <MoreHorizontal
                                size={16}
                                strokeWidth={1.9}
                            />

                        </button>


                        {menuOpen && (

                            <div className="recent-menu">

                                <button
                                    type="button"
                                    className="recent-menu-item"
                                    onClick={
                                        handleShare
                                    }
                                >

                                    <Share2
                                        size={14}
                                        strokeWidth={1.8}
                                    />


                                    <span>
                                        Share
                                    </span>

                                </button>


                                {canDelete && (

                                    <button
                                        type="button"
                                        className="recent-menu-item recent-menu-delete"
                                        disabled={
                                            isDeleting
                                        }
                                        onClick={
                                            handleDelete
                                        }
                                    >

                                        <Trash2
                                            size={14}
                                            strokeWidth={1.8}
                                        />


                                        <span>

                                            {isDeleting
                                                ? "Deleting..."
                                                : "Delete"
                                            }

                                        </span>

                                    </button>

                                )}

                            </div>

                        )}

                    </div>

                </div>

            </div>

        </div>

    );

}


// =========================================================
// TASK TITLE
// =========================================================

function getTaskTitle(goal) {

    if (!goal) {

        return "Untitled task";

    }


    if (goal.length <= 32) {

        return goal;

    }


    return `${goal.slice(0, 32)}...`;

}


// =========================================================
// TASK ICON
// =========================================================

function getTaskIcon(status) {

    if (status === "COMPLETED") {

        return "✓";

    }


    if (
        status ===
        "WAITING_FOR_HUMAN"
    ) {

        return "◉";

    }


    if (status === "FAILED") {

        return "×";

    }


    if (status === "STOPPED") {

        return "■";

    }


    if (
        status ===
        "EVALUATION_UNAVAILABLE"
    ) {

        return "⚠";

    }


    return "◆";

}


// =========================================================
// STATUS TYPE
// =========================================================

function getStatusType(status) {

    if (status === "COMPLETED") {

        return "completed";

    }


    if (
        status ===
        "WAITING_FOR_HUMAN"
    ) {

        return "review";

    }


    if (status === "FAILED") {

        return "failed";

    }


    if (status === "STOPPED") {

        return "stopped";

    }


    if (
        status ===
        "EVALUATION_UNAVAILABLE"
    ) {

        return "evaluation-unavailable";

    }


    return "review";

}


// =========================================================
// WORKFLOW STATUS
// =========================================================

function getWorkflowStage(status) {

    if (!status) {

        return 0;

    }


    if (
        status === "STARTING" ||
        status === "PLANNING"
    ) {

        return 1;

    }


    if (status === "RESEARCHING") {

        return 2;

    }


    if (
        status === "CODING" ||
        status === "CREATING_CONTENT" ||
        status === "REVISING"
    ) {

        return 3;

    }


    if (
        status === "EVALUATING" ||
        status === "EVALUATION_UNAVAILABLE"
    ) {

        return 4;

    }


    if (status === "WAITING_FOR_HUMAN") {

        return 5;

    }


    if (status === "FINALIZING") {

        return 6;

    }


    if (status === "COMPLETED") {

        return 7;

    }


    return 0;

}


// =========================================================
// WORKFLOW STEP STATUS
// =========================================================

function getWorkflowStepStatus(
    status,
    agent
) {

    const stage =
        getWorkflowStage(status);


    const agentStages = {

        planner: 1,
        researcher: 2,
        coder: 3,
        evaluator: 4,
        human: 5,
        finalizer: 6

    };


    const agentStage =
        agentStages[agent];


    if (!agentStage) {

        return "";

    }


    /*
     * Gemini evaluator quota/error state.
     *
     * The evaluator did not successfully complete,
     * so it is shown as waiting rather than DONE.
     */

    if (
        status ===
        "EVALUATION_UNAVAILABLE"
    ) {

        if (agent === "evaluator") {

            return "waiting";

        }


        if (agentStage < 4) {

            return "completed";

        }


        return "waiting";

    }


    /*
     * Human review state.
     */

    if (
        status ===
        "WAITING_FOR_HUMAN"
    ) {

        if (agent === "human") {

            return "active";

        }


        if (agentStage < 5) {

            return "completed";

        }


        return "";

    }


    /*
     * Fully completed workflow.
     */

    if (
        status ===
        "COMPLETED"
    ) {

        return "completed";

    }


    /*
     * Failed/stopped workflows:
     * completed previous stages remain completed.
     */

    if (
        status === "FAILED" ||
        status === "STOPPED"
    ) {

        if (
            stage >
            agentStage
        ) {

            return "completed";

        }


        if (
            stage ===
            agentStage
        ) {

            return "active";

        }


        return "";

    }


    /*
     * Normal running workflow.
     */

    if (
        stage >
        agentStage
    ) {

        return "completed";

    }


    if (
        stage ===
        agentStage
    ) {

        return "active";

    }


    return "";

}


// =========================================================
// WORKFLOW LINE STATUS
// =========================================================

function getWorkflowLineStatus(
    status,
    previousAgent
) {

    const stage =
        getWorkflowStage(status);


    const agentStages = {

        planner: 1,
        researcher: 2,
        coder: 3,
        evaluator: 4,
        human: 5

    };


    const previousStage =
        agentStages[previousAgent];


    if (!previousStage) {

        return "";

    }


    if (
        status === "COMPLETED" ||
        stage > previousStage
    ) {

        return "completed";

    }


    return "";

}


// =========================================================
// WORKER PILL CLASS & STATUS
// =========================================================

function getWorkerPillClass(taskState, worker) {
    if (!taskState) {
        return "";
    }

    const status = taskState.status;
    const stage = getWorkflowStage(status);

    if (worker === "researcher") {
        if (status === "RESEARCHING") {
            return "worker-active";
        }
        if (taskState.research || stage > 2) {
            return "worker-done";
        }
    }

    if (worker === "coder") {
        if (status === "CODING") {
            return "worker-active";
        }
        if (taskState.code || stage > 3) {
            return "worker-done";
        }
    }

    if (worker === "content") {
        if (status === "CREATING_CONTENT") {
            return "worker-active";
        }
        if (taskState.content || stage > 3) {
            return "worker-done";
        }
    }

    return "";
}


function getWorkerPillStatusText(taskState, worker) {
    if (!taskState) {
        return "Ready";
    }

    const status = taskState.status;
    const stage = getWorkflowStage(status);

    if (worker === "researcher") {
        if (status === "RESEARCHING") {
            return "Active";
        }
        if (taskState.research || stage > 2) {
            return "Done";
        }
    }

    if (worker === "coder") {
        if (status === "CODING") {
            return "Active";
        }
        if (taskState.code || stage > 3) {
            return "Done";
        }
    }

    if (worker === "content") {
        if (status === "CREATING_CONTENT") {
            return "Active";
        }
        if (taskState.content || stage > 3) {
            return "Done";
        }
    }

    return "Ready";
}


// =========================================================
// DECISION BRANCH CLASS
// =========================================================

function getDecisionBranchClass(taskState, branch) {
    if (!taskState) {
        return "";
    }

    const status = taskState.status;

    if (branch === "revision") {
        if (status === "REVISING") {
            return "decision-active decision-revising";
        }
        if (taskState.revision_count > 0) {
            return "decision-had-revision";
        }
    }

    if (branch === "finalizer") {
        if (status === "FINALIZING") {
            return "decision-active";
        }
        if (status === "COMPLETED") {
            return "decision-completed";
        }
    }

    return "";
}


// =========================================================
// WORKFLOW BADGE
// =========================================================

function getWorkflowBadge(status) {

    if (!status) {

        return "READY";

    }


    const labels = {

        STARTING:
            "STARTING",

        PLANNING:
            "PLANNING",

        RESEARCHING:
            "RESEARCHING",

        CODING:
            "CODING",

        CREATING_CONTENT:
            "CONTENT",

        REVISING:
            "REVISING",

        EVALUATING:
            "EVALUATING",

        WAITING_FOR_HUMAN:
            "WAITING FOR HUMAN",

        FINALIZING:
            "FINALIZING",

        COMPLETED:
            "COMPLETED",

        FAILED:
            "FAILED",

        STOPPED:
            "STOPPED",

        EVALUATION_UNAVAILABLE:
            "EVALUATION UNAVAILABLE"

    };


    return (
        labels[status] ||
        status ||
        "RUNNING"
    );

}


// =========================================================
// WORKFLOW BADGE CLASS
// =========================================================

function getWorkflowBadgeClass(
    status
) {

    if (!status) {

        return "";

    }


    if (
        status ===
        "COMPLETED"
    ) {

        return "workflow-badge-completed";

    }


    if (
        status ===
        "FAILED"
    ) {

        return "workflow-badge-failed";

    }


    if (
        status ===
        "WAITING_FOR_HUMAN"
    ) {

        return "workflow-badge-waiting";

    }


    if (
        status ===
        "STOPPED"
    ) {

        return "workflow-badge-stopped";

    }


    if (
        status ===
        "EVALUATION_UNAVAILABLE"
    ) {

        return "workflow-badge-failed";

    }


    return "workflow-badge-active";

}


// =========================================================
// WORKFLOW DOT CLASS
// =========================================================

function getWorkflowDotClass(
    status
) {

    if (
        status ===
        "COMPLETED"
    ) {

        return "workflow-dot-completed";

    }


    if (
        status ===
        "FAILED"
    ) {

        return "workflow-dot-failed";

    }


    if (
        status ===
        "WAITING_FOR_HUMAN"
    ) {

        return "workflow-dot-waiting";

    }


    if (
        status ===
        "STOPPED"
    ) {

        return "workflow-dot-stopped";

    }


    if (
        status ===
        "EVALUATION_UNAVAILABLE"
    ) {

        return "workflow-dot-failed";

    }


    if (status) {

        return "workflow-dot-active";

    }


    return "";

}


// =========================================================
// AI TEAM STATUS
// =========================================================

function getTeamStatus(
    status,
    agent
) {

    const workflowStage =
        getWorkflowStage(status);


    const agentStages = {

        planner: 1,
        researcher: 2,
        coder: 3,
        evaluator: 4

    };


    const agentStage =
        agentStages[agent];


    if (
        !agentStage ||
        !status
    ) {

        return "";

    }


    if (
        status ===
        "WAITING_FOR_HUMAN" &&
        agent === "evaluator"
    ) {

        return "completed";

    }


    if (
        status ===
        "EVALUATION_UNAVAILABLE" &&
        agent === "evaluator"
    ) {

        return "";

    }


    if (
        status ===
        "COMPLETED"
    ) {

        return "completed";

    }


    if (
        workflowStage >
        agentStage
    ) {

        return "completed";

    }


    if (
        workflowStage ===
        agentStage
    ) {

        return "active";

    }


    return "";

}


// =========================================================
// TASK TIME
// =========================================================

function formatTaskTime(
    createdAt
) {

    if (!createdAt) {

        return "";

    }


    const created =
        new Date(createdAt);


    if (
        Number.isNaN(
            created.getTime()
        )
    ) {

        return "";

    }


    const now =
        new Date();


    const difference =
        now.getTime() -
        created.getTime();


    const minutes =
        Math.floor(
            difference / 60000
        );


    if (minutes < 1) {

        return "Just now";

    }


    if (minutes < 60) {

        return `${minutes} min ago`;

    }


    const hours =
        Math.floor(
            minutes / 60
        );


    if (hours < 24) {

        return `${hours} hr ago`;

    }


    const days =
        Math.floor(
            hours / 24
        );


    if (days === 1) {

        return "Yesterday";

    }


    return `${days} days ago`;

}


// =========================================================
// STATUS LABEL
// =========================================================

function formatStatus(
    status
) {

    const labels = {

        STARTING:
            "Starting",

        PLANNING:
            "Planning",

        RESEARCHING:
            "Researching",

        CODING:
            "Coding",

        CREATING_CONTENT:
            "Creating content",

        EVALUATING:
            "Evaluating",

        WAITING_FOR_HUMAN:
            "Waiting for your review",

        REVISING:
            "Revising",

        FINALIZING:
            "Finalizing",

        COMPLETED:
            "Completed",

        FAILED:
            "Failed",

        STOPPED:
            "Stopped",

        EVALUATION_UNAVAILABLE:
            "Evaluation unavailable"

    };


    return (
        labels[status] ||
        status ||
        "Ready"
    );

}


// =========================================================
// ARTIFACT SIZE
// =========================================================

function formatArtifactSize(
    size
) {

    if (
        !Number.isFinite(size)
    ) {

        return "";

    }


    if (
        size < 1024
    ) {

        return `${size} B`;

    }


    if (
        size <
        1024 * 1024
    ) {

        return `${(
            size / 1024
        ).toFixed(1)} KB`;

    }


    return `${(
        size /
        (1024 * 1024)
    ).toFixed(1)} MB`;

}


export default Dashboard;
