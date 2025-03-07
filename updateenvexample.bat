@echo off
echo # Core credentials > .env.example
echo API_KEY=your_api_key_here >> .env.example
echo DB_PASSWORD=your_database_password >> .env.example
echo SECRET_TOKEN=your_secret_token >> .env.example
echo. >> .env.example
echo # API service credentials >> .env.example
echo MAIL_API_KEY=your_mail_api_key_here >> .env.example
echo LOGGING_API_KEY=your_logging_api_key_here >> .env.example
echo ANALYTICS_API_KEY=your_analytics_api_key_here >> .env.example
echo PAYMENT_API_KEY=your_payment_api_key_here >> .env.example
echo MOVIE_DB_API_KEY=your_movie_db_api_key_here >> .env.example
echo USER_MGMT_API_KEY=your_user_management_api_key_here >> .env.example
echo CDN_API_KEY=your_cdn_api_key_here >> .env.example
echo. >> .env.example
echo # STIX/TAXII integration >> .env.example
echo TAXII_SERVER_URL=https://taxii.example.com >> .env.example
echo TAXII_USERNAME=your_taxii_username >> .env.example
echo TAXII_PASSWORD=your_taxii_password >> .env.example
echo TAXII_COLLECTION_ID=your_collection_id >> .env.example 