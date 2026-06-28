import io
import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

import pandas as pd
from project_templates.import_views import convert_rows_to_folders

csv_content = (
    "Goal_Title,Folder_Name,Document_Name,Document_Content,Task_Title,Task_Description,Est_Hours,Assignee_Email,Priority\n"
    "Mobile App Project,Phase 1 > Planning,Scope Document,This is scope,Draft Scope,Review with client,4.5,test@example.com,high\n"
    "Mobile App Project,Phase 2 > Build,,,,,Code Setup,Install packages,8,,medium\n"
)

try:
    df = pd.read_csv(io.StringIO(csv_content))
    df = df.where(pd.notnull(df), None)
    print("Parsed Dataframe successfully!")
    print(df)
    rows = df.to_dict(orient='records')
    print("Converted to dict records!")
    folder_data = convert_rows_to_folders(df)
    print("Converted rows to folders successfully!")
except Exception as e:
    import traceback
    traceback.print_exc()
