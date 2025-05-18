# CU 편의점 2025년 5월 근무표 생성 프로그램
# 야간조 2일 교대 반영 버전

from datetime import datetime, timedelta
import pandas as pd
import os

weekday_kor = ["월", "화", "수", "목", "금", "토", "일"]

def 이전요일(요일):
    idx = weekday_kor.index(요일)
    return weekday_kor[(idx - 1) % 7]

def 다음요일(요일):
    idx = weekday_kor.index(요일)
    return weekday_kor[(idx + 1) % 7]

def load_직원명부():
    file_path = r"c:\python\name.txt"
    직원명부 = {}
    with open(file_path, encoding='utf-8') as f:
        next(f)
        for line in f:
            name, group, days = line.strip().split(',')
            휴무요일 = days.split('|') if days else []
            직원명부[name] = {"조": group, "휴무요일": 휴무요일}
    return 직원명부

def load_공휴일():
    file_path = r"c:\python\holiday.txt"
    with open(file_path, encoding='utf-8') as f:
        return [line.strip() for line in f.readlines() if line.strip()]

def load_야간지원():
    file_path = r"c:\python\afternoon_night_support.txt"
    지원자 = {}
    with open(file_path, encoding='utf-8') as f:
        for line in f:
            date, name = line.strip().split(',')
            지원자[date] = name
    return 지원자

def 계산_근무시간(기록):
    return 기록["오전"] * 8 + 기록["오후"] * 8 + 기록["야간"] * 12

def 추천휴무일_계산(이름, 휴무요일목록, is_야간지원자=False):
    후보요일 = []
    if is_야간지원자:
        for 요일 in 휴무요일목록:
            후보요일.append(이전요일(요일))
            후보요일.append(다음요일(요일))
    else:
        for 요일 in 휴무요일목록:
            후보요일.append(이전요일(요일))

    후보날짜 = []
    for day in range(1, 32):
        dt = datetime(2025, 5, day)
        if weekday_kor[dt.weekday()] in 후보요일:
            후보날짜.append(dt.strftime("%Y-%m-%d"))
    return 후보날짜

def create_schedule():
    직원명부 = load_직원명부()
    공휴일 = load_공휴일()
    오후조_야간지원일 = load_야간지원()

    start_date = datetime(2025, 5, 1)
    end_date = datetime(2025, 5, 31)

    총_근무일 = [(start_date + timedelta(days=i)).strftime("%Y-%m-%d")
              for i in range((end_date - start_date).days + 1)
              if (start_date + timedelta(days=i)).weekday() < 5 and                  (start_date + timedelta(days=i)).strftime("%Y-%m-%d") not in 공휴일]

    개인별_근무일수 = {name: {"오전": 0, "오후": 0, "야간": 0} for name in 직원명부}
    출근기록 = {name: {} for name in 직원명부}
    순번 = {"오전조": 0, "오후조": 0}
    야간조_순서 = [name for name, info in 직원명부.items() if info["조"] == "야간조"]
    근무표 = []
    야간지원_기록 = []

    야간_가능일 = [d for d in 총_근무일 if d not in 오후조_야간지원일]
    야간_일정표 = {}
    for i, date_str in enumerate(야간_가능일):
        담당자 = 야간조_순서[(i // 2) % len(야간조_순서)]  # <- 2일 교대
        야간_일정표[date_str] = 담당자

    for date_str in 총_근무일:
        current = datetime.strptime(date_str, "%Y-%m-%d")
        요일 = weekday_kor[current.weekday()]
        오후야간지원자 = 오후조_야간지원일.get(date_str)

        오전 = []
        오후 = []
        야간 = ""

        오전후보 = [name for name, info in 직원명부.items() if info["조"] == "오전조" and 요일 not in info["휴무요일"]]
        for _ in range(min(3, len(오전후보))):
            이름 = 오전후보[순번["오전조"] % len(오전후보)]
            if 이름 not in 오전:
                오전.append(이름)
                개인별_근무일수[이름]["오전"] += 1
                출근기록[이름][date_str] = "근무"
                순번["오전조"] += 1

        오후후보 = [name for name, info in 직원명부.items() if info["조"] == "오후조" and 요일 not in info["휴무요일"] and name != 오후야간지원자]
        for _ in range(min(2, len(오후후보))):
            이름 = 오후후보[순번["오후조"] % len(오후후보)]
            if 이름 not in 오후:
                오후.append(이름)
                개인별_근무일수[이름]["오후"] += 1
                출근기록[이름][date_str] = "근무"
                순번["오후조"] += 1

        if 오후야간지원자:
            야간 = f"{오후야간지원자}(오후근무)"
            개인별_근무일수[오후야간지원자]["야간"] += 1
            출근기록[오후야간지원자][date_str] = "근무"
            야간지원_기록.append({"날짜": date_str, "이름": 오후야간지원자})
        else:
            담당자 = 야간_일정표[date_str]
            야간 = 담당자
            개인별_근무일수[담당자]["야간"] += 1
            출근기록[담당자][date_str] = "근무"

        근무표.append({"일자": f"{current.day}일({요일})", "오전": " ".join(오전), "오후": " ".join(오후), "야간": 야간})

    return pd.DataFrame(근무표), 개인별_근무일수, 출근기록, 야간지원_기록, 직원명부

if __name__ == "__main__":
    df, 개인별_근무일수, 출근기록, 야간지원_기록, 직원명부 = create_schedule()

    print("=== 📅 5월 근무표 ===")
    print(df.to_string(index=False))

    print("\n=== 📊 개인별 근무시간 ===")
    통계표 = []
    for 이름, 기록 in 개인별_근무일수.items():
        총시간 = 계산_근무시간(기록)
        print(f"{이름}: 오전 {기록['오전']}일, 오후 {기록['오후']}일, 야간 {기록['야간']}일 → 총 {총시간}시간")
        통계표.append({"이름": 이름, "오전 근무일수": 기록["오전"], "오후 근무일수": 기록["오후"], "야간 근무일수": 기록["야간"], "총 근무시간": 총시간})

    통계_df = pd.DataFrame(통계표)
    출근표 = pd.DataFrame(출근기록).T
    출근표.index.name = "이름"
    야간지원_df = pd.DataFrame(야간지원_기록)

    기준시간 = 160
    초과자_리스트 = []
    for 이름, 기록 in 개인별_근무일수.items():
        총시간 = 계산_근무시간(기록)
        if 총시간 > 기준시간:
            is_support = any(이름 == row["이름"] for row in 야간지원_기록)
            추천날짜 = 추천휴무일_계산(이름, 직원명부[이름]["휴무요일"], is_support)
            초과자_리스트.append({"이름": 이름, "초과시간": 총시간 - 기준시간, "추천휴무일": ", ".join(추천날짜)})

    조정결과 = pd.DataFrame(초과자_리스트)

    with pd.ExcelWriter(r"c:\python\근무표_2025_05.xlsx", engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='5월 근무표', index=False)
        통계_df.to_excel(writer, sheet_name='개인별 통계', index=False)
        출근표.to_excel(writer, sheet_name='출근표', index=True)
        조정결과.to_excel(writer, sheet_name='초과근무조정', index=False)
        야간지원_df.to_excel(writer, sheet_name='야간지원자기록', index=False)

    print("\n=== 🛠 초과근무자 및 휴무 추천일 ===")
    print(조정결과.to_string(index=False))
