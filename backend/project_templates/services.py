from django.shortcuts import get_object_or_404
from .models import ProjectTemplate, TemplateFolder, TemplateItem, GoalFolder, GoalItem
from organizations.models import Organization
from goals.models import Goals
from tasks.models import Task
from django.contrib.auth import get_user_model
import csv
import io
from django.utils.dateparse import parse_date

class TemplateService:
    @staticmethod
    def replace_placeholders(text, placeholders):
        if not text or not isinstance(text, str):
            return text
        for key, value in placeholders.items():
            placeholder_str = f"{{{key}}}"
            text = text.replace(placeholder_str, str(value))
        return text

    @staticmethod
    def replace_placeholders_recursive(data, placeholders):
        if isinstance(data, str):
            return TemplateService.replace_placeholders(data, placeholders)
        elif isinstance(data, dict):
            return {k: TemplateService.replace_placeholders_recursive(v, placeholders) for k, v in data.items()}
        elif isinstance(data, list):
            return [TemplateService.replace_placeholders_recursive(v, placeholders) for v in data]
        return data

    @staticmethod
    def apply_template_to_goal(template, goal_instance, placeholders=None, user=None):
        if placeholders is None:
            placeholders = {}
            
        User = get_user_model()
        created_goals = {goal_instance.title.lower(): goal_instance}

        users_to_schedule = set()

        def copy_folder(template_folder, target_goal, parent_goal_folder=None):
            folder_name = TemplateService.replace_placeholders(template_folder.name, placeholders)
            
            new_folder = GoalFolder.objects.create(
                goal=target_goal,
                parent=parent_goal_folder,
                name=folder_name,
                order=template_folder.order
            )
            
            for item in template_folder.items.all():
                item_name = TemplateService.replace_placeholders(item.name, placeholders)
                item_content = TemplateService.replace_placeholders_recursive(item.content, placeholders)
                item_url = TemplateService.replace_placeholders(item.url or '', placeholders)
                
                if item.item_type == 'task':
                    # Extract standard task attributes
                    task_desc = item_content.get('description', '')
                    estimated_hours = item_content.get('estimated_hours', None)
                    task_priority = item_content.get('priority', 'medium')
                    
                    # Extract new mapping fields
                    task_impact = item_content.get('impact')
                    try:
                        task_impact = int(task_impact) if task_impact else 5
                    except ValueError:
                        task_impact = 5
                        
                    task_risk = item_content.get('risk', 'medium')
                    if task_risk not in ['low', 'medium', 'high']:
                        task_risk = 'medium'
                        
                    task_due_date = item_content.get('due_date')
                    if task_due_date:
                        task_due_date = parse_date(task_due_date) if isinstance(task_due_date, str) else task_due_date
                    
                    # Handle assignee (single assignee ForeignKey)
                    assignees_emails = item_content.get('assignees', [])
                    assigned_user = None
                    for email in assignees_emails:
                        if email == 'owner' and target_goal.owner:
                            assigned_user = target_goal.owner
                            break
                        elif email == 'created_by' and user:
                            assigned_user = user
                            break
                        else:
                            member_user = User.objects.filter(email__iexact=email).first()
                            if not member_user:
                                from django.db.models import Q
                                member_user = User.objects.filter(
                                    Q(first_name__icontains=email) | 
                                    Q(last_name__icontains=email)
                                ).first()
                            if member_user:
                                assigned_user = member_user
                                break
                    
                    # Track users to trigger auto-scheduling later
                    if assigned_user:
                        users_to_schedule.add(assigned_user.id)
                    
                    # Create standard Task linked to the target Goal
                    task_instance = Task.objects.create(
                        organization=target_goal.organization,
                        goal=target_goal,
                        title=item_name,
                        description=task_desc,
                        priority=task_priority,
                        impact=task_impact,
                        risk=task_risk,
                        due_date=task_due_date,
                        estimated_hours=estimated_hours,
                        status='todo',
                        created_by=user,
                        assignee=assigned_user,
                        schedule_status='QUEUED' if assigned_user else 'QUEUED'  # Will be queued for processing
                    )
                    
                    # Create GoalItem of type 'task' referencing the created task_id
                    GoalItem.objects.create(
                        folder=new_folder,
                        item_type='task',
                        name=item_name,
                        content={'task_id': str(task_instance.id)},
                        order=item.order
                    )
                else:
                    GoalItem.objects.create(
                        folder=new_folder,
                        item_type=item.item_type,
                        name=item_name,
                        content=item_content,
                        url=item_url,
                        order=item.order
                    )
                
            for sub in template_folder.subfolders.all():
                copy_folder(sub, target_goal, new_folder)
                
        root_folders = template.folders.filter(parent__isnull=True)
        for rf in root_folders:
            folder_goal_title = getattr(rf, 'goal_title', '')
            if folder_goal_title:
                folder_goal_title_resolved = TemplateService.replace_placeholders(folder_goal_title, placeholders).strip()
            else:
                folder_goal_title_resolved = ""

            if folder_goal_title_resolved:
                target_key = folder_goal_title_resolved.lower()
                if target_key in created_goals:
                    target_goal = created_goals[target_key]
                else:
                    existing_goal = Goals.objects.filter(
                        organization=goal_instance.organization,
                        title=folder_goal_title_resolved
                    ).first()
                    if existing_goal:
                        if existing_goal.is_deleted:
                            existing_goal.restore()
                        target_goal = existing_goal
                    else:
                        target_goal = Goals.objects.create(
                            organization=goal_instance.organization,
                            title=folder_goal_title_resolved,
                            description=f"Imported from template: {template.name}",
                            owner=goal_instance.owner,
                            created_by=goal_instance.created_by,
                            due_date=goal_instance.due_date,
                            priority=goal_instance.priority,
                            timeframe=goal_instance.timeframe,
                            template_type='custom'
                        )
                    created_goals[target_key] = target_goal
            else:
                target_goal = goal_instance

            copy_folder(rf, target_goal)
            
        # Automatically trigger scheduling for any user who was assigned a task
        if users_to_schedule:
            from tasks.services.scheduler import schedule_tasks_for_assignee
            for user_id in users_to_schedule:
                schedule_tasks_for_assignee(assignee_id=user_id, org_id=goal_instance.organization.id)

    @staticmethod
    def create_template_from_goal(goal_instance, org, template_name, user):
        template = ProjectTemplate.objects.create(
            organization=org,
            name=template_name,
            created_by=user
        )
        
        def copy_to_template(goal_folder, parent_template_folder=None):
            new_folder = TemplateFolder.objects.create(
                template=template,
                parent=parent_template_folder,
                name=goal_folder.name,
                order=goal_folder.order
            )
            for item in goal_folder.items.all():
                TemplateItem.objects.create(
                    folder=new_folder,
                    item_type=item.item_type,
                    name=item.name,
                    content=item.content,
                    url=item.url,
                    order=item.order
                )
            for sub in goal_folder.subfolders.all():
                copy_to_template(sub, new_folder)
                
        root_goal_folders = goal_instance.folders.filter(parent__isnull=True)
        for rgf in root_goal_folders:
            copy_to_template(rgf)
            
        return template

    @staticmethod
    def bulk_import_csv(org, file_obj, user):
        csv_file = io.StringIO(file_obj.read().decode('utf-8-sig'))
        reader = csv.DictReader(csv_file)
        
        goals_created = 0
        tasks_created = 0
        created_goals = {}
        users_to_schedule = set()
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        for row in reader:
            item_type = row.get('Type', '').strip().lower()
            title = row.get('Title', '').strip()
            desc = row.get('Description', '').strip()
            parent_title = row.get('Parent_Goal_Title', '').strip()
            start_date_raw = row.get('Start_Date', '').strip()
            due_date_raw = row.get('Due_Date', '').strip()
            priority = row.get('Priority', 'medium').strip().lower()
            
            if not title:
                continue
                
            start_date = parse_date(start_date_raw) if start_date_raw else None
            due_date = parse_date(due_date_raw) if due_date_raw else None
            
            if priority not in ['low', 'medium', 'high']:
                priority = 'medium'

            # Parse Impact and Risk fields (required)
            impact_raw = row.get('Impact', '').strip().lower()
            risk_raw = row.get('Risk', '').strip().lower()
            impact_map = {'high': 10, 'medium': 5, 'low': 1}
            impact = impact_map.get(impact_raw, 5)
            risk = risk_raw if risk_raw in ['low', 'medium', 'high'] else 'medium'            
            if item_type == 'goal':
                goal = Goals.objects.create(
                    organization=org,
                    title=title,
                    description=desc,
                    owner=user,
                    created_by=user,
                    start_date=start_date,
                    due_date=due_date,
                    priority=priority
                )
                created_goals[title] = goal
                goals_created += 1
            elif item_type == 'task':
                goal_obj = created_goals.get(parent_title)
                if not goal_obj and parent_title:
                    goal_obj = Goals.objects.filter(organization=org, title=parent_title).first()
                    
                # Validate required Impact and Risk fields
                if not impact_raw or not risk_raw:
                    raise ValueError('Impact and Risk columns are required for each task.')
                
                # Robust assignee parsing (handle "Assignee_Email", "Assignee Email", etc.)
                assignee_email = ''
                for k, v in row.items():
                    if k and k.strip().lower().replace('_', ' ') in ['assignee email', 'assignee', 'email']:
                        assignee_email = v.strip()
                        break

                assignee = None
                if assignee_email:
                    assignee = User.objects.filter(email__iexact=assignee_email).first()
                    if not assignee:
                        from django.db.models import Q
                        assignee = User.objects.filter(
                            Q(first_name__icontains=assignee_email) | 
                            Q(last_name__icontains=assignee_email)
                        ).first()

                est_hours_val = row.get('Est_Hours', '').strip()
                est_hours = None
                if est_hours_val:
                    try:
                        est_hours = float(est_hours_val)
                    except ValueError:
                        pass

                task = Task.objects.create(
                    organization=org,
                    title=title,
                    description=desc,
                    goal=goal_obj,
                    created_by=user,
                    start_date=start_date,
                    due_date=due_date,
                    priority=priority,
                    impact=impact,
                    risk=risk,
                    assignee=assignee,
                    estimated_hours=est_hours,
                    schedule_status='QUEUED',
                    visibility_type='organization'
                )
                if assignee:
                    users_to_schedule.add(assignee.id)
                    
                tasks_created += 1
                
        if users_to_schedule:
            from tasks.services.scheduler import schedule_tasks_for_assignee
            for user_id in users_to_schedule:
                schedule_tasks_for_assignee(assignee_id=user_id, org_id=org.id)
                
        return goals_created, tasks_created
