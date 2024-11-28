import os
import pytest # type: ignore
from flask import Flask
from io import BytesIO

@pytest.fixture(scope='module')
def client():
    # Set the MONGO_URI environment variable to point to the test database
    os.environ['MONGO_URI'] = 'mongodb://mongo:27017/test_artist_db'

    # Import the Flask app using the application factory
    from app import create_app
    flask_app = create_app()
    testing_client = flask_app.test_client()

    # Establish an application context before running the tests.
    ctx = flask_app.app_context()
    ctx.push()

    # Initialize the test database with sample data
    collection = flask_app.config['db']['artists']
    collection.delete_many({})  # Ensure the collection is empty before tests
    collection.insert_many([
        {
            'name': 'Test Artist 1',
            'genre': 'Test Genre 1',
            'bio': 'Bio for Test Artist 1',
            'image': 'test_artist_1.jpg',
            'songs': [
                {'title': 'Test Song 1', 'link': 'https://example.com/test_song_1'}
            ]
        },
        {
            'name': 'Test Artist 2',
            'genre': 'Test Genre 2',
            'bio': 'Bio for Test Artist 2',
            'image': 'test_artist_2.jpg',
            'songs': [
                {'title': 'Test Song 2', 'link': 'https://example.com/test_song_2'}
            ]
        },
    ])

    yield testing_client  # this is where the testing happens!

    # Clean up: Drop the test database after tests
    collection.drop()
    ctx.pop()

def test_index(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'Test Artist 1' in response.data or b'Taylor Swift' in response.data  # Depending on which data is displayed

def test_artists(client):
    response = client.get('/artists/')
    assert response.status_code == 200
    assert b'Test Artist 1' in response.data
    assert b'Test Artist 2' in response.data

def test_artist_detail(client):
    # Get the artist ID for 'Test Artist 1'
    collection = client.application.config['db']['artists']
    artist = collection.find_one({'name': 'Test Artist 1'})
    artist_id = str(artist['_id'])
    response = client.get(f'/artist/{artist_id}')
    assert response.status_code == 200
    assert b'Test Artist 1' in response.data

def test_add_artist(client):
    data = {
        'name': 'Test Artist 3',
        'genre': 'Test Genre 3',
        'bio': 'Bio for Test Artist 3',
        'song_title[]': ['Test Song 3'],
        'song_link[]': ['https://example.com/test_song_3']
    }

    # Open the image file
    image_path = 'static/images/test_artist_3.jpg'
    with open(image_path, 'rb') as img_file:
        data['image'] = (img_file, 'test_artist_3.jpg')

        response = client.post('/add_artist', data=data, content_type='multipart/form-data', follow_redirects=True)
        assert response.status_code == 200
        assert b'Test Artist 3' in response.data

    # Retrieve the artist from the database to get the '_id'
    collection = client.application.config['db']['artists']
    artist = collection.find_one({'name': 'Test Artist 3'})
    assert artist is not None, "Artist not found in database after POST request"

    # Construct the uploaded image filename
    uploaded_image_filename = f"{artist['_id']}_test_artist_3.jpg"
    uploaded_image_path = os.path.join(client.application.config['UPLOAD_FOLDER'], uploaded_image_filename)
    if os.path.exists(uploaded_image_path):
        os.remove(uploaded_image_path)
