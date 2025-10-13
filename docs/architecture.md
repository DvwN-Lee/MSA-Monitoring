# Cloud-Native 마이크로서비스 플랫폼 시스템 설계서

**문서 버전**: 1.0  
**작성일**: 2025년 9월 30일

---

## 1. 시스템 개요

### 1.1. 아키텍처 원칙
- **Infrastructure as Code (IaC)**: 모든 인프라는 Terraform 코드로 정의하고 관리하여 재현성과 일관성을 보장한다.
- **GitOps**: Git 저장소를 단일 진실 공급원(Single Source of Truth)으로 삼아 모든 배포를 자동화하고 추적한다.
- **Observability**: 시스템의 상태를 외부에서 완벽히 이해할 수 있도록 Metrics, Logs, Traces 수집을 기본으로 한다.
- **Security by Default**: 모든 통신은 암호화를 기본으로 하며, 최소 권한 원칙을 따른다.

### 1.2. 기술 스택 개요
- **Cloud**: AWS
- **Container Orchestration**: Amazon EKS (Kubernetes)
- **IaC**: Terraform
- **CI/CD**: GitHub Actions, Argo CD
- **Service Mesh**: Istio
- **Monitoring**: Prometheus, Grafana
- **Logging**: Loki, Promtail
- **Application**: Go, Python (FastAPI)
- **Database**: PostgreSQL, Redis

> **참고**: 각 기술 스택의 상세한 선택 이유는 `../adr/` 디렉토리의 기술 결정 기록(ADR) 문서를 참조하십시오.

### 1.3. 문서 구조 안내

본 설계서는 시스템 아키텍처의 **핵심 개념과 구조**를 설명합니다. 

**상세 구현 정보 위치:**
- **Terraform 변수 및 모듈 설정**: `terraform/` 디렉토리의 코드 및 주석
- **Kubernetes 리소스 상세**: `k8s/` 디렉토리의 매니페스트 및 Kustomize 설정
- **CI/CD 파이프라인 스크립트**: `.github/workflows/` 디렉토리
- **애플리케이션 로직**: 각 서비스의 소스 코드 및 README

> **개인 프로젝트 고려**: 1인 프로젝트이므로 모든 구현 세부사항을 문서화하는 대신, 핵심 설계 결정과 아키텍처 패턴에 집중했습니다.

---

## 2. 시스템 아키텍처

### 2.1. 전체 아키텍처 다이어그램

### 2.2. 네트워크 아키텍처 (VPC)
- **VPC CIDR**: `10.0.0.0/16`
- **Public Subnets**: 2개의 가용 영역(AZ)에 걸쳐 Public Subnet 2개 구성. (ALB, NAT Gateway 용도)
- **Private Subnets**: 2개의 가용 영역(AZ)에 걸쳐 Private Subnet 2개 구성. (EKS Worker Nodes 용도)
- **NAT Gateway**: Private Subnet의 아웃바운드 인터넷 통신을 위해 1개의 NAT Gateway를 Public Subnet에 배치. (비용 절감)
- **Security Groups**: 각 리소스 그룹(ALB, EKS Nodes, DB)에 필요한 최소한의 포트만 허용하도록 규칙 설정.

---

## 3. CI/CD 파이프라인 설계

### 3.1. GitHub Actions 워크플로우 (CI)
- **Trigger**: `main` 브랜치로의 `push` 또는 `pull_request`
- **Jobs**:
  1.  **Lint & Test**: `golangci-lint`, `flake8` 실행 및 `go test`, `pytest`로 단위 테스트와 커버리지 측정.
  2.  **Build**: Docker 멀티 스테이지 빌드를 통해 경량화된 컨테이너 이미지 생성.
  3.  **Scan**: Trivy를 사용하여 이미지의 보안 취약점 스캔.
  4.  **Push**: 빌드된 이미지를 AWS ECR에 푸시.
  5.  **Update Manifests**: GitOps 저장소의 Kustomize 이미지 태그를 새로운 Git SHA로 자동 업데이트 후 커밋.

### 3.2. Argo CD 구성 (CD)
- **Application 설정**: App of Apps 패턴을 사용하여 여러 마이크로서비스를 단일 Application으로 관리.
- **Sync Policy**:
  - `automated`: GitOps 저장소 변경 시 자동 동기화.
  - `prune: true`: Git에서 삭제된 리소스를 클러스터에서도 자동 제거.
  - `selfHeal: true`: 클러스터 상태가 Git과 달라지면 자동으로 Git 상태로 복구.

---

## 4. 모니터링 & 로깅 설계

- **Prometheus**: Prometheus Operator를 사용하여 설치 및 관리. ServiceMonitor CRD를 통해 신규 서비스를 자동으로 탐지하고 메트릭 수집.
- **Grafana**: Golden Signals 대시보드(Latency, Traffic, Errors, Saturation)를 기본으로 구성. Alertmanager와 연동하여 Slack으로 장애 알림 전송.
- **Loki**: Promtail을 DaemonSet으로 각 노드에 배포하여 컨테이너 로그를 수집. Loki는 이를 저장하고, Grafana에서 `LogQL`을 통해 조회.

---

## 5. 보안 설계

- **Istio mTLS**: `PeerAuthentication` 정책을 `STRICT` 모드로 설정하여 네임스페이스 내 모든 서비스 간 통신을 암호화.
- **Network Policy**: Kubernetes의 Network Policy를 사용하여 Pod 간의 통신을 명시적으로 허용. (예: `blog-service`는 `db-service`의 5432 포트로만 접근 가능)
- **Secrets 관리**: 데이터베이스 암호 등 민감 정보는 Kubernetes Secrets에 저장하고, AWS Secrets Manager와 연동하는 방안을 고려. (Could-Have)

---

## 참고 문서

- **[요구사항 명세서](./requirements.md)**
- **[프로젝트 계획서](./project-plan.md)**
- **[기술 결정 기록 (ADR)](./adr/)**
