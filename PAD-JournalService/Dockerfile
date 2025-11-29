FROM php:8.2-cli

# Install MySQL extensions
RUN docker-php-ext-install mysqli pdo pdo_mysql

# Copy application files
COPY . /var/www/html/

# Set working directory
WORKDIR /var/www/html

# Expose port
EXPOSE 3004

# Start PHP built-in server
CMD ["php", "-S", "0.0.0.0:3004"]