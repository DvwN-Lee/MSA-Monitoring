# Cloud-Native 마이크로서비스 플랫폼 프로젝트 계획서

**문서 버전**: 1.0
**작성일**: 2025년 10월 1일

---

## 1. 프로젝트 타임라인

- **프로젝트 시작일**: 2025년 9월 29일
- **프로젝트 종료 예정일**: 2025년 10월 31일 (총 5주)
- **주요 마일스톤**:
  - **Week 1**: AWS EKS 인프라 구축 완료 (`terraform apply`)
  - **Week 2**: CI/CD 파이프라인 완성 (Git Push -> 자동 배포)
  - **Week 3~4**: 기본 모니터링 시스템 구축 (Grafana 대시보드)
  - **Week 5**: 최종 테스트, 문서화 및 프로젝트 마감

---

## 2. 개발 일정 (주차별 계획)

| 주차 | 핵심 목표 | 상세 태스크 | 완료 기준 |
|:---|:---|:---|:---|
| **1주차** | **인프라 기반 구축 (IaC)** | - Terraform 학습 및 AWS 환경 설정<br>- VPC, Subnet, NAT GW 모듈 작성<br>- EKS 클러스터 및 노드 그룹 모듈 작성<br>- PostgreSQL StatefulSet 배포 및 앱 연결 테스트 | `terraform apply`로 EKS 클러스터 생성 성공 |
| **2주차** | **CI/CD 파이프라인 자동화** | - GitHub Actions 워크플로우 설계 (Lint, Test, Scan, Build)<br>- ECR에 이미지 푸시 자동화<br>- GitOps 저장소 구성<br>- Argo CD 설치 및 EKS 클러스터 연동 | Git Push 후 5분 내 EKS에 자동 배포 성공 |
| **3주차** | **관측성 시스템 구축** | - Prometheus Operator 및 Grafana 설치<br>- 각 서비스에 `/metrics` 엔드포인트 추가<br>- Golden Signals Grafana 대시보드 제작<br>- AlertManager + Slack 연동 및 테스트 알람 설정 | Grafana에서 모든 서비스 메트릭 실시간 조회 |
| **4주차** | **Should-Have 기능 구현** | - (순위 1) Loki + Promtail 중앙 로깅 시스템 구축<br>- (순위 2) Istio 설치 및 mTLS STRICT 모드 활성화<br>- (순위 3) ADR(기술결정기록) 3건 이상 작성 | Should-Have 요구사항 최소 2개 이상 완료 |
| **5주차** | **최종 테스트 및 문서화** | - k6를 이용한 부하 테스트 (100 RPS 목표)<br>- README, Architecture 등 핵심 문서 최종 검토<br>- 데모 시나리오 준비 | 성능 목표(NFR-1) 달성 및 모든 문서 초안 완료 |

---

## 3. 진행률 체크리스트

### Must-Have (필수)
- [ ] Terraform으로 EKS 인프라 구축 완료
- [ ] PostgreSQL StatefulSet 배포 및 데이터 영속성 확인
- [ ] GitHub Actions CI 파이프라인 (Lint, Test, Scan, Build) 동작
- [ ] Argo CD를 통한 GitOps 배포 자동화 완료
- [ ] Prometheus + Grafana 모니터링 대시보드 구축
- [ ] Slack을 통한 장애 알림 수신 확인

### Should-Have (권장)
- [ ] Loki 중앙 로깅 시스템 구축
- [ ] Istio mTLS 활성화
- [ ] API Gateway에 Rate Limiter 구현
- [ ] ADR 3건 이상 작성

---

## 4. 위험 관리 계획

| 위험 요소 | 발생 확률 | 영향도 | 대응 전략 |
|:---|:---:|:---:|:---|
| **1. 시간 부족** | 높음 | 치명적 | - **사전 방지**: 매주 일요일 진행률 점검, Must-Have에 모든 노력 집중.<br>- **상황 발생 시**: Should-Have, Could-Have 항목을 과감히 포기하고 필수 기능 완성에만 집중한다. |
| **2. AWS 비용 초과** | 중간 | 높음 | - **사전 방지**: AWS Billing Alarm ($30, $40) 설정. 주말/야간에는 노드 수를 0으로 축소.<br>- **상황 발생 시**: Spot Instance로 즉시 전환. 최악의 경우, EKS를 삭제하고 Terraform 코드 완성으로 포트폴리오 가치를 증명한다. |
| **3. Istio의 복잡성** | 중간 | 중간 | - **사전 방지**: mTLS 활성화라는 최소 범위만 목표로 한다. 고급 기능(Canary 등)은 Could-Have로 명확히 분리.<br>- **상황 발생 시**: 문제 해결에 1일 이상 소요되면 즉시 Istio를 롤백하고, "시간 부족으로 시도했으나 제외"로 기록한다. |

---

## 5. 자원 계획

- **인력**: 1명 (본인)
- **예산**: 월 $50 (AWS Free Tier 및 학생 크레딧 적극 활용)
- **시간**: 주당 약 20~30시간 투입 예상