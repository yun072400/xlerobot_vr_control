# 🥽 XLerobot MetaQuest VR Control System

MetaQuest VR 헤드셋으로 XLerobot 이중 팔 로봇을 원격 조종하는 통합 시스템입니다.

## 📋 목차

- [주요 기능](#주요-기능)
- [시스템 요구사항](#시스템-요구사항)
- [설치 및 설정](#설치-및-설정)
- [사용 방법](#사용-방법)
- [제어 가이드](#제어-가이드)
- [설정 및 최적화](#설정-및-최적화)
- [문제 해결](#문제-해결)

## 주요 기능

✅ **실시간 VR 트래킹**
- MetaQuest 컨트롤러 위치 및 회전 실시간 감지
- 저지연 응답 (100Hz 제어 루프)

✅ **듀얼 암 제어**
- 양쪽 팔 독립적 제어
- 역운동학(IK) 자동 계산
- 부드러운 비례 제어(P-Control)

✅ **고급 기능**
- 손목 플렉스/롤 제어
- 그리퍼 개폐 (트리거 기반)
- 헤드/베이스 무브먼트
- 응급 정지(Emergency Stop)

✅ **안전 기능**
- 조인트 각도 제한
- 속도 제한
- 충돌 감지 준비
- 비상 중단 버튼

## 시스템 요구사항

### 하드웨어

- **MetaQuest 3 또는 Pro** VR 헤드셋
- **XLerobot** 로봇 (듀얼 SO100 암)
- **연결된 PC** (Ubuntu 20.04+ 권장)
- **로컬 네트워크** 연결 (WiFi/Ethernet)

### 소프트웨어

- Python 3.12+
- LeRobot 라이브러리
- XLeVR 라이브러리
- 필수 의존성: NumPy, PyTorch, etc.

## 설치 및 설정

### 1단계: LeRobot 설치

```bash
cd /home/choyunsang/lerobot

# 전체 의존성 설치 (권장)
uv sync --locked --extra all

# 또는 필수 만 설치
uv sync --locked
```

### 2단계: XLeVR 설정

XLeVR이 다음 경로에 설치되어 있는지 확인하세요:

```
/home/choyunsang/XLeRobot/XLeVR/
```

필요시 `xlerobot_vr_control.py`의 `XLEVR_PATH`를 수정하세요:

```python
XLEVR_PATH = "/your/path/to/XLeVR"
```

### 3단계: 파일 확인

다음 파일들이 `/home/choyunsang/lerobot/examples/` 에 있는지 확인하세요:

```
xlerobot_vr_control.py      # 메인 제어 프로그램
metaquest_config.py         # MetaQuest 설정
run_vr_control.py           # 실행 스크립트
vr_monitor.py               # VR 모니터링
README_VR_CONTROL.md        # 이 파일
```

### 4단계: 로봇 연결

1. XLerobot 로봇 전원 켜기
2. PC와 로봇 연결 확인 (USB/네트워크)
3. 로봇 드라이버 설치 확인

## 사용 방법

### 빠른 시작

```bash
cd /home/choyunsang/lerobot/examples

# 방법 1: 진단 도구 포함 (권장)
uv run python3 run_vr_control.py

# 방법 2: 직접 실행
uv run python3 xlerobot_vr_control.py
```

### 단계별 실행 과정

1. **시스템 체크**
   ```
   🔍 Checking dependencies...
   ✅ NumPy
   ✅ LeRobot
   🔍 Checking XLeVR path...
   ```

2. **로봇 연결**
   ```
   🤖 Connecting to XLerobot...
   ✅ Successfully connected to robot
   ✅ Robot is calibrated and ready
   ```

3. **초기화**
   ```
   🎯 Moving to zero position...
   ⚙️  Initializing controllers...
   ```

4. **VR 연결**
   ```
   📱 Connect your MetaQuest VR headset
   Open your VR headset browser and navigate to:
   https://<your-ip>:8443
   ```

5. **제어 시작**
   ```
   ✅ VR Monitor is running
   🚀 Main VR control loop started
   ```

## 제어 가이드

### MetaQuest 컨트롤러 매핑

#### 오른쪽 컨트롤러 (Right Hand)
```
┌─────────────────────────────────────┐
│   오른쪽 팔 제어                      │
├─────────────────────────────────────┤
│ 💫 위치 이동   → 팔 말단 위치 제어   │
│ 🔄 회전       → 손목 플렉스/롤       │
│ 🎯 트리거     → 그리퍼 열기/닫기    │
│ 👆 Grip 버튼  → 힘 제어             │
│ 📍 Thumbstick → 헤드 회전            │
│ Ⓐ A 버튼     → 보조 기능            │
│ Ⓑ B 버튼     → 보조 기능            │
└─────────────────────────────────────┘
```

#### 왼쪽 컨트롤러 (Left Hand)
```
┌─────────────────────────────────────┐
│   왼쪽 팔 제어                      │
├─────────────────────────────────────┤
│ 💫 위치 이동   → 팔 말단 위치 제어  │
│ 🔄 회전       → 손목 플렉스/롤      │
│ 🎯 트리거     → 그리퍼 열기/닫기   │
│ 👆 Grip 버튼  → 힘 제어             │
│ 📍 Thumbstick → 베이스 이동 (옵션)  │
│ Ⓧ X 버튼     → 보조 기능           │
│ Ⓨ Y 버튼     → 응급 정지           │
└─────────────────────────────────────┘
```

#### 헤드셋 (Headset)
```
┌─────────────────────────────────────┐
│   헤드셋 트래킹                      │
├─────────────────────────────────────┤
│ 👓 위치 추적   → 1인칭 시점         │
│ 🔍 방향 추적   → 카메라 각도        │
└─────────────────────────────────────┘
```

### 동작 예시

**우측 팔을 앞으로 내밀기:**
1. 오른쪽 컨트롤러를 앞으로 움직임
2. 로봇 우측 팔이 자동으로 따라옴

**물체 집기:**
1. 물체 위에 팔 말단 위치
2. 트리거를 눌러서 그리퍼 닫기
3. 컨트롤러를 위로 올리면 로봇도 들어올림

**헤드 회전:**
1. 오른쪽 컨트롤러 Thumbstick 좌우로 움직임
2. 로봇 헤드가 회전함

## 설정 및 최적화

### 기본 설정 파일: `metaquest_config.py`

#### 감도 조정 (Sensitivity)

```python
# 적게 → 느리지만 정확함, 많게 → 빠르지만 부정확함
POSITION_SCALE = 0.01   # 위치 감도 (0.005 ~ 0.05)
ANGLE_SCALE = 4.0       # 각도 감도 (1.0 ~ 10.0)
```

#### 움직임 제한 (Limits)

```python
DELTA_LIMIT = 0.01      # 최대 위치 변화 (meter/frame)
ANGLE_LIMIT = 8.0       # 최대 각도 변화 (deg/frame)
```

#### 업데이트 속도 (Rate)

```python
CONTROL_LOOP_RATE = 100  # Hz (50-200 권장)
```

#### 안전 제한 (Safety)

```python
MAX_ARM_SPEED = 1.0         # m/s
MAX_JOINT_SPEED = 45.0      # degrees/s
ENABLE_EMERGENCY_STOP = True
```

### 조정 절차

1. **처음 시작할 때:**
   - 기본값 사용

2. **팔이 너무 빠르게 반응하면:**
   - `POSITION_SCALE` 감소 (예: 0.01 → 0.005)
   - `ANGLE_SCALE` 감소 (예: 4.0 → 2.0)

3. **팔이 너무 느리게 반응하면:**
   - `POSITION_SCALE` 증가 (예: 0.01 → 0.02)
   - `ANGLE_SCALE` 증가 (예: 4.0 → 8.0)

4. **미세한 떨림이 있으면:**
   - `DELTA_LIMIT` 증가 (예: 0.01 → 0.02)
   - `ANGLE_LIMIT` 증가 (예: 8.0 → 12.0)

## 문제 해결

### 문제 1: 로봇과 연결 안됨

**증상:**
```
❌ Failed to connect to robot
```

**해결 방법:**
```bash
# 1. 로봇 전원 확인
# 2. USB 케이블 확인
# 3. 드라이버 설치 확인

# 4. 진단 실행
uv run python3 run_vr_control.py
```

### 문제 2: VR 헤드셋 연결 안됨

**증상:**
```
❌ VR monitor initialization failed
No response from https://computer-ip:8443
```

**해결 방법:**

1. **XLeVR 확인**
   ```bash
   ls -la /home/choyunsang/XLeRobot/XLeVR/
   ```

2. **포트 확인**
   ```bash
   sudo lsof -i :8443
   ```

3. **방화벽 확인**
   ```bash
   sudo ufw status
   sudo ufw allow 8443  # 필요시
   ```

4. **네트워크 확인**
   ```bash
   # PC IP 확인
   hostname -I
   
   # 헤드셋에서 https://your-ip:8443 접속
   ```

### 문제 3: 팔이 움직이지 않음

**증상:**
```
VR input received but arm not moving
```

**해결 방법:**

```python
# metaquest_config.py 확인
# 1. 조인트 제한 확인
MetaQuestSafety.check_joint_limits("shoulder_pan", value)

# 2. 역운동학 확인
kin_right.inverse_kinematics(x, y)

# 3. 로봇 상태 확인
robot.get_observation()
```

### 문제 4: 응답 지연 (Latency)

**증상:**
```
VR input delayed, arm responds slowly
```

**해결 방법:**

1. **네트워크 최적화**
   ```bash
   # WiFi 대신 이더넷 사용
   # 2.4GHz → 5GHz WiFi로 변경
   ```

2. **성능 최적화**
   ```python
   # metaquest_config.py
   CONTROL_LOOP_RATE = 200  # 100 → 200으로 증가
   ```

3. **배경 프로세스 종료**
   ```bash
   # 불필요한 애플리케이션 종료
   # 시스템 리소스 모니터링: top, htop
   ```

### 문제 5: 그리퍼 반응 없음

**증상:**
```
Trigger pressed but gripper not moving
```

**해결 방법:**

```python
# metaquest_config.py
TRIGGER_THRESHOLD = 0.5  # 0.5 → 0.3으로 감소해보기

# xlerobot_vr_control.py에서 확인
if hasattr(vr_goal, 'metadata'):
    print(f"Trigger value: {vr_goal.metadata.get('trigger', 0)}")
```

### 문제 6: 역운동학 실패

**증상:**
```
[right] VR IK failed: ...
```

**해결 방법:**

1. **목표 위치 확인**
   ```
   도달 가능 범위 내인지 확인
   x: 0.1 ~ 0.3 (meter)
   y: -0.2 ~ 0.2 (meter)
   ```

2. **초기 위치 재설정**
   ```python
   left_arm.move_to_zero_position(robot)
   right_arm.move_to_zero_position(robot)
   ```

### 문제 7: 응급 정지 버튼

**사용 방법:**

```
옵션 1: Y 버튼 (왼쪽 컨트롤러)
  - 모든 모션 멈춤
  - 그리퍼만 유지

옵션 2: 키보드 ESC 키
  - 프로그램 종료
  - 로봇 연결 해제
```

## 고급 기능

### 커스텀 제어 모드 추가

```python
# xlerobot_vr_control.py에 추가

class CustomControlMode:
    """사용자 정의 제어 모드"""
    
    def __init__(self, arm):
        self.arm = arm
    
    def apply_constraint(self, target_pos):
        """제약 조건 적용"""
        # 예: 수평 평면에만 제한
        target_pos['z'] = 0.1  # Z 고정
        return target_pos
```

### 녹화 및 재생

```python
# 제어 데이터 녹화
import json
from datetime import datetime

# 제어 명령 녹화
with open(f"vr_control_{datetime.now()}.json", "w") as f:
    json.dump(recorded_actions, f)

# 재생 (별도 스크립트)
# 녹화된 데이터를 로봇에 다시 적용
```

### 자동 평형 유지

```python
# 로봇 베이스 자동 안정화
class AutoBalancing:
    def stabilize(self, robot_state):
        """로봇 중심 자동 유지"""
        imu_data = robot_state.get_imu()
        if imu_data.roll > 0.1:
            # 베이스 이동으로 보정
            pass
```

## 유용한 명령어

```bash
# 로그 확인
tail -f ~/.lerobot/logs/vr_control.log

# 네트워크 모니터링
watch -n 1 'netstat -an | grep 8443'

# 리소스 모니터링
htop

# 프로세스 종료
pkill -f "xlerobot_vr_control"

# 포트 강제 해제
sudo lsof -i :8443 | grep LISTEN | awk '{print $2}' | xargs kill -9
```

## 문서 및 참고자료

- [LeRobot GitHub](https://github.com/huggingface/lerobot)
- [MetaQuest Documentation](https://developer.oculus.com/documentation/)
- [XLeRobot 설명서](https://github.com/xLeRobot/XLeRobot)

## 라이선스

이 프로젝트는 LeRobot 라이선스를 따릅니다.

## 지원

문제가 발생하면:

1. 이 README의 문제 해결 섹션 확인
2. 로그 파일 확인
3. 진단 스크립트 실행: `uv run python3 run_vr_control.py`

---

**마지막 업데이트:** 2024년 5월 6일
**버전:** 1.0
