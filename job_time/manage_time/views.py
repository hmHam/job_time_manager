import requests
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.db import IntegrityError
from rest_framework.views import APIView
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer

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
    MemberSerializer,
)
from job_time.manage_time.models import Member

@auth
def push(event, data, options={}, headers={}):
    data["to"] = event['source']['userId']
    print(data)
    URL = 'https://api.line.me/v2/bot/message/push'
    res = requests.post(URL, json=data, headers=headers)
    print(res.json())
    return Response({}, status=res.status_code)


class LineMessageWebhookMixin(object):
    def get_event(self):
        print(self.request.data)
        event = self.request.data['events'][0]
        self.cache_line_id(event)
        return event


    def cache_line_id(self, event):
        serializer = CacheLineIDSerializer(data=event)
        if serializer.is_valid():
            return serializer.cache()
        

class ProfileView(LineMessageWebhookMixin, APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'prof.html'

    def get(self, request):
        event = self.get_event()
        serializer = MemberSerializer(data=event)
        return Response({
            'serializer': serializer,
            'member': serializer.validated_data['member']
        })

    def post(self, request):
        event = self.get_event()
        serializer = MemberSerializer(data=event)
        if not serializer.is_valid():
            return Response({
                'serializer': serializer,
                'member': serializer.validated_data['member']
            })
        serializer.save()
        return push(event, )


class TimeManageAPIView(LineMessageWebhookMixin, APIView):
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

    def get_serializer(self, event):
        s = self.serializer_map.get(event['type'], SorrySerializer)
        if isinstance(s, dict):
            s = s['data'][event['postback']['data']]
        return s(data=event)

    def post(self, request, format=None):
        try:
            self.event = self.get_event()
            serializer = self.get_serializer(self.event)
            print(serializer)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return push(event, serializer.data)
        except ValidationError as e:
            print(e.detail)
            detail = e.detail['non_field_errors'][0] if 'non_field_errors' in e.detail else e.detail[0]
            return push(event, 
                {
                    'messages': [
                        {
                            'type': 'text',
                            'text': detail.title()
                        }
                    ]
                }
            )
        return Response({'detail': 'その他'})
    
    def handle_exception(self, exc):
        if isinstance(exc, IntegrityError):
            return push(self.event, str(exc))
        return super().handle_exception(exc)
        


