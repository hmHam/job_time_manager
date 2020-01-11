from datetime import datetime
import requests
from rest_framework.views import APIView
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from django.contrib.auth.models import User
from job_time.auth import auth
from job_time.manage_time.models import Attendance, Break, Member, LineID

@auth
def push(event, data, headers={}):
    data["to"] = event['source']['userId']
    URL = 'https://api.line.me/v2/bot/message/push'
    res = requests.post(URL, json=data, headers=headers)
    print(res.json())
    return Response({}, status=res.status_code)


def get_time_stamp(event):
    return datetime.fromtimestamp(event['timestamp'] // 1000)
            
class TimeManageAPIView(APIView):
    def get(self, reqeust, format=None):
        return Response({})

    def cache_line_id(self, event):
        userId = event['source']['userId']
        line_id = LineID.objects.filter(text=userId).first()
        if line_id is None:
            return LineID.objects.create(text=userId)
        return line_id
        
    def post(self, request, format=None):
        event = self.request.data['events'][0]
        self.cache_line_id(event)
        if event['type'] == 'follow':
            return self.follow(event)
        elif event['type'] == 'postback':
            if event['postback']['data'] == 'clock_in':
                return self.clock_in(event)
            elif event['postback']['data'] == 'break_end':
                return self.break_end(event)
            elif event['postback']['data'] == 'clock_out':
                return self.clock_out(event)
            elif event['postback']['data'] == 'break_start':
                return self.break_start(event)
        return Response({})

    def follow(self, event):
        '''アカウントをフォローした際にユーザーを作成する'''
        userId = event['source']['userId']
        user = User.objects.create(username=userId)
        print('userID', userId)
        Member.objects.create(
            user=user,
            line_id=LineID.objects.filter(text=userId).first()
        )
        data = {
            "messages" : [
                {
                    'type': 'text',
                    'text': '%sを作成しました' % userId
                },
            ]
        }
        return push(event, data)

    def get_month_salary(self, event):
        '''現在の月での給料を取得'''
        pass

    def clock_in(self, event):
        '''出勤'''
        print(' call clock in')
        member = Member.objects.filter(
            line_id__text=event['source']['userId']
        ).first()
        clock_in_time = get_time_stamp(event)
        Attendance.objects.create(
            clock_in_time=clock_in_time,
            date=clock_in_time.date(),
            member=member
        )
        return push(
            event,
            {
                'messages': [
                    {
                        'type': 'text',
                        'text': 'おはようございます'
                    }
                ]
            }
        )

    def break_end(self, event):
        '''休憩終了'''
        print(' call break end')
        member = Member.objects.filter(
            line_id__text=event['source']['userId']
        ).first()
        break_end_time = get_time_stamp(event)
        at = Attendance.objects.filter(
            date=break_end_time.date(),
            member=member
        ).first()
        brk = at.break_set.first()
        brk.end_time = break_end_time
        brk.save()
        return push(
            event,
            {
                'messages': [
                    {
                        'type': 'text',
                        'text': 'おかえりなさいませ'
                    }
                ]
            }
        )
        

    def clock_out(self, event):
        '''退勤'''
        print(' call clock out')
        member = Member.objects.filter(
            line_id__text=event['source']['userId']
        ).first()
        clock_out_time = get_time_stamp(event)
        at = Attendance.objects.filter(
            date=clock_out_time.date(),
            member=member
        ).first()
        at.clock_out_time = clock_out_time
        at.save()
        return push(
            event,
            {
                'messages': [
                    {
                        'type': 'text',
                        'text': 'お疲れ様でした'
                    }
                ]
            }
        )

    def break_start(self, event):
        '''途中休憩開始'''
        print(' call break start')
        member = Member.objects.filter(
            line_id__text=event['source']['userId']
        ).first()
        break_start_time = get_time_stamp(event)
        at = Attendance.objects.filter(
            date=break_start_time.date(),
            member=member
        ).first()
        Break.objects.create(
            attendance=at,
            start_time=break_start_time
        )
        return push(
            event,
            {
                'messages': [
                    {
                        'type': 'text',
                        'text': 'いってらっしゃいませ'
                    }
                ]
            }
        )
