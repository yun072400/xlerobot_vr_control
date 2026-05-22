#!/usr/bin/env python3
"""
저장된 데이터셋을 불러와서 로봇에 액션을 전송하는 데모
record.py를 참조하여 작성했습니다.

사용법:
    python demo_test.py --dataset_repo_id so100_vr_demo --dataset_root ~/Dataset
"""

import logging
import time
from pathlib import Path

from lerobot.robots.so100_follower.so100_follower import SO100Follower
from lerobot.robots.so100_follower.config_so100_follower import SO100FollowerConfig
from lerobot.datasets.lerobot_dataset import LeRobotDataset
from lerobot.utils.robot_utils import precise_sleep

# 설정
PORT = "/dev/ttyACM1"
DATASET_NAME = "so100_vr_demo"  # 불러올 데이터셋 이름
DATASET_ROOT = Path.home() / "Dataset"  # 데이터셋이 저장된 경로
FPS = 30


def main():
    """메인 함수"""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # 1. 로봇 연결
    logger.info(f"🤖 SO100 로봇 연결 중 ({PORT})...")
    try:
        robot_config = SO100FollowerConfig(port=PORT)
        robot = SO100Follower(robot_config)
        robot.connect()
        logger.info("✅ 로봇 연결 성공!")
    except Exception as e:
        logger.error(f"❌ 로봇 연결 실패: {e}")
        return
    
    # 2. 캘리브레이션 확인
    if not robot.is_calibrated:
        logger.warning("⚠️  로봇이 캘리브레이션되지 않음!")
        robot.disconnect()
        return
    
    # 3. 데이터셋 불러오기 (record.py 참조)
    logger.info(f"📁 데이터셋 로드 중: {DATASET_NAME}")
    try:
        # 최신 타임스탬프 데이터셋 찾기
        dataset_dirs = sorted(DATASET_ROOT.glob(f"{DATASET_NAME}_*"))
        
        if not dataset_dirs:
            logger.error(f"❌ {DATASET_NAME}_* 데이터셋을 찾을 수 없습니다!")
            logger.info(f"   {DATASET_ROOT} 디렉토리 확인: {list(DATASET_ROOT.glob('*'))}")
            robot.disconnect()
            return
        
        latest_dataset_root = dataset_dirs[-1]
        logger.info(f"✅ 최신 데이터셋 로드: {latest_dataset_root}")
        
        dataset = LeRobotDataset(DATASET_NAME, root=str(latest_dataset_root))
        logger.info(f"✅ 데이터셋 로드 완료!")
        logger.info(f"   에피소드: {dataset.num_episodes}")
        logger.info(f"   프레임: {len(dataset)}")
        
    except Exception as e:
        logger.error(f"❌ 데이터셋 로드 실패: {e}")
        robot.disconnect()
        return
    
    # 4. 첫 번째 에피소드에서 액션 추출 및 로봇에 전송
    logger.info("🎬 첫 번째 에피소드의 액션을 로봇에 전송합니다...")
    
    try:
        # 첫 번째 에피소드 인덱스 범위
        episode_start_index = dataset.episode_data_index[0][0]  # 첫 번째 에피소드 시작
        episode_end_index = dataset.episode_data_index[0][1]    # 첫 번째 에피소드 끝
        
        logger.info(f"📍 에피소드 1: 프레임 {episode_start_index} ~ {episode_end_index}")
        
        # 첫 10개 프레임만 실행 (짧은 데모)
        num_frames_to_run = min(10, episode_end_index - episode_start_index)
        logger.info(f"🚀 {num_frames_to_run}개 프레임 실행...")
        
        for frame_idx in range(episode_start_index, episode_start_index + num_frames_to_run):
            loop_start = time.perf_counter()
            
            # 데이터셋에서 프레임 가져오기
            frame_data = dataset[frame_idx]
            
            # 액션 추출 (record.py의 build_dataset_frame 역순)
            # 오른팔(right_arm)의 액션만 추출
            action = {}
            for key, value in frame_data.items():
                if key.startswith("action_right_arm_"):
                    # "action_right_arm_shoulder_pan.pos" → "right_arm_shoulder_pan.pos"
                    action_key = key.replace("action_", "")
                    action[action_key] = float(value)
            
            if not action:
                logger.warning(f"⚠️  프레임 {frame_idx}에서 액션을 찾을 수 없음")
                continue
            
            # 로봇에 액션 전송 (record.py에서와 동일)
            sent_action = robot.send_action(action)
            
            logger.info(
                f"📤 프레임 {frame_idx - episode_start_index + 1}/{num_frames_to_run} "
                f"| 액션 전송 완료"
            )
            
            # 30Hz 유지
            elapsed = time.perf_counter() - loop_start
            precise_sleep(1.0 / FPS - elapsed)
        
        logger.info(f"✅ 액션 전송 완료!")
        
    except Exception as e:
        logger.error(f"❌ 액션 전송 중 오류: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 정리
        logger.info("🧹 리소스 정리 중...")
        robot.disconnect()
        logger.info("✅ 완료!")


if __name__ == "__main__":
    main()
