from django.db import models

# Create your models here.
class Test(models.Model):
    name = models.CharField(max_length=255)  

class Study(models.Model):
    studyDisplayName = models.CharField(max_length=20)
    studyDesc = models.CharField(max_length=255)
    startDate = models.DateField()
    endDate = models.DateField()

class Cohort(models.Model):
    cohortDisplayName = models.CharField(max_length=20)
    cohortDesc = models.CharField(max_length=255)
    startDate = models.DateField()
    endDate = models.DateField()
    study = models.ForeignKey(Study, on_delete=models.CASCADE)
    
class Fed(models.Model):
    fedDisplayName = models.CharField(max_length=20)
    cohort = models.ForeignKey(Cohort, on_delete=models.CASCADE)
   
class Mouse(models.Model): 
    mouseDisplayName = models.CharField(max_length=20)
    genotype = models.CharField(max_length=10) 
    sex = models.IntegerField(default=0) # 1 for male, 2 for female 
    dob = models.DateField()
    fed = models.ForeignKey(Fed, on_delete=models.CASCADE)

class FedDataRaw(models.Model):
    actTimestamp = models.DateTimeField()
    deviceNumber = models.CharField(max_length=10)
    batteryVol = models.CharField(max_length=10)
    motorTurns = models.CharField(max_length=5)
    sessionType = models.CharField(max_length=20)
    event = models.IntegerField(default=0) # 1 for poke, 2 for pellet
    activePoke = models.IntegerField(default=0) # 1 for left, 2 for right
    leftPokeCount = models.IntegerField(default=0)
    rightPokeCount = models.IntegerField(default=0)
    pelletCount = models.IntegerField(default=0)
    retrievalTime = models.IntegerField(default=0)
    mouse = models.ForeignKey(Mouse, on_delete=models.CASCADE)

class FedDataByHour(models.Model):
    leftPokeCount = models.IntegerField(default=0)
    rightPokeCount = models.IntegerField(default=0)
    pelletCount = models.IntegerField(default=0)
    activePoke = models.IntegerField(default=0) # 1 for left, 2 for right
    pokeAcc = models.DecimalField(default=0.0, max_digits=7, decimal_places=6)
    startTime = models.DateTimeField()
    endTime = models.DateTimeField()
    numHour = models.IntegerField(default=0) #1-8
    fedDate = models.DateField()
    fedDaySinceCohortStart = models.IntegerField(default=0)
    mouse = models.ForeignKey(Mouse, on_delete=models.CASCADE)

class FedDataByDay(models.Model):
    leftPokeCount = models.IntegerField(default=0)
    rightPokeCount = models.IntegerField(default=0)
    pelletCount = models.IntegerField(default=0)
    activePoke = models.IntegerField(default=0) # 1 for left, 2 for right
    pokeAcc = models.DecimalField(default=0.0, max_digits=7, decimal_places=6)
    fedDate = models.DateField()
    fedDaySinceCohortStart = models.IntegerField(default=0)
    mouse = models.ForeignKey(Mouse, on_delete=models.CASCADE)

