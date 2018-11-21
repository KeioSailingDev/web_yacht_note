from google.cloud import bigquery

def bq_create_table(dataset_id, tablename):
    bigquery_client = bigquery.Client()
    dataset_ref = bigquery_client.dataset(dataset_id)

    # Prepares a reference to the table
    table_ref = dataset_ref.table(tablename)

    try:
        bigquery_client.get_table(table_ref)
    except:
        schema = [
            bigquery.SchemaField('log_id', 'STRING', mode='REQUIRED', description='UUID'),
            bigquery.SchemaField('loggingTime', 'TIMESTAMP', mode='NULLABLE', description='loggingTime(JST)'),
            bigquery.SchemaField('device_id', 'STRING', mode='NULLABLE', description='device_id'),
            bigquery.SchemaField('locationLatitude', 'FLOAT64', mode='NULLABLE', description='locationLatitude(WGS84)'),
            bigquery.SchemaField('locationLongitude', 'FLOAT64', mode='NULLABLE', description='locationLongitude(WGS84)'),
            bigquery.SchemaField('locationTrueHeading', 'FLOAT64', mode='NULLABLE', description='motionPitch(°)'),
            bigquery.SchemaField('motionPitch', 'FLOAT64', mode='NULLABLE', description='motionPitch(rad)'),
            bigquery.SchemaField('motionRoll', 'FLOAT64', mode='NULLABLE', description='motionRoll(rad)'),
            bigquery.SchemaField('motionYaw', 'FLOAT64', mode='NULLABLE', description='motionYaw(rad)'),
            bigquery.SchemaField('speed', 'FLOAT64', mode='NULLABLE', description='speed(m/s)'),
            bigquery.SchemaField('distance', 'FLOAT64', mode='NULLABLE', description='distanse(m)'),
        ]
        table = bigquery.Table(table_ref, schema=schema)
        table = bigquery_client.create_table(table)
        print('table {} created.'.format(table.table_id))

if __name__ == '__main__':
    dataset_id = "smartphone_log"
    tablename = "sensorlog"
    bq_create_table(dataset_id, tablename)
