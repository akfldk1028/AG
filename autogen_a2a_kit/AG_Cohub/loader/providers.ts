/**
 * ============================================
 * PROVIDERS - Provider 설정 로더
 * ============================================
 *
 * providers.json을 로드하고 타입 적용
 *
 * !! 이 파일은 수정할 필요 없음 !!
 * - 새 provider 추가: providers.json만 수정
 */

import { PatternCategory, LayoutType, PatternConnection } from "./types";

// ============================================
// 타입 정의
// ============================================

export interface ParticipantConfig {
  name: string;
  description: string;
  systemMessage: string;
}

export interface ProviderConfig {
  full: string;
  category: PatternCategory;
  layout: LayoutType;
  icon: string;
  colors: { primary: string; secondary: string };
  communicationStyle: "turn-based" | "broadcast" | "request-response" | "event-driven";
  connections: PatternConnection[];
  requiresModelClient: boolean;
  defaultParticipants: {
    en: ParticipantConfig[];
    ko: ParticipantConfig[];
  };
}

export type ProviderName = "RoundRobinGroupChat" | "SelectorGroupChat" | "Swarm" | "MagenticOneGroupChat";
export type ProviderRegistry = Record<ProviderName, ProviderConfig>;

// ============================================
// JSON 로드
// ============================================

// Vite/Webpack에서는 JSON import 지원
// Node.js에서는 require 또는 fs.readFileSync 사용
import providersJson from "./providers.json";

// _README 필드 제거하고 타입 적용
const { _README, ...providers } = providersJson as any;
export const PROVIDERS: ProviderRegistry = providers as ProviderRegistry;

// ============================================
// 헬퍼 함수들
// ============================================

/** Provider 이름에서 클래스명 추출 */
export function extractProviderShort(provider: string): string {
  const parts = provider.split(".");
  return parts[parts.length - 1];
}

/** Provider 설정 가져오기 */
export function getProvider(providerFull: string): ProviderConfig | undefined {
  const shortName = extractProviderShort(providerFull);
  return PROVIDERS[shortName as ProviderName];
}

/** 카테고리 */
export function getCategory(provider: string): PatternCategory {
  return getProvider(provider)?.category || "sequential";
}

/** 레이아웃 */
export function getLayout(provider: string): LayoutType {
  return getProvider(provider)?.layout || "chain";
}

/** 아이콘 */
export function getIcon(provider: string): string {
  return getProvider(provider)?.icon || "HelpCircle";
}

/** 색상 */
export function getColors(provider: string): { primary: string; secondary: string } {
  return getProvider(provider)?.colors || { primary: "#6b7280", secondary: "#9ca3af" };
}

/** 통신 스타일 */
export function getCommunicationStyle(provider: string): ProviderConfig["communicationStyle"] {
  return getProvider(provider)?.communicationStyle || "turn-based";
}

/** 연결 정보 */
export function getConnections(provider: string): PatternConnection[] {
  return getProvider(provider)?.connections || [{ type: "sequential", from: "agent[i]", to: "agent[i+1]" }];
}

/** model_client 필요 여부 */
export function requiresModelClient(provider: string): boolean {
  return getProvider(provider)?.requiresModelClient ?? false;
}

/** 기본 참여자 (국제화 지원) */
export function getDefaultParticipants(provider: string, lang: "en" | "ko" = "en"): ParticipantConfig[] {
  const config = getProvider(provider);
  if (!config) {
    return PROVIDERS.RoundRobinGroupChat.defaultParticipants[lang];
  }
  return config.defaultParticipants[lang] || config.defaultParticipants.en;
}

export default PROVIDERS;
