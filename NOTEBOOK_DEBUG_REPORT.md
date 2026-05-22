# 🔴 SO100 데이터 수집 노트북 - 전체 점검 보고서

## 문제 현상
- ❌ VR 제어가 작동하지 않음
- ❌ 데이터셋이 생성되지 않음
- ❌ 버튼을 눌렀을 때 아무 일도 일어나지 않음

---

## 🔍 **발견된 5가지 핵심 문제**

### ❌ **문제 1: `build_dataset_frame` 함수 스코프 오류**
**위치**: Cell #VSC-053db43d (SECTION 1B)
**원인**: `initialize_dataset()` 함수 내에서만 import됨
**영향**: UI Manager의 `_run_control_loop()`에서 접근 불가 → **데이터가 저장되지 않음**

**현재 코드**:
```python
def initialize_dataset(globals_dict):
    try:
        import yaml  # ❌ 로컬 import
        from lerobot.datasets.lerobot_dataset import LeRobotDataset  # ❌ 로컬 import
        from lerobot.utils.feature_utils import build_dataset_frame, hw_to_dataset_features  # ❌ 로컬 import
```

**필요한 수정**: **전역 import로 변경**
```python
# 셀 #VSC-192473f0 (라이브러리 import) 에 추가:
from lerobot.datasets.lerobot_dataset import LeRobotDataset
from lerobot.utils.feature_utils import build_dataset_frame, hw_to_dataset_features
import yaml
from pathlib import Path
```

---

### ❌ **문제 2: VR 서버 미시작**
**위치**: Cell #VSC-0cde81e8 (UI Manager 클래스)
**원인**: `_control_thread_worker()`에서 `initialize_dataset()`만 호출, **VR 모니터 시작 missing**
**영향**: **VR 연결이 안 됨 → 제어 불가**

**현재 코드**:
```python
def _control_thread_worker(self):
    # ✅ 데이터셋만 초기화
    initialize_dataset(self.globals_dict)
    # ❌ VR 모니터 초기화 missing!
    # ❌ VR 서버 시작 missing!
    self._run_control_loop()
```

**필요한 수정**: VR 모니터 초기화 및 시작 추가
```python
def _control_thread_worker(self):
    # 데이터셋 초기화
    initialize_dataset(self.globals_dict)
    
    # ✅ VR 모니터 초기화 및 시작 필요!
    vr_monitor = VRControlMonitor()
    if not vr_monitor.initialize():
        self.set_status("❌ VR 모니터 초기화 실패")
        return
    
    # ✅ 이벤트 루프 스레드에서 VR 서버 시작
    event_loop_thread.run_coroutine(vr_monitor.start_monitoring_async())
    
    self._run_control_loop()
```

---

### ❌ **문제 3: config.yaml 없을 때 KeyError**
**위치**: Cell #VSC-053db43d (SECTION 1B)
**원인**: Config 파일 없을 때 `task_name` 변수 미정의
**영향**: Dataset 경로 설정 시 **KeyError 발생 → 초기화 실패**

**현재 코드**:
```python
if not config_path.exists():
    # ... 기본값 설정 ...
    # ❌ task_name 미정의!
else:
    # config.yaml 로드
    task_name = dataset_config.get('task_name', 'SO100_VR_teleoperation')

# 아래에서 task_name 사용
dataset_path = dataset_path.joinpath(task_name)  # ❌ KeyError 가능
```

**필요한 수정**:
```python
if not config_path.exists():
    # ... 기본값 설정 ...
    task_name = "SO100_VR_teleoperation"  # ✅ 기본값 추가!
```

---

### ❌ **문제 4: 메타데이터 설정 초기화 미흡**
**위치**: Cell #VSC-0cde81e8 (UI Manager)
**원인**: 버튼 클릭 시 metadata_config 재설정 안 함
**영향**: 이전 세션 설정이 계속 사용됨

**현재 코드**:
```python
def _control_thread_worker(self):
    # ❌ metadata_config 초기화 missing!
    initialize_dataset(self.globals_dict)
    self._run_control_loop()
```

**필요한 수정**:
```python
def _control_thread_worker(self):
    # ✅ 메타데이터 설정 초기화
    self.globals_dict['metadata_config'] = {
        'override_buttons': False,
        'buttons_squeeze_value': True,
        'add_buttons_field': True,
    }
    initialize_dataset(self.globals_dict)
    self._run_control_loop()
```

---

### ❌ **문제 5: 종료 시 리소스 정리 missing**
**위치**: Cell #VSC-0cde81e8 (UI Manager)
**원인**: `_control_thread_worker()` finally 블록에서 VR 모니터/데이터셋 정리 안 함
**영향**: 리소스 누수 + 다음 세션 시 문제 발생

**현재 코드**:
```python
finally:
    self.control_running = False
    self.control_thread_started = False
    # ❌ VR 모니터 정리 missing!
    # ❌ 데이터셋 finalize missing!
    self.set_status("✅ 제어 종료 - 데이터 저장됨")
```

**필요한 수정**:
```python
finally:
    try:
        # ✅ VR 모니터 정리
        vr_monitor = self.globals_dict.get('vr_monitor')
        if vr_monitor:
            vr_monitor.is_running = False
        
        # ✅ 데이터셋 최종화
        dataset = self.globals_dict.get('dataset')
        if dataset:
            dataset.finalize()
    except Exception as e:
        logger.error(f"정리 중 오류: {e}")
    
    self.control_running = False
    self.control_thread_started = False
```

---

## ✅ **수정 순서 (우선순위 순)**

### 1️⃣ **라이브러리 임포트 수정** (높은 우선순위)
**셀**: #VSC-192473f0 (맨 첫 셀)
- [ ] `build_dataset_frame`, `hw_to_dataset_features` 전역 import 추가
- [ ] `yaml`, `Path` 전역 import 추가
- **이유**: 다른 함수들이 이를 사용하기 때문에 가장 먼저 수정 필요

### 2️⃣ **데이터셋 함수 수정** (높은 우선순위)
**셀**: #VSC-053db43d (SECTION 1B)
- [ ] 로컬 import 제거 (이미 전역에서 import됨)
- [ ] `config.yaml` 없을 때 `task_name`, `num_image_processes`, `num_image_threads`, `batch_encoding_size` 기본값 추가
- [ ] `return None` 추가 (에러 시)
- **이유**: 데이터셋 초기화가 실패하면 전체 시스템 작동 불가

### 3️⃣ **UI Manager 메인 수정** (높은 우선순위)
**셀**: #VSC-0cde81e8 (UI Manager 클래스)

**3-1) `_control_thread_worker()` 수정**:
- [ ] metadata_config 초기화 추가
- [ ] VR 모니터 초기화 및 시작 추가
- [ ] VR 서버 시작 추가
- [ ] finally 블록에 정리 로직 추가
- **이유**: 이것이 핵심 제어 루프 시작 함수

**3-2) `_run_control_loop()` 수정** (검증 필요):
- [ ] `build_dataset_frame` 전역으로 접근 가능한지 확인

---

## 🔧 **상세 수정 방법**

### **수정 1: 라이브러리 import 추가**

현재 셀 (라이브러리 import):
```python
from typing import Optional, Dict, Any

# Setup logging
```

변경 후:
```python
from typing import Optional, Dict, Any
import yaml
from pathlib import Path

# ✅ Import dataset utilities at global scope
from lerobot.datasets.lerobot_dataset import LeRobotDataset
from lerobot.utils.feature_utils import build_dataset_frame, hw_to_dataset_features

# Setup logging
```

---

### **수정 2: 데이터셋 함수 수정**

#### 2-1) 로컬 import 제거

```python
# ❌ 현재
def initialize_dataset(globals_dict):
    print("📊 Initializing Dataset from config.yaml...")
    try:
        import yaml
        from pathlib import Path
        from lerobot.datasets.lerobot_dataset import LeRobotDataset
        from lerobot.utils.feature_utils import build_dataset_frame, hw_to_dataset_features

# ✅ 변경 후
def initialize_dataset(globals_dict):
    print("📊 Initializing Dataset from config.yaml...")
    try:
        # yaml, Path, LeRobotDataset, build_dataset_frame 모두 전역에서 import됨
```

#### 2-2) config.yaml 미존재 시 기본값 추가

```python
# ❌ 현재
if not config_path.exists():
    print(f"❌ Config file not found: {config_path}")
    print("   Using default values instead...")
    dataset_repo_id = "your_username/so100_vr_teleop_data"
    dataset_root = "./datasets"
    dataset_fps = 30
    single_task = "VR teleoperation control"
    num_episodes = 10

# ✅ 변경 후
if not config_path.exists():
    print(f"❌ Config file not found: {config_path}")
    print("   Using default values instead...")
    dataset_repo_id = "your_username/so100_vr_teleop_data"
    dataset_root = "./datasets"
    dataset_fps = 30
    single_task = "VR teleoperation control"
    task_name = "SO100_VR_teleoperation"  # ✅ 추가
    num_episodes = 10
    num_image_processes = 0  # ✅ 추가
    num_image_threads = 4  # ✅ 추가
    batch_encoding_size = 1  # ✅ 추가
```

#### 2-3) 에러 처리 개선

```python
# ❌ 현재
    except Exception as e:
        logger.error(f"❌ Dataset initialization failed: {e}")
        traceback.print_exc()

# ✅ 변경 후
    except Exception as e:
        logger.error(f"❌ Dataset initialization failed: {e}")
        traceback.print_exc()
        return None  # ✅ 추가
```

---

### **수정 3: UI Manager 메인 로직 수정**

#### 3-1) `_control_thread_worker()` 메서드 수정

```python
# ❌ 현재
def _control_thread_worker(self):
    try:
        self.set_status("🔄 데이터셋 초기화 중...")
        logger.info("🔄 데이터셋 초기화 중...")
        
        initialize_dataset(self.globals_dict)
        
        self.set_status("✅ 데이터셋 준비 완료! 제어 시작 중...")
        logger.info("✅ 데이터셋 준비 완료")
        time.sleep(1)
        
        self._run_control_loop()

# ✅ 변경 후
def _control_thread_worker(self):
    try:
        # ✅ Step 1: 메타데이터 설정 초기화
        self.set_status("🔄 메타데이터 설정 중...")
        self.globals_dict['metadata_config'] = {
            'override_buttons': False,
            'buttons_squeeze_value': True,
            'add_buttons_field': True,
        }
        
        # ✅ Step 2: 데이터셋 초기화
        self.set_status("🔄 데이터셋 초기화 중...")
        logger.info("🔄 데이터셋 초기화 중...")
        dataset = initialize_dataset(self.globals_dict)
        if dataset is None:
            self.set_status("❌ 데이터셋 초기화 실패")
            logger.error("❌ 데이터셋 초기화 실패")
            return
        
        # ✅ Step 3: VR 모니터 초기화 및 시작
        self.set_status("🌐 VR 서버 시작 중...")
        logger.info("🌐 VR 서버 시작 중...")
        
        # VR 모니터 재초기화
        if self.globals_dict.get('event_loop_thread') is None:
            event_loop_thread = AsyncEventLoopThread()
            event_loop_thread.start()
            event_loop_thread.ready.wait(timeout=5)
            self.globals_dict['event_loop_thread'] = event_loop_thread
            self.globals_dict['event_loop'] = event_loop_thread.loop
        
        vr_monitor = VRControlMonitor()
        if not vr_monitor.initialize():
            self.set_status("❌ VR 모니터 초기화 실패")
            logger.error("❌ VR 모니터 초기화 실패")
            return
        
        self.globals_dict['vr_monitor'] = vr_monitor
        
        # VR 서버 시작
        event_loop_thread = self.globals_dict.get('event_loop_thread')
        if event_loop_thread:
            future = event_loop_thread.run_coroutine(vr_monitor.start_monitoring_async())
            time.sleep(1)
        
        # ✅ Step 4: 제어 루프 시작
        self.set_status("✅ 모든 준비 완료! 제어 시작 중...")
        logger.info("✅ 모든 준비 완료")
        time.sleep(1)
        
        self._run_control_loop()
```

#### 3-2) Finally 블록 수정

```python
# ❌ 현재
        except Exception as e:
            self.set_status(f"❌ 오류: {str(e)}")
            logger.error(f"❌ 제어 오류: {e}")
            traceback.print_exc()
        finally:
            self.control_running = False
            self.control_thread_started = False
            self.set_status("✅ 제어 종료 - 데이터 저장됨")

# ✅ 변경 후
        except Exception as e:
            self.set_status(f"❌ 오류: {str(e)}")
            logger.error(f"❌ 제어 오류: {e}")
            traceback.print_exc()
        finally:
            # ✅ 정리 및 리소스 해제
            try:
                # VR 모니터 정리
                vr_monitor = self.globals_dict.get('vr_monitor')
                if vr_monitor:
                    vr_monitor.is_running = False
                    logger.info("✅ VR 모니터 정리 완료")
                
                # 데이터셋 최종화
                dataset = self.globals_dict.get('dataset')
                if dataset:
                    dataset.finalize()
                    logger.info(f"✅ 데이터셋 최종화: {dataset.num_episodes} 에피소드, {dataset.num_frames} 프레임")
            except Exception as cleanup_error:
                logger.error(f"❌ 정리 중 오류: {cleanup_error}")
            
            self.control_running = False
            self.control_thread_started = False
            self.set_status("✅ 제어 종료 - 데이터 저장됨")
```

---

## 📋 **체크리스트**

- [ ] 수정 1: 라이브러리 import 추가 완료
- [ ] 수정 2: 데이터셋 함수 수정 완료
- [ ] 수정 3: UI Manager 수정 완료
- [ ] 노트북 재실행 및 테스트
- [ ] 버튼 클릭 시 상태 변화 확인
- [ ] 데이터셋 생성 확인
- [ ] VR 연결 확인

---

## 🧪 **테스트 방법**

1. **노트북 커널 재시작** (Ctrl+Shift+P → "Restart Kernel")
2. **SECTION 1 실행** (로봇 연결)
3. **UI 패널 셀 실행** (버튼 생성)
4. **"데이터 생성 및 제어 시작" 클릭**
5. **콘솔 로그 확인**:
   - ✅ "🔄 메타데이터 설정 중..." → "✅ 메타데이터 설정 중..." 
   - ✅ "🔄 데이터셋 초기화 중..." → "✅ DATASET INITIALIZED"
   - ✅ "🌐 VR 서버 시작 중..." → VR URL 출력
   - ✅ "✅ 모든 준비 완료! 제어 시작 중..."

---

## 📞 **추가 지원**

만약 수정 후에도 문제가 있다면:
1. 각 셀을 따로 실행해보기
2. 콘솔 에러 메시지 확인
3. `logger.info()` 메시지를 통해 어느 단계에서 멈추는지 확인
4. 각 globals_dict 변수 확인
