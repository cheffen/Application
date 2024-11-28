import os
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
from pymongo import MongoClient
from bson.objectid import ObjectId
from bson.errors import InvalidId

def create_app():
    app = Flask(__name__)
    app.config['UPLOAD_FOLDER'] = 'static/images/'
    app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
    app.secret_key = 'your_secret_key'  # Needed for secure sessions (e.g., flash messages)

    # Create the upload folder if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Read the MongoDB URI from the environment variable or use the default
    # Ensure it uses 'localhost' to connect to MongoDB within the same pod
    mongo_uri = os.environ.get('MONGO_URI', 'mongodb://mongo:27017/artist_db')
    client = MongoClient(mongo_uri)

    db = client.get_default_database()
    collection = db['artists']

    def allowed_file(filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

    @app.route('/')
    def index():
        artists = collection.find().limit(3)
        artists = list(artists)  # Convert cursor to list to allow indexing
        for artist in artists:
            artist['_id'] = str(artist['_id'])
        return render_template('index.html', artists=artists)

    @app.route('/artists/')
    def artists():
        artists = collection.find()
        artists = list(artists)
        for artist in artists:
            artist['_id'] = str(artist['_id'])
        return render_template('artists.html', artists=artists)

    @app.route('/artist/<artist_id>')
    def artist(artist_id):
        try:
            artist = collection.find_one({'_id': ObjectId(artist_id)})
        except InvalidId:
            return "Invalid artist ID", 400
        if artist:
            # Convert _id to string for consistency in templates
            artist['_id'] = str(artist['_id'])
            return render_template('artist.html', artist=artist)
        else:
            return "Artist not found", 404

    @app.route('/add_artist', methods=['GET', 'POST'])
    def add_artist():
        if request.method == 'POST':
            name = request.form['name']
            genre = request.form['genre']
            bio = request.form['bio']

            # Generate a unique ObjectId for the artist
            artist_id = ObjectId()

            # Handle the image upload
            if 'image' not in request.files:
                return "No image part", 400
            file = request.files['image']
            if file.filename == '':
                return "No selected image", 400
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Append the ObjectId to the filename to ensure uniqueness
                filename = f"{artist_id}_{filename}"
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(image_path)
            else:
                return "Invalid image file", 400

            # Handle songs
            songs = []
            song_titles = request.form.getlist('song_title[]')
            song_links = request.form.getlist('song_link[]')
            for title, link in zip(song_titles, song_links):
                songs.append({'title': title, 'link': link})

            # Insert the new artist into the database with the assigned ObjectId
            collection.insert_one({
                '_id': artist_id,
                'name': name,
                'genre': genre,
                'bio': bio,
                'image': filename,
                'songs': songs
            })

            return redirect(url_for('artists'))

        return render_template('add_artist.html')

    @app.route('/about')
    def about():
        return render_template('about.html')

    @app.route('/contact')
    def contact():
        return render_template('contact.html')

    # Route to serve uploaded images
    @app.route('/static/images/<filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    # Insert Demo Artists if Collection is Empty
    if collection.count_documents({}) == 0:
        demo_artists = [
            {
                '_id': ObjectId(),
                'name': 'Taylor Swift',
                'genre': 'Pop',
                'bio': 'An American singer-songwriter known for narrative songs.',
                'image': 'taylor_swift.jpg',
                'songs': [
                    {'title': 'Love Story', 'link': 'https://example.com/love_story'},
                    {'title': 'Blank Space', 'link': 'https://example.com/blank_space'}
                ]
            },
            {
                '_id': ObjectId(),
                'name': 'Ed Sheeran',
                'genre': 'Singer-Songwriter',
                'bio': 'A British singer-songwriter known for his acoustic guitar performances.',
                'image': 'ed_sheeran.jpg',
                'songs': [
                    {'title': 'Shape of You', 'link': 'https://example.com/shape_of_you'},
                    {'title': 'Perfect', 'link': 'https://example.com/perfect'}
                ]
            },
            {
                '_id': ObjectId(),
                'name': 'Beyoncé',
                'genre': 'R&B',
                'bio': 'An American singer, songwriter, and actress, known for her powerful vocals.',
                'image': 'beyonce.jpg',
                'songs': [
                    {'title': 'Halo', 'link': 'https://example.com/halo'},
                    {'title': 'Crazy in Love', 'link': 'https://example.com/crazy_in_love'}
                ]
            },
            {
                '_id': ObjectId(),
                'name': 'Bruno Mars',
                'genre': 'Pop',
                'bio': 'An American singer-songwriter known for his stage performances.',
                'image': 'bruno_mars.jpg',
                'songs': [
                    {'title': 'Uptown Funk', 'link': 'https://example.com/uptown_funk'},
                    {'title': 'Just the Way You Are', 'link': 'https://example.com/just_the_way_you_are'}
                ]
            },
            {
                '_id': ObjectId(),
                'name': 'Holy Temple',
                'genre': 'Experimental',
                'bio': 'An enigmatic artist shrouded in mystery, known for avant-garde performances.',
                'image': 'holy_temple.jpg',
                'songs': [
                    {'title': 'Mystic Dawn', 'link': 'https://example.com/mystic_dawn'},
                    {'title': 'Echoes of Silence', 'link': 'https://example.com/echoes_of_silence'}
                ]
            },
            # Add more artists as needed
        ]
        # Update image filenames to include the artist's ObjectId
        for artist in demo_artists:
            artist['_id'] = ObjectId()
            artist['image'] = f"{artist['_id']}_{artist['image']}"
        collection.insert_many(demo_artists)
        print("Inserted demo artists into the database.")

        # Copy demo images to the upload folder
        for artist in demo_artists:
            src_image_path = os.path.join('demo_images', artist['image'].split('_', 1)[1])  # Original filename
            dest_image_path = os.path.join(app.config['UPLOAD_FOLDER'], artist['image'])
            if os.path.exists(src_image_path):
                # Copy the image to the upload folder with the new filename
                from shutil import copyfile
                copyfile(src_image_path, dest_image_path)
            else:
                print(f"Demo image {src_image_path} not found.")

    # Store the database in app config for access in other parts of the app
    app.config['db'] = db

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0')
