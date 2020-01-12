from django.contrib import admin
from job_time.manage_time.models import (
    Member,
    LineID,
    Attendance,
    Break,
    Salary,
)
# Register your models here.
admin.site.register(Member)
admin.site.register(LineID)
admin.site.register(Attendance)
admin.site.register(Break)
admin.site.register(Salary)