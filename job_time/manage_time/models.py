from django.db import models
from django.contrib.auth.models import User

class LineID(models.Model):
    text = models.CharField(max_length=128)

    def __str__(self):
        return '(line_id)=%s' % self.text

class Member(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    line_id = models.ForeignKey(LineID, on_delete=models.PROTECT)
    name = models.CharField(max_length=128, default='')
    hourly_wage = models.PositiveIntegerField(default=1000)
    def __str__(self):
        return '{}: {}'.format(self.name, self.line_id.text)

# Create your models here.
class Attendance(models.Model):
    member = models.ForeignKey(Member, on_delete=models.PROTECT)
    date = models.DateField(unique=True)
    clock_in_time = models.DateTimeField()
    clock_out_time = models.DateTimeField(null=True)
    def __str__(self):
        return self.date.strftime('%Y年%m月%d日出勤')
  
class Salary(models.Model):
    class Meta:
        verbose_name = verbose_name_plural = '日当'
    date = models.DateField(unique=True)
    money = models.PositiveIntegerField(verbose_name='金額')


class Break(models.Model):
    class Meata:
        ordering = ['-start_time']
    attendance = models.ForeignKey(Attendance, on_delete=models.PROTECT)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True)
    def __str__(self):
        return '{}　休憩 {}'.format(
            self.attendance.date.strftime('%Y年%m月%d日'),
            self.start_time.strftime('%H:%mから')
        )

