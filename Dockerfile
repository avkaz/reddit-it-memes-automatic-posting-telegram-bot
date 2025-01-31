# Use an official Python runtime as a parent docker ps -aimage
FROM python:3.10.4

# Set the working directory to /app
WORKDIR /app1

# Copy the current directory contents into the container at /app
COPY requirements.txt /app1

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install ffmpeg
RUN apt-get update && \
    apt-get install -y ffmpeg \
    && rm -rf /var/lib/apt/lists/*




COPY . /app1

# Make port available to the world outside this container
CMD ["python", "main.py"]
