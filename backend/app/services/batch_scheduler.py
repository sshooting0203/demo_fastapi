import asyncio
import schedule
import time
from datetime import datetime
from .ranking_service import RankingService
from .search_service import SearchService

class BatchScheduler:
    def __init__(self):
        self.ranking_service = RankingService()
        self.search_service = SearchService()
        self.is_running = False
    
    async def cleanup_old_logs(self):
        """30일 이상 된 검색 로그 정리"""
        try:
            print(f"[{datetime.now()}] 검색 로그 정리 시작...")
            await self.search_service.cleanup_old_search_logs(30)
            await self.ranking_service.cleanup_old_logs()
            print(f"[{datetime.now()}] 검색 로그 정리 완료")
        except Exception as e:
            print(f"[{datetime.now()}] 검색 로그 정리 오류: {str(e)}")
    
    async def recalculate_rankings(self):
        """전체 국가 랭킹 재계산"""
        try:
            print(f"[{datetime.now()}] 랭킹 재계산 시작...")
            await self.ranking_service.recalculate_all_rankings()
            print(f"[{datetime.now()}] 랭킹 재계산 완료")
        except Exception as e:
            print(f"[{datetime.now()}] 랭킹 재계산 오류: {str(e)}")
    
    async def daily_maintenance(self):
        """일일 유지보수 작업"""
        try:
            print(f"[{datetime.now()}] 일일 유지보수 시작...")
            
            # 1. 오래된 로그 정리
            await self.cleanup_old_logs()
            
            # 2. 랭킹 재계산 (주 1회만)
            if datetime.now().weekday() == 0:  # 월요일
                await self.recalculate_rankings()
            
            print(f"[{datetime.now()}] 일일 유지보수 완료")
            
        except Exception as e:
            print(f"[{datetime.now()}] 일일 유지보수 오류: {str(e)}")
    
    def start_scheduler(self):
        """스케줄러 시작"""
        if self.is_running:
            print("스케줄러가 이미 실행 중입니다.")
            return
        
        self.is_running = True
        
        # 매일 새벽 2시에 유지보수 실행
        schedule.every().day.at("02:00").do(self._run_daily_maintenance)
        
        # 매시간 검색 로그 정리 (선택사항)
        schedule.every().hour.do(self._run_cleanup_logs)
        
        print("배치 스케줄러가 시작되었습니다.")
        print("- 일일 유지보수: 매일 새벽 2시")
        print("- 로그 정리: 매시간")
        
        # 스케줄러 루프 실행
        while self.is_running:
            schedule.run_pending()
            time.sleep(60)  # 1분마다 체크
    
    def stop_scheduler(self):
        """스케줄러 중지"""
        self.is_running = False
        print("배치 스케줄러가 중지되었습니다.")
    
    def _run_daily_maintenance(self):
        """일일 유지보수 실행 (동기 래퍼)"""
        asyncio.create_task(self.daily_maintenance())
    
    def _run_cleanup_logs(self):
        """로그 정리 실행 (동기 래퍼)"""
        asyncio.create_task(self.cleanup_old_logs())
    
    async def run_manual_cleanup(self):
        """수동 로그 정리 실행"""
        await self.cleanup_old_logs()
    
    async def run_manual_ranking_recalc(self):
        """수동 랭킹 재계산 실행"""
        await self.recalculate_rankings()

# 전역 인스턴스
batch_scheduler = BatchScheduler()

# FastAPI 시작 시 스케줄러 시작 (선택사항)
def start_background_scheduler():
    """백그라운드에서 스케줄러 실행"""
    import threading
    scheduler_thread = threading.Thread(target=batch_scheduler.start_scheduler, daemon=True)
    scheduler_thread.start()
    return scheduler_thread
