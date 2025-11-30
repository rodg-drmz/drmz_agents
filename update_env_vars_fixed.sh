#!/bin/bash
# Safe auto-replacement of environment variable names

echo 'Updating .env file...'

sed -i '' 's/^MODEL=/DRMZ_MODEL_NAME=/' .env
sed -i '' 's/^OPENAI_API_KEEY=/DRMZ_OPENAI_API_KEY=/' .env
sed -i '' 's/^SERPER_API_KEEY=/DRMZ_SERPER_API_KEY=/' .env
sed -i '' 's/^SGAI_API_KEEY=/DRMZ_SGAI_API_KEY=/' .env
sed -i '' 's/^TWITTER_API_KEEY=/DRMZ_TWITTER_API_KEY=/' .env
sed -i '' 's/^TWITTER_API_SECREET=/DRMZ_TWITTER_API_SECRET=/' .env
sed -i '' 's/^TWITTER_ACCESS_TOKEEN=/DRMZ_TWITTER_ACCESS_TOKEN=/' .env
sed -i '' 's/^TWITTER_ACCESS_TOKEEN_SECREET=/DRMZ_TWITTER_ACCESS_TOKEN_SECRET=/' .env
sed -i '' 's/^PYTHONPATH=/DRMZ_PYTHONPATH=/' .env
sed -i '' 's/^DISCORD_BOT_TOKEEN=/DRMZ_DISCORD_BOT_TOKEN=/' .env
sed -i '' 's/^MORPHEUS_API_URL=/DRMZ_MORPHEUS_API_URL=/' .env
sed -i '' 's/^ANVIL_API_URL=/DRMZ_ANVIL_API_URL=/' .env

echo 'Updating Python files recursively...'

find . -type f -name '*.py' -exec sed -i '' 's/os.getenv([\"'\'']MODEL[\"'\''])/os.getenv("DRMZ_MODEL_NAME")/g' {} +
find . -type f -name '*.py' -exec sed -i '' 's/os.getenv([\"'\'']OPENAI_API_KEEY[\"'\''])/os.getenv("DRMZ_OPENAI_API_KEY")/g' {} +
find . -type f -name '*.py' -exec sed -i '' 's/os.getenv([\"'\'']SERPER_API_KEEY[\"'\''])/os.getenv("DRMZ_SERPER_API_KEY")/g' {} +
find . -type f -name '*.py' -exec sed -i '' 's/os.getenv([\"'\'']SGAI_API_KEEY[\"'\''])/os.getenv("DRMZ_SGAI_API_KEY")/g' {} +
find . -type f -name '*.py' -exec sed -i '' 's/os.getenv([\"'\'']TWITTER_API_KEEY[\"'\''])/os.getenv("DRMZ_TWITTER_API_KEY")/g' {} +
find . -type f -name '*.py' -exec sed -i '' 's/os.getenv([\"'\'']TWITTER_API_SECREET[\"'\''])/os.getenv("DRMZ_TWITTER_API_SECRET")/g' {} +
find . -type f -name '*.py' -exec sed -i '' 's/os.getenv([\"'\'']TWITTER_ACCESS_TOKEEN[\"'\''])/os.getenv("DRMZ_TWITTER_ACCESS_TOKEN")/g' {} +
find . -type f -name '*.py' -exec sed -i '' 's/os.getenv([\"'\'']TWITTER_ACCESS_TOKEEN_SECREET[\"'\''])/os.getenv("DRMZ_TWITTER_ACCESS_TOKEN_SECRET")/g' {} +
find . -type f -name '*.py' -exec sed -i '' 's/os.getenv([\"'\'']PYTHONPATH[\"'\''])/os.getenv("DRMZ_PYTHONPATH")/g' {} +
find . -type f -name '*.py' -exec sed -i '' 's/os.getenv([\"'\'']DISCORD_BOT_TOKEEN[\"'\''])/os.getenv("DRMZ_DISCORD_BOT_TOKEN")/g' {} +
find . -type f -name '*.py' -exec sed -i '' 's/os.getenv([\"'\'']MORPHEUS_API_URL[\"'\''])/os.getenv("DRMZ_MORPHEUS_API_URL")/g' {} +
find . -type f -name '*.py' -exec sed -i '' 's/os.getenv([\"'\'']ANVIL_API_URL[\"'\''])/os.getenv("DRMZ_ANVIL_API_URL")/g' {} +

echo '✅ All done!'
