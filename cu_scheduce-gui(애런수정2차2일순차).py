
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import pandas as pd
import os

def load_직원명부():
    file_path = r"c:\python\name.txt"
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

def load_야간지원자():
    file_path = r"c:\python\night_applicant.txt"
    if not os.path.exists(file_path):
        return {}
    야간지원자 = {}
    with open(file_path, encoding='utf-8') as f:
        for line in f:
            date, name = line.strip().split(',')
            야간지원자[date] = name
    return 야간지원자

def 계산_근무시간(근무기록):
    return 근무기록["오전"] * 8 + 근무기록["오후"] * 8 + 근무기록["야간"] * 12

def create_schedule_fixed(year, month):
    직원명부 = load_직원명부()
    야간지원자 = load_야간지원자()
    start_date = datetime(year, month, 1)
    end_date = datetime(year, month, (datetime(year, month + 1, 1) - timedelta(days=1)).day)
    weekday_kor = ["월", "화", "수", "목", "금", "토", "일"]

    개인별_근무일수 = {name: {"오전": 0, "오후": 0, "야간": 0} for name in 직원명부}
    출근기록 = {name: {} for name in 직원명부}
    순번 = {"오전조": 0, "오후조": 0}
    야간조_순서 = [name for name, info in 직원명부.items() if info["조"] == "야간조"]
    근무표 = []
    야간지원_배정_기록 = []

    for i in range((end_date - start_date).days + 1):
        date = start_date + timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")
        for name in 출근기록:
            출근기록[name][date_str] = "휴무"

    # 야간조 순환 방식 변경: 2일 근무, 2일 휴무
    야간_일정표 = {}
    for i in range((end_date - start_date).days + 1):
        current = start_date + timedelta(days=i)
        date_str = current.strftime("%Y-%m-%d")
        if (i // 4) % 2 == 0:  # 2일 근무, 2일 휴무
            담당자 = 야간조_순서[(i // 2) % len(야간조_순서)]
            야간_일정표[date_str] = 담당자

    for i in range((end_date - start_date).days + 1):
        current = start_date + timedelta(days=i)
        요일 = weekday_kor[current.weekday()]
        일자 = current.day
        date_str = current.strftime("%Y-%m-%d")
        오후야간지원자 = 야간지원자.get(date_str)

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
        for _ in range(min(3, len(오후후보))):
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
            야간지원_배정_기록.append({
                "날짜": date_str,
                "이름": 오후야간지원자,
                "배정여부": "무조건 배정됨"
            })
        else:
            담당자 = 야간_일정표.get(date_str, "")
            if 담당자:
                야간 = 담당자
                개인별_근무일수[담당자]["야간"] += 1
                출근기록[담당자][date_str] = "근무"

        근무표.append({
            "일자": f"{일자}일({요일})",
            "오전": " ".join(오전),
            "오후": " ".join(오후),
            "야간": 야간
        })

    df = pd.DataFrame(근무표)
    output_path = f"c:/python/근무표_{year}_{month:02d}.xlsx"
    with pd.ExcelWriter(output_path, mode='w', engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name=f"{month}월 근무표", index=False)
    return output_path

# GUI 구성
def run_gui():
    root = tk.Tk()
    root.title("📅 근무표 자동 생성기")
    root.geometry("300x200")

    tk.Label(root, text="연도 선택").pack(pady=5)
    year_cb = ttk.Combobox(root, values=[2025, 2026], state="readonly")
    year_cb.set(2025)
    year_cb.pack()

    tk.Label(root, text="월 선택").pack(pady=5)
    month_cb = ttk.Combobox(root, values=list(range(1, 13)), state="readonly")
    month_cb.set(5)
    month_cb.pack()

    def generate():
        try:
            y = int(year_cb.get())
            m = int(month_cb.get())
            path = create_schedule_fixed(y, m)
            messagebox.showinfo("완료", f"근무표 생성 완료!\n저장 위치: {path}")
        except Exception as e:
            messagebox.showerror("오류", str(e))

    ttk.Button(root, text="근무표 생성", command=generate).pack(pady=20)

    root.mainloop()

if __name__ == "__main__":
    run_gui()
