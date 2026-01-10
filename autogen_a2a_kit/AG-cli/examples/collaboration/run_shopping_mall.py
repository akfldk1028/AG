# AG-CLI Collaboration Example: Shopping Mall
# 여러 에이전트가 협업하여 쇼핑몰을 만드는 예제
"""
이 예제는 AG-CLI의 협업 아키텍처를 보여줍니다.

실행 전 필요한 서버:
1. Message Bus: python mcp/message_bus.py (포트 8100)
2. SharedMemory: python mcp/shared_memory.py (포트 8101)

사용법:
    python run_shopping_mall.py

에이전트 협업 흐름:
1. Orchestrator가 요청을 분석하고 작업 분배
2. DB Agent가 스키마 설계 → SharedMemory에 저장
3. Backend Agent가 API 개발 → SharedMemory에 스펙 저장
4. Frontend Agent가 UI 개발 (API 스펙 참조)
5. Test Agent가 테스트 작성

모든 대화가 실시간으로 표시됩니다!
"""
import asyncio
import sys
from pathlib import Path

# 상위 디렉토리 import 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.base_collaborative import CollaborativeAgent


class DBAgent(CollaborativeAgent):
    """DB 전문 에이전트"""

    def __init__(self):
        super().__init__(
            name="db_agent",
            folder="db",
            expertise="PostgreSQL/Database Design"
        )

    async def design_schema(self, tables: list) -> dict:
        """테이블 스키마 설계"""
        await self.say("스키마 설계 시작합니다.", to="orchestrator")

        # Claude CLI로 스키마 생성
        task = f"""다음 테이블들의 PostgreSQL 스키마를 설계해주세요:
{', '.join(tables)}

각 테이블에 대해:
1. id는 UUID 사용
2. created_at, updated_at 타임스탬프 포함
3. 적절한 외래키 관계 설정
4. 인덱스 추가

schema.sql 파일로 저장해주세요."""

        result = await self.work(task)

        if result.get("success"):
            # 스키마 정보를 SharedMemory에 저장
            schema_info = {
                "tables": tables,
                "file": "db/schema.sql"
            }
            await self.share("schema", schema_info)
            await self.publish_event("schema_ready", schema_info)

        return result


class BackendAgent(CollaborativeAgent):
    """Backend 전문 에이전트"""

    def __init__(self):
        super().__init__(
            name="backend_agent",
            folder="backend",
            expertise="FastAPI/Python"
        )

    async def create_api(self, endpoints: list) -> dict:
        """API 엔드포인트 생성"""
        # 먼저 스키마 정보 확인
        schema = await self.get_schema()

        if not schema:
            # DB Agent에게 질문
            response = await self.ask(
                "스키마 정보가 필요해요. 현재 설계된 테이블 알려줄 수 있어요?",
                to="db_agent"
            )
            await asyncio.sleep(1)  # 응답 대기

        await self.say("API 개발 시작합니다.", to="orchestrator")

        # Claude CLI로 API 생성
        task = f"""FastAPI로 다음 API 엔드포인트를 만들어주세요:
{', '.join(endpoints)}

요구사항:
1. Pydantic 모델로 입출력 정의
2. SQLAlchemy 연동 (models.py)
3. CRUD 엔드포인트 (GET, POST, PUT, DELETE)
4. 적절한 에러 처리
5. OpenAPI 문서화

참고 스키마:
{schema if schema else '스키마 정보 없음'}

api/ 폴더에 파일 생성해주세요."""

        result = await self.work(task, context={"schema": schema})

        if result.get("success"):
            # API 스펙을 SharedMemory에 저장
            api_spec = {
                "endpoints": [
                    {"path": f"/api/{e}", "methods": ["GET", "POST", "PUT", "DELETE"]}
                    for e in endpoints
                ]
            }
            await self.share("api_spec", api_spec)
            await self.publish_event("api_ready", api_spec)

        return result


class FrontendAgent(CollaborativeAgent):
    """Frontend 전문 에이전트"""

    def __init__(self):
        super().__init__(
            name="frontend_agent",
            folder="frontend",
            expertise="React/TypeScript"
        )

    async def create_components(self, components: list) -> dict:
        """React 컴포넌트 생성"""
        # API 스펙 확인
        api_spec = await self.get_api_spec()

        if not api_spec:
            # Backend Agent에게 질문
            await self.ask(
                "API 스펙이 필요해요. 현재 만들어진 엔드포인트 알려줄 수 있어요?",
                to="backend_agent"
            )
            await asyncio.sleep(1)
            api_spec = await self.get_api_spec()

        await self.say("컴포넌트 개발 시작합니다.", to="orchestrator")

        # Claude CLI로 컴포넌트 생성
        task = f"""React/TypeScript로 다음 컴포넌트를 만들어주세요:
{', '.join(components)}

요구사항:
1. TypeScript 타입 정의
2. TailwindCSS 스타일링
3. 로딩/에러 상태 처리
4. API 연동 (react-query 또는 fetch)

API 스펙:
{api_spec if api_spec else 'API 스펙 없음'}

src/components/ 폴더에 파일 생성해주세요."""

        result = await self.work(task, context={"api_spec": api_spec})

        if result.get("success"):
            await self.publish_event("frontend_ready", {"components": components})

        return result


class TestAgent(CollaborativeAgent):
    """Test 전문 에이전트"""

    def __init__(self):
        super().__init__(
            name="test_agent",
            folder="tests",
            expertise="pytest/Testing"
        )

    async def write_tests(self) -> dict:
        """테스트 작성"""
        # 스키마와 API 스펙 가져오기
        schema = await self.get_schema()
        api_spec = await self.get_api_spec()

        await self.say("테스트 작성 시작합니다.", to="orchestrator")

        task = f"""pytest로 테스트를 작성해주세요.

테스트 대상:
1. DB 모델 단위 테스트
2. API 엔드포인트 통합 테스트
3. 주요 비즈니스 로직 테스트

스키마:
{schema if schema else '없음'}

API:
{api_spec if api_spec else '없음'}

tests/ 폴더에 파일 생성해주세요."""

        result = await self.work(task, context={"schema": schema, "api_spec": api_spec})

        if result.get("success"):
            await self.publish_event("tests_ready", {})

        return result


class Orchestrator:
    """오케스트레이터 - 에이전트들을 조율"""

    def __init__(self):
        self.db_agent = DBAgent()
        self.backend_agent = BackendAgent()
        self.frontend_agent = FrontendAgent()
        self.test_agent = TestAgent()

    async def connect_all(self):
        """모든 에이전트 연결"""
        agents = [
            self.db_agent,
            self.backend_agent,
            self.frontend_agent,
            self.test_agent
        ]

        results = await asyncio.gather(*[a.connect() for a in agents])
        return all(results)

    async def disconnect_all(self):
        """모든 에이전트 연결 해제"""
        await asyncio.gather(
            self.db_agent.disconnect(),
            self.backend_agent.disconnect(),
            self.frontend_agent.disconnect(),
            self.test_agent.disconnect()
        )

    async def build_shopping_mall(self):
        """쇼핑몰 프로젝트 빌드"""
        print("=" * 60)
        print("🛍️  쇼핑몰 프로젝트 빌드 시작")
        print("=" * 60)

        # 1. DB 스키마 설계
        print("\n[Phase 1] DB 스키마 설계")
        await self.db_agent.design_schema([
            "users",
            "categories",
            "products",
            "orders",
            "order_items"
        ])

        await asyncio.sleep(2)  # 이벤트 전파 대기

        # 2. Backend API 개발
        print("\n[Phase 2] Backend API 개발")
        await self.backend_agent.create_api([
            "users",
            "auth",
            "categories",
            "products",
            "orders"
        ])

        await asyncio.sleep(2)

        # 3. Frontend 개발
        print("\n[Phase 3] Frontend 개발")
        await self.frontend_agent.create_components([
            "ProductList",
            "ProductCard",
            "ProductDetail",
            "CategoryNav",
            "Cart",
            "Checkout",
            "UserAuth"
        ])

        await asyncio.sleep(2)

        # 4. 테스트 작성
        print("\n[Phase 4] 테스트 작성")
        await self.test_agent.write_tests()

        print("\n" + "=" * 60)
        print("🎉 쇼핑몰 프로젝트 빌드 완료!")
        print("=" * 60)


async def main():
    """메인 함수"""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║           AG-CLI Collaboration Demo: Shopping Mall            ║
╠═══════════════════════════════════════════════════════════════╣
║                                                               ║
║  이 예제는 여러 에이전트가 협업하여 쇼핑몰을 만드는           ║
║  과정을 보여줍니다.                                           ║
║                                                               ║
║  실행 전 필요한 서버:                                          ║
║  1. Message Bus: python mcp/message_bus.py                    ║
║  2. SharedMemory: python mcp/shared_memory.py                 ║
║                                                               ║
║  실시간 대화 뷰어:                                            ║
║  http://localhost:8100/viewer                                 ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
    """)

    orchestrator = Orchestrator()

    # 에이전트 연결
    if not await orchestrator.connect_all():
        print("\n❌ 에이전트 연결 실패!")
        print("   Message Bus와 SharedMemory 서버가 실행 중인지 확인하세요.")
        print("\n   시작 명령:")
        print("   python mcp/message_bus.py")
        print("   python mcp/shared_memory.py")
        return

    try:
        # 쇼핑몰 빌드
        await orchestrator.build_shopping_mall()
    finally:
        # 연결 해제
        await orchestrator.disconnect_all()


if __name__ == "__main__":
    asyncio.run(main())
