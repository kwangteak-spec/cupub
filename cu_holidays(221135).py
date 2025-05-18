from datetime import datetime, timedelta, date
import pandas as pd
import os

# 직원명부 불러오기

def load_직원명부():
    file_path = r"c:\\python\\name.txt"
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"직원명부 파일을 찾을 수 없습니다: {file_path}")
    직원명부 = {}
    with open(file_path, encoding='utf-8') as f:
        next(f)
        for line in f:
            name, group, days = line.strip().split(',')
            휴무요일 = days.split('|') if days else []
            직원명부[name] = {"조": group, "휴무요일": 휴무요일}
    return 직원명부

# 공휴일 불러오기 및 기준 근무시간 계산

def load_공휴일목록(경로=r"c:\\python\\holidays.txt"):
    if not os.path.exists(경로):
        with open(경로, "w", encoding="utf-8") as f:
            f.write("# YYYY-MM-DD 형식으로 공휴일 날짜를 입력하세요.\n")
        print(f"✅ 공휴일 정보 파일을 생성했습니다. 날짜를 입력하세요: {경로}")
        return set()
    holidays = set()
    with open(경로, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                try:
                    holidays.add(datetime.strptime(line, "%Y-%m-%d").date())
                except ValueError:
                    print(f"⚠️ 날짜 형식 오류: {line} (올바른 형식: YYYY-MM-DD)")
    return holidays

def get_기준근무시간(연도=2025, 월=5):
    start_date = date(연도, 월, 1)
    end_date = date(연도, 월, 31)
    공휴일목록 = load_공휴일목록()
    근무일수 = 0
    current = start_date
    while current <= end_date:
        if current.weekday() < 5 and current not in 공휴일목록:
            근무일수 += 1
        current += timedelta(days=1)
    기준시간 = 근무일수 * 8
    return 근무일수, 기준시간

# 근무시간 계산

def 계산_근무시간(근무기록):
    return 근무기록["오전"] * 8 + 근무기록["오후"] * 8 + 근무기록["야간"] * 12

# 추천 휴무일 계산

def 추천_휴무일(기존_휴무요일):
    요일순서 = ["월", "화", "수", "목", "금", "토", "일"]
    if not 기존_휴무요일:
        return None
    첫째 = 기존_휴무요일[0]
    idx = 요일순서.index(첫째)
    추천요일 = 요일순서[idx - 1]
    return 추천요일

# 초과근무 자동 조정

def apply_auto_rest(df, 개인별_근무일수, 출근기록, 직원명부):
    print("\n=== ⚠️ 초과 근무자 조정 및 자동 휴무일 지정 ===")
    기준근무시간 = get_기준근무시간()[1]
    초과자_리스트 = []
    for 이름, 기록 in 개인별_근무일수.items():
        총시간 = 계산_근무시간(기록)
        if 총시간 > 기준근무시간:
            초과시간 = 총시간 - 기준근무시간
            제거_일수 = 0
            for 날짜, 상태 in 출근기록[이름].items():
                if 초과시간 < 12: break
                if 상태 == "근무" and df[df['일자'].str.contains(f"{int(날짜[-2:])}일")]["야간"].str.contains(이름).any():
                    출근기록[이름][날짜] = "휴무"
                    기록["야간"] -= 1
                    초과시간 -= 12
                    제거_일수 += 1
            for shift in ["오전", "오후"]:
                for 날짜, 상태 in 출근기록[이름].items():
                    if 초과시간 < 8: break
                    if 상태 == "근무" and df[df['일자'].str.contains(f"{int(날짜[-2:])}일")][shift].str.contains(이름).any():
                        출근기록[이름][날짜] = "휴무"
                        기록[shift] -= 1
                        초과시간 -= 8
                        제거_일수 += 1
            추천 = 추천_휴무일(직원명부[이름]["휴무요일"])
            초과자_리스트.append({
                "이름": 이름,
                "초과시간": 총시간 - 기준근무시간,
                "제거_일수": 제거_일수,
                "추천휴무요일": 추천
            })
    return pd.DataFrame(초과자_리스트)
def create_schedule():
    직원명부 = load_직원명부()
    start_date = datetime(2025, 5, 1)
    end_date = datetime(2025, 5, 31)
    weekday_kor = ["월", "화", "수", "목", "금", "토", "일"]

    오후조_야간지원일 = {
        "2025-05-05": "김제원",
        "2025-05-09": "장영대",
        "2025-05-16": "장영대",
        "2025-05-19": "김제원",
        "2025-05-26": "김제원"
    }

    개인별_근무일수 = {name: {"오전": 0, "오후": 0, "야간": 0} for name in 직원명부}
    출근기록 = {name: {} for name in 직원명부}
    순번 = {"오전조": 0, "오후조": 0}
    야간조_순서 = [name for name, info in 직원명부.items() if info["조"] == "야간조"]
    근무표 = []

    for i in range((end_date - start_date).days + 1):
        date = start_date + timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")
        for name in 출근기록:
            출근기록[name][date_str] = "휴무"

    야간_날짜리스트 = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)
                   if (start_date + timedelta(days=i)).strftime("%Y-%m-%d") not in 오후조_야간지원일]

    야간_일정표 = {}
    for i, day in enumerate(야간_날짜리스트):
        담당자 = 야간조_순서[(i // 2) % 2]
        if i == len(야간_날짜리스트) - 1 and len(야간_날짜리스트) % 2 != 0:
            담당자 = 야간조_순서[1]
        date_str = day.strftime("%Y-%m-%d")
        야간_일정표[date_str] = 담당자

    for i in range((end_date - start_date).days + 1):
        current = start_date + timedelta(days=i)
        요일 = weekday_kor[current.weekday()]
        일자 = current.day
        date_str = current.strftime("%Y-%m-%d")
        오후야간지원자 = 오후조_야간지원일.get(date_str)

        오전 = []
        오후 = []
        야간 = ""

        오전후보 = [name for name, info in 직원명부.items() if info["조"] == "오전조" and 요일 not in info["휴무요일"]]
        for _ in range(2):
            if 오전후보:
                이름 = 오전후보[순번["오전조"] % len(오전후보)]
                if 이름 not in 오전:
                    오전.append(이름)
                    개인별_근무일수[이름]["오전"] += 1
                    출근기록[이름][date_str] = "근무"
                    순번["오전조"] += 1

        오후후보 = [name for name, info in 직원명부.items() if info["조"] == "오후조" and 요일 not in info["휴무요일"] and name != 오후야간지원자]
        for _ in range(3):
            if 오후후보:
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
        else:
            담당자 = 야간_일정표[date_str]
            야간 = 담당자
            개인별_근무일수[담당자]["야간"] += 1
            출근기록[담당자][date_str] = "근무"

        근무표.append({
            "일자": f"{일자}일({요일})",
            "오전": " ".join(오전),
            "오후": " ".join(오후),
            "야간": 야간
        })

    return pd.DataFrame(근무표), 개인별_근무일수, 직원명부, 출근기록
 #추천 휴무 요일에 해당하는 5월 날짜 목록 생성
def 추천휴무일_날짜목록(추천결과):
    날짜모음 = []
    for _, row in 추천결과.iterrows():
        이름 = row["이름"]
        추천요일 = row["추천휴무요일"]
        if 추천요일 is None:
            continue
        날짜들 = []
        for i in range(31):
            d = datetime(2025, 5, i + 1)
            if d.strftime("%a") in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
                if d.strftime("%a") == 추천요일:
                    날짜들.append(d.strftime("%Y-%m-%d"))
                else:
                    weekday_kor = ["월", "화", "수", "목", "금", "토", "일"]
                    if weekday_kor[d.weekday()] == 추천요일:
                        날짜들.append(d.strftime("%Y-%m-%d"))
        날짜모음.append({
            "이름": 이름,
            "추천휴무요일": 추천요일,
            "해당날짜들": ", ".join(날짜들)
        })
    return pd.DataFrame(날짜모음)


# 실행
if __name__ == "__main__":
    df, 개인별_근무일수, 직원명부, 출근기록 = create_schedule()

    print("=== 📅 5월 근무표 ===")
    print(df.to_string(index=False))

    print("\n=== 📊 개인별 근무일수 및 근무시간 ===")
    통계표 = []
    for 이름, 기록 in 개인별_근무일수.items():
        총시간 = 계산_근무시간(기록)
        print(f"{이름}: 오전 {기록['오전']}일, 오후 {기록['오후']}일, 야간 {기록['야간']}일 → 총 {총시간}시간")
        통계표.append({
            "이름": 이름,
            "오전 근무일수": 기록["오전"],
            "오후 근무일수": 기록["오후"],
            "야간 근무일수": 기록["야간"],
            "총 근무시간": 총시간
        })

    통계_df = pd.DataFrame(통계표)
    출근표 = pd.DataFrame(출근기록).T
    출근표.index.name = "이름"

    print("\n=== 📌 개인별 날짜별 출근표 (근무/휴무) ===")
    print(출근표.to_string())

    # 초과근무자 자동 조정
    조정결과 = apply_auto_rest(df, 개인별_근무일수, 출근기록, 직원명부)
    print("\n=== 🛠 조정 결과 ===")
    print(조정결과.to_string(index=False))

    # 저장
    output_path = r"c:\\python\\근무표_2025_05.xlsx"
    with pd.ExcelWriter(output_path, engine='openpyxl', mode='w') as writer:
        df.to_excel(writer, sheet_name='5월 근무표', index=False)
        통계_df.to_excel(writer, sheet_name='개인별 통계', index=False)
        출근표.to_excel(writer, sheet_name='출근표', index=True)
        조정결과.to_excel(writer, sheet_name='초과근무조정', index=False)
        추천날짜표 = 추천휴무일_날짜목록(조정결과)
        추천날짜표.to_excel(writer, sheet_name='추천휴무일', index=False)

    print(f"\n✅ 엑셀 파일 저장 완료: {output_path}")


# create_schedule 및 추천휴무일_날짜목록 함수는 기존대로 아래에 추가하여 사용합니다.
# 실행부 (if __name__ == '__main__') 안에서 기준근무시간 계산, 근무표 생성, 초과근무 판단, 엑셀 저장 포함하여 완성하세요.
