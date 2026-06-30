from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
import uuid
from django.utils import timezone
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    """Main User Table - Email based authentication"""
    username = None 
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    email = models.EmailField(unique=True) 
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(null=True, blank=True)
    phone = models.CharField(max_length=15, null=True, blank=True)
    
    city = models.CharField(max_length=100, blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    job_title = models.CharField(max_length=100, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    education = models.CharField(max_length=255, blank=True, null=True)
    
    setup_step = models.IntegerField(default=1)
    must_change_password = models.BooleanField(default=False)

    past_performance = models.PositiveIntegerField(default=80, help_text="Past performance score (0-100)")
    experience_score = models.PositiveIntegerField(default=80, help_text="Experience score (0-100)")
    efficiency_score = models.PositiveIntegerField(default=80, help_text="Default efficiency score (0-100)")
    availability_score = models.PositiveIntegerField(default=100, help_text="Default availability score (0-100)")
    current_workload_score = models.PositiveIntegerField(default=0, help_text="Default workload score (0-100)")

    def get_assigned_hours(self):
        active_tasks = self.assigned_tasks.exclude(status='done')
        total_hours = 0.0
        for task in active_tasks:
            if task.estimated_hours is not None and task.estimated_hours > 0:
                total_hours += float(task.estimated_hours)
            elif task.estimated_minutes is not None and task.estimated_minutes > 0:
                total_hours += task.estimated_minutes / 60.0
        return total_hours

    def get_efficiency(self):
        total = self.assigned_tasks.count()
        if total > 0:
            completed = self.assigned_tasks.filter(status='done').count()
            return (completed / total) * 100.0
        return float(self.efficiency_score)

    def get_availability(self):
        today = timezone.localdate()
        on_leave = self.leave_requests.filter(
            status='Approved',
            start_date__lte=today,
            end_date__gte=today
        ).exists()
        if on_leave:
            return 0.0
        return float(self.availability_score)

    def calculate_score(self):
        """
        Calculate and return the final Employee Score.
        """
        return float(self.experience_score)

    def calculate_fatigue(self):
        """
        Calculate and return the Fatigue Score.
        """
        return 0.0

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        db_table = 'user_table'

    def __str__(self):
        return self.email

class OTPVerification(models.Model):
    phone = models.CharField(max_length=255)
    otp = models.CharField(max_length=6)
    expires_at = models.DateTimeField()
    attempts = models.IntegerField(default=0)
    purpose = models.CharField(max_length=20, default='register')
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.expires_at

    class Meta:
        db_table = 'user_otpverification'
        ordering = ['-created_at']

class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reset_tokens')
    token = models.CharField(max_length=100, unique=True)
    otp = models.CharField(max_length=6, null=True, blank=True)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_passwordresettoken'
        ordering = ['-created_at']


class LeaveRequest(models.Model):
    LEAVE_TYPES = [
        ('Sick', 'Sick Leave'),
        ('Casual', 'Casual Leave'),
        ('Earned', 'Earned Leave'),
        ('WFH', 'Work From Home'),
        ('Half_Day', 'Half Day'),
        ('Comp_Off', 'Comp Off'),
        ('Optional', 'Optional Leave'),
        ('Maternity_Paternity', 'Maternity/Paternity Leave'),
        ('Annual', 'Annual Leave'),
        ('Unpaid', 'Unpaid Leave'),
    ]
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leave_requests')
    organization = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE, related_name='leave_requests', null=True, blank=True)
    leave_type = models.CharField(max_length=50, choices=LEAVE_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_leaves')
    
    # New Fields
    rejection_reason = models.TextField(blank=True, null=True)
    cancellation_reason = models.TextField(blank=True, null=True)
    number_of_days = models.FloatField(default=1.0)
    attachment = models.FileField(upload_to='leave_attachments/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_leaverequest'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.leave_type} ({self.start_date} to {self.end_date})"

class LeaveBalance(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leave_balances')
    organization = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE, related_name='leave_balances')
    leave_type = models.CharField(max_length=50, choices=LeaveRequest.LEAVE_TYPES)
    total_days = models.FloatField(default=0.0)
    used_days = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_leavebalance'
        unique_together = ('user', 'organization', 'leave_type')

    def remaining_days(self):
        return max(0.0, self.total_days - self.used_days)

    def __str__(self):
        return f"{self.user.email} - {self.leave_type} - {self.remaining_days()} remaining"

class UserWorkingSchedule(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='working_schedule')
    work_start_time = models.TimeField(default='10:00:00')
    work_end_time = models.TimeField(default='19:00:00')
    lunch_break_start = models.TimeField(default='13:00:00')
    lunch_break_end = models.TimeField(default='14:00:00')
    no_lunch_break = models.BooleanField(default=False)
    tea_break_start = models.TimeField(default='17:00:00')
    tea_break_end = models.TimeField(default='17:30:00')
    no_tea_break = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        from datetime import datetime, timedelta, time
        if self.work_start_time:
            dummy_date = datetime.today()
            
            def parse_time(val):
                if isinstance(val, str):
                    try: return time.fromisoformat(val)
                    except ValueError: pass
                return val

            w_start = parse_time(self.work_start_time)
            self.work_start_time = w_start
            
            w_end = parse_time(self.work_end_time) if self.work_end_time else None
            if not w_end:
                w_end_dt = datetime.combine(dummy_date, w_start) + timedelta(hours=9)
                w_end = w_end_dt.time()
            self.work_end_time = w_end
            
            self.lunch_break_start = parse_time(self.lunch_break_start)
            self.lunch_break_end = parse_time(self.lunch_break_end)
            self.tea_break_start = parse_time(self.tea_break_start)
            self.tea_break_end = parse_time(self.tea_break_end)
            
            w_start_dt = datetime.combine(dummy_date, self.work_start_time)
            w_end_dt = datetime.combine(dummy_date, self.work_end_time)
            if w_end_dt <= w_start_dt:
                w_end_dt += timedelta(days=1)
            
            def normalize_dt(t):
                dt = datetime.combine(dummy_date, t)
                if t < w_start:
                    dt += timedelta(days=1)
                return dt
                
            l_start_dt = normalize_dt(self.lunch_break_start)
            l_end_dt = normalize_dt(self.lunch_break_end)
            t_start_dt = normalize_dt(self.tea_break_start)
            t_end_dt = normalize_dt(self.tea_break_end)
            
            if (l_end_dt - l_start_dt).total_seconds() > 3600:
                l_end_dt = l_start_dt + timedelta(minutes=60)
            
            if (t_end_dt - t_start_dt).total_seconds() > 1800:
                t_end_dt = t_start_dt + timedelta(minutes=30)
                
            l_start_dt = max(w_start_dt, min(l_start_dt, w_end_dt))
            l_end_dt = max(w_start_dt, min(l_end_dt, w_end_dt))
            self.lunch_break_start = l_start_dt.time()
            self.lunch_break_end = l_end_dt.time()
            
            t_start_dt = max(w_start_dt, min(t_start_dt, w_end_dt))
            t_end_dt = max(w_start_dt, min(t_end_dt, w_end_dt))
            self.tea_break_start = t_start_dt.time()
            self.tea_break_end = t_end_dt.time()
            
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'user_working_schedule'

@receiver(post_save, sender=User)
def create_user_working_schedule(sender, instance, created, **kwargs):
    if created:
        UserWorkingSchedule.objects.get_or_create(user=instance)

@receiver(post_save, sender=UserWorkingSchedule)
def schedule_dynamic_reschedule_on_working_hours_change(sender, instance, **kwargs):
    if getattr(instance, '_skip_dynamic_reschedule', False):
        return
    from django.db import transaction
    def do_reschedule():
        from tasks.services.scheduler import SchedulerService
        SchedulerService.reschedule_user_future_tasks(instance.user_id)
    transaction.on_commit(do_reschedule)

@receiver(post_save, sender=LeaveRequest)
def schedule_dynamic_reschedule_on_leave_save(sender, instance, **kwargs):
    if instance.status in ['Approved', 'Cancelled']:
        from django.db import transaction
        def do_reschedule():
            from tasks.services.scheduler import SchedulerService
            SchedulerService.reschedule_user_future_tasks(instance.user_id)
        transaction.on_commit(do_reschedule)

@receiver(post_delete, sender=LeaveRequest)
def schedule_dynamic_reschedule_on_leave_delete(sender, instance, **kwargs):
    if instance.status == 'Approved':
        from django.db import transaction
        def do_reschedule():
            from tasks.services.scheduler import SchedulerService
            SchedulerService.reschedule_user_future_tasks(instance.user_id)
        transaction.on_commit(do_reschedule)
