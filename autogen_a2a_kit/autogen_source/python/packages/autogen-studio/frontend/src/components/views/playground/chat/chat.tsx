import * as React from "react";
import { Button, message, Tooltip, Dropdown } from "antd";
import type { MenuProps } from "antd";
import { convertFilesToBase64, getServerUrl } from "../../../utils/utils";
import { IStatus } from "../../../types/app";
import {
  Run,
  Message,
  WebSocketMessage,
  TeamConfig,
  AgentMessageConfig,
  RunStatus,
  TeamResult,
  Session,
  Component,
  ModelClientStreamingChunkEvent,
} from "../../../types/datamodel";
import { appContext } from "../../../../hooks/provider";
import ChatInput from "./chatinput";
import { teamAPI } from "../../teambuilder/api";
import { sessionAPI } from "../api";
import RunView from "./runview";
import { createTimeoutConfig } from "./types";
import {
  ChevronRight,
  MessagesSquare,
  SplitSquareHorizontal,
  X,
  Network,
  GitBranch,
  Activity,
  ArrowRight,
  Circle,
  Shuffle,
  ChevronDown,
} from "lucide-react";
import AgentFlow from "./agentflow/agentflow";
import SessionDropdown from "./sessiondropdown";
import { RcFile } from "antd/es/upload";
import { useSettingsStore } from "../../settings/store";
import { getPatternById, getPatternByProvider, getPatternSelectorPrompt, PATTERN_LIBRARY, PatternDefinition } from "./agentflow/patterns/pattern-schema";
import { applyPatternComplete, validateTeamForExecution } from "./team-runtime";
const logo = require("../../../../images/landing/welcome.svg").default;

interface ChatViewProps {
  session: Session | null;
  isCompareMode?: boolean;
  isSecondaryView?: boolean; // To know if this is the right panel
  onCompareClick?: () => void;
  onExitCompare?: () => void;
  onSessionChange?: (session: Session) => void;
  availableSessions?: Session[];
  showCompareButton?: boolean;
}

export default function ChatView({
  session,
  isCompareMode = false,
  isSecondaryView = false,
  onCompareClick,
  onExitCompare,
  onSessionChange,
  availableSessions = [],
  showCompareButton = true,
}: ChatViewProps) {
  const serverUrl = getServerUrl();
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<IStatus | null>({
    status: true,
    message: "All good",
  });

  // Core state
  const [existingRuns, setExistingRuns] = React.useState<Run[]>([]);
  const [currentRun, setCurrentRun] = React.useState<Run | null>(null);
  const [messageApi, contextHolder] = message.useMessage();

  const chatContainerRef = React.useRef<HTMLDivElement | null>(null);
  const [streamingContent, setStreamingContent] = React.useState<{
    runId: number;
    content: string;
    source: string;
  } | null>(null);

  // View mode: "pattern" shows team structure, "execution" shows actual message flow
  const [viewMode, setViewMode] = React.useState<"pattern" | "execution">("pattern");

  // Pattern selection from schema (all 8 patterns available!)
  const [selectedPatternId, setSelectedPatternId] = React.useState<string>("sequential");

  // Get current pattern definition from schema
  const selectedPattern = React.useMemo(() =>
    getPatternById(selectedPatternId) || PATTERN_LIBRARY[0],
    [selectedPatternId]
  );

  // Pattern menu items generated from schema (not hardcoded!)
  const patternMenuItems: MenuProps["items"] = React.useMemo(() =>
    PATTERN_LIBRARY.map((pattern: PatternDefinition) => ({
      key: pattern.id,
      icon: pattern.id === "sequential" ? <ArrowRight className="w-4 h-4" /> :
            pattern.id === "selector" ? <Circle className="w-4 h-4" /> :
            pattern.id === "swarm" ? <Shuffle className="w-4 h-4" /> :
            pattern.id === "reflection" ? <Activity className="w-4 h-4" /> :
            <Network className="w-4 h-4" />,
      label: pattern.name,
    })),
    []
  );

  // Context and config
  const { user } = React.useContext(appContext);
  // const { session, sessions } = useConfigStore();
  const [activeSocket, setActiveSocket] = React.useState<WebSocket | null>(
    null
  );
  const [teamConfig, setTeamConfig] =
    React.useState<Component<TeamConfig> | null>(null);

  // Get modified teamConfig based on selected pattern using modular team-runtime
  // Updated to use applyPatternComplete for full configuration
  const effectiveTeamConfig = React.useMemo((): Component<TeamConfig> | null => {
    if (!selectedPatternId) return teamConfig;

    // Use the enhanced applyPatternComplete function from team-runtime
    // This ensures model_client and termination_condition are properly set
    const result = applyPatternComplete(teamConfig, selectedPatternId);

    // ===== DEBUGGING: Provider Change Log =====
    console.log("🔄 PATTERN APPLIED:", {
      patternId: selectedPatternId,
      originalProvider: teamConfig?.provider,
      newProvider: result.teamConfig?.provider,
      providerChanged: teamConfig?.provider !== result.teamConfig?.provider,
      isNewTeam: result.isNewTeam,
    });

    // Log any warnings during development
    if (result.warnings.length > 0) {
      console.log("Pattern configuration warnings:", result.warnings);
    }

    // Validate the resulting config
    const validation = validateTeamForExecution(result.teamConfig);
    if (!validation.valid) {
      console.warn("Team validation errors:", validation.errors);
    }
    if (validation.warnings.length > 0) {
      console.log("Team validation warnings:", validation.warnings);
    }

    return result.teamConfig;
  }, [teamConfig, selectedPatternId]);

  // Get settings for timeout configuration
  const { uiSettings } = useSettingsStore();
  const timeoutConfig = React.useMemo(
    () => createTimeoutConfig(uiSettings.human_input_timeout_minutes || 3),
    [uiSettings.human_input_timeout_minutes]
  );

  const inputTimeoutRef = React.useRef<NodeJS.Timeout | null>(null);
  const activeSocketRef = React.useRef<WebSocket | null>(null);

  // Create a Message object from AgentMessageConfig
  const createMessage = (
    config: AgentMessageConfig,
    runId: number,
    sessionId: number
  ): Message => ({
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    config,
    session_id: sessionId,
    run_id: runId,
    user_id: user?.id || undefined,
  });

  // Load existing runs when session changes
  const loadSessionRuns = async () => {
    if (!session?.id || !user?.id) return;

    try {
      const response = await sessionAPI.getSessionRuns(session.id, user.id);
      setExistingRuns(response.runs);
    } catch (error) {
      console.error("Error loading session runs:", error);
      messageApi.error("Failed to load chat history");
    }
  };

  React.useEffect(() => {
    if (session?.id) {
      loadSessionRuns();
      setCurrentRun(null);
    } else {
      setExistingRuns([]);
      setCurrentRun(null);
    }
  }, [session?.id]);

  // Load team config
  React.useEffect(() => {
    if (session?.team_id && user?.id) {
      teamAPI
        .getTeam(session.team_id, user.id)
        .then((team) => {
          setTeamConfig(team.component);
        })
        .catch((error) => {
          console.error("Error loading team config:", error);
          // messageApi.error("Failed to load team config");
          setTeamConfig(null);
        });
    }
  }, [session]);

  // Sync selectedPatternId with loaded teamConfig's provider
  // This ensures the UI pattern matches the actual team configuration
  React.useEffect(() => {
    if (teamConfig?.provider) {
      const detectedPattern = getPatternByProvider(teamConfig.provider);
      if (detectedPattern) {
        setSelectedPatternId(detectedPattern.id);
      }
    }
  }, [teamConfig]);

  React.useEffect(() => {
    setTimeout(() => {
      if (chatContainerRef.current && existingRuns.length > 0) {
        // Scroll to bottom to show latest run
        chatContainerRef.current.scrollTo({
          top: chatContainerRef.current.scrollHeight,
          behavior: "auto", // Use 'auto' instead of 'smooth' for initial load
        });
      }
    }, 450);
  }, [existingRuns.length, currentRun?.messages]);

  // Cleanup socket on unmount
  React.useEffect(() => {
    return () => {
      if (inputTimeoutRef.current) {
        clearTimeout(inputTimeoutRef.current);
      }
      activeSocket?.close();
    };
  }, [activeSocket]);

  const createRun = async (sessionId: number): Promise<number> => {
    return await sessionAPI.createRun(sessionId, user?.id || "");
  };

  const handleWebSocketMessage = (message: WebSocketMessage) => {
    setCurrentRun((current) => {
      if (!current || !session?.id) return null;
      // console.log("WebSocket message:", message);

      switch (message.type) {
        case "error":
          if (inputTimeoutRef.current) {
            clearTimeout(inputTimeoutRef.current);
            inputTimeoutRef.current = null;
          }
          if (activeSocket) {
            activeSocket.close();
            setActiveSocket(null);
            activeSocketRef.current = null;
          }
          console.log("Error: ", message.error);

          const updatedErrorRun = {
            ...current,
            status: "error" as RunStatus,
            error_message: message.error || "An error occurred",
          };

          // Add to existing runs
          setExistingRuns((prev) => [...prev, updatedErrorRun]);
          return null; // Clear current run

        case "message_chunk":
          if (!message.data) return current;

          // Update streaming content
          try {
            const chunk = message.data as ModelClientStreamingChunkEvent;
            setStreamingContent((prev) => ({
              runId: current.id,
              content: (prev?.content || "") + (chunk.content || ""),
              source: chunk.source || "assistant",
            }));
          } catch (error) {
            console.error("Error parsing message chunk:", error);
          }

          return current; // Keep current run unchanged

        case "message":
          setStreamingContent(null);
          if (!message.data) return current;

          // Create new Message object from websocket data
          const newMessage = createMessage(
            message.data as AgentMessageConfig,
            current.id,
            session.id
          );

          return {
            ...current,
            messages: [...current.messages, newMessage],
          };

        case "input_request":
          if (inputTimeoutRef.current) {
            clearTimeout(inputTimeoutRef.current);
          }

          inputTimeoutRef.current = setTimeout(() => {
            const socket = activeSocketRef.current;
            console.log("Input timeout", socket);

            if (socket?.readyState === WebSocket.OPEN) {
              socket.send(
                JSON.stringify({
                  type: "stop",
                  reason: timeoutConfig.DEFAULT_MESSAGE,
                  code: timeoutConfig.WEBSOCKET_CODE,
                })
              );
              setCurrentRun((prev) =>
                prev
                  ? {
                      ...prev,
                      status: "stopped",
                      error_message: timeoutConfig.DEFAULT_MESSAGE,
                    }
                  : null
              );
            }
          }, timeoutConfig.DURATION_MS);

          return {
            ...current,
            status: "awaiting_input",
          };
        case "result":
        case "completion":
          // When run completes, move it to existingRuns
          const status: RunStatus =
            message.status === "complete"
              ? "complete"
              : message.status === "error"
              ? "error"
              : "stopped";

          const isTeamResult = (data: any): data is TeamResult => {
            return (
              data &&
              "task_result" in data &&
              "usage" in data &&
              "duration" in data
            );
          };

          const updatedRun = {
            ...current,
            status,
            team_result:
              message.data && isTeamResult(message.data) ? message.data : null,
          };

          // Add to existing runs if complete
          if (status === "complete") {
            if (inputTimeoutRef.current) {
              clearTimeout(inputTimeoutRef.current);
              inputTimeoutRef.current = null;
            }
            if (activeSocket) {
              activeSocket.close();
              setActiveSocket(null);
              activeSocketRef.current = null;
            }
            setExistingRuns((prev) => [...prev, updatedRun]);
            return null;
          }

          return updatedRun;

        default:
          return current;
      }
    });
  };

  const handleError = (error: any) => {
    console.error("Error:", error);
    message.error("Error during request processing");

    setCurrentRun((current) => {
      if (!current) return null;

      const errorRun = {
        ...current,
        status: "error" as const,
        error_message:
          error instanceof Error ? error.message : "Unknown error occurred",
      };

      // Add failed run to existing runs
      setExistingRuns((prev) => [...prev, errorRun]);
      return null; // Clear current run
    });

    setError({
      status: false,
      message:
        error instanceof Error ? error.message : "Unknown error occurred",
    });
  };

  const handleInputResponse = async (response: string) => {
    if (!activeSocketRef.current || !currentRun) return;

    if (activeSocketRef.current.readyState !== WebSocket.OPEN) {
      console.error(
        "Socket not in OPEN state:",
        activeSocketRef.current.readyState
      );
      handleError(new Error("WebSocket connection not available"));
      return;
    }

    // Clear timeout when response received
    if (inputTimeoutRef.current) {
      clearTimeout(inputTimeoutRef.current);
      inputTimeoutRef.current = null;
    }

    try {
      activeSocketRef.current.send(
        JSON.stringify({
          type: "input_response",
          response: response,
        })
      );

      setCurrentRun((current) => {
        if (!current) return null;
        return {
          ...current,
          status: "active",
        };
      });
    } catch (error) {
      handleError(error);
    }
  };

  const handleCancel = async () => {
    if (!activeSocketRef.current || !currentRun) return;

    // Clear timeout when manually cancelled
    if (inputTimeoutRef.current) {
      clearTimeout(inputTimeoutRef.current);
      inputTimeoutRef.current = null;
    }
    try {
      activeSocketRef.current.send(
        JSON.stringify({
          type: "stop",
          reason: "Cancelled by user",
        })
      );

      setCurrentRun((current) => {
        if (!current) return null;
        return {
          ...current,
          status: "stopped",
        };
      });
    } catch (error) {
      handleError(error);
    }
  };

  const runTask = async (query: string, files: RcFile[] = []) => {
    setError(null);
    setLoading(true);

    // Add explicit cleanup
    if (activeSocket) {
      activeSocket.close();
      setActiveSocket(null);
      activeSocketRef.current = null;
    }

    if (inputTimeoutRef.current) {
      clearTimeout(inputTimeoutRef.current);
      inputTimeoutRef.current = null;
    }

    if (!session?.id || !effectiveTeamConfig) {
      setLoading(false);
      return;
    }

    try {
      const runId = await createRun(session.id);

      // Process files using the extracted function
      const processedFiles = await convertFilesToBase64(files);

      // Initialize run state BEFORE websocket connection
      setCurrentRun({
        id: runId,
        created_at: new Date().toISOString(),
        status: "created", // Start with created status
        messages: [],
        task: [
          {
            content: query,
            source: "user",
          },
        ],
        team_result: null,
        error_message: undefined,
      });

      // Setup WebSocket with files
      const socket = setupWebSocket(runId, query, processedFiles);
      setActiveSocket(socket);
      activeSocketRef.current = socket;
    } catch (error) {
      handleError(error);
    } finally {
      setLoading(false);
    }
  };

  const setupWebSocket = (
    runId: number,
    query: string,
    files: { name: string; type: string; content: string }[]
  ): WebSocket => {
    if (!session || !session.id) {
      throw new Error("Invalid session configuration");
    }
    // Close existing socket if any
    if (activeSocket?.readyState === WebSocket.OPEN) {
      activeSocket.close();
    }

    const baseUrl = getBaseUrl(serverUrl);
    const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const auth_token = localStorage.getItem("auth_token");
    const wsUrl = `${wsProtocol}//${baseUrl}/api/ws/runs/${runId}?token=${auth_token}`;

    const socket = new WebSocket(wsUrl);

    // Initialize current run
    setCurrentRun({
      id: runId,
      created_at: new Date().toISOString(),
      status: "active",

      task: [
        createMessage(
          { content: query, source: "user" },
          runId,
          session.id || 0
        ).config,
      ],
      team_result: null,
      messages: [],
      error_message: undefined,
    });

    socket.onopen = () => {
      // Send start message with effectiveTeamConfig (modified based on selected pattern)
      socket.send(
        JSON.stringify({
          type: "start",
          task: query,
          files: files,
          team_config: effectiveTeamConfig,
        })
      );
    };

    socket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        handleWebSocketMessage(message);
      } catch (error) {
        console.error("WebSocket message parsing error:", error);
      }
    };

    socket.onclose = () => {
      activeSocketRef.current = null;
      setActiveSocket(null);
    };

    socket.onerror = (error) => {
      handleError(error);
    };

    return socket;
  };

  // Helper for WebSocket URL
  const getBaseUrl = (url: string): string => {
    try {
      let baseUrl = url.replace(/(^\w+:|^)\/\//, "");
      if (baseUrl.startsWith("localhost")) {
        baseUrl = baseUrl.replace("/api", "");
      } else if (baseUrl === "/api") {
        baseUrl = window.location.host;
      } else {
        baseUrl = baseUrl.replace("/api", "").replace(/\/$/, "");
      }
      return baseUrl;
    } catch (error) {
      console.error("Error processing server URL:", error);
      throw new Error("Invalid server URL configuration");
    }
  };

  return (
    <div className="text-primary h-[calc(100vh-165px)] bg-primary relative rounded flex-1 scroll">
      {contextHolder}
      <div className="flex pt-2 items-center justify-between text-sm h-10">
        <div className="flex items-center gap-2 min-w-0 overflow-hidden flex-1 pr-4">
          {isCompareMode ? (
            <SessionDropdown
              session={session}
              availableSessions={availableSessions}
              onSessionChange={onSessionChange || (() => {})}
              className="w-full"
            />
          ) : (
            <>
              <span className="text-primary font-medium whitespace-nowrap flex-shrink-0">
                Sessions
              </span>
              {session && (
                <>
                  <ChevronRight className="w-4 h-4 text-secondary flex-shrink-0" />
                  <Tooltip title={session.name}>
                    <span className="text-secondary truncate overflow-hidden">
                      {session.name}
                    </span>
                  </Tooltip>
                </>
              )}
            </>
          )}
        </div>

        <div className="flex items-center gap-2 flex-shrink-0 whitespace-nowrap">
          {/* Pattern Selector Dropdown - All patterns from schema */}
          {teamConfig && (
            <Dropdown
              menu={{
                items: patternMenuItems,
                onClick: ({ key }) => setSelectedPatternId(key),
                selectedKeys: [selectedPatternId],
              }}
              trigger={["click"]}
            >
              <Tooltip title={selectedPattern?.description || "Select collaboration pattern"}>
                <button className="flex items-center gap-1 px-2 py-1.5 rounded-md text-xs bg-secondary hover:bg-tertiary transition-colors border border-secondary">
                  {selectedPatternId === "sequential" && <ArrowRight className="w-3.5 h-3.5" />}
                  {selectedPatternId === "selector" && <Circle className="w-3.5 h-3.5" />}
                  {selectedPatternId === "swarm" && <Shuffle className="w-3.5 h-3.5" />}
                  {!["sequential", "selector", "swarm"].includes(selectedPatternId) && <Network className="w-3.5 h-3.5" />}
                  <span className="hidden sm:inline">
                    {selectedPattern?.name?.split(" ")[0] || "Pattern"}
                  </span>
                  <ChevronDown className="w-3 h-3" />
                </button>
              </Tooltip>
            </Dropdown>
          )}

          {/* View Mode Toggle Button */}
          {teamConfig && (
            <div className="flex items-center bg-secondary rounded-md p-0.5">
              <Tooltip title="Pattern View - Shows team collaboration structure">
                <button
                  onClick={() => setViewMode("pattern")}
                  className={`flex items-center gap-1 px-2 py-1 rounded text-xs transition-colors ${
                    viewMode === "pattern"
                      ? "bg-accent text-white"
                      : "text-secondary hover:text-primary"
                  }`}
                >
                  <GitBranch className="w-3.5 h-3.5" />
                  Pattern
                </button>
              </Tooltip>
              <Tooltip title="Execution View - Shows actual message flow">
                <button
                  onClick={() => setViewMode("execution")}
                  className={`flex items-center gap-1 px-2 py-1 rounded text-xs transition-colors ${
                    viewMode === "execution"
                      ? "bg-accent text-white"
                      : "text-secondary hover:text-primary"
                  }`}
                >
                  <Activity className="w-3.5 h-3.5" />
                  Execution
                </button>
              </Tooltip>
            </div>
          )}
          {!isCompareMode && !isSecondaryView && showCompareButton && (
            <Button
              type="text"
              onClick={onCompareClick}
              icon={<SplitSquareHorizontal className="w-4 h-4" />}
            >
              Compare
            </Button>
          )}
          {isCompareMode && isSecondaryView && (
            <Button
              type="text"
              onClick={onExitCompare}
              icon={<X className="w-4 h-4" />}
            >
              Exit Compare
            </Button>
          )}
        </div>
      </div>
      <div className="flex flex-col h-full">
        <div
          ref={chatContainerRef}
          className="flex-1 overflow-y-auto scroll mt-2 min-h-0 relative"
        >
          <div id="scroll-gradient" className="scroll-gradient h-8 top-0">
            {" "}
            <span className="  inline-block h-6"></span>{" "}
          </div>
          <>
            {teamConfig && (
              <>
                {/* Existing Runs - use effectiveTeamConfig to show selected pattern visualization */}
                {existingRuns.map((run, index) => (
                  <RunView
                    teamConfig={effectiveTeamConfig || teamConfig}
                    key={run.id + "-review-" + index + "-" + selectedPatternId}
                    run={run}
                    isFirstRun={index === 0}
                    viewMode={viewMode}
                    selectedPatternId={selectedPatternId}
                  />
                ))}

                {/* Current Run - use effectiveTeamConfig (being executed with selected pattern) */}
                {currentRun && effectiveTeamConfig && (
                  <RunView
                    run={currentRun}
                    teamConfig={effectiveTeamConfig}
                    onInputResponse={handleInputResponse}
                    onCancel={handleCancel}
                    isFirstRun={existingRuns.length === 0}
                    streamingContent={streamingContent}
                    viewMode={viewMode}
                    selectedPatternId={selectedPatternId}
                  />
                )}

                {/* No existing runs - Show team pattern preview */}

                {!currentRun && existingRuns.length === 0 && effectiveTeamConfig && (
                  <div className="flex flex-col items-center justify-center h-[80%]">
                    <div className="text-center mb-4">
                      <Network
                        strokeWidth={1}
                        className="w-12 h-12 mb-2 inline-block text-secondary"
                      />
                      <div className="font-medium mb-1">
                        {selectedPattern?.name || "Pattern"}
                      </div>
                      <div className="text-secondary text-sm">
                        Enter a task to start the conversation
                      </div>
                    </div>

                    {/* Team Pattern Preview */}
                    <div className="w-full max-w-2xl h-[350px] bg-tertiary rounded-lg border border-secondary">
                      <AgentFlow
                        teamConfig={effectiveTeamConfig}
                        run={{
                          id: 0,
                          created_at: new Date().toISOString(),
                          status: "created",
                          messages: [],
                          task: [],
                          team_result: null,
                          error_message: undefined,
                        }}
                        viewMode="pattern"
                        selectedPatternId={selectedPatternId}
                      />
                    </div>
                  </div>
                )}
              </>
            )}

            {/* No team config */}
            {!teamConfig && (
              <div className="flex items-center justify-center h-[80%]">
                <div className="text-center  ">
                  <MessagesSquare
                    strokeWidth={1}
                    className="w-64 h-64 mb-4 inline-block"
                  />
                  <div className="  font-medium mb-2">
                    No team configuration found for this session (may have been
                    deleted).{" "}
                  </div>
                  <div className="text-secondary text-sm">
                    Add a team to the session to get started.
                  </div>
                </div>
              </div>
            )}
          </>
        </div>

        {session && effectiveTeamConfig && (
          <div className="flex-shrink-0">
            <ChatInput
              onSubmit={runTask}
              loading={loading}
              error={error}
              disabled={
                currentRun?.status === "awaiting_input" ||
                currentRun?.status === "active"
              }
            />
          </div>
        )}
      </div>
    </div>
  );
}
