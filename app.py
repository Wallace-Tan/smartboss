import firebase_admin
from firebase_admin import credentials, db
from flask import Flask, request, session, redirect, url_for, render_template, jsonify, send_file
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
from dotenv import load_dotenv
import os
import google.generativeai as genai
from gemini_model import ai_prediction, startup_prompt, startup_refinement_prompt, marketing_simulation_prompt, marketing_refinement_prompt
from datetime import datetime
import time
import random

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)  # Generates a secure random key

# Path to your Firebase service account key JSON file
cred_path = 'Google SmartBoss/firebase_credentials.json'  # Replace with your actual path

# Your Firebase Database URL (Correct Format)
database_url = 'https://smartboss-c0021-default-rtdb.asia-southeast1.firebasedatabase.app/'  # Replace with your actual URL

# Initialize db_ref outside the conditional blocks
db_ref = None

# Initialize Firebase Admin SDK if not already initialized
if not firebase_admin._apps:
    try:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred, {
            'databaseURL': database_url
        })
        db_ref = db.reference('/')
        print("Firebase Admin SDK initialized successfully.")
    except Exception as e:
        print(f"Error initializing Firebase Admin SDK: {e}")
else:
    db_ref = db.reference('/')
    print("Firebase Admin SDK already initialized.")

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        users_ref = db_ref.child('users')
        user_data = users_ref.order_by_child('email').equal_to(email).get()
        
        if user_data:
            user_id, user_info = list(user_data.items())[0]  # Get the first matched user
            stored_password = user_info.get('password', '')

            # Check password
            if check_password_hash(stored_password, password):
                session['user_id'] = user_id  # Store user ID in session
                return redirect(url_for('profile'))  # Redirect to dashboard
            else:
                return render_template('login.html', error="Invalid password.")
        else:
            return render_template('login.html', error="User not found.")

    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        newpassword = request.form['confirm_password']
        company_name = request.form['company_name']
        
        # Check if any required field is empty
        if not email or not password or not newpassword or not company_name:
            return render_template('signup.html', error="All fields are required.")

        # Check if password and newpassword match
        if password != newpassword:
            return render_template('signup.html', error="Passwords do not match.")

        if db_ref:
            users_ref = db_ref.child('users')
            # Check if the email already exists
            existing_user = users_ref.order_by_child('email').equal_to(email).get()
            if existing_user:
                return render_template('signup.html', error="email already exists.")

            hashed_password = generate_password_hash(password)
            user_data = {
                'email': email,
                'password': hashed_password,
                'company_name': company_name,
                'confirm_password': password  # Store the hashed password again for confirmation
            }
            users_ref.push(user_data)
            return redirect(url_for('login'))  # Redirect to login after successful registration
        else:
            return render_template('signup.html', error="Database error. Cannot signup user.")
    
    return render_template('signup.html')


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    users_ref = db_ref.child('users').child(user_id)

    if request.method == 'POST':
        age = request.form['age']
        city = request.form['city']

        details = {
            "age": age,
            "city": city
        }
        users_ref.child('details').set(details)

    # Retrieve user details
    user_details = users_ref.get()
    print(f"User details retrieved: {user_details}")

    details_exist = user_details is not None and 'details' in user_details

    return render_template('dashboard.html', user_details=user_details, details_exist=details_exist)

@app.route("/profile", methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    users_ref = db_ref.child('users').child(user_id)
       
    if request.method == 'POST':
        mission = request.form.get('mission')
        vision = request.form.get('vision')
        company_description = request.form.get('company-description')
        company_size = request.form.get('company-size')
        industry = request.form.get('industry')
        city = request.form.get('city')
        postal_code = request.form.get('postal_code')
        state = request.form.get('state')

        established_year = request.form.get('established-year')
        company_website = request.form.get('company-website')
        company_email = request.form.get('company-email')
        company_phone = request.form.get('company-phone')
        business_type = request.form.get('business-type')
        company_status = request.form.get('company-status')

        social_media = {
            'linkedin': request.form.get('linkedin'), # Updated names
            'twitter': request.form.get('twitter'),   # Updated names
            'facebook': request.form.get('facebook') # Updated names
        }

        core_products = request.form.get('core-products') # Updated name
        target_audience = request.form.get('target-audience') # Updated name
        revenue_model = request.form.get('revenue-model')
        industry_keywords = request.form.get('industry-keywords') # Updated name

        profile_data = {
            'mission': mission,
            'vision': vision,
            'company_description': company_description,
            'company_size': company_size,
            'industry': industry,
            'city': city,
            'postal_code': postal_code,
            'state': state,
            'established_year': established_year,
            'company_website': company_website,
            'company_email': company_email,
            'company_phone': company_phone,
            'business_type': business_type,
            'company_status': company_status,
            'social_media': social_media,
            'core_products': core_products,
            'target_audience': target_audience,
            'revenue_model': revenue_model,
            'industry_keywords': industry_keywords
        }

        users_ref.child('company_profile').set(profile_data)
        message = "Profile updated successfully!"

        # Reload the data after saving
        user_details = users_ref.get()
        company_profile = user_details.get('company_profile', {})

        return render_template("profile.html", company_profile=company_profile, user_details=user_details, message=message)

    user_details = users_ref.get()
    company_profile = user_details.get('company_profile', {})

    return render_template("profile.html", company_profile=company_profile, user_details=user_details)

@app.route('/startup', methods=['GET', 'POST'])
def startup():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    users_ref = db_ref.child('users').child(user_id)

    if request.method == 'POST':
        # Generate a unique ID
        timestamp = str(int(time.time() * 1000))
        random_part = ''.join(random.choices('abcdef0123456789', k=10))
        uniqueId = f"{timestamp}_{random_part}"

        # Retrieve form data
        form_data = {k: request.form.get(k) for k in [
            "industry", "company_size", "startup_idea"
        ]}

        # Convert form data to a structured string input
        user_input = "\n".join([f"{k}: {v}" for k, v in form_data.items() if v])

        # Generate AI prediction
        prediction_result = startup_prompt.generate_response(user_input)
        prediction_paragraphs = [p.strip() for p in prediction_result.split('\n') if p.strip()] # Split into paragraphs and remove empty ones

        print(prediction_paragraphs)
        
        startup_prediction_description = {
            "industry": request.form.get('industry'),
            "company_size": request.form.get('company_size'),
            "startup_idea": request.form.get('startup_idea'),
            "prediction_result": prediction_paragraphs,
            "conversation": [] # Initialize conversation history
        }

        users_ref.child('startup_prediction').child(uniqueId).set(startup_prediction_description)

        return render_template('startup_result.html', prediction_paragraphs=prediction_paragraphs, form_data=form_data, uniqueId=uniqueId)

    return render_template('startup.html')

@app.route('/startup_submit_comment', methods=['POST'])
def startup_submit_comment():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    user_id = session['user_id']
    unique_id = request.form.get('uniqueId')
    comment_text = request.form.get('comment')

    if not unique_id or not comment_text:
        return jsonify({'error': 'Missing data'}), 400

    users_ref = db_ref.child('users').child(user_id).child('startup_prediction').child(unique_id)
    previous_data = users_ref.get()

    if not previous_data:
        return jsonify({'error': 'Prediction not found'}), 404

    previous_input = "\n".join([f"{k}: {v}" for k, v in previous_data.items() if k in ["industry", "company_size", "startup_idea"]])
    previous_prediction = "\n".join(previous_data.get('prediction_result', []))
    # conversation_history = previous_data.get('conversation', []) # Retrieve previous conversation

    # Construct input for Gemini with previous context and new comment
    prompt_input = f"""Previous Input:\n{previous_input}\n\nPrevious AI Thoughts:\n{previous_prediction}\n\nUser Question/Comment:\n\n{comment_text}\n\nAI Response:"""

    # Generate AI response using a prompt designed for iterative refinement and responding to user
    ai_response = startup_refinement_prompt.generate_response(prompt_input)
    ai_response_paragraphs = [p.strip() for p in ai_response.split('\n') if p.strip()]

    existing_predictions = previous_data.get('prediction_result', [])
    combined_predictions = existing_predictions + ai_response_paragraphs
    users_ref.update({'prediction_result': combined_predictions})

    return jsonify({'success': True, 'ai_response': ai_response_paragraphs})
    
@app.route("/startup_summary")
def startup_summary():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    unique_id = request.args.get('uniqueId')

    users_ref = db_ref.child('users').child(user_id)
    users_starup_data = users_ref.child('startup_prediction').child(unique_id).get()
    users_startup_prediction_data = users_ref.child('startup_prediction').child(unique_id).child("prediction_result").get()

    industry = None
    company_size = None
    product_service = None
    problem_solved = None
    target_audience = None
    unique_selling_proposition = None
    market_considerations = None

    if isinstance(users_startup_prediction_data, list):
        for i, item in enumerate(users_startup_prediction_data):
            stripped_item = item.strip()
            if stripped_item == '- Industry:'.strip():
                if i + 1 < len(users_startup_prediction_data):
                    industry = users_startup_prediction_data[i + 1]
            elif stripped_item == '- Company Size:'.strip():
                if i + 1 < len(users_startup_prediction_data):
                    company_size = users_startup_prediction_data[i + 1]
            elif stripped_item == '- Product/Service:'.strip():
                if i + 1 < len(users_startup_prediction_data):
                    product_service = users_startup_prediction_data[i + 1]
            elif stripped_item == '- Problem Solved:'.strip():
                if i + 1 < len(users_startup_prediction_data):
                    problem_solved = users_startup_prediction_data[i + 1]
            elif stripped_item == '- Target Audience:'.strip():
                if i + 1 < len(users_startup_prediction_data):
                    target_audience = users_startup_prediction_data[i + 1]
            elif stripped_item == '- Unique Selling Proposition:'.strip():
                if i + 1 < len(users_startup_prediction_data):
                    unique_selling_proposition = users_startup_prediction_data[i + 1]
            elif stripped_item == '- General Market Considerations:'.strip():
                if i + 1 < len(users_startup_prediction_data):
                    market_considerations = users_startup_prediction_data[i + 1]

    return render_template('startup_summary.html', 
                            startup_data=users_starup_data,
                            startup_prediction_data=users_startup_prediction_data,
                            industry=industry,
                            company_size=company_size,
                            product_service=product_service,
                            problem_solved=problem_solved,
                            target_audience=target_audience,
                            unique_selling_proposition=unique_selling_proposition,
                            market_considerations=market_considerations)


@app.route("/history")
def history():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    users_ref = db_ref.child('users').child(user_id)
    users_startup_history_ref = users_ref.child('startup_prediction').get()
    users_prediction_history_ref = users_ref.child('prediction_summary').get()

    return render_template('history.html', startup_history=users_startup_history_ref, prediction_history=users_prediction_history_ref)

@app.route("/simulation", methods=['GET', 'POST'])
def simulation():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        choice = request.form.get('choice')
        return redirect(url_for('simulation_input', choice=choice))

    return render_template("simulation.html")

@app.route("/simulation_input", methods=['GET', 'POST'])
def simulation_input():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    users_ref = db_ref.child('users').child(user_id)

    choice = request.args.get('choice')

    if request.method == 'POST':

        timestamp = str(int(time.time() * 1000))
        random_part = ''.join(random.choices('abcdef0123456789', k=10))
        uniqueId = f"{timestamp}_{random_part}"

        if choice == 'marketing':
            form_data = {k: request.form.get(k) for k in [
                "industry", "company_size", "startup_idea",
                "total_budget", "average_customer_value", "conversion_rate",
                "target_specificity", "paid_ads_allocation", "brand_awareness",
                "marketing_description"
            ]}
            user_input = "\n".join([f"{k}: {v}" for k, v in form_data.items() if v])
            prediction_result = marketing_simulation_prompt.generate_response(user_input)
            prediction_paragraphs = [p.strip() for p in prediction_result.split('\n') if p.strip()]

            users_ref.child('plan_simulation_summary').child("marketing").child(uniqueId).set(form_data)

            session['result_prediction_paragraphs'] = prediction_paragraphs
            session['user_input'] = user_input
            session['result_uniqueId'] = uniqueId

        return redirect(url_for('simulation_plan'))
    return render_template("simulation_input.html", choice=choice)

@app.route("/simulation_plan")
def simulation_plan():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    users_ref = db_ref.child('users').child(user_id)

    prediction_paragraphs = session['result_prediction_paragraphs']
    user_input = session['user_input']
    uniqueId = session['result_uniqueId']

    return render_template("simulation_plan.html")

@app.route('/marketing_submit_comment', methods=['POST'])
def marketing_submit_comment():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    user_id = session['user_id']
    unique_id = request.form.get('uniqueId')
    comment_text = request.form.get('comment')

    if not unique_id or not comment_text:
        return jsonify({'error': 'Missing data'}), 400

    users_ref = db_ref.child('users').child(user_id).child('plan_simulation_summary').child('marketing')
    previous_data = users_ref.get()

    if not previous_data:
        return jsonify({'error': 'Marketing simulation not found'}), 404

    # Optional: get previous conversation history
    conversation_history = previous_data.get('conversation', [])

    # Prepare previous input (only showing relevant keys)
    relevant_keys = [
        "industry", "total_budget", "average_customer_value",
        "conversion_rate", "target_specificity", "paid_ads_allocation",
        "brand_awareness", "marketing_description"
    ]
    previous_input = "\n".join([f"{k}: {v}" for k, v in previous_data.items() if k in relevant_keys])

    previous_prediction = "\n".join(previous_data.get('prediction_result', []))

    # Construct prompt for Gemini or AI model
    prompt_input = f"""Previous Marketing Input:\n{previous_input}\n\nPrevious AI Insights:\n{previous_prediction}\n\nConversation History:\n{' '.join(conversation_history)}\n\nUser Question/Comment:\n{comment_text}\n\nAI Response:"""

    # Generate AI response
    ai_response = marketing_refinement_prompt.generate_response(prompt_input)
    ai_response_paragraphs = [p.strip() for p in ai_response.split('\n') if p.strip()]

    # Update conversation history
    updated_conversation = conversation_history + [f"You: {comment_text}", f"AI: {ai_response}"]

    # Save back to Firebase
    users_ref.child(unique_id).update({
        'prediction_result': ai_response_paragraphs,
        'conversation': updated_conversation
    })

    return jsonify({'success': True, 'ai_response': ai_response_paragraphs})

    
@app.route("/simulation_result")
def simulation_result():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    prediction_paragraphs = session['result_prediction_paragraphs']
    user_input = session['user_input']
    uniqueId = session['result_uniqueId']

    return render_template(
        'simulation_result.html',
        prediction_paragraphs=prediction_paragraphs,
        user_input=user_input,
        uniqueId=uniqueId
    )
                            
@app.route("/simulation_summary")
def simulation_summary():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    users_ref = db_ref.child('users').child(user_id)
    return render_template('simulation_summary.html')

@app.route("/testing")
def testing():
    return render_template("testing.html")
    
if __name__ == '__main__':
    app.run(debug=True)