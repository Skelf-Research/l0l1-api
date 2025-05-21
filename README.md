# l0l1 - SQL Analysis and Collaboration Platform

> **⚠️ Project Status: Work in Progress**
>
> This project is currently under active development. Features, setup instructions, and documentation may change frequently. Use at your own risk and feel free to contribute!

l0l1 is a platform for data analysts to analyze SQL schemas and queries, collaborate on insights, and leverage AI-powered features for query completion and explanation.

## Setup (Early Preview)

1. Clone the repository:
   ```
   git clone https://github.com/shakydata/l0l1.git
   cd l0l1
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```
   export FLASK_APP=run.py
   export OPENAI_API_KEY=your_openai_api_key
   export JWT_SECRET_KEY=your_jwt_secret_key
   ```

5. Initialize the database and create an admin user:
   ```
   flask init-db
   flask create-admin admin admin@example.com
   ```

## Running the Application (Alpha)

1. Start the Redis server (for background tasks):
   ```
   redis-server
   ```

2. In a new terminal, start the Dramatiq workers:
   ```
   dramatiq app.tasks
   ```

3. In another terminal, start the Flask application:
   ```
   flask run
   ```

4. Open a web browser and navigate to `http://localhost:5000` to access the l0l1 dashboard.

## Running Tests

To run the tests, use the following command:
```
pytest
```

## Contributing

Please read CONTRIBUTING.md for details on our code of conduct and the process for submitting pull requests. All contributions are welcome, especially as the project is in its early stages.

## License

This project is licensed under the MIT License - see the LICENSE.md file for details.