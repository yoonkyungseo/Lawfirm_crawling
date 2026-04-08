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

        # url 중복제거
        final_df = combined_df.drop_duplicates(
            subset=['url'], 
            keep='first' # 첫 번째 데이터만 남김
        ).copy()

        print("김앤장 concat & 중복 제거 완료")
    else:
        print("저장된 김앤장 인사정보 파일이 없습니다.")

    try:
        find_quitter_folder = folders[-2]
        before_csv_files = glob.glob(os.path.join(f'data/{find_quitter_folder}', f"Kim_and_Chang_{find_quitter_folder.replace("-","")[2:]}.csv"))
        if before_csv_files:
            df_old = pd.read_csv(before_csv_files[0])
            if not df_old.empty:
                df_old['temp_id'] = df_old['url'].astype(str)
                final_df['temp_id'] = final_df['url'].astype(str)
                # 퇴사자 정보 추출
                retired_info = df_old[~df_old['temp_id'].isin(final_df['temp_id'])].copy()
                final_df.drop(columns=['temp_id'], inplace=True)

                if not retired_info.empty:
                    retired_info['new'] = "Out"
                    retired_info.drop(columns=['temp_id'], inplace=True)
                    save_df = pd.concat([final_df, retired_info], ignore_index=True)
                else:
                    save_df = final_df
            else:
                save_df = final_df
        else:
            save_df = final_df
    except IndexError:
        save_df = final_df
    
    print(f"중복 제거 전: {final_df} → 중복 제거 후: {len(save_df)}")
    latest_date = latest_folder.replace('-',"")[2:]
    save_df.to_csv(f"data/{latest_folder}/Kim_and_Chang_{latest_date}.csv", index=False, encoding='utf-8-sig')
    print("김앤장 인사정보 파일 저장 완료!")
except FileNotFoundError:
    print("파일을 찾을 수 없습니다.")