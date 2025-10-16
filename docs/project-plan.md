# Cloud-Native 마이크로서비스 플랫폼 프로젝트 계획서

**문서 버전**: 2.0  
**작성일**: 2025년 10월 13일

---

## 문서 변경 이력

| 문서 버전 | 날짜 | 변경 내용 | 수정된 계획 항목 |
|----------|------|----------|-----------------|
| **1.0** | 2025-10-01 | 초안 작성 (AWS 기반 계획) | AWS EKS 환경을 기준으로 5주 개발 계획 수립 |
| **2.0** | 2025-10-13 | • **인프라 구축 대상을 AWS → Solid Cloud로 변경**<br>• **Terraform 코드가 Solid Cloud용으로 작성됨**<br>• **비용 계획을 리소스 계획으로 수정** (Solid Cloud는 무료), AWS 배포는 선택사항(Phase 3)으로 재정의, 위험 관리에 Solid Cloud 장애 시나리오 추가 | 개발 환경, 주차별 개발 계획, 위험 관리, 자원 계획 |

---

## 1. 프로젝트 개요

### 1.1. 프로젝트 정보
- **프로젝트명**: Cloud-Native 마이크로서비스 플랫폼 v2.0
- **개발자**: [이름]
- **소속**: 단국대학교 컴퓨터공학과
- **프로젝트 유형**: 졸업 프로젝트

### 1.2. 타임라인
- **시작일**: 2025년 9월 29일
- **종료 예정일**: 2025년 10월 31일
- **총 기간**: 5주

### 1.3. 개발 환경
- **개발/테스트**: 단국대학교 Solid Cloud
- **최종 배포**: AWS (선택사항, 테스트 완료 후)

---

## 2. 주차별 개발 계획

### Week 1: 인프라 기반 구축 (9/29 ~ 10/5)

#### 목표
Terraform을 사용하여 Solid Cloud에 Kubernetes 클러스터와 기본 인프라 구축

#### 세부 작업
1. **Terraform 학습 및 환경 설정**
   - Terraform 기본 문법 학습
   - Solid Cloud 접속 및 권한 확인
   - Terraform Provider 설정

2. **네트워크 구성**
   - VPC 및 Subnet 설정
   - 보안 그룹 구성
   - Load Balancer 설정

3. **Kubernetes 클러스터 구축**
   - 클러스터 생성 및 노드 그룹 설정
   - kubectl 연결 확인
   - 기본 네임스페이스 구성

4. **PostgreSQL 배포**
   - StatefulSet으로 PostgreSQL 배포
   - PersistentVolume 설정
   - 데이터베이스 초기화 및 연결 테스트

#### 완료 기준
- [ ] `terraform apply`로 클러스터 생성 성공
- [ ] kubectl로 클러스터 접근 가능
- [ ] PostgreSQL이 정상적으로 실행되고 데이터 저장 확인

---

### Week 2: CI/CD 파이프라인 구축 (10/6 ~ 10/12)

#### 목표
GitHub Actions와 Argo CD를 연동하여 자동 배포 파이프라인 완성

#### 세부 작업
1. **GitHub Actions CI 파이프라인**
   - 워크플로우 파일 작성 (`.github/workflows/`)
   - Lint & Test 단계 구성
   - Trivy 보안 스캔 설정
   - 컨테이너 이미지 빌드 및 Push

2. **GitOps 저장소 구성**
   - Kubernetes 매니페스트 저장소 생성
   - Kustomize를 사용한 환경별 설정 관리
   - 이미지 태그 자동 업데이트 스크립트

3. **Argo CD 설치 및 설정**
   - Argo CD Helm Chart 설치
   - Application CRD 작성
   - GitOps 저장소 연동
   - 자동 동기화 정책 설정

4. **통합 테스트**
   - Git Push → 자동 빌드 → 자동 배포 전체 플로우 테스트
   - 롤백 시나리오 테스트

#### 완료 기준
- [ ] Git Push 시 GitHub Actions가 자동 실행
- [ ] Argo CD가 변경 사항을 감지하고 자동 배포
- [ ] 전체 파이프라인이 5분 이내 완료

---

### Week 3: 관측성 시스템 구축 (10/13 ~ 10/19)

#### 목표
Prometheus, Grafana, Loki를 설치하여 시스템 모니터링 환경 구축

#### 세부 작업
1. **Prometheus & Grafana 설치**
   - Prometheus Operator 설치
   - Grafana 설치 및 Prometheus 연동
   - ServiceMonitor CRD 설정

2. **애플리케이션 메트릭 수집**
   - 각 서비스에 `/metrics` 엔드포인트 추가
   - Prometheus로 메트릭 수집 확인
   - 커스텀 메트릭 정의 (요청 수, 응답 시간 등)

3. **Grafana 대시보드 구성**
   - Golden Signals 대시보드 작성
     - Latency (응답 시간)
     - Traffic (요청 수)
     - Errors (에러율)
     - Saturation (리소스 사용률)
   - Kubernetes 클러스터 상태 대시보드

4. **알림 설정**
   - AlertManager 설정
   - Slack 연동 (선택사항)
   - 주요 알림 규칙 정의 (CPU 90% 이상, Pod 재시작 등)

#### 완료 기준
- [ ] Grafana에서 모든 서비스의 메트릭 확인 가능
- [ ] 대시보드에서 시스템 상태를 한눈에 파악
- [ ] 테스트 알림이 정상 발송됨

---

### Week 4: Should-Have 기능 구현 (10/20 ~ 10/26)

#### 목표
권장 요구사항 중 핵심 기능 2~3개 선택하여 구현

#### 우선순위별 작업

**Priority 1: Loki 중앙 로깅 시스템**
- Loki 및 Promtail 설치
- 모든 서비스 로그 수집 설정
- Grafana에서 로그 조회 및 검색 테스트

**Priority 2: Istio 서비스 메시**
- Istio 설치
- 서비스에 Sidecar 자동 주입 설정
- mTLS STRICT 모드 활성화
- 서비스 간 암호화 통신 확인

**Priority 3: Rate Limiting (시간 여유 시)**
- API Gateway에 Token Bucket 알고리즘 구현
- 요청 제한 테스트 (예: 100 req/sec)

#### 완료 기준
- [ ] Loki를 통한 로그 수집 및 Grafana 조회 가능
- [ ] Istio mTLS가 활성화되고 서비스 간 암호화 확인
- [ ] (선택) Rate Limiting 동작 확인

---

### Week 5: 테스트 및 문서화 (10/27 ~ 10/31)

#### 목표
최종 테스트 수행 및 프로젝트 문서 완성

#### 세부 작업

1. **성능 테스트**
   - k6를 사용한 부하 테스트
   - 목표: 100 RPS에서 P95 응답 시간 < 500ms
   - 결과 분석 및 병목 지점 파악

2. **장애 시나리오 테스트**
   - Pod 강제 종료 시 자동 복구 확인
   - 데이터베이스 연결 끊김 처리
   - 서비스 롤백 테스트

3. **보안 검증**
   - Trivy 스캔 결과 확인 (취약점 0개)
   - mTLS 암호화 확인
   - Network Policy 동작 검증

4. **문서 최종 검토**
   - README 업데이트
   - 아키텍처 문서 최종 수정
   - ADR(기술 결정 기록) 3건 이상 작성
   - 프로젝트 회고 작성

5. **데모 준비**
   - Git Push → 자동 배포 시연 준비
   - Grafana 대시보드 시연
   - 주요 기능 데모 시나리오 작성

#### 완료 기준
- [ ] 모든 성능 및 보안 목표 달성
- [ ] 프로젝트 문서 완성
- [ ] 데모 준비 완료

---

## 3. 마일스톤

| 날짜 | 마일스톤 | 완료 여부 |
|------|----------|-----------|
| 10/5 | Solid Cloud 인프라 구축 완료 | ⬜ |
| 10/12 | CI/CD 파이프라인 구축 완료 | ⬜ |
| 10/19 | 모니터링 시스템 구축 완료 | ⬜ |
| 10/26 | Should-Have 기능 2개 이상 완료 | ⬜ |
| 10/31 | 프로젝트 최종 완료 | ⬜ |

---

## 4. 위험 관리

### 4.1. 주요 위험 요소

| 위험 | 발생 확률 | 영향도 | 대응 전략 |
|------|-----------|--------|-----------|
| **시간 부족** | 높음 | 치명적 | - 매주 일요일 진행률 점검<br>- Must-Have에 집중<br>- 진행이 느리면 Should-Have 과감히 포기 |
| **Solid Cloud 장애** | 중간 | 높음 | - 로컬 환경(Minikube)을 백업으로 유지<br>- 장애 발생 시 로컬에서 개발 지속 |
| **Istio 복잡도** | 중간 | 중간 | - mTLS만 목표로 최소 범위 설정<br>- 1일 이상 소요 시 롤백 |
| **성능 목표 미달성** | 낮음 | 중간 | - 병목 지점 프로파일링<br>- 캐싱 전략 적용<br>- 최악의 경우 목표치 조정 |

### 4.2. 비상 계획

**만약 3주차 이후에도 Must-Have가 완료되지 않은 경우**:
1. Should-Have 전체 포기
2. 문서화 작업 최소화
3. 남은 시간을 Must-Have 완성에 집중

---

## 5. 자원 계획

### 5.1. 인력
- **개발**: 1명 (본인)
- **주당 투입 시간**: 20~30시간

### 5.2. 인프라
- **개발/테스트**: Solid Cloud (무료)
- **최종 배포**: AWS (선택사항, Free Tier 활용)

### 5.3. 도구 및 소프트웨어
- **필수**: Terraform, kubectl, Docker, Git
- **선택**: k6 (부하 테스트), Lens (Kubernetes IDE)

---

## 6. 향후 계획

### 6.1. 프로젝트 완료 후
- Solid Cloud 테스트 완료 시 AWS 배포 시도
- 포트폴리오 및 이력서에 프로젝트 추가
- 기술 블로그에 개발 과정 정리

### 6.2. 추가 개선 사항 (선택)
- Canary 배포 전략 도입
- ArgoCD Image Updater 적용
- Horizontal Pod Autoscaler (HPA) 구성
- Jaeger를 통한 분산 추적 시스템 구축

---

## 7. 체크리스트

### Must-Have (필수)
- [ ] Terraform으로 Kubernetes 클러스터 생성
- [ ] PostgreSQL StatefulSet 배포 및 데이터 영속성 확인
- [ ] GitHub Actions CI 파이프라인 동작
- [ ] Argo CD GitOps 배포 자동화
- [ ] Prometheus + Grafana 모니터링 대시보드
- [ ] 모든 서비스 정상 동작 확인

### Should-Have (권장)
- [ ] Loki 중앙 로깅 시스템
- [ ] Istio mTLS 활성화
- [ ] ADR 3건 이상 작성

### Could-Have (선택)
- [ ] Rate Limiting 구현
- [ ] Jaeger 분산 추적
- [ ] HPA 자동 확장

---

## 참고 문서
- **[요구사항 명세서](./requirements.md)**
- **[시스템 설계서](./architecture.md)**
- **[기술 결정 기록 (ADR)](./adr/)**
