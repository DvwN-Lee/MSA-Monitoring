# Load Balancer & Stats Aggregator (load-balancer)

## 1. 개요
- **시스템의 중앙 관문 및 모니터링 허브**: `load-balancer`는 외부의 모든 요청을 수신하여 적절한 서비스(`api-gateway`, `dashboard-ui` 등)로 분배하는 **리버스 프록시**이자, 시스템 전체의 상태와 성능 지표를 수집하여 **통합된 모니터링 데이터를 제공**하는 핵심 서비스임
- **Go 기반의 고성능 구현**: 높은 동시성 처리 능력을 위해 Go 언어로 작성되었으며, 표준 라이브러리와 `gorilla/websocket`을 사용하여 효율적인 프록시 및 WebSocket 서버를 구현함
- **모니터링 데이터의 시작 지점**: `dashboard-ui`가 시각화하는 모든 실시간 데이터(RPS, 응답 시간, 서비스 상태 등)는 이 서비스의 `/stats` 엔드포인트를 통해 제공됨

## 2. 핵심 기능 및 책임
- **요청 프록시**: 외부 요청 경로에 따라 트래픽을 분배
    - `/api/*`: `api-gateway`로 전달
    - `/blog/*`: `blog-service`의 SPA UI로 전달
    - 그 외 (`/`): `dashboard-ui`로 전달
- **통계 집계 (Stats Aggregation)**: `/stats` 엔드포인트를 통해 모든 하위 마이크로서비스의 `/stats` 엔드포인트를 **병렬로 호출**하고, 수집된 데이터를 자신의 통계와 결합하여 단일 JSON 응답으로 제공
- **실시간 지표 계산**: 수신하는 모든 요청을 분석하여, **최근 10초**를 기준으로 시스템의 실시간 처리량(RPS)과 평균 응답 시간을 직접 계산
- **"실제 트래픽" 구분**: 단순 헬스 체크나 정적 UI 요청과 실제 API 호출(`- /api/*`)을 구분하여, 의미 있는 성능 지표만 계산하고 대시보드에 표시
- **WebSocket 하트비트 처리**: `dashboard-ui`로부터의 WebSocket 연결을 처리하여, API 트래픽이 없을 때도 시스템이 활성 상태임을 감지할 수 있도록 지원

## 3. 기술적 구현 (`main.go`)
- `load-balancer`의 핵심은 **`statsMiddleware`**를 통한 요청 데이터 수집과, **`/stats` 핸들러**를 통한 데이터 집계 및 계산 로직에 있음

### 3.1. 통계 미들웨어 (`statsMiddleware`)
- 이 미들웨어는 프록시되는 모든 HTTP 요청을 감싸서, 각 요청의 시작 시간과 처리 시간을 측정
- **"실제 API 트래픽" 필터링**:
    - 요청 경로가 `/api/`로 시작하고,
    - HTTP 메서드가 `HEAD`가 아니며,
    - `X-Heartbeat` 헤더가 `true`가 아닌 요청만 **"실제 API 트래픽"**으로 간주
- 이렇게 필터링된 "실제 트래픽"에 대해서만 RPS와 평균 응답 시간 계산을 위한 데이터를 별도로 기록함 (`apiRequests`, `apiResponseSamples`). 이를 통해 UI 리소스 요청과 같은 부가적인 트래픽을 성능 지표에서 제외하여 측정의 정확도를 높임

### 3.2. 통계 집계 및 계산 로직 (`/stats` 핸들러)

1.  **자체 지표 계산 (Sliding Window 방식)**:
    - **실시간 RPS**: 현재 시간 기준으로 **최근 10초 동안** 발생한 "실제 API 트래픽" 요청 수를 10으로 나누어 계산
    - **실시간 평균 응답 시간**: 동일하게 최근 10초 동안의 "실제 API 트래픽" 요청들의 처리 시간 평균을 계산
    - 이 "Sliding Window" 방식을 통해 순간적인 부하 변화에도 민감하게 반응하는 최신 지표를 제공
2.  **하위 서비스 상태 병렬 수집**:
    - `api-gateway`, `user-service` 등 모든 하위 서비스의 `/stats` URL 목록을 정의
    - Go의 **고루틴(goroutine)**과 **`sync.WaitGroup`**을 사용하여 모든 서비스에 동시에 상태 정보를 요청함
    - `fetchServiceStats` 함수 내에서 각 서비스 호출에 **2초의 타임아웃**을 설정. 특정 서비스가 응답하지 않더라도 전체 집계가 지연되거나 실패하는 것을 방지
3.  **데이터 통합**: 자체적으로 계산한 실시간 지표와 각 하위 서비스로부터 수집한 상태 정보를 하나의 거대한 JSON 객체로 통합하여 최종적으로 반환

### 3.3. WebSocket 하트비트 처리 로직
- **`/api/ws-heartbeat` 핸들러**:
    - `gorilla/websocket` 라이브러리를 사용하여 HTTP 요청을 WebSocket 연결로 업그레이드
    - 클라이언트(`dashboard-ui`)로부터 메시지를 수신할 때마다, 현재 시간을 `wsActivities` 슬라이스에 기록
    - `/stats` 핸들러는 이 `wsActivities` 기록을 확인하여, 최근 10초 내에 WebSocket 활동이 있었는지 판단
    - 이 활동 여부를 `has_real_traffic` 플래그에 반영. 따라서 API 호출이 없어도 WebSocket 연결만 유지되면 대시보드는 "IDLE" 상태로 전환되지 않음

## 4. 제공 엔드포인트
|경로|메서드|설명|
|:---|:---|:---|
|`/`|`GET`|`dashboard-ui`로 요청을 프록시. 모니터링 대시보드의 기본 진입점|
|`/api/*`|`ANY`|`api-gateway`로 모든 API 관련 요청을 프록시|
|`/blog/*`|`GET`|`blog-service`의 SPA UI로 요청을 프록시|
|`/stats`|`GET`|모든 서비스의 상태와 실시간 성능 지표를 집계하여 JSON으로 반환|
|`/api/ws-heartbeat`|`GET`|`dashboard-ui`의 하트비트를 위한 WebSocket 연결 엔드포인트|
|`/lb-health`|`GET`|로드밸런서 자체의 상태를 확인하는 헬스 체크 엔드포인트|

## 5. 컨테이너화 (`Dockerfile`)
- `api-gateway`와 동일하게, Go 소스 코드를 정적 바이너리로 컴파일한 후 `scratch` 이미지에 복사하는 **Multi-stage Docker build** 방식을 사용하여, 매우 가볍고 보안성이 높은 최종 이미지를 생성함

## 6. 설정
- `LB_PORT`: 로드밸런서가 실행될 포트 (기본값: `7100`)
- `API_GATEWAY_URL`: 프록시할 API 게이트웨이의 주소
- `DASHBOARD_UI_URL`: 프록시할 대시보드 UI의 주소
- `AUTH_SERVICE_URL`, `BLOG_SERVICE_URL`, `USER_SERVICE_URL`: `/stats` 집계 시 호출할 각 서비스의 주소