import pandas as pd
import psycopg2
from urllib.parse import urlparse

file_path = "TheIDOLS_SPs.xlsx"  # Replace with the actual Excel file path

df = pd.read_excel(file_path, engine="openpyxl")  # Specify engine if necessary

# Define the SP columns
sp_columns = ["SP1", "SP2", "SP3", "SP4", "SP5"]

# Split each SP column into Name and Skills
for sp in sp_columns:
    df[f"{sp}_Name"] = df[sp].str.split(" ", n=1).str[0]  # Extract the first word as Name
    df[f"{sp}_Skills"] = df[sp].str.split(" ", n=1).str[1]  # Extract the rest as Skills

# Drop the original SP columns (optional)
df = df.drop(columns=sp_columns)

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



# Iterate through the rows and insert into the database
for _, row in df.iterrows():
    # Check if the player already exists
    cursor.execute("SELECT * FROM Player WHERE Name = %s", (row["Name"].lower(),))
    player_exists = cursor.fetchone()

    # If the player exists, skip this row
    if player_exists:
        # Update the existing player's data
        cursor.execute(
            """
            UPDATE Player
            SET Club_Name = %s, SP1_Name = %s, SP1_Skills = %s,
                SP2_Name = %s, SP2_Skills = %s, SP3_Name = %s, SP3_Skills = %s,
                SP4_Name = %s, SP4_Skills = %s, SP5_Name = %s, SP5_Skills = %s,
                Nerf = %s, Most_Common_Batting_Skill = %s, PR = %s, last_updated = CURRENT_DATE, team_name = %s
            WHERE Name = %s
            """,
            (
                row["Club_Name"],
                row["SP1_Name"], row["SP1_Skills"],
                row["SP2_Name"], row["SP2_Skills"],
                row["SP3_Name"], row["SP3_Skills"],
                row["SP4_Name"], row["SP4_Skills"],
                row["SP5_Name"], row["SP5_Skills"],
                row["Nerf"], row.get("Most_Common_Batting_Skill", ""),
                row["PR"], row.get("Team_Name", ""),
                row["Name"]
            )
        )

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
    if not player_exists:
        cursor.execute(
            """
            INSERT INTO Player (
                Name, Club_Name, SP1_Name, SP1_Skills,
                SP2_Name, SP2_Skills, SP3_Name, SP3_Skills,
                SP4_Name, SP4_Skills, SP5_Name, SP5_Skills,
                Nerf, Most_Common_Batting_Skill, PR, last_updated, nerf_updated, team_name
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_DATE, CURRENT_DATE, %s)
            """,
            (
                row["Name"].lower(),
                club_name,
                row["SP1_Name"], row["SP1_Skills"],
                row["SP2_Name"], row["SP2_Skills"],
                row["SP3_Name"], row["SP3_Skills"],
                row["SP4_Name"], row["SP4_Skills"],
                row["SP5_Name"], row["SP5_Skills"],
                row["Nerf"], row.get("Most_Common_Batting_Skill", ""),
                row["PR"], row.get("Team_Name", ""),
            )
        )

# Commit and close
connection.commit()
cursor.close()
connection.close()

print("Data successfully inserted into the database!")
