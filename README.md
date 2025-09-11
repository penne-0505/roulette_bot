# Roulette DS Bot

## Docker Deployment

1. **Build the image**

   ```bash
   docker build -t roulette-bot .
   ```

2. **Run the container**:

   ```bash
   docker run -e CLIENT_TOKEN=<your_token> \
              -e FIREBASE_CREDENTIALS=<your_credentials_url> \
              -p 8000:8000 \
              roulette-bot
   ```

3. **Alternatively, use docker-compose**

   ```bash
   docker-compose up --build
   ```

Make sure the environment variables `CLIENT_TOKEN` and `FIREBASE_CREDENTIALS` are set with valid values before running the container.
