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
    ProfileRedirectSerializer,
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
        

class ProfileView(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'prof.html'

    def get_member(self):
        return Member.objects.filter(
            line_id__text=self.request.query_params['line_id']
        ).first()

    def get(self, request):
        member = self.get_member()
        serializer = MemberSerializer(member)
        return Response({
            'serializer': serializer,
            'member': member
        })

    def post(self, request):
        member = self.get_member()
        serializer = MemberSerializer(member, data=request.data)
        if not serializer.is_valid():
            return Response({
                'serializer': serializer,
                'member': serializer.validated_data['member']
            })
        serializer.save()
        return push(event, serializer.data)


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
                'profile_redirect': ProfileRedirectSerializer
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
            return push(self.event, serializer.data)
        except ValidationError as e:
            print(e.detail)
            detail = e.detail['non_field_errors'][0] if 'non_field_errors' in e.detail else e.detail[0]
            return push(self.event, 
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
            return push(self.event,                 {
                'messages': [
                    {
                        'type': 'text',
                        'text': str(exc)
                    }
                ]
            })
        return super().handle_exception(exc)
        


