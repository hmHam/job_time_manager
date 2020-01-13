from django.db import models
from django.db.models import Sum
from django.contrib.auth.models import User
from django.db.models import DurationField, ExpressionWrapper, F


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

  
class Salary(models.Model):
    class Meta:
        verbose_name = verbose_name_plural = '日当'
    attendance = models.OneToOneField('Attendance', on_delete=models.CASCADE)
    money = models.FloatField(verbose_name='金額')


# Create your models here.
class Attendance(models.Model):
    class Meta:
        ordering = ['-clock_in_time']
    member = models.ForeignKey(Member, on_delete=models.PROTECT)
    date = models.DateField(unique=True)
    clock_in_time = models.DateTimeField()
    clock_out_time = models.DateTimeField(null=True)
    def __str__(self):
        return self.date.strftime('%Y年%m月%d日出勤')
    
    def get_break_total(self):
        total = self.break_set.annotate(
            break_time=ExpressionWrapper(
                F('end_time') - F('start_time'),
                output_field=DurationField()
            )
        ).aggregate(total=Sum('break_time'))['total']
        return total.seconds if total is not None else 0

    def get_work_time(self):
        # hourで計算
        brk_total_time = self.get_break_total()
        work_time = self.clock_out_time - self.clock_in_time
        work_time = work_time.seconds
        work_time -= brk_total_time
        # secondsなのでhourに変換
        return work_time / 3600
    
    def save(self, **kwargs):
        super().save(**kwargs)
        if self.clock_out_time is not None:
            # 終了時刻が入力された際は当日の給料を計算して保存
            work_time = self.get_work_time()
            related_salary = Salary.objects.filter(attendance=self).first()
            if related_salary is None:
                related_salary = Salary.objects.create(
                    attendance=self,
                    money=0
                )
            related_salary.money = self.member.hourly_wage * work_time
            related_salary.save()
        return self

class Break(models.Model):
    class Meata:
        ordering = ['-start_time']
    attendance = models.ForeignKey(Attendance, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True)
    
    def __str__(self):
        return '{}　休憩 {}'.format(
            self.attendance.date.strftime('%Y年%m月%d日'),
            self.start_time.strftime('%H:%mから')
        )

