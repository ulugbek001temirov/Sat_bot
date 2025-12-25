# from django.contrib import admin
# from django.utils.html import format_html
# from .models import User, Test, Question, TestResult

# @admin.register(User)
# class UserAdmin(admin.ModelAdmin):
#     list_display = ['phone', 'first_name', 'last_name', 'telegram_id', 'registered_date']
#     search_fields = ['phone', 'first_name', 'last_name']
#     readonly_fields = ['registered_date']


# class QuestionInline(admin.TabularInline):
#     model = Question
#     extra = 1
#     fields = ['module', 'question_number', 'question_text', 'option_a', 'option_b', 
#               'option_c', 'option_d', 'correct_answer']


# @admin.register(Test)
# class TestAdmin(admin.ModelAdmin):
#     list_display = ['name', 'status_display', 'question_count_display', 'is_active', 'created_date']
#     list_filter = ['is_active', 'is_complete', 'created_date']
#     search_fields = ['name', 'description']
#     readonly_fields = ['is_complete', 'created_date', 'question_summary']
#     inlines = [QuestionInline]
    
#     def status_display(self, obj):
#         if obj.is_complete:
#             return format_html('<span style="color: green;">✅ Complete</span>')
#         return format_html('<span style="color: orange;">⚠️ Incomplete</span>')
#     status_display.short_description = 'Status'
    
#     def question_count_display(self, obj):
#         counts = obj.get_question_counts()
#         m1_color = "green" if counts['module1'] == 27 else "red"
#         m2_color = "green" if counts['module2'] == 27 else "red"
#         return format_html(
#             f'M1: <span style="color: {m1_color};">{counts["module1"]}/27</span> | M2: <span style="color: {m2_color};">{counts["module2"]}/27</span>'
#         )
#     question_count_display.short_description = 'Questions'
    
#     def question_summary(self, obj):
#         if obj.pk:
#             counts = obj.get_question_counts()
#             status = '✅ Test is complete and ready!' if obj.is_complete else '⚠️ Add more questions to complete the test'
#             return format_html(
#                 f'<div style="padding: 10px; background: #f0f0f0; border-radius: 5px;">'
#                 f'<strong>Question Summary:</strong><br>'
#                 f'Module 1: {counts["module1"]}/27 questions<br>'
#                 f'Module 2: {counts["module2"]}/27 questions<br>'
#                 f'Total: {counts["total"]}/54 questions<br><br>'
#                 f'<strong>Status:</strong> {status}'
#                 f'</div>'
#             )
#         return "Save the test first to see question summary"
#     question_summary.short_description = 'Summary'


# @admin.register(Question)
# class QuestionAdmin(admin.ModelAdmin):
#     list_display = ['test', 'module', 'question_number', 'correct_answer']
#     list_filter = ['test', 'module']
#     search_fields = ['question_text', 'test__name']
#     ordering = ['test', 'module', 'question_number']


# @admin.register(TestResult)
# class TestResultAdmin(admin.ModelAdmin):
#     list_display = ['user', 'test', 'estimated_score', 'module1_score', 'module2_score', 'test_date']
#     list_filter = ['test', 'test_date']
#     search_fields = ['user__first_name', 'user__last_name', 'user__phone']
#     readonly_fields = ['user', 'test', 'test_date', 'module1_correct', 'module1_total',
#                        'module2_correct', 'module2_total', 'estimated_score',
#                        'module1_time_taken', 'module2_time_taken']
    
#     def module1_score(self, obj):
#         return f"{obj.module1_correct}/{obj.module1_total}"
#     module1_score.short_description = 'Module 1'
    
#     def module2_score(self, obj):
#         return f"{obj.module2_correct}/{obj.module2_total}"
#     module2_score.short_description = 'Module 2'
from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import User, Test, Question, TestResult

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['phone', 'first_name', 'last_name', 'telegram_id', 'registered_date']
    search_fields = ['phone', 'first_name', 'last_name']
    readonly_fields = ['registered_date']


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    fields = ['module', 'question_number', 'question_text', 'image', 'option_a', 'option_b', 
              'option_c', 'option_d', 'correct_answer']


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ['name', 'status_display', 'question_count_display', 'is_active', 'created_date']
    list_filter = ['is_active', 'is_complete', 'created_date']
    search_fields = ['name', 'description']
    readonly_fields = ['is_complete', 'created_date', 'question_summary']
    inlines = [QuestionInline]
    fields = ['name', 'description', 'image', 'is_active']
    
    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        test = form.instance
        module1_count = test.questions.filter(module=1).count()
        module2_count = test.questions.filter(module=2).count()
        test.is_complete = module1_count == 27 and module2_count == 27
        test.save(update_fields=['is_complete'])
    
    def status_display(self, obj):
        counts = obj.get_question_counts()
        is_complete = counts['module1'] == 27 and counts['module2'] == 27
        if is_complete:
            return mark_safe('<span style="color: green;">✅ Complete</span>')
        return mark_safe('<span style="color: orange;">⚠️ Incomplete</span>')
    status_display.short_description = 'Status'
    def question_count_display(self, obj):
        counts = obj.get_question_counts()
        m1_color = "green" if counts['module1'] == 27 else "red"
        m2_color = "green" if counts['module2'] == 27 else "red"

        html = 'M1: <span style="color: {0};">{1}/27</span> | M2: <span style="color: {2};">{3}/27</span>'.format(
            m1_color, counts['module1'], m2_color, counts['module2']
        )
        
        return mark_safe(html)
    question_count_display.short_description = 'Questions'
    
    def question_summary(self, obj):
        if obj.pk:
            counts = obj.get_question_counts()
            is_complete = counts['module1'] == 27 and counts['module2'] == 27
            status_text = '✅ Test is complete and ready!' if is_complete else '⚠️ Add more questions to complete the test'
            
            summary_html = '''
                <div style="padding: 10px; background: #f0f0f0; border-radius: 5px;">
                    <strong>Question Summary:</strong><br>
                    Module 1: {0}/27 questions<br>
                    Module 2: {1}/27 questions<br>
                    Total: {2}/54 questions<br><br>
                    <strong>Status:</strong> {3}
                </div>
            '''.format(counts['module1'], counts['module2'], counts['total'], status_text)
            
            return mark_safe(summary_html)
        return "Save the test first to see question summary"
    question_summary.short_description = 'Summary'


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['test', 'module', 'question_number', 'correct_answer', 'has_image']
    list_filter = ['test', 'module']
    search_fields = ['question_text', 'test__name']
    ordering = ['test', 'module', 'question_number']
    fields = ['test', 'module', 'question_number', 'question_text', 'image', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_answer']
    
    def has_image(self, obj):
        return bool(obj.image)
    has_image.boolean = True
    has_image.short_description = 'Image'


@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display = ['user', 'test', 'estimated_score', 'module1_score', 'module2_score', 'test_date']
    list_filter = ['test', 'test_date']
    search_fields = ['user__first_name', 'user__last_name', 'user__phone']
    readonly_fields = ['user', 'test', 'test_date', 'module1_correct', 'module1_total',
                       'module2_correct', 'module2_total', 'estimated_score',
                       'module1_time_taken', 'module2_time_taken']
    
    def module1_score(self, obj):
        return f"{obj.module1_correct}/{obj.module1_total}"
    module1_score.short_description = 'Module 1'
    
    def module2_score(self, obj):
        return f"{obj.module2_correct}/{obj.module2_total}"
    module2_score.short_description = 'Module 2'
