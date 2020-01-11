from rest_framework.views import APIView
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from django.contrib.auth.models import User

# Create your views here.


class TimeManageAPIView(APIView):
    def get(self, reqeust, format=None):
        return Response({})

    def post(self, request, format=None):
        event_type = self.request.data['type']
        print(request.data)
        if event_type == 'follow':
            return self.follow(request.data)
        # elif event_type == 'postback':
        #     print(request.data)
        return Response({})

    def follow(self, data):
        '''アカウントをフォローした際にユーザーを作成する'''
        pass

    def clock_in(self, data):
        '''出勤'''
        pass

    def temporary_colock_in(self, data):
        '''途中休憩後、再出勤'''
        pass

    def clock_out(self, data):
        '''退勤'''
        pass

    def temporary_colock_out(self, data):
        '''途中休憩'''
        pass
