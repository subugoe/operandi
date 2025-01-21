import pandas as pd
from re import match as re_match, IGNORECASE as re_IGNORECASE
from os import listdir
from os.path import join, isfile
from sqlite3 import connect as sqlite3_connect


def convert_rss_to_gb(rss):
    """
    Converts a memory usage string (e.g., '126.9 MB', '2048 KB') to gigabytes as a float.

    Parameters:
    - peak_rss (str): Memory usage string.

    Returns:
    - float: Memory usage in gigabytes.
    """
    match = re_match(r"([\d\.]+)\s*(KB|MB|GB)", rss, re_IGNORECASE)
    if match:
        value = float(match.group(1))
        unit = match.group(2).upper()
        if unit == "KB":
            return value / 1048576  # (1024 ** 2)
        elif unit == "MB":
            return value / 1024
        elif unit == "GB":
            return value
    # Return None if the format is invalid
    return None


def convert_duration_to_seconds(duration):
    """
    Converts a duration string (e.g., '5m 4s', '3.4s') to seconds as a float.

    Parameters:
    - duration (str): Duration string.

    Returns:
    - float: Duration in seconds.
    """
    match = re_match(r"(?:(\d+)m)?\s*(?:(\d+\.?\d*)s)?", duration)
    if match:
        minutes = int(match.group(1)) if match.group(1) else 0
        seconds = float(match.group(2)) if match.group(2) else 0.0
        return minutes * 60 + seconds
    # Return None if the format is invalid
    return None


def process_trace_file(file_path):
    """
    Processes a trace file to retain only enabled metrics and stores data in a database.

    Parameters:
    - file_path (str): Path to the trace file (assumes TSV format).
    - conn (object): Database connection object.
    - workflow_id (int): ID of the workflow for data association.
    - enabled_metrics (list): List of metrics to be retained.
    """

    # Load the trace data (assuming it's in TSV format)
    df = pd.read_csv(file_path, sep="\t")
    df["duration"] = df["duration"].apply(convert_duration_to_seconds)
    df["%cpu"] = df["%cpu"].str.replace("%", "").astype(float)
    df["peak_rss"] = df["peak_rss"].apply(convert_rss_to_gb)

    conn = sqlite3_connect('workflow_db.db')
    cursor = conn.cursor()

    # Insert filtered data into the nextflow_traces table
    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO nextflow_traces (name, submit, duration, cpu_percent, peak_rss, workflow_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (row['name'], row['submit'], row['duration'], row['%cpu'], row['peak_rss'], row['workflow_id']))
    conn.commit()
    conn.close()


for file_name in listdir("nf-traces"):
    file_path = join("nf-traces", file_name)
    if isfile(file_path):
        process_trace_file(file_path)


conn = sqlite3_connect("workflow_db.db")
cursor = conn.cursor()
# Fetch and print the contents of the nextflow_traces table
cursor.execute("SELECT * FROM nextflow_traces")
rows = cursor.fetchall()

# Get column names from cursor.description
column_names = [description[0] for description in cursor.description]

# Print column names
print(" | ".join(column_names))

# Print the table rows
for row in rows:
    print(" | ".join(map(str, row)))
#
conn.close()
