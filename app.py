import os
import boto3
import hashlib
import random
from flask import Flask, render_template, request, redirect, url_for
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail



app = Flask(__name__)

sendgrid_key = os.environ.get('SENDGRID_KEY')
from_email = os.environ.get('EMAIL_ADDR')
to_email = os.environ.get('MY_EMAIL_ADDR')
s3_key = os.environ.get('S3_KEY')
s3_secret = os.environ.get('S3_SECRET')
bucketname = os.environ.get('S3_BUCKET')

s3 = boto3.client('s3', aws_access_key_id=s3_key, aws_secret_access_key=s3_secret)
def calculate_file_md5(filename):
    hash_md5 = hashlib.md5()
    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def get_site_files(s3, bucketname, max_size_mb=10):
    max_size_bytes = max_size_mb * 1024 * 1024  # Convert MB to bytes
    s3_objs = s3.list_objects_v2(Bucket=bucketname, Prefix='site/')
    
    if 'Contents' not in s3_objs:
        app.logger.info("No files found in the bucket.")
        return
    
    for obj in s3_objs['Contents']:
        # Skip if file size is larger than 10MB
        if obj['Size'] > max_size_bytes:
            app.logger.info(f"Skipped {obj['Key']} due to size (> {max_size_mb}MB).")
            continue

        local_filename = obj['Key'].replace('site/', '', 1)
        local_dir = os.path.dirname(local_filename)

        # Ensure the local directory exists
        if not os.path.exists(local_dir):
            os.makedirs(local_dir)

        # If the file exists locally, compare MD5; else, download
        if os.path.exists(local_filename):
            local_md5 = calculate_file_md5(local_filename)
            s3_etag = obj['ETag'].strip('"')

            if local_md5 != s3_etag:
                s3.download_file(bucketname, obj['Key'], local_filename)
                app.logger.info(f"Downloaded {local_filename} - local version differed.")
            else:
                app.logger.info(f"Skipped {local_filename} - local version is identical.")
        else:
            s3.download_file(bucketname, obj['Key'], local_filename)
            app.logger.info(f"Downloaded {local_filename} - did not exist locally.")


app.logger.info('getting site files...')
get_site_files(s3, bucketname)   
app.logger.info('site files acquired!')

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

def get_pet_imgs():
    current_directory = os.getcwd()
    directory = os.path.join(current_directory, 'static', 'images', 'pet_imgs')
    pet_pics = [f for f in os.listdir(directory) if f.endswith('.png')]
    return pet_pics

pet_pics = get_pet_imgs()

@app.route('/')
def home():
    blog_posts = get_posts('blog')
    career_posts = get_posts('career')
    page_posts = get_posts('pages')
    pet_pic = 'images/pet_imgs/'+random.choice(pet_pics)
    return render_template('index.html', blog_posts=blog_posts, career_posts=career_posts, page_posts=page_posts, pet_pic=pet_pic)

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
        app.logger.info(response.status_code)
        app.logger.info(response.body)
        app.logger.info(response.headers)
    except Exception as e:
        app.logger.info(e.message)
