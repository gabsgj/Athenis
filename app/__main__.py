from app.app import create_app
import os

if __name__ == '__main__':
    app = create_app()
    port = int(os.getenv("PORT", "8080"))
    debug = os.getenv("FLASK_DEBUG") == "1"
    app.run(host='0.0.0.0', port=port, debug=debug)
