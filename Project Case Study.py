MAIN.PY ---

from dq_framework import DQFramework
from utils.file_writer import save_as_csv, save_as_html
from utils.email_sender import send_email
from utils.load_data import load_csv_to_db
import os

def parse_config(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    config = {}
    for line in lines:
        if ":" in line:
            key, val = line.strip().split(":")
            config[key.strip()] = [v.strip() for v in val.strip().split(',')]
    return config

if __name__ == "__main__":
    # Step 1: Read config
    config = parse_config("config/table_validation.txt")
    csv_path = config['csv_file'][0]

    # Step 2: Load data into SQLite
    table_name_for_report = os.path.splitext(os.path.basename(csv_path))[0]
    load_csv_to_db(csv_path=csv_path, table_name=table_name_for_report)

    # Step 3: Run validation
    dq = DQFramework(csv_path)
    dq.null_check(config['null_check_columns'])
    dq.duplicate_check(config['duplicate_check_columns'])

    if "custom_query_files" in config and "custom_query_table_names" in config:
        custom_files = config["custom_query_files"]
        custom_tables = config["custom_query_table_names"]

        for hql_file, table_name in zip(custom_files, custom_tables):
            dq.custom_query_check(
                hql_file_path=hql_file,
                table_name=table_name,
                db_path="sample.db"
            )
        if custom_tables:
            table_name_for_report = custom_tables[0]

    # Step 4: Get results
    result_df = dq.get_results()

    # Step 5: Save reports
    os.makedirs("output", exist_ok=True)
    save_as_csv(result_df)
    html_path = save_as_html(result_df, table_name=table_name_for_report)

    # Step 6: Send Email
    if html_path:
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        send_email(
            subject="CSV DQ Validation Report",
            body_html=html_content,
            to_email="thegouravgupta7@gmail.com",       # ✅ replace if needed
            from_email="thegouravgupta7@gmail.com",           # ✅ replace if needed
            password="***************"                       # ✅ your Gmail App password
        )
    else:
        print("❌ No HTML report generated. Email not sent.")




EMAIL_SENDER.PY --------

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_email(
    subject,
    body_html,
    to_email,
    from_email="thegouravgupta7@gmail.com",
    password="*************",
    smtp_server="smtp.gmail.com",
    smtp_port=587,
):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email

    part = MIMEText(body_html, "html")
    msg.attach(part)

    try:
        print("Connecting to SMTP...")
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)
        server.starttls()
        print("Logging in...")
        server.login(from_email, password)
        print("Sending email...")
        server.sendmail(from_email, to_email, msg.as_string())
        server.quit()
        print("✅ Email sent successfully!")
        print(f"TO: {to_email}")
        print(f"FROM: {from_email}")
        print(f"SUBJECT: {subject}")
        print(f"BODY SIZE: {len(body_html)} bytes")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")



FILE_WRITER.PY ---------

import pandas as pd
import time

def save_as_csv(df, path="output/dq_report.csv"):
    df.to_csv(path, index=False)
    print(f"✅ Saved report to {path}")

def save_as_html(df, table_name="Unknown", path="output/dq_report.html"):
    timestamp = int(time.time())

    html = f"""
    <html>
    <body>
      <h2 style="font-family: Arial, sans-serif; color: #333;">
        Validation Framework Report
      </h2>
      <p style="font-family: Arial, sans-serif; font-size: 14px;">
        <strong>Table Name:</strong> {table_name}<br>
        <strong>Date:</strong> {timestamp}
      </p>
      <table border="1" cellspacing="0" cellpadding="5" 
             style="border-collapse: collapse; font-family: Arial, sans-serif; font-size: 14px;">
        <tr>
    """

    # Header
    for col in df.columns:
        html += f'<th style="background-color: #f2f2f2;">{col}</th>'
    html += "</tr>"

    # Rows
    for _, row in df.iterrows():
        html += "<tr>"
        for col in df.columns:
            val = row[col]
            if col == "Validation Result":
                if val == "Pass":
                    cell_style = 'color: green; font-weight: bold;'
                else:
                    cell_style = 'color: red; font-weight: bold;'
                html += f'<td style="{cell_style}">{val}</td>'
            else:
                html += f"<td>{val}</td>"
        html += "</tr>"

    html += """
      </table>
    </body>
    </html>
    """

    with open(path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ HTML report saved to {path}")
    return path




LOAD_DATA.PY --------------------

import pandas as pd
import sqlite3
import os

def load_csv_to_db(csv_path="data/employee.csv", db_path="sample.db", table_name="employee"):
    if not os.path.exists(csv_path):
        print(f"❌ CSV file not found at: {csv_path}")
        return False

    try:
        df = pd.read_csv(csv_path)
        conn = sqlite3.connect(db_path)
        df.to_sql(table_name, conn, if_exists="replace", index=False)
        conn.close()
        print(f"✅ Loaded '{csv_path}' into '{db_path}' as table '{table_name}'.")
        return True
    except Exception as e:
        print(f"❌ Failed to load CSV into DB: {e}")
        return False

if __name__ == "__main__":
    load_csv_to_db()





DQ_FRAMEWORK.PY  --------------------

import pandas as pd
import sqlite3
import os

class DQFramework:
    def __init__(self, csv_path):
        self.csv_path = csv_path
        self.df = pd.read_csv(csv_path)
        self.results = []

    def null_check(self, columns):
        for col in columns:
            count = self.df[col].isnull().sum()
            self.results.append({
                "Column": col,
                "Check": "Null Check",
                "Validation Result": "Fail" if count > 0 else "Pass",
                "True Value": count
            })

    def duplicate_check(self, pk_columns):
        count = self.df.duplicated(subset=pk_columns).sum()
        self.results.append({
            "Column": ", ".join(pk_columns),
            "Check": "Duplicate Check",
            "Validation Result": "Fail" if count > 0 else "Pass",
            "True Value": count
        })

    def custom_query_check(self, hql_file_path, table_name, db_path="sample.db"):
        if not os.path.exists(hql_file_path):
            print(f"❌ HQL file not found: {hql_file_path}")
            self.results.append({
                "Column": table_name,
                "Check": "Custom Query Check",
                "Validation Result": "Fail",
                "True Value": "File Not Found"
            })
            return

        with open(hql_file_path, "r") as f:
            hql = f.read()

        try:
            conn = sqlite3.connect(db_path)
            result = conn.execute(hql)
            rows = result.fetchall()
            count = len(rows)
            conn.close()

            self.results.append({
                "Column": table_name,
                "Check": "Custom Query Check",
                "Validation Result": "Pass" if count == 0 else "Fail",
                "True Value": count
            })

        except Exception as e:
            self.results.append({
                "Column": table_name,
                "Check": "Custom Query Check",
                "Validation Result": "Fail",
                "True Value": str(e)
            })

    def get_results(self):
        return pd.DataFrame(self.results)





EMPLOYEE.CSV  ------------------DATA


emp_id,name,department,email,salary
1,John,Sales,john@example.com,50000
2,Priya,HR,priya@example.com,48000
3,Ravi,Engineering,,60000
4,,Marketing,anita@example.com,55000
5,Anita,Sales,anita@example.com,55000
6,Suresh,Engineering,suresh@example.com,65000
7,Kavita,,kavita@example.com,
8,John,Sales,john.d@example.com,51000
2,Priya,HR,priya@example.com,48000
9,Mohan,Finance,,45000
10,,HR,mystery@example.com,47000
11,Aarti,Engineering,aarti@example.com,
12,John,Engineering,johnny@example.com,50000
13,Shaam,Finance,shaam@example.com,44000
14,Rita,Sales,rita@example.com,52000
15,Ankit,Engineering,,62000
16,Kiran,Support,kiran@example.com,40000
17,Salim,Sales,salim@example.com,50000
18,Saloni,HR,,46000
19,,Marketing,unknown@example.com,
20,Meera,Finance,meera@example.com,47000




CONFIG
TABLE_VALIDATION.TXT

csv_file: data/employee.csv
null_check_columns: emp_id,name,department,email,salary
duplicate_check_columns: emp_id
custom_query_files: config/table_dq.hql
custom_query_table_names: employee


OUTPUT :

Column,Check,Validation Result,True Value
emp_id,Null Check,Pass,0
name,Null Check,Fail,3
department,Null Check,Fail,1
email,Null Check,Fail,4
salary,Null Check,Fail,3
emp_id,Duplicate Check,Fail,1
employee,Custom Query Check,Pass,0
