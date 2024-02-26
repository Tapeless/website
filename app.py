import os
from flask import Flask, render_template, request, redirect, url_for
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

app = Flask(__name__)

sendgrid_key = os.environ.get('SENDGRID_KEY')
from_email = os.environ.get('EMAIL_ADDR')
to_email = os.environ.get('MY_EMAIL_ADDR')

mail = Mail(app)

def get_posts(category: str=None):
    current_directory = os.getcwd()
    directory = os.path.join(current_directory,'templates', category)
    posts = [f for f in os.listdir(directory) if f.endswith('.html')]
    return posts

def get_objs():
    current_directory = os.getcwd()
    directory = os.path.join(current_directory, 'static', 'objects')
    objs = [f for f in os.listdir(directory) if f.endswith('.obj')]
    return objs

@app.route('/')
def home():
    blog_posts = get_posts('blog')
    career_posts = get_posts('career')
    page_posts = get_posts('pages')
    return render_template('index.html', blog_posts=blog_posts, career_posts=career_posts, page_posts=page_posts)

@app.route('/blog/<post_name>')
def blog_post(post_name):
    return render_template(f'blog/{post_name}')

@app.route('/career/<post_name>')
def career(post_name):
    return render_template(f'career/{post_name}')

@app.route('/pages/<post_name>')
def page(post_name):
    if post_name == '3d_landing.html':
        return redirect(url_for('obj_landing'))
    return render_template(f'pages/{post_name}')

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        message = request.form.get('message')
        send_email(message)
        
        return '<div class="feedback-response">Your message was successfully sent. Thank you!! (✿❛‿❛✿)</div>'
    return render_template('feedback.html')

@app.route('/3d_landing')
def obj_landing():
    objs = get_objs()
    return render_template('pages/3d_landing.html', objs=objs)

@app.route('/3d/<obj>')
def obj_viewer(obj):
    obj_name = obj.replace('_', ' ').split('.')[0]
    mtl = obj.replace('.obj','.mtl')
    return render_template('3d_template.html', obj=obj, obj_name=obj_name, mtl=mtl)

@app.route('/modelviewer')
def view_model():
    return render_template('test.html')


def send_email(content):
    message = Mail(
        from_email=from_email,
        to_emails=to_email,
        subject='Site Feedback',
        plain_text_content=content)
    
    try:
        sg = SendGridAPIClient(sendgrid_key)  # Use your SendGrid API Key
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(e.message)
