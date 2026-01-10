import React, { useState, useEffect } from "react";
import { Modal, Input, Button, message, Spin, Tag, InputNumber, Tabs, List, Badge } from "antd";
import { Link2, CheckCircle, AlertCircle, Wrench, Clock, Zap, Bot, Users, RefreshCw } from "lucide-react";

interface A2AImportModalProps {
  open: boolean;
  onClose: () => void;
  onImportTool?: (toolConfig: any) => void;
  onImportAgent?: (agentConfig: any) => void;
}

interface ImportResult {
  status: boolean;
  message: string;
  agent_name?: string;
  agent_description?: string;
  skills?: Array<{ name: string; description: string }>;
  tool_config?: any;
  agent_config?: any;  // A2AAgent ComponentModel
}

interface RecentAgent {
  url: string;
  name: string;
  timestamp: number;
}

interface RegisteredAgent {
  name: string;
  display_name: string;
  url: string;
  description: string;
  skills: Array<{ name: string; description: string }>;
  is_online: boolean;
  last_checked?: string;
}

const STORAGE_KEY = "a2a_recent_agents";

export const A2AImportModal: React.FC<A2AImportModalProps> = ({
  open,
  onClose,
  onImportTool,
  onImportAgent,
}) => {
  const [url, setUrl] = useState("");
  const [port, setPort] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ImportResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [recentAgents, setRecentAgents] = useState<RecentAgent[]>([]);
  const [registeredAgents, setRegisteredAgents] = useState<RegisteredAgent[]>([]);
  const [registryLoading, setRegistryLoading] = useState(false);
  const [activeTab, setActiveTab] = useState("quick");

  // Load recent agents from localStorage
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        setRecentAgents(JSON.parse(stored));
      }
    } catch (e) {
      console.error("Failed to load recent agents:", e);
    }

    // Load registered agents and check status when modal opens
    if (open) {
      checkAllAgentsStatus();  // 모달 열릴 때 자동으로 상태 확인
    }
  }, [open]);

  // Auto-refresh status every 10 seconds when modal is open and on registry tab
  useEffect(() => {
    if (!open || activeTab !== "registry") return;

    const interval = setInterval(() => {
      checkAllAgentsStatus(true);  // silent mode for auto-refresh
    }, 10000);  // 10초마다 자동 새로고침

    return () => clearInterval(interval);
  }, [open, activeTab]);

  // Load registered agents from backend registry
  const loadRegisteredAgents = async () => {
    setRegistryLoading(true);
    try {
      const response = await fetch("/api/a2a/registry");
      if (response.ok) {
        const data = await response.json();
        setRegisteredAgents(data.agents || []);
      }
    } catch (e) {
      console.error("Failed to load registered agents:", e);
    } finally {
      setRegistryLoading(false);
    }
  };

  // Check all agents status (silent=true for auto-refresh without messages)
  const checkAllAgentsStatus = async (silent: boolean = false) => {
    if (!silent) setRegistryLoading(true);
    try {
      const response = await fetch("/api/a2a/registry/check-all", { method: "POST" });
      if (response.ok) {
        const data = await response.json();
        setRegisteredAgents(data.agents || []);
        if (!silent) message.success(data.message);
      }
    } catch (e) {
      if (!silent) message.error("상태 확인 실패");
    } finally {
      if (!silent) setRegistryLoading(false);
    }
  };

  // Get agent component config from registry
  const getAgentComponent = async (name: string): Promise<any> => {
    try {
      const response = await fetch(`/api/a2a/registry/${name}/component`);
      if (response.ok) {
        const data = await response.json();
        return data.component;
      }
    } catch (e) {
      console.error("Failed to get agent component:", e);
    }
    return null;
  };

  // Save recent agent to localStorage
  const saveRecentAgent = (agentUrl: string, agentName: string) => {
    const newAgent: RecentAgent = {
      url: agentUrl,
      name: agentName,
      timestamp: Date.now(),
    };

    const updated = [newAgent, ...recentAgents.filter(a => a.url !== agentUrl)].slice(0, 5);
    setRecentAgents(updated);

    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
    } catch (e) {
      console.error("Failed to save recent agents:", e);
    }
  };

  const handleCheck = async (targetUrl?: string) => {
    let agentCardUrl = targetUrl || url.trim();

    // If only port number provided, construct localhost URL
    if (!agentCardUrl && port) {
      agentCardUrl = `http://localhost:${port}`;
    }

    if (!agentCardUrl) {
      message.warning("포트 번호 또는 URL을 입력하세요.");
      return;
    }

    // Add protocol if missing
    if (!agentCardUrl.startsWith("http")) {
      agentCardUrl = "http://" + agentCardUrl;
    }

    // Add agent.json path if missing
    if (!agentCardUrl.includes("/.well-known/agent.json")) {
      agentCardUrl = agentCardUrl.replace(/\/$/, "") + "/.well-known/agent.json";
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch("/api/a2a/import", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ agent_card_url: agentCardUrl }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Import failed");
      }

      const data: ImportResult = await response.json();
      setResult(data);

      // Save to recent agents
      if (data.status && data.agent_name) {
        const baseUrl = agentCardUrl.replace("/.well-known/agent.json", "");
        saveRecentAgent(baseUrl, data.agent_name);
      }
    } catch (err: any) {
      setError(err.message || "Agent Card를 가져올 수 없습니다.");
    } finally {
      setLoading(false);
    }
  };

  // Import as tool (FunctionTool)
  const handleImportAsTool = () => {
    if (result?.tool_config && onImportTool) {
      onImportTool(result.tool_config);
      message.success(`${result.agent_name} 도구가 추가되었습니다!`);
      handleClose();
    }
  };

  // Import as agent (A2AAgent)
  const handleImportAsAgent = () => {
    if (result?.agent_config && onImportAgent) {
      onImportAgent(result.agent_config);
      message.success(`${result.agent_name} 에이전트가 팀에 추가되었습니다!`);
      handleClose();
    }
  };

  // Add agent from registry by name
  const handleAddFromRegistry = async (agent: RegisteredAgent) => {
    if (!onImportAgent) {
      message.warning("에이전트 추가 기능이 연결되지 않았습니다.");
      return;
    }

    const component = await getAgentComponent(agent.name);
    if (component) {
      onImportAgent(component);
      message.success(`${agent.display_name} 에이전트가 팀에 추가되었습니다!`);
      handleClose();
    } else {
      message.error("에이전트 컴포넌트를 가져올 수 없습니다.");
    }
  };

  const handleClose = () => {
    setUrl("");
    setPort(null);
    setResult(null);
    setError(null);
    onClose();
  };

  const quickPorts = [8001, 8002, 8003, 8004, 8005];

  return (
    <Modal
      title={
        <div className="flex items-center gap-2">
          <Link2 className="w-5 h-5" />
          <span>A2A 에이전트 가져오기</span>
        </div>
      }
      open={open}
      onCancel={handleClose}
      footer={null}
      width={600}
    >
      <div className="space-y-4 py-4">
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={[
            {
              key: "quick",
              label: (
                <span className="flex items-center gap-1">
                  <Zap className="w-4 h-4" />
                  빠른 연결
                </span>
              ),
              children: (
                <div className="space-y-4">
                  {/* Port Number Input */}
                  <div>
                    <label className="block text-sm font-medium mb-2">
                      포트 번호 입력 (localhost)
                    </label>
                    <div className="flex gap-2">
                      <InputNumber
                        placeholder="예: 8002"
                        value={port}
                        onChange={(value) => setPort(value)}
                        min={1}
                        max={65535}
                        className="flex-1"
                        onPressEnter={() => handleCheck()}
                        disabled={loading}
                      />
                      <Button
                        type="primary"
                        onClick={() => handleCheck()}
                        loading={loading}
                        disabled={!port}
                      >
                        연결
                      </Button>
                    </div>
                  </div>

                  {/* Quick Port Buttons */}
                  <div>
                    <label className="block text-sm font-medium mb-2">
                      자주 사용하는 포트
                    </label>
                    <div className="flex flex-wrap gap-2">
                      {quickPorts.map((p) => (
                        <Button
                          key={p}
                          size="small"
                          onClick={() => {
                            setPort(p);
                            handleCheck(`http://localhost:${p}`);
                          }}
                          loading={loading && port === p}
                        >
                          :{p}
                        </Button>
                      ))}
                    </div>
                  </div>

                  {/* Recent Agents */}
                  {recentAgents.length > 0 && (
                    <div>
                      <label className="block text-sm font-medium mb-2">
                        <Clock className="w-4 h-4 inline mr-1" />
                        최근 사용한 에이전트
                      </label>
                      <div className="space-y-1">
                        {recentAgents.map((agent, idx) => (
                          <Button
                            key={idx}
                            type="text"
                            className="w-full text-left justify-start"
                            onClick={() => handleCheck(agent.url)}
                            loading={loading}
                          >
                            <span className="font-medium">{agent.name}</span>
                            <span className="text-gray-400 ml-2 text-xs">{agent.url}</span>
                          </Button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ),
            },
            {
              key: "url",
              label: (
                <span className="flex items-center gap-1">
                  <Link2 className="w-4 h-4" />
                  URL 직접 입력
                </span>
              ),
              children: (
                <div>
                  <label className="block text-sm font-medium mb-2">
                    A2A 서버 URL
                  </label>
                  <div className="flex gap-2">
                    <Input
                      placeholder="http://example.com:8002"
                      value={url}
                      onChange={(e) => setUrl(e.target.value)}
                      onPressEnter={() => handleCheck()}
                      disabled={loading}
                    />
                    <Button type="primary" onClick={() => handleCheck()} loading={loading}>
                      확인
                    </Button>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    원격 서버나 커스텀 URL을 입력할 때 사용하세요.
                  </p>
                </div>
              ),
            },
            {
              key: "registry",
              label: (
                <span className="flex items-center gap-1">
                  <Users className="w-4 h-4" />
                  등록된 에이전트
                  {registeredAgents.length > 0 && (
                    <Badge count={registeredAgents.length} size="small" />
                  )}
                </span>
              ),
              children: (
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">
                      이름으로 빠르게 팀에 추가할 수 있습니다.
                    </span>
                    <Button
                      size="small"
                      icon={<RefreshCw className="w-3 h-3" />}
                      onClick={checkAllAgentsStatus}
                      loading={registryLoading}
                    >
                      상태 확인
                    </Button>
                  </div>

                  {registryLoading ? (
                    <div className="flex items-center justify-center py-8">
                      <Spin />
                    </div>
                  ) : registeredAgents.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                      <Bot className="w-12 h-12 mx-auto mb-2 opacity-50" />
                      <p>등록된 에이전트가 없습니다.</p>
                      <p className="text-xs mt-1">
                        "빠른 연결"에서 에이전트를 가져오면 자동으로 등록됩니다.
                      </p>
                    </div>
                  ) : (
                    <List
                      dataSource={registeredAgents}
                      renderItem={(agent) => (
                        <List.Item
                          className="hover:bg-gray-50 rounded px-2"
                          actions={[
                            <Button
                              key="add"
                              type="primary"
                              size="small"
                              icon={<Bot className="w-3 h-3" />}
                              onClick={() => handleAddFromRegistry(agent)}
                              disabled={!agent.is_online}
                            >
                              팀에 추가
                            </Button>
                          ]}
                        >
                          <List.Item.Meta
                            avatar={
                              <Badge
                                status={agent.is_online ? "success" : "default"}
                                text={<Bot className="w-5 h-5" />}
                              />
                            }
                            title={
                              <span className="flex items-center gap-2">
                                {agent.display_name}
                                {agent.is_online ? (
                                  <Tag color="green" className="text-xs">온라인</Tag>
                                ) : (
                                  <Tag color="default" className="text-xs">오프라인</Tag>
                                )}
                              </span>
                            }
                            description={
                              <div>
                                <div className="text-xs text-gray-500">{agent.url}</div>
                                <div className="text-xs">{agent.description}</div>
                              </div>
                            }
                          />
                        </List.Item>
                      )}
                    />
                  )}
                </div>
              ),
            },
          ]}
        />

        {/* Loading */}
        {loading && (
          <div className="flex items-center justify-center py-8">
            <Spin size="large" />
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center gap-2 text-red-600">
              <AlertCircle className="w-5 h-5" />
              <span className="font-medium">연결 실패</span>
            </div>
            <p className="text-red-600 mt-1 text-sm">{error}</p>
          </div>
        )}

        {/* Result */}
        {result && result.status && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex items-center gap-2 text-green-600 mb-3">
              <CheckCircle className="w-5 h-5" />
              <span className="font-medium">에이전트 발견!</span>
            </div>

            <div className="space-y-2">
              <div>
                <span className="font-medium">이름:</span>{" "}
                <span>{result.agent_name}</span>
              </div>
              <div>
                <span className="font-medium">설명:</span>{" "}
                <span className="text-gray-600">{result.agent_description}</span>
              </div>

              {result.skills && result.skills.length > 0 && (
                <div>
                  <span className="font-medium">스킬:</span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {result.skills.map((skill, idx) => (
                      <Tag key={idx} icon={<Wrench className="w-3 h-3" />}>
                        {skill.name}
                      </Tag>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="mt-4 pt-4 border-t border-green-200">
              <p className="text-sm text-gray-600 mb-3">
                이 에이전트를 어떻게 추가하시겠습니까?
              </p>
              <div className="flex justify-end gap-2">
                <Button onClick={handleClose}>취소</Button>
                {onImportTool && result.tool_config && (
                  <Button onClick={handleImportAsTool} icon={<Wrench className="w-4 h-4" />}>
                    도구 추가
                  </Button>
                )}
                {onImportAgent && result.agent_config && (
                  <Button type="primary" onClick={handleImportAsAgent} icon={<Bot className="w-4 h-4" />}>
                    에이전트로 추가
                  </Button>
                )}
              </div>
              <p className="text-xs text-gray-500 mt-2">
                💡 <strong>에이전트로 추가</strong>: 팀의 직접 참여자로 추가 (권장)<br />
                💡 <strong>도구 추가</strong>: 다른 에이전트가 호출하는 도구로 추가
              </p>
            </div>
          </div>
        )}

        {/* Help - only show when no result/error */}
        {!loading && !result && !error && (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 text-sm text-gray-600">
            💡 로컬에서 실행 중인 A2A 에이전트의 포트 번호만 입력하면 됩니다.
          </div>
        )}
      </div>
    </Modal>
  );
};

export default A2AImportModal;
