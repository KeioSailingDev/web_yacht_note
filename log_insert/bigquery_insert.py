from google.cloud import bigquery
import pandas as pd
import numpy as np
from sys import argv
import uuid
import random
from datetime import datetime, timedelta
import glob
import pyproj

def concat_data(input_files):
    logs = pd.DataFrame()
    use_cols = ['loggingTime(txt)',"deviceID(txt)", 'locationLatitude(WGS84)',
    'locationLongitude(WGS84)','locationSpeed(m/s)','locationTrueHeading(°)',
    'motionYaw(rad)','motionRoll(rad)','motionPitch(rad)', "distance"]
    grs80 = pyproj.Geod(ellps='GRS80')  # GRS80楕円体

    # 一行ずつ
    for i in range(len(input_files)):
        log_tmp = pd.read_csv(input_files[i])

        # 一つ前の緯度経度
        log_tmp["lat_before"] = log_tmp['locationLatitude(WGS84)'].shift(1)
        log_tmp["lng_before"] = log_tmp['locationLongitude(WGS84)'].shift(1)

        # 距離を計算
        distance_list = []
        for index, row in log_tmp.iterrows():
            try:
                azimuth, bkw_azimuth, distance = grs80.inv(row["locationLongitude(WGS84)"],
                row["locationLatitude(WGS84)"],
                row["lng_before"],
                row["lat_before"])
            except:
                distance = 0
            distance_list.append(distance)

        # 結果をまとめる
        log_tmp["distance"] = distance_list
        log_tmp = log_tmp[use_cols]

        # 追加
        logs = logs.append(log_tmp)

    return logs

def export_items_to_bigquery(dataset_id, tablename,rows_to_insert):
    # Instantiates a client
    bigquery_client = bigquery.Client()

    # Prepares a reference to the dataset
    dataset_ref = bigquery_client.dataset(dataset_id)

    table_ref = dataset_ref.table(tablename)
    table = bigquery_client.get_table(table_ref)  # API call

    errors = bigquery_client.insert_rows(table, rows_to_insert)  # API request
    print(errors)
    assert errors == []


if __name__ == '__main__':
    # bigquery args
    dataset_id = "smartphone_log"
    tablename = "sensorlog"

    # args
    args = argv
    input_dir = args[1]
    input_files = glob.glob(input_dir + "/*")
    print(input_files)

    # read csv
    table = concat_data(input_files)

    # rows list by tuple
    rows_to_insert = []
    max_index = len(table) - 1
    for index, row in table.iterrows():
        row = row.fillna(0)
        log_row = (
        str(uuid.uuid4()),
        datetime.strptime(row['loggingTime(txt)'][:-6], '%Y-%m-%d %H:%M:%S.%f') - timedelta(hours=9),
        row['deviceID(txt)'],
        row['locationLatitude(WGS84)'],
        row['locationLongitude(WGS84)'],
        row['locationTrueHeading(°)'],
        row['motionYaw(rad)'],
        row['motionRoll(rad)'],
        row['motionPitch(rad)'],
        row['locationSpeed(m/s)'],
        row['distance'])

        rows_to_insert.append(log_row)

        if (index % 5000 == 0 and index != 0) or (index == max_index):
            # export
            export_items_to_bigquery(dataset_id, tablename, rows_to_insert)

            # reset list
            rows_to_insert = []
