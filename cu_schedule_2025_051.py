from datetime import datetime, timedelta
import pandas as pd
import os

weekday_kor = ["월", "화", "수", "목", "금", "토", "일"]

def 이전요일(요일):
    idx = weekday_kor.index(요일)
    return weekday_kor[(idx - 1) % 7]

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

def 추천휴무일_계산(이름, 휴무요일목록):
    후보요일 = set()
    if 휴무요일목록:
        첫 = 휴무요일목록[0]
        후보요일.add(weekday_kor[(weekday_kor.index(첫) - 1) % 7])
    후보날짜 = []
    for d in range(1, 32):
        dt = datetime(2025, 5, d)
        if weekday_kor[dt.weekday()] in 후보요일:
            후보날짜.append(dt.strftime("%Y-%m-%d"))
    return 후보날짜

def 계산_근무시간(기록):
    총근무일 = 기록["오전"] + 기록["오후"] + 기록["야간"]
    야간가중치 = 기록["야간"] * 4
    return 총근무일 * 8 + 야간가중치

def create_schedule():
    직원명부 = load_직원명부()
    공휴일 = load_공휴일()
    오후조_야간지원일 = load_야간지원()
    start_date = datetime(2025, 5, 1)
    end_date = datetime(2025, 5, 31)

    총_근무일 = [(start_date + timedelta(days=i)).strftime("%Y-%m-%d")
                for i in range((end_date - start_date).days + 1)]

    개인별_근무일수 = {name: {"오전": 0, "오후": 0, "야간": 0} for name in 직원명부}
    출근기록 = {name: {} for name in 직원명부}
    순번 = {"오전조": 0, "오후조": 0}
    야간조_순서 = [name for name, info in 직원명부.items() if info["조"] == "야간조"]
    근무표, 야간지원_기록 = [], []

    if len(야간조_순서) == 0:
        raise ValueError("야간조 인원이 없습니다.")

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
        for _ in range(min(2, len(오후후보))):
            이름 = 오후후보[순번["오후조"] % len(오후후보)]
            if 이름 not in 오후:
                오후.append(이름)
                개인별_근무일수[이름]["오후"] += 1
                출근기록[이름][date_str] = "오후"
                순번["오후조"] += 1

        if 오후야간지원자:
            개인별_근무일수[오후야간지원자]["야간"] += 1
            출근기록[오후야간지원자][date_str] = "야간"
            야간 = f"{오후야간지원자}(오후근무)"
            야간지원_기록.append({"날짜": date_str, "이름": 오후야간지원자})
        else:
            담당자 = 야간_일정표.get(date_str, "")
            if 담당자:
                개인별_근무일수[담당자]["야간"] += 1
                출근기록[담당자][date_str] = "야간"
            야간 = 담당자 if 담당자 else "없음"

        if not 오전:
            오전 = ["없음"]
        if not 오후:
            오후 = ["없음"]
        if not 야간:
            야간 = "없음"

        근무표.append({
            "일자": f"{current.day}일({요일})",
            "오전": " ".join(오전),
            "오후": " ".join(오후),
            "야간": 야간
        })

    return pd.DataFrame(근무표), 개인별_근무일수, 출근기록, 야간지원_기록, 직원명부, 계산_근무시간, 추천휴무일_계산

if __name__ == "__main__":
    df, 개인별_근무일수, 출근기록, 야간지원_기록, 직원명부, 계산_근무시간, 추천휴무일_계산 = create_schedule()

    print("=== 📅 근무표 ===")
    print(df.to_string(index=False))

    기준 = 160
    추천표 = []
    print("\n=== 📊 개인별 근무시간 (새 계산 기준) ===")
    for 이름, 기록 in 개인별_근무일수.items():
        총 = 계산_근무시간(기록)
        print(f"{이름}: 오전 {기록['오전']}일, 오후 {기록['오후']}일, 야간 {기록['야간']}일 → 총 {총}시간")
        if 총 > 기준:
            추천휴무일 = 추천휴무일_계산(이름, 직원명부[이름]["휴무요일"])
            추천표.append({
                "이름": 이름,
                "총 근무시간": 총,
                "추천 휴무일": ", ".join(추천휴무일)
            })

    print("\n=== ✅ 휴무 추천일 (160시간 초과자, 새 기준) ===")
    for r in 추천표:
        print(f"{r['이름']}: 총 {r['총 근무시간']}시간 → 추천: {r['추천 휴무일']}")
