from os import path
from rest_framework.serializers import ModelSerializer, Serializer
from rest_framework import serializers
from django.db.models import Sum
from django.conf import settings
from rest_framework.exceptions import ValidationError
from django.contrib.auth.models import User
from job_time.manage_time.models import (
    Attendance,
    Break,
    Member,
    LineID,
)
from job_time.manage_time.mixins import (
    LineIDGetter,
    MemberGetter,
    AttendanceGetterMixin
)

class CacheLineIDSerializer(LineIDGetter, Serializer):
    def cache(self):
        userId = self.validated_data['line_id']
        line_id = LineID.objects.filter(text=userId).first()
        if line_id is None:
            return LineID.objects.create(text=userId)
        return line_id


class SorrySerializer(LineIDGetter, Serializer):
    def to_representation(self, data):
        return {'messages': [
            {
                'type': 'text',
                'text': '対応していないアクションです'
            },
        ]}


class MemberSerializer(ModelSerializer):
    class Meta:
        model = Member
        fields = [
            'name',
            'hourly_wage',
        ]
    

class FollowSerializer(LineIDGetter, ModelSerializer):
    class Meta:
        model = Member
        fields = []

    def create(self, validated_data):
        print('follow ')
        user = User.objects.create(
            username=validated_data['line_id']
        )
        print('userID', userId)
        return Member.objects.create(
            user=user,
            line_id=LineID.objects.filter(text=userId).first()
        )

    def to_representation(self, data):
        return {'messages': [
            {
                'type': 'template',
                'altText': 'This is template',
                'template': {
                    'type': 'buttons',
                    'text': '''
                    フォローありがとうございます、{}を作成しました!!
                    詳細情報を設定する場合は、以下のボタンを押してください
                    '''.format(self.validated_data['line_id']),
                    'actions': [
                        {
                            'type': 'uri',
                            'label': '設定',
                            'uri': path.join(settings.HOST_URL, 'profile')
                        }
                    ]
                }
            }
        ]}

class SalarySerializer(MemberGetter, Serializer):
    '''今月の給料を出力して返信'''    
    def save(self, **kwargs):
        pass

    def get_month_attendances(self):
        return Attendance.objects.filter(
            date__month=self.validated_data['date'].month
        )

    def get_attendant_days(self, attendances):
        attendances = attendances.order_by('clock_in_time')
        days = [
            (
                at.date.day,
                at.work_time.seconds // 3600
            ) for at in attendances
        ]
        if len(days) == 0:
            return ['今月の出勤日はありません']
        days_report = []
        total_work_hour = 0
        for day in days:
            days_report.append(
                '{}日: {:.1f}時間'.format(*day)
            )
            total_work_hour += day[1]
        days_report.append(
            '総労働時間: {:.1f}'.format(total_work_hour)
        )
        return days_report

    def get_month_total(self, attendances):
        if not attendances.exists():
            return 0
        attendant_month = attendances.first().date.month
        wage = self.member.hourly_wage
        total_work_time = attendances.aggregate(
            total_work_time=Sum('work_time')
        )['total_work_time']
        total_work_time = total_work_time if total_work_time is not None else 0
        total_salary = (total_work_time.seconds // 3600) * self.member.hourly_wage
        if attendances.filter(clock_out_time__isnull=True).exists():
            # 最新の出勤の退勤時刻が埋まっているかを確認
            raise ValidationError("未退勤の出勤があります")
        return total_salary
        

    def month_salary_report(self):
        text = '{padding} \n今月({date})の給与\n {padding}'.format(
            padding='-' * 5,
            date=self.validated_data['date'].strftime('%-Y/%-m/%-d')
        )
        month_attendances = self.get_month_attendances()
        print(month_attendances)
        text = [text] + self.get_attendant_days(month_attendances)
        text += [
            '-' * 20,
            '¥{:>25,.0f}'.format(
                self.get_month_total(month_attendances)
            )
        ]
        text += ['-' * 20]
        text += ['時給{:,}円で計算'.format(
            self.validated_data['member'].hourly_wage
        )]
        return "\n".join(text)

    def to_representation(self, data):
        return {'messages': [
            {
                'type': 'text',
                'text': self.month_salary_report()
            }
        ]}


class ClockInSerializer(MemberGetter, ModelSerializer):
    class Meta:
        model = Attendance
        fields = []
    
    def create(self, validated_data):
        print('clock in time')
        return Attendance.objects.create(
            clock_in_time=validated_data['time'],
            date=validated_data['date'],
            member=validated_data['member']
        )

    def to_representation(self, data):
        print('hoge')
        return {'messages': [{
                'type': 'text',
                'text': 'おはようございます'
            }
        ]}


class ClockOutSerializer(AttendanceGetterMixin, ModelSerializer):
    class Meta:
        model = Attendance
        fields = []
    
    def validate(self, event):
        data = super().validate(event)
        self.instance = data['attendance']
        return data

    def update(self, instance, validated_data):
        print('clock out')
        instance.clock_out_time = validated_data['time']
        instance.save()
        return instance

    def to_representation(self, data):
        return {'messages': [
            {
                'type': 'text',
                'text': 'お疲れ様でした'
            }
        ]}


class BreakStartSerializer(AttendanceGetterMixin, ModelSerializer):
    class Meta:
        model = Break
        fields = []
    
    def validate(self, event):
        data = super().validate(event)
        # TODO: 前に作られた休憩モデルの終了時刻がセットされていない場合はエラー
        if Break.objects.filter(
            attendance=data['attendance'],
            end_time__isnull=True
        ).exists():
            raise ValidationError("前回の休憩の終了が確認されていません")
        return data
    
    def create(self, validated_data):
        return Break.objects.create(
            attendance=validated_data['attendance'],
            start_time=validated_data['time']
        )

    def to_representation(self, data):
        return {'messages': [
            {
                'type': 'text',
                'text': 'いってらっしゃいませ'
            }
        ]}
        

class BreakEndSerializer(AttendanceGetterMixin, ModelSerializer):
    class Meta:
        model = Break
        fields = []
    
    def validate(self, event):
        data = super().validate(event)
        attendance = data['attendance']
        print(attendance.break_set.values('start_time'))
        self.instance = attendance.break_set.last()
        print(self.instance)
        if self.instance is None or self.instance.end_time is not None:
            raise ValidationError("本日の休憩開始が確認されていません")
        return data

    def update(self, instance, validated_data):
        instance.end_time = validated_data['time']
        instance.save()
        return instance

    def to_representation(self, data):
        return {'messages': [
            {
                'type': 'text',
                'text': 'おかえりなさいませ'
            }
        ]}
        