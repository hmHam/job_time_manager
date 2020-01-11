from django.db import models


# Create your models here.
class Attendance(models.Model):
    date = models.DateField(unique=True)
    clock_in_time = models.DateTimeField()
    clock_out_time = models.DateTimeField(null=True)
    

class Break(models.Model):
    class Meata:
        ordering = ['-start_time']
    attendance = models.ForeignKey(Attendance, on_delete=models.PROTECT)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True)

