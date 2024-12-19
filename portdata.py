import pandas as pd
import psycopg2
from urllib.parse import urlparse

file_path = "NFS Clubs Scouting.xlsx"  # Replace with the actual Excel file path

df = pd.read_excel(file_path, engine="openpyxl")  # Specify engine if necessary
df["Name"] = df["Name"].astype(str)

# Convert player names and club names to lowercase
df["Name"] = df["Name"].str.lower().str.replace(" ", "")
df["Club_Name"] = df["Club_Name"].str.lower()

# Fill empty Club_Name values with "no club"
df["Club_Name"].fillna("no club", inplace=True)
df["Nerf"].fillna("", inplace=True)
df["PR"].fillna(9999, inplace=True)

DATABASE_URL = "postgres://u4kqn7e60puiu1:p4a4ecc6673558b8a08d820c48a4456038a4752c358a0f1de9396f15fd58c6945@cd27da2sn4hj7h.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/d6p7k4of1m96ql"
result = urlparse(DATABASE_URL)
connection = psycopg2.connect(
    database=result.path[1:],
    user=result.username,
    password=result.password,
    host=result.hostname,
    port=result.port
)
cursor = connection.cursor()

x = 0

# Iterate through the rows and insert into the database
for _, row in df.iterrows():
    if x == 500:
        break
    x += 1
    try:
        # Check if the player already exists
        cursor.execute("SELECT * FROM Player WHERE Name = %s", (row["Name"].lower(),))
        player_exists = cursor.fetchone()

        # If the player exists, skip this row
        if player_exists:
            continue

        # If Club_Name is empty, set it to "no club"
        club_name = row["Club_Name"].lower() if row["Club_Name"] else "no club"

        # Check if the Club_Name exists
        cursor.execute("SELECT * FROM Club WHERE Club_Name = %s", (club_name,))
        club_exists = cursor.fetchone()

        # If the club doesn't exist, create it
        if not club_exists:
            cursor.execute(
                """
                INSERT INTO Club (Club_Name)
                VALUES (%s)
                """,
                (club_name,)
            )
            print(f"Created new club: {club_name}")

        # Insert the player into the Player table
        cursor.execute(
            """
            INSERT INTO Player (
                Name, Club_Name,
                SP1_Name, SP1_Skills,
                SP2_Name, SP2_Skills,
                SP3_Name, SP3_Skills,
                SP4_Name, SP4_Skills,
                SP5_Name, SP5_Skills,
                Nerf, PR, last_updated, nerf_updated, team_name
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_DATE, CURRENT_DATE, %s)
            """,
            (
                row["Name"].lower(),
                club_name,
                row.get("SP1_Name", ""), row.get("SP1_Skills", ""),
                row.get("SP2_Name", ""), row.get("SP2_Skills", ""),
                row.get("SP3_Name", ""), row.get("SP3_Skills", ""),
                row.get("SP4_Name", ""), row.get("SP4_Skills", ""),
                row.get("SP5_Name", ""), row.get("SP5_Skills", ""),
                row["Nerf"],
                row["PR"],
                row.get("Team_Name", ""),
            )
        )
    except Exception as e:
        # Log the error and continue to the next row
        print(f"Error processing row: {row.to_dict()} - {e}")

# Commit and close
connection.commit()
cursor.close()
connection.close()

print("Data successfully inserted into the database!")
