# Use the official Python image
FROM python:3.9

# Set the working directory
WORKDIR /code

# Copy the requirements file
COPY ./requirements.txt /code/requirements.txt

# Install the dependencies
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copy the application code
COPY . /code

# Create the data directory and set permissions (Hugging Face runs as user 1000)
RUN mkdir -p /code/data && chmod 777 /code/data

# Command to run the application
CMD ["gunicorn", "-b", "0.0.0.0:7860", "app:app"]
