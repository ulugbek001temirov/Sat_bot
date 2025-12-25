from django.db import models
from django.core.exceptions import ValidationError

class User(models.Model):
    phone = models.CharField(max_length=20, unique=True, primary_key=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    telegram_id = models.BigIntegerField(unique=True, null=True, blank=True)
    registered_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.phone})"


class Test(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='images/', blank=True, null=True)
    created_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_complete = models.BooleanField(default=False, editable=False)
    
    class Meta:
        verbose_name = 'Test'
        verbose_name_plural = 'Tests'
        ordering = ['-created_date']
    
    def __str__(self):
        status = "✅ Complete" if self.is_complete else "⚠️ Incomplete"
        return f"{self.name} {status}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
    
    def get_question_counts(self):
        module1_count = self.questions.filter(module=1).count()
        module2_count = self.questions.filter(module=2).count()
        return {
            'module1': module1_count,
            'module2': module2_count,
            'total': module1_count + module2_count
        }


class Question(models.Model):
    MODULE_CHOICES = [
        (1, 'Module 1'),
        (2, 'Module 2'),
    ]
    
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='questions')
    module = models.IntegerField(choices=MODULE_CHOICES)
    question_number = models.IntegerField()
    question_text = models.TextField()
    image = models.ImageField(upload_to='images/', blank=True, null=True)
    option_a = models.TextField()
    option_b = models.TextField()
    option_c = models.TextField()
    option_d = models.TextField()
    correct_answer = models.CharField(max_length=1, choices=[
        ('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')
    ])
    
    class Meta:
        verbose_name = 'Question'
        verbose_name_plural = 'Questions'
        ordering = ['test', 'module', 'question_number']
        unique_together = ['test', 'module', 'question_number']
    
    def __str__(self):
        return f"{self.test.name} - Module {self.module} - Q{self.question_number}"
    
    def clean(self):
        # Validate question numbers
        if self.module == 1 and not (1 <= self.question_number <= 27):
            raise ValidationError("Module 1 questions must be numbered 1-27")
        if self.module == 2 and not (1 <= self.question_number <= 27):
            raise ValidationError("Module 2 questions must be numbered 1-27")
        
        # Check if adding this question would exceed the limit
        if self.pk is None and self.test.pk is not None:  # New question on saved test
            existing_count = Question.objects.filter(
                test=self.test, 
                module=self.module
            ).count()
            if existing_count >= 27:
                raise ValidationError(f"Module {self.module} already has 27 questions")


class TestResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='test_results')
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='results')
    test_date = models.DateTimeField(auto_now_add=True)
    
    module1_correct = models.IntegerField()
    module1_total = models.IntegerField(default=27)
    module2_correct = models.IntegerField()
    module2_total = models.IntegerField(default=27)
    estimated_score = models.IntegerField()
    
    module1_time_taken = models.IntegerField(help_text="Time taken in seconds")
    module2_time_taken = models.IntegerField(help_text="Time taken in seconds")
    
    class Meta:
        verbose_name = 'Test Result'
        verbose_name_plural = 'Test Results'
        ordering = ['-test_date']
    
    def __str__(self):
        return f"{self.user} - {self.test.name} - Score: {self.estimated_score}"
