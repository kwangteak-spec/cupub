
from datetime import datetime, timedelta
import pandas as pd
import os
from openpyxl import load_workbook

weekday_kor = ["월", "화", "수", "목", "금", "토", "일"]

# (중략) 기존 함수 및 create_schedule() 함수는 동일

if __name__ == "__main__":
    df, 개인별_근무일수, 출근기록, 야간지원_기록, 직원명부 = create_schedule()
    adddays = load_adddays()

    for 이름 in 출근기록:
        for date in adddays:
            if date in 출근기록[이름]:
                근무타입 = 출근기록[이름][date]
                if 근무타입 in 개인별_근무일수[이름]:
                    개인별_근무일수[이름][근무타입] -= 1
                del 출근기록[이름][date]

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

    수정후_df = df.copy()
    수정후_출근표 = pd.DataFrame(출근기록).T
    수정후_출근표.index.name = "이름"
    수정후_통계_df = pd.DataFrame(통계표)

    file_path = "c:/python/근무표_유동인원_2025_05.xlsx"
    if os.path.exists(file_path):
        os.remove(file_path)

    with pd.ExcelWriter(file_path, engine='openpyxl', mode='w') as writer:
        수정후_df.to_excel(writer, sheet_name="근무표(수정후)", index=False)
        수정후_통계_df.to_excel(writer, sheet_name="근무통계(수정후)", index=False)
        수정후_출근표.to_excel(writer, sheet_name="출근기록(수정후)", index=True)

    print("\n=== 📊 수정 후 개인별 근무시간 및 상태 ===")
    for 항목 in 통계표:
        print(f"{항목['이름']}: 오전 {항목['오전 근무일수']}일, 오후 {항목['오후 근무일수']}일, 야간 {항목['야간 근무일수']}일 → 총 {항목['총 근무시간']}시간 → {항목['근무상태']}")

    print(f"\n✅ 엑셀 파일 새로 저장 완료: {file_path}")
