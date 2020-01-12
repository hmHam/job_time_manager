from datetime import datetime
from rest_framework.exceptions import ValidationError
from job_time.manage_time.models import Attendance, Member

def get_time_stamp(event):
    return datetime.fromtimestamp(event['timestamp'] // 1000)


class LineIDGetter(object):
    def to_internal_value(self, data):
        return data

    def validate(self, event):
        event_datetime = get_time_stamp(event)
        return {
            'line_id': self.initial_data['source']['userId'],
            'time': event_datetime,
            'date': event_datetime.date(),
        }


class MemberGetter(LineIDGetter):
    def validate(self, event):
        data = super().validate(event)
        data['member'] = Member.objects.filter(
            line_id__text=data['line_id']
        ).first()
        return data


class AttendanceGetterMixin(MemberGetter):
    def validate(self, event):
        data = super().validate(event)
        queryset = Attendance.objects.filter(
            date=data['date'],
            member=data['member']
        )
        if not queryset.exists():
            raise ValidationError("本日の出勤が確認されていません")
        data['attendance'] = queryset.first()
        if data['attendance'].clock_out_time is not None:
            raise ValidationError("本日はすでに退勤が記録されています")
        return data