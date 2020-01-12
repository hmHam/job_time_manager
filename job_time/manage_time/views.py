import requests
from rest_framework.views import APIView
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from job_time.auth import auth
from job_time.manage_time.serializers import (
    CacheLineIDSerializer,
    FollowSerializer,
    ClockInSerializer,
    ClockOutSerializer,
    BreakStartSerializer,
    BreakEndSerializer,
    SorrySerializer,
    SalarySerializer,
)

@auth
def push(event, messages, options={}, headers={}):
    data = {}
    data['messages'] = messages
    data["to"] = event['source']['userId']
    print(data)
    URL = 'https://api.line.me/v2/bot/message/push'
    res = requests.post(URL, json=data, headers=headers)
    print(res.json())
    return Response({}, status=res.status_code)


class TimeManageAPIView(APIView):
    serializer_map = {
        'follow': FollowSerializer,
        'postback': {
            'data': {
                'clock_in': ClockInSerializer,
                'clock_out': ClockOutSerializer,
                'break_start': BreakStartSerializer,
                'break_end': BreakEndSerializer,
                'salary': SalarySerializer,
            }
        }
    }
    def cache_line_id(self, event):
        serializer = CacheLineIDSerializer(data=event)
        if serializer.is_valid():
            return serializer.cache()
        
    def get_serializer(self, event):
        s = self.serializer_map.get(event['type'], SorrySerializer)
        if isinstance(s, dict):
            s = s['data'][event['postback']['data']]
        return s(data=event)

    def post(self, request, format=None):
        try:
            event = self.request.data['events'][0]
            self.cache_line_id(event)
            serializer = self.get_serializer(event)\
            print(serializer)
            serializer.is_valid(raise_exception=True)
            return push(event, serializer.data)
        except ValidationError as e:
            print(e.detail)
            return push(event, [
                {
                    'type': 'text',
                    'text': str(e)
                }
            ])
        return Response({'detail': 'その他'})

