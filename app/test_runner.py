from app.app import app

if __name__ == '__main__':
    app.testing = True
    client = app.test_client()
    res = client.get('/api/v1/health')
    print(res.json)
