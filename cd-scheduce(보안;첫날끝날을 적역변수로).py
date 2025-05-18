from datetime import datetime, timedelta
import pandas as pd
import os

# 전역 변수로 선언
def create_dates(year, month):
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = datetime(year, month + 1, 1) - timedelta(days=1)
    return start_date, end_date

# 예시: 2025년 5월의 시작일과 종료일 생성
year = 2025
month = 5
START_DATE, END_DATE = create_dates(year, month)

weekday_kor = ["월", "화", "수", "목", "금", "토", "일"]

# 법정 근무시간 계산
def calculate_법정근무시간(start_date, end_date, holidays):
    총_근무일 = [(start_date + timedelta(days=i)).strftime("%Y-%m-%d") for i in range((end_date - start_date).days + 1)]
    실제_근무가능일수 = [d for d in 총_근무일 if weekday_kor[datetime.strptime(d, '%Y-%m-%d').weekday()] not in ['토', '일'] and d not in holidays]
    return len(실제_근무가능일수) * 8

# 공휴일 불러오기
def load_공휴일():
    file_path = r"c:/python/holiday.txt"
    holidays = []
    with open(file_path, encoding='utf-8') as f:
        for line in f:
            holidays.append(line.strip())
    return holidays

holidays = load_공휴일()
법정근무시간 = calculate_법정근무시간(START_DATE, END_DATE, holidays)

# 데이터 불러오기
def load_직원명부():
    file_path = r"c:/python/name.txt"
    직원명부 = {}
    with open(file_path, encoding='utf-8') as f:
        next(f)
        for line in f:
            name, group, days = line.strip().split(',')
            휴무요일 = days.split('|') if days else []
            직원명부[name] = {"조": group, "휴무요일": 휴무요일}
    return 직원명부

# 야간 지원자 불러오기
def load_야간지원():
    file_path = r"c:/python/afternoon_night_support.txt"
    야간지원자 = {}
    with open(file_path, encoding='utf-8') as f:
        for line in f:
            if line.strip():
                날짜, 이름 = line.strip().split(',')
                야간지원자[날짜] = 이름
    return 야간지원자

# 추가 제외일 불러오기
def load_adddays():
    file_path = r"c:/python/adddays.txt"
    adddays_by_name = {}
    with open(file_path, encoding='utf-8') as f:
        for line in f:
            if line.strip():
                name, day = line.strip().split(',')
                if name not in adddays_by_name:
                    adddays_by_name[name] = []
                adddays_by_name[name].append(day)
    return adddays_by_name

# 근무시간 계산
def 계산_근무시간(기록):
    총오전오후 = 기록["오전"] + 기록["오후"]
    총야간 = 기록["야간"]
    return (총오전오후 * 8) + (총야간 * 12)

# 추천휴무일 계산
def 추천휴무일계산(이름, 직원명부):
    후보요일 = set()
    if 직원명부[이름]["휴무요일"]:
        첫 = 직원명부[이름]["휴무요일"][0]
        후보요일.add(weekday_kor[(weekday_kor.index(첫) - 1) % 7])
    후보날짜 = []
    for d in range(1, 32):
        dt = datetime(2025, 5, d)
        if weekday_kor[dt.weekday()] in 후보요일:
            후보날짜.append(dt.strftime("%Y-%m-%d"))
    return 후보날짜

# 근무표 생성
def create_schedule():
    직원명부 = load_직원명부()
    오후조_야간지원일 = load_야간지원()
    adddays_by_name = load_adddays()

    총_근무일 = [(START_DATE + timedelta(days=i)).strftime("%Y-%m-%d") for i in range((END_DATE - START_DATE).days + 1)]

    개인별_근무일수 = {name: {"오전": 0, "오후": 0, "야간": 0} for name in 직원명부}
    출근기록 = {name: {} for name in 직원명부}
    야간지원기록 = []

    순번 = {"오전조": 0, "오후조": 0}
    야간순번 = 0

    근무표 = []

    for date_str in 총_근무일:
        current = datetime.strptime(date_str, "%Y-%m-%d")
        요일 = weekday_kor[current.weekday()]
        오후야간지원자 = 오후조_야간지원일.get(date_str)

        오전, 오후 = [], []

        # 오전조 배정
        오전후보 = [n for n, v in 직원명부.items() if v["조"] == "오전조" and 요일 not in v["휴무요일"]]
        for _ in range(min(3, len(오전후보))):
            이름 = 오전후보[순번["오전조"] % len(오전후보)]
            if 이름 not in 오전:
                오전.append(이름)
                개인별_근무일수[이름]["오전"] += 1
                출근기록[이름][date_str] = "오전"
                순번["오전조"] += 1

        # 오후조 배정
        오후후보 = [n for n, v in 직원명부.items() if v["조"] == "오후조" and 요일 not in v["휴무요일"]]
        for _ in range(min(4, len(오후후보))):
            이름 = 오후후보[순번["오후조"] % len(오후후보)]
            if 이름 not in 오후:
                오후.append(이름)
                if 이름 != 오후야간지원자:
                    개인별_근무일수[이름]["오후"] += 1
                    출근기록[이름][date_str] = "오후"
                순번["오후조"] += 1

        # 야간조 배정
        if 오후야간지원자:
            야간담당자 = 오후야간지원자
        else:
            야간담당자 = "신대철" if (야간순번 // 2) % 2 == 0 else "한미자"
            야간순번 += 1

        개인별_근무일수[야간담당자]["야간"] += 1
        출근기록[야간담당자][date_str] = "야간"
        if 오후야간지원자:
            야간지원기록.append({"날짜": date_str, "이름": 오후야간지원자})

        근무표.append({
            "일자": f"{current.day}일({요일})",
            "오전": " ".join(오전),
            "오후": " ".join(오후),
            "야간": 야간담당자
        })

    # adddays 반영
    for 이름, 날짜목록 in adddays_by_name.items():
        for 날짜 in 날짜목록:
            if 이름 in 출근기록 and 날짜 in 출근기록[이름]:
                근무타입 = 출근기록[이름][날짜]
                if 근무타입 in 개인별_근무일수[이름]:
                    개인별_근무일수[이름][근무타입] -= 1
                del 출근기록[이름][날짜]

    return pd.DataFrame(근무표), 개인별_근무일수, 출근기록, 야간지원기록, 직원명부

if __name__ == "__main__":
    df, 개인별_근무일수, 출근기록, 야간지원기록, 직원명부 = create_schedule()

    print("\n=== 📅 근무표 ===")
    print(df.to_string(index=False))

    print("\n=== 📋 개인별 출근현황 ===")

    # 📅 5월 1일부터 31일까지 날짜 목록 생성
    모든날짜 = [(START_DATE + timedelta(days=i)).strftime("%Y-%m-%d") for i in range((END_DATE - START_DATE).days + 1)]

    # 📋 개인별 출근현황 표 생성
    출근표 = pd.DataFrame(index=직원명부.keys(), columns=모든날짜)

    # 🖊️ 출
