/**
 * ============================================
 * AG_Cohub Pattern Loader - 진입점
 * ============================================
 *
 * ## 파일 구조 (4개만!)
 *
 * ```
 * loader/
 * ├── index.ts       ← 이 파일 (진입점)
 * ├── types.ts       ← 타입 정의
 * ├── providers.json ← Provider 설정 (수정 대상)
 * ├── providers.ts   ← JSON 로더
 * └── converter.ts   ← 변환 로직
 * ```
 *
 * ## 수정이 필요한 경우
 *
 * | 작업 | 수정 파일 |
 * |------|----------|
 * | 새 패턴 추가 | patterns/*.json |
 * | 새 provider 추가 | providers.json |
 * | 타입 변경 | types.ts |
 *
 * ## 사용법
 *
 * ```typescript
 * // Frontend (Vite)
 * import { createPatternLibrary } from './loader';
 * const modules = import.meta.glob('../patterns/*.json', { eager: true });
 * const library = createPatternLibrary(modules);
 *
 * // Backend (Node.js)
 * import { loadAllPatterns } from './loader';
 * const library = await loadAllPatterns('./patterns');
 * ```
 */

// ============================================
// 타입 Re-export
// ============================================

export * from "./types";
export type { ProviderConfig, ProviderName, ParticipantConfig } from "./providers";

// ============================================
// Provider 설정 Re-export
// ============================================

export {
  PROVIDERS,
  getProvider,
  extractProviderShort,
  getCategory,
  getLayout,
  getIcon,
  getColors,
  getCommunicationStyle,
  getConnections,
  requiresModelClient,
  getDefaultParticipants,
} from "./providers";

// ============================================
// 변환 함수 Re-export
// ============================================

export {
  DEFAULT_MODEL_CLIENT,
  DEFAULT_TERMINATION,
  convertToPatternDefinition,
  buildTeamTemplate,
  convertAllPatterns,
  buildAllTemplates,
} from "./converter";

// ============================================
// 메인 함수들
// ============================================

import { CoHubPatternJSON, PatternDefinition, Component, TeamConfig } from "./types";
import { convertToPatternDefinition, buildTeamTemplate } from "./converter";

/**
 * 패턴 라이브러리 인터페이스
 */
export interface PatternLibrary {
  PATTERN_LIBRARY: PatternDefinition[];
  PATTERN_TEMPLATES: Record<string, Component<TeamConfig>>;
  getPatternById: (id: string) => PatternDefinition | undefined;
  getTemplateById: (id: string) => Component<TeamConfig> | undefined;
}

/**
 * Vite glob import에서 패턴 라이브러리 생성
 *
 * @example
 * ```typescript
 * const modules = import.meta.glob('../patterns/*.json', { eager: true });
 * const library = createPatternLibrary(modules);
 * ```
 */
export function createPatternLibrary(
  modules: Record<string, { default: CoHubPatternJSON } | CoHubPatternJSON>
): PatternLibrary {
  const patterns: PatternDefinition[] = [];
  const templates: Record<string, Component<TeamConfig>> = {};

  for (const [path, module] of Object.entries(modules)) {
    // _로 시작하는 파일 스킵
    if (path.includes("/_")) continue;

    const json = ("default" in module ? module.default : module) as CoHubPatternJSON;
    patterns.push(convertToPatternDefinition(json));
    templates[json.id] = buildTeamTemplate(json);
  }

  patterns.sort((a, b) => a.id.localeCompare(b.id));

  return {
    PATTERN_LIBRARY: patterns,
    PATTERN_TEMPLATES: templates,
    getPatternById: (id) => patterns.find((p) => p.id === id),
    getTemplateById: (id) => templates[id],
  };
}

/**
 * 디렉토리에서 패턴 로드 (Node.js용)
 *
 * @example
 * ```typescript
 * const library = await loadAllPatterns('./patterns');
 * ```
 */
export async function loadAllPatterns(patternsDir: string): Promise<PatternLibrary> {
  const fs = await import("fs");
  const path = await import("path");

  const files = fs
    .readdirSync(patternsDir)
    .filter((f: string) => f.endsWith(".json") && !f.startsWith("_"));

  const patterns: PatternDefinition[] = [];
  const templates: Record<string, Component<TeamConfig>> = {};

  for (const file of files) {
    const content = fs.readFileSync(path.join(patternsDir, file), "utf-8");
    const json: CoHubPatternJSON = JSON.parse(content);
    patterns.push(convertToPatternDefinition(json));
    templates[json.id] = buildTeamTemplate(json);
  }

  patterns.sort((a, b) => a.id.localeCompare(b.id));

  return {
    PATTERN_LIBRARY: patterns,
    PATTERN_TEMPLATES: templates,
    getPatternById: (id) => patterns.find((p) => p.id === id),
    getTemplateById: (id) => templates[id],
  };
}

// ============================================
// 상수
// ============================================

export const PATTERN_CATEGORIES = [
  { id: "sequential", label: "Sequential", description: "Fixed order execution" },
  { id: "dynamic", label: "Dynamic", description: "Runtime agent selection" },
  { id: "parallel", label: "Parallel", description: "Concurrent execution" },
  { id: "hierarchical", label: "Hierarchical", description: "Multi-level coordination" },
] as const;
