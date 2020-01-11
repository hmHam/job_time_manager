from django.contrib import admin
from job_time.manage_time.models import (
    Member,
    LineID,
    Attendance,
    Break
)
# Register your models here.
admin.site.register(Member)
admin.site.register(LineID)
admin.site.register(Attendance)
admin.site.register(Break)