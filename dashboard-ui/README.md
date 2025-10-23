# Dashboard UI Service (dashboard-ui)

## 1. 개요
- **실시간 모니터링 프론트엔드**: `dashboard-ui`는 전체 마이크로서비스의 상태를 시각적으로 보여주는 웹 기반 대시보드임
- **순수 웹 기술로 구현**: 별도의 프론트엔드 프레임워크 없이 **HTML, CSS, 순수 JavaScript(Vanilla JS)**만으로 구성되어 있으며, 데이터 시각화를 위해 **Chart.js** 라이브러리를 사용함
- **데이터 소스**: 대시보드에 표시되는 모든 데이터는 `load-balancer`의 `/stats` 엔드포인트를 주기적으로 호출(Polling)하여 얻어옴

## 2. 핵심 기능 및 책임
- **실시간 지표 시각화**: 시스템의 전체 처리량(RPS), 평균 응답 시간 등의 핵심 성능 지표(KPI)를 실시간 차트와 숫자로 시각화
- **서비스 상태 종합 표시**: `load-balancer`를 포함한 모든 개별 마이크로서비스와 데이터 저장소(DB, Cache)의 상태를 `Online` / `Offline` / `Degraded` 등으로 명확하게 표시
- **IDLE 상태 방지 (WebSocket 하트비트)**: 실제 API 트래픽이 없는 경우에도 `load-balancer`가 시스템을 '활성' 상태로 인지하도록 WebSocket 기반의 하트비트 신호를 전송. 이를 통해 트래픽이 없을 때 대시보드 지표가 멈추는 것을 방지함
- **사용자 인터페이스**: 모니터링 시작/중지, 수동 새로고침, WebSocket 하트비트 활성화/비활성화 등 사용자가 직접 대시보드를 제어할 수 있는 컨트롤 버튼을 제공

## 3. 기술 구현 (`script.js`)
- 대시보드의 모든 로직은 단일 JavaScript 파일(`script.js`) 내에서 각 기능별로 **모듈화된 객체**(`apiService`, `chartModule`, `statusModule` 등)를 통해 체계적으로 관리됨

### 3.1. 모듈 기반 아키텍처 및 이벤트 버스
- **기능별 모듈**: `apiService` (API 통신), `chartModule` (차트 관리), `statusModule` (상태 텍스트 업데이트) 등 각 객체가 특정 UI 요소나 기능을 전담하여 코드의 응집도를 높임
- **`eventBus`를 통한 통신**: `apiService`가 `/stats` API로부터 새로운 데이터를 받아오면, `eventBus.publish('statsUpdated', ...)`를 통해 데이터 수신 이벤트를 발행함. `chartModule`이나 `statusModule`과 같은 다른 모듈들은 이 이벤트를 구독(`subscribe`)하고 있다가, 이벤트가 발생하면 각자 맡은 UI를 업데이트하는 방식으로 동작. 이를 통해 모듈 간의 직접적인 의존성을 제거함

### 3.2. WebSocket 하트비트 로직
- **"IDLE" 상태 문제**: `load-balancer`는 `/api/*` 경로로 실제 요청이 들어올 때만 트래픽으로 집계함. 따라서 사용자가 API를 호출하지 않으면, LB는 트래픽이 없는 것으로 판단하여 대시보드에 "IDLE" 상태를 표시하고 RPS와 응답 시간 업데이트를 멈춤
- **해결 방안**: 이 문제를 해결하기 위해 `wsHeartbeat` 객체를 구현함
    1.  대시보드가 로드되면 `load-balancer`의 `/api/ws-heartbeat` 엔드포인트로 WebSocket 연결을 시도
    2.  연결이 성공하면, 5초마다 주기적으로 `"hb"`라는 간단한 메시지를 서버로 전송
    3.  `load-balancer`는 이 WebSocket 활동을 '실제 트래픽'으로 간주하여, API 호출이 없더라도 시스템이 계속 활성 상태인 것으로 판단하고 지표를 지속적으로 계산함

### 3.3. 동적 UI 렌더링
- `statusModule`은 `statsUpdated` 이벤트가 발생할 때마다 전달받은 JSON 데이터를 분석
- 서비스별 상태(`healthy`, `unhealthy`)에 따라 CSS 클래스(`metric-good`, `metric-danger`)를 동적으로 변경하여 상태 표시기의 색상과 텍스트를 업데이트함
- `chartModule`은 동일한 이벤트로부터 `requests_per_second` 값을 추출하여 차트에 새로운 데이터 포인트를 추가하고, 가장 오래된 데이터는 제거하여 차트가 항상 최신 상태를 유지하도록 함

## 4. 제공 엔드포인트
|경로|메서드|설명|
|:---|:---|:---|
|`/`|`GET`|Nginx가 `index.html` 파일을 서빙하는 기본 경로. 대시보드 애플리케이션의 진입점|
|`/script.js`|`GET`|대시보드의 모든 동적 로직을 포함하는 JavaScript 파일|

## 5. 컨테이너화 (`Dockerfile`)
- **웹 서버**: 경량 웹 서버인 **`nginx:1.27-alpine`** 이미지를 기반으로 하여 효율적인 정적 파일 서빙을 수행
- **콘텐츠 배포**: `COPY` 명령어를 사용하여 `index.html`과 `script.js` 파일을 Nginx의 기본 웹 루트 디렉터리인 `/usr/share/nginx/html/`로 복사하여 컨테이너가 시작될 때 바로 서비스할 수 있도록 구성

## 6. 설정
- `dashboard-ui` 서비스는 별도의 환경 변수 설정이 없음. API 호출 주기(`refreshInterval`), 차트의 최대 데이터 포인트 수(`maxChartPoints`) 등 모든 주요 설정은 `script.js` 파일 상단의 `config` 객체에 하드코딩되어 있음