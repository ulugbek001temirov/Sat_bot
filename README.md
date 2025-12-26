SETUP INSTRUCTIONS:
1. first of create venv:
    python -m venv venv
    venv/Scripts/activate 

2. install all important libraries:
    pip install -r requirements.txt
   
3. Create .env and add these 2:
    TELEGRAM_BOT_TOKEN="paste there"
    SECRET_KEY="paste there"
4. Add your SECRET_KEY and your BOT_TOKEN in .env:
    
5. Run Migrations:
   python manage.py makemigrations
   python manage.py migrate

6. Create Superuser:
   python manage.py createsuperuser

7. Run Django Server (in one terminal):
   python manage.py runserver

8. Access Admin Panel:
   http://localhost:8000/admin
   - Login with superuser credentials
   - Add tests and questions

9. Run but (in another one teminal):
    python run_bot.py

ADMIN PANEL WORKFLOW:

1. Add New Test:
   - Go to Tests section
   - Click "Add Test"
   - Enter name and description
   - Save

2. Add Questions:
   - Click on the test
   - Use inline forms or add questions separately
   - Must add exactly 27 questions for Module 1
   - Must add exactly 27 questions for Module 2
   - Test automatically becomes "Complete" when all 54 questions are added

3. Manage Tests:
   - Mark tests as active/inactive
   - View question counts
   - See completion status


