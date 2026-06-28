from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()

from drf_spectacular.utils import extend_schema_field

from .models import UserWorkingSchedule

class UserWorkingScheduleSerializer(serializers.ModelSerializer):
    lunch_duration_minutes = serializers.SerializerMethodField()
    tea_duration_minutes = serializers.SerializerMethodField()

    class Meta:
        model = UserWorkingSchedule
        fields = [
            "work_start_time", "work_end_time", 
            "lunch_break_start", "lunch_break_end",
            "tea_break_start", "tea_break_end",
            "lunch_duration_minutes", "tea_duration_minutes"
        ]
        read_only_fields = []

    @extend_schema_field(serializers.IntegerField())
    def get_lunch_duration_minutes(self, obj):
        if obj.lunch_break_start and obj.lunch_break_end:
            from datetime import datetime
            dummy = datetime.today()
            diff = (datetime.combine(dummy, obj.lunch_break_end) - datetime.combine(dummy, obj.lunch_break_start)).total_seconds() / 60.0
            if diff < 0:
                diff += 1440
            return int(diff)
        return 60

    @extend_schema_field(serializers.IntegerField())
    def get_tea_duration_minutes(self, obj):
        if obj.tea_break_start and obj.tea_break_end:
            from datetime import datetime
            dummy = datetime.today()
            diff = (datetime.combine(dummy, obj.tea_break_end) - datetime.combine(dummy, obj.tea_break_start)).total_seconds() / 60.0
            if diff < 0:
                diff += 1440
            return int(diff)
        return 30

class UserSerializer(serializers.ModelSerializer):
    employee_score = serializers.SerializerMethodField()
    fatigue_score = serializers.SerializerMethodField()
    working_schedule = UserWorkingScheduleSerializer(read_only=False, required=False)

    class Meta:
        model = User
        fields = [
            "id", "email", "first_name", "last_name", "phone", "city", 
            "date_of_birth", "job_title", "department", 
            "profile_picture", "bio", "education", "setup_step",
            "experience_score", "availability_score", "current_workload_score",
            "employee_score", "fatigue_score", "working_schedule"
        ]
        read_only_fields = ["id", "setup_step", "email", "employee_score", "fatigue_score"]

    def to_internal_value(self, data):
        # Support multipart/form-data where working_schedule fields are flattened
        if hasattr(data, 'copy'):
            mutable_data = data.copy()
        else:
            mutable_data = dict(data)
            
        schedule_keys = [
            'work_start_time', 'work_end_time', 
            'lunch_break_start', 'lunch_break_end',
            'tea_break_start', 'tea_break_end',
            'lunch_duration_minutes', 'tea_duration_minutes'
        ]
        
        schedule_data = {}
        for key in schedule_keys:
            if key in mutable_data:
                schedule_data[key] = mutable_data.get(key)
                
        # Do not inject dictionary into QueryDict to avoid stringification issues
        # Remove flat keys from mutable_data so DRF doesn't complain
        for key in schedule_keys:
            if key in mutable_data:
                del mutable_data[key]
                
        validated_data = super().to_internal_value(mutable_data)
        
        # Attach the raw schedule_data explicitly for the update() method
        if schedule_data:
            validated_data['working_schedule'] = schedule_data
            
        return validated_data

    def validate(self, attrs):
        schedule_data = attrs.get('working_schedule')
        if schedule_data:
            from datetime import time, datetime, timedelta
            
            def parse_time(val):
                if isinstance(val, time): return val
                if isinstance(val, str):
                    try: return time.fromisoformat(val)
                    except ValueError: pass
                return None

            dummy_date = datetime.today()
            def to_dt(t):
                if not t: return None
                return datetime.combine(dummy_date, t)

            w_start = parse_time(schedule_data.get('work_start_time'))
            if not w_start and self.instance and hasattr(self.instance, 'working_schedule'):
                w_start = self.instance.working_schedule.work_start_time

            w_end = parse_time(schedule_data.get('work_end_time'))
            if not w_end and self.instance and hasattr(self.instance, 'working_schedule'):
                w_end = self.instance.working_schedule.work_end_time

            ls = parse_time(schedule_data.get('lunch_break_start'))
            if not ls and self.instance and hasattr(self.instance, 'working_schedule'):
                ls = self.instance.working_schedule.lunch_break_start

            le = parse_time(schedule_data.get('lunch_break_end'))
            if not le and self.instance and hasattr(self.instance, 'working_schedule'):
                le = self.instance.working_schedule.lunch_break_end

            ts = parse_time(schedule_data.get('tea_break_start'))
            if not ts and self.instance and hasattr(self.instance, 'working_schedule'):
                ts = self.instance.working_schedule.tea_break_start

            te = parse_time(schedule_data.get('tea_break_end'))
            if not te and self.instance and hasattr(self.instance, 'working_schedule'):
                te = self.instance.working_schedule.tea_break_end

            def get_dur(start, end):
                if not start or not end: return 0
                dt1 = to_dt(start)
                dt2 = to_dt(end)
                diff = (dt2 - dt1).total_seconds() / 60.0
                if diff < 0: diff += 1440
                return diff

            if ls and le:
                ldur = get_dur(ls, le)
                if ldur > 60:
                    raise serializers.ValidationError({"lunch_break_end": "Lunch break cannot exceed 60 minutes."})
                if ldur < 1:
                    raise serializers.ValidationError({"lunch_break_end": "Lunch break must be at least 1 minute."})
            
            if ts and te:
                tdur = get_dur(ts, te)
                if tdur > 30:
                    raise serializers.ValidationError({"tea_break_end": "Tea break cannot exceed 30 minutes."})
                if tdur < 1:
                    raise serializers.ValidationError({"tea_break_end": "Tea break must be at least 1 minute."})

            if ls and le and ts and te and w_start and w_end:
                def normalize(t, ref_start):
                    dt = to_dt(t)
                    ref = to_dt(ref_start)
                    if dt < ref:
                        dt += timedelta(days=1)
                    return dt

                l1 = normalize(ls, w_start)
                l2 = l1 + timedelta(minutes=get_dur(ls, le))
                t1 = normalize(ts, w_start)
                t2 = t1 + timedelta(minutes=get_dur(ts, te))

                w1 = to_dt(w_start)
                w2 = normalize(w_end, w_start)
                if w2 <= w1:
                    w2 += timedelta(days=1)

                if l1 < w1 or l2 > w2:
                    raise serializers.ValidationError({"lunch_break_start": "Lunch break must be within working hours."})
                if t1 < w1 or t2 > w2:
                    raise serializers.ValidationError({"tea_break_start": "Tea break must be within working hours."})

                if l1 < t2 and t1 < l2:
                    raise serializers.ValidationError({"tea_break_start": "Tea break cannot overlap with lunch break."})

        return super().validate(attrs)

    def update(self, instance, validated_data):
        schedule_data = validated_data.pop('working_schedule', None)
        
        # Update user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update nested working_schedule
        if schedule_data is not None:
            schedule, created = UserWorkingSchedule.objects.get_or_create(user=instance)
            
            needs_reschedule = False
            if not created:
                from datetime import time
                def parse_time(val):
                    if isinstance(val, time): return val
                    if isinstance(val, str):
                        try: return time.fromisoformat(val)
                        except ValueError: pass
                    return None
                
                for attr, value in schedule_data.items():
                    if attr in ['lunch_duration_minutes', 'tea_duration_minutes']:
                        continue
                    old_val = getattr(schedule, attr)
                    new_val = parse_time(value)
                    if old_val != new_val:
                        needs_reschedule = True
                        break
            else:
                needs_reschedule = True

            for attr, value in schedule_data.items():
                if attr in ['lunch_duration_minutes', 'tea_duration_minutes']:
                        continue
                setattr(schedule, attr, value)
            schedule._skip_dynamic_reschedule = True
            schedule.save()
            
        return instance

    @extend_schema_field(serializers.FloatField())
    def get_employee_score(self, obj):
        return obj.calculate_score()

    @extend_schema_field(serializers.FloatField())
    def get_fatigue_score(self, obj):
        return obj.calculate_fatigue()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["email", "password"]

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
        )
        return user

class ChangePasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    new_password = serializers.CharField(required=True)

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True)

class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

class RegisterRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(
        error_messages={
            'invalid': 'Please enter a valid email address',
            'required': 'Please enter a valid email address',
            'blank': 'Please enter a valid email address'
        }
    )
    password = serializers.CharField(write_only=True)

class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField()

class RequestEmailChangeSerializer(serializers.Serializer):
    new_email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate_new_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

class VerifyEmailChangeSerializer(serializers.Serializer):
    new_email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)


from .models import LeaveRequest

class LeaveRequestSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    approved_by_email = serializers.EmailField(source='approved_by.email', read_only=True)
    user_name = serializers.SerializerMethodField()
    approved_by_name = serializers.SerializerMethodField()

    class Meta:
        model = LeaveRequest
        fields = [
            'id', 'user', 'user_email', 'user_name',
            'organization', 'leave_type', 'start_date', 'end_date',
            'reason', 'status', 'approved_by', 'approved_by_email', 'approved_by_name',
            'rejection_reason', 'cancellation_reason', 'number_of_days', 'attachment',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'status', 'approved_by', 'created_at', 'updated_at', 'number_of_days']

    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.email

    def get_approved_by_name(self, obj):
        if obj.approved_by:
            return f"{obj.approved_by.first_name} {obj.approved_by.last_name}".strip() or obj.approved_by.email
        return None

    def validate(self, data):
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        # Validate start_date <= end_date
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError("Start date must be before or equal to end date.")

        # Overlapping leave check for the user
        request = self.context.get('request')
        user = request.user if request else None
        if user:
            overlapping = LeaveRequest.objects.filter(
                user=user,
                status__in=['Pending', 'Approved'],
                start_date__lte=end_date,
                end_date__gte=start_date
            )
            if self.instance:
                overlapping = overlapping.exclude(id=self.instance.id)
            if overlapping.exists():
                raise serializers.ValidationError("You already have a pending or approved leave request during this period.")
            
            # Calculate number_of_days
            from datetime import timedelta
            if start_date and end_date:
                # Basic days calculation (excluding weekends could be added here)
                days = (end_date - start_date).days + 1
                leave_type = data.get('leave_type')
                if leave_type == 'Half_Day':
                    days = 0.5
                data['number_of_days'] = float(days)

                # Balance check
                org = data.get('organization') or (self.instance.organization if self.instance else None)
                if org and leave_type not in ['Unpaid', 'Maternity_Paternity', 'WFH']:
                    from .models import LeaveBalance
                    # Auto-create a default 10 day balance if none exists
                    balance, created = LeaveBalance.objects.get_or_create(
                        user=user,
                        organization=org,
                        leave_type=leave_type,
                        defaults={'total_days': 10.0, 'used_days': 0.0}
                    )
                    if balance.remaining_days() < days:
                        raise serializers.ValidationError(f"Insufficient leave balance. You have {balance.remaining_days()} days remaining for {leave_type}.")

        return data

from .models import LeaveBalance

class LeaveBalanceSerializer(serializers.ModelSerializer):
    remaining_days = serializers.FloatField(read_only=True)
    leave_type_display = serializers.CharField(source='get_leave_type_display', read_only=True)

    class Meta:
        model = LeaveBalance
        fields = ['id', 'user', 'organization', 'leave_type', 'leave_type_display', 'total_days', 'used_days', 'remaining_days', 'updated_at']
        read_only_fields = ['id', 'remaining_days']
