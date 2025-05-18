
from datetime import datetime, timedelta
import pandas as pd
import os

weekday_kor = ["월", "화", "수", "목", "금", "토", "일"]

# === 파일 불러오기 ===
def load_직원명부():
    file_path = r"c:\\python\\name.txt"
    직원명부 = {}
    with open(file_path, encoding='utf-8') as f:
        next(f)
        for line in f:
            name, group, days = line.strip().split(',')
            휴무요일 = days.split('|') if days else []
            직원명부[name] = {"조": group, "휴무요일": 휴무요일}
    return 직원명부

def load_공휴일():
    with open(r"c:\\python\\holiday.txt", encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

def load_야간지원():
    with open(r"c:\\python\\afternoon_night_support.txt", encoding='utf-8') as f:
        return {line.strip().split(',')[0]: line.strip().split(',')[1] for line in f if line.strip()}

def load_adddays():
    file_path = r"c:\\python\\adddays.txt"
    if os.path.exists(file_path):
        with open(file_path, encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    return []

# === 근무시간 계산 ===
def 계산_근무시간(기록):
    총근무일 = 기록["오전"] + 기록["오후"] + 기록["야간"]
    야간가중치 = 기록["야간"] * 4
    return 총근무일 * 8 + 야간가중치

# === 스케줄 생성 ===
def create_schedule():
    직원명부 = load_직원명부()
    공휴일 = load_공휴일()
    오후조_야간지원일 = load_야간지원()
    start_date = datetime(2025, 5, 1)
    end_date = datetime(2025, 5, 31)

    총_근무일 = [(start_date + timedelta(days=i)).strftime("%Y-%m-%d") for i in range((end_date - start_date).days + 1)]

    개인별_근무일수 = {name: {"오전": 0, "오후": 0, "야간": 0} for name in 직원명부}
    출근기록 = {name: {} for name in 직원명부}
    순번 = {"오전조": 0, "오후조": 0}
    야간조_순서 = [name for name, info in 직원명부.items() if info["조"] == "야간조"]
    근무표, 야간지원_기록 = [], []

    야간_일정표 = {}
    for i, d in enumerate([d for d in 총_근무일 if d not in 오후조_야간지원일]):
        담당자 = 야간조_순서[(i // 2) % len(야간조_순서)]
        야간_일정표[d] = 담당자

    for date_str in 총_근무일:
        current = datetime.strptime(date_str, "%Y-%m-%d")
        요일 = weekday_kor[current.weekday()]
        오후야간지원자 = 오후조_야간지원일.get(date_str)
        오전, 오후 = [], []

        오전후보 = [n for n, v in 직원명부.items() if v["조"] == "오전조" and 요일 not in v["휴무요일"]]
        for _ in range(min(3, len(오전후보))):
            이름 = 오전후보[순번["오전조"] % len(오전후보)]
            if 이름 not in 오전:
                오전.append(이름)
                개인별_근무일수[이름]["오전"] += 1
                출근기록[이름][date_str] = "오전"
                순번["오전조"] += 1

        오후후보 = [n for n, v in 직원명부.items() if v["조"] == "오후조" and 요일 not in v["휴무요일"] and n != 오후야간지원자]
        for _ in range(min(4, len(오후후보))):
            이름 = 오후후보[순번["오후조"] % len(오후후보)]
            if 이름 not in 오후:
                오후.append(이름)
                개인별_근무일수[이름]["오후"] += 1
                출근기록[이름][date_str] = "오후"
                순번["오후조"] += 1

        if 오후야간지원자:
            개인별_근무일수[오후야간지원자]["야간"] += 1
            출근기록[오후야간지원자][date_str] = "야간"
            야간지원_기록.append({"날짜": date_str, "이름": 오후야간지원자})
        else:
            담당자 = 야간_일정표.get(date_str, "")
            if 담당자:
                개인별_근무일수[담당자]["야간"] += 1
                출근기록[담당자][date_str] = "야간"

        if not 오전:
            오전 = ["없음"]
        if not 오후:
            오후 = ["없음"]

        근무표.append({
            "일자": f"{current.day}일({요일})",
            "오전": " ".join(오전),
            "오후": " ".join(오후),
            "야간": 오후야간지원자 if 오후야간지원자 else 담당자
        })

    return pd.DataFrame(근무표), 개인별_근무일수, 출근기록, 야간지원_기록, 직원명부

# === 메인 실행 ===
if __name__ == "__main__":
    df, 개인별_근무일수, 출근기록, 야간지원_기록, 직원명부 = create_schedule()
    adddays = load_adddays()

    # 출근기록 수정
    for 이름 in 출근기록:
        for date in adddays:
            if date in 출근기록[이름]:
                근무타입 = 출근기록[이름][date]
                if 근무타입 in 개인별_근무일수[이름]:
                    개인별_근무일수[이름][근무타입] -= 1
                del 출근기록[이름][date]

    # 통계 재작성
    통계표 = []
    기준근무시간 = 160
    for 이름, 기록 in 개인별_근무일수.items():
        총시간 = 계산_근무시간(기록)
        총일수 = 기록["오전"] + 기록["오후"] + 기록["야간"]
        상태 = "정상근무"
        if 총시간 < 기준근무시간:
            상태 = f"{기준근무시간-총시간}시간 월차처리"
        elif 총시간 > 기준근무시간:
            상태 = f"{총시간-기준근무시간}시간 추가근무"

        통계표.append({
            "이름": 이름,
            "오전 근무일수": 기록["오전"],
            "오후 근무일수": 기록["오후"],
            "야간 근무일수": 기록["야간"],
            "총 근무일수": 총일수,
            "총 근무시간": 총시간,
            "근무상태": 상태
        })

    통계_수정후_df = pd.DataFrame(통계표)

    # 기존 파일에 새 시트로 추가 저장
    with pd.ExcelWriter("c:/python/근무표_유동인원_2025_05.xlsx", engine='openpyxl', mode='a') as writer:
        통계_수정후_df.to_excel(writer, sheet_name="근무통계(수정후)", index=False)

    print("\n✅ 수정된 개인별 근무통계 엑셀 저장 완료!")
