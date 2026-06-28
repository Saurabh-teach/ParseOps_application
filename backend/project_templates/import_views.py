import csv
import io
from rest_framework import views, status, permissions
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from organizations.models import Organization
from goals.models import Goals
from tasks.models import Task
from django.contrib.auth import get_user_model
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils.dateparse import parse_date

from .services import TemplateService

User = get_user_model()

class BulkImportCSVView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, org_slug):
        org = get_object_or_404(Organization, slug=org_slug)
        file_obj = request.FILES.get('file')
        
        if not file_obj:
            return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            goals_created, tasks_created = TemplateService.bulk_import_csv(org, file_obj, request.user)
            return Response({
                "status": "Import successful", 
                "goals_created": goals_created,
                "tasks_created": tasks_created
            })
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def convert_rows_to_folders(df):
    import uuid
    import pandas as pd
    
    root_folders = []
    
    def get_or_create_folder(folder_path_list, folder_list, goal_title):
        if not folder_path_list:
            return None
        first_part = folder_path_list[0]
        target_folder = None
        for folder in folder_list:
            if folder['name'].lower() == first_part.lower() and folder.get('goal_title', '').lower() == goal_title.lower():
                target_folder = folder
                break
        if not target_folder:
            target_folder = {
                'id': str(uuid.uuid4()),
                'name': first_part,
                'goal_title': goal_title,
                'items': [],
                'subfolders': []
            }
            folder_list.append(target_folder)
            
        if len(folder_path_list) > 1:
            return get_or_create_folder(folder_path_list[1:], target_folder['subfolders'], goal_title)
        return target_folder

    for index, row in df.iterrows():
        def clean(k):
            try:
                val = row.get(k, '')
            except Exception:
                return ''
            if val is None:
                return ''
            try:
                if pd.isna(val):
                    return ''
            except (ValueError, TypeError):
                pass
            return str(val).strip()
            
        goal_title = clean('Goal_Title')
        folder_name = clean('Folder_Name')
        doc_name = clean('Document_Name')
        doc_content = clean('Document_Content')
        task_title = clean('Task_Title')
        task_desc = clean('Task_Description')
        est_hours_val = row.get('Est_Hours', None)
        
        assignee_email = ''
        for k, v in row.items():
            if k and str(k).strip().lower().replace('_', ' ') in ['assignee email', 'assignee', 'email']:
                assignee_email = str(v).strip()
                break
                
        priority = clean('Priority').lower()
        impact = clean('Impact')
        risk = clean('Risk')
        if priority not in ['low', 'medium', 'high', 'urgent']:
            priority = 'medium'
            
        est_hours = None
        if est_hours_val is not None and not pd.isna(est_hours_val):
            try:
                est_hours = float(est_hours_val)
            except ValueError:
                pass
                
        due_date_raw = clean('Due_Date')
        due_date = None
        if due_date_raw:
            due_date = str(due_date_raw)
                
        folder_path = [p.strip() for p in folder_name.replace('>', '/').split('/') if p.strip()]
        if not folder_path:
            default_folder_name = goal_title if goal_title else "General"
            folder_obj = get_or_create_folder([default_folder_name], root_folders, goal_title)
        else:
            folder_obj = get_or_create_folder(folder_path, root_folders, goal_title)
            
        if doc_name:
            folder_obj['items'].append({
                'id': str(uuid.uuid4()),
                'name': doc_name,
                'item_type': 'document',
                'content': {'text': doc_content},
                'url': '',
                'order': len(folder_obj['items'])
            })
            
        if task_title:
            assignees = [assignee_email] if assignee_email else []
            folder_obj['items'].append({
                'id': str(uuid.uuid4()),
                'name': task_title,
                'item_type': 'task',
                'content': {
                    'description': task_desc,
                    'estimated_hours': est_hours,
                    'priority': priority,
                    'impact': impact,
                    'risk': risk,
                    'due_date': due_date,
                    'assignees': assignees
                },
                'url': '',
                'order': len(folder_obj['items'])
            })
            
    return root_folders


class TemplateCSVImportView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, org_slug):
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)
            
        filename = file_obj.name.lower()
        try:
            import pandas as pd
        except ImportError:
            return Response({
                "error": "pandas and openpyxl libraries are required on the server to parse template files."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        try:
            if filename.endswith('.csv'):
                df = pd.read_csv(file_obj)
            elif filename.endswith(('.xls', '.xlsx')):
                df = pd.read_excel(file_obj)
            else:
                return Response({"error": "Unsupported file format. Please upload CSV or Excel."}, status=status.HTTP_400_BAD_REQUEST)

            # Sanitize: replace NaN/None with empty strings for object columns,
            # and with None for numeric columns, then convert to Python-native types
            # so Django's JSON serializer doesn't choke on numpy.nan / numpy.float64.
            import numpy as np

            def sanitize_value(val):
                """Convert numpy/pandas types to JSON-safe Python types."""
                if val is None:
                    return None
                if isinstance(val, float) and (np.isnan(val) or np.isinf(val)):
                    return None
                if isinstance(val, (np.integer,)):
                    return int(val)
                if isinstance(val, (np.floating,)):
                    return float(val)
                if isinstance(val, (np.bool_,)):
                    return bool(val)
                return val

            rows = []
            for _, row in df.iterrows():
                rows.append({col: sanitize_value(row[col]) for col in df.columns})

            folder_data = convert_rows_to_folders(df)
            
            goal_title = ""
            for row in rows:
                title = str(row.get('Goal_Title', '') or '').strip()
                if title and title.lower() != 'nan':
                    goal_title = title
                    break
                    
            return Response({
                "rows": rows,
                "folder_data": folder_data,
                "goal_title": goal_title
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({"error": f"Failed to parse file: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
