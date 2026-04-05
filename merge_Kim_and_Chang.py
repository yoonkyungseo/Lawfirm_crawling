import os
import glob
import pandas as pd

base_path = 'data'
try:
    folders = [f for f in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, f))]
    folders.sort()
    latest_folder = folders[-1] # 가장 최근 폴더 선택
    kim_chang_csv_files = glob.glob(os.path.join(f'data/{latest_folder}', "Kim_and_Chang*.csv"))
    if kim_chang_csv_files:
        df_lst = []
        for kim_chang_file in kim_chang_csv_files:
            kim_chang_csv = pd.read_csv(kim_chang_file)
            df_lst.append(kim_chang_csv)
        combined_df = pd.concat(df_lst, ignore_index=True)
        initial_cnt = len(combined_df)

        # (이름, 이메일, 전화번호) 중복제거
        final_df = combined_df.drop_duplicates(
            subset=['name', 'email', 'call'], 
            keep='first' # 첫 번째 데이터만 남김
        )

        print(f"중복 제거 전: {initial_cnt} → 중복 제거 후: {len(final_df)}")
        latest_date = latest_folder.replace('-',"")[2:]
        final_df.to_csv(f"data/{latest_folder}/Kim_and_Chang_{latest_date}.csv", index=False, encoding='utf-8-sig')
        print("김앤장 중복 제거 완료")

        # 우선 만들어진 각각의 파일은 삭제 안함

    else:
        print("저장된 김앤장 인사정보 파일이 없습니다.")
except FileNotFoundError:
    print("파일을 찾을 수 없습니다.")