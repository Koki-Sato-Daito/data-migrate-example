from django.db import models


class Model1(models.Model):
    attr1 = models.CharField(max_length=100)
    attr2 = models.CharField(max_length=100)


# class Model2(models.Model):
#     attr1 = models.CharField(max_length=100)
#     attr2 = models.CharField(max_length=100)